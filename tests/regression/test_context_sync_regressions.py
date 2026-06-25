import pytest
from unittest.mock import MagicMock, patch
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.automation.engine import AutomationEngine
from src.core.command_parser import CommandParser
from src.core.history_manager import HistoryManager
from src.planner.resolver import CommandResolver
from src.planner.task_planner import TaskPlanner
from src.automation.executor import Executor
from src.tools.registry import ToolRegistry
from src.context.application_state_manager import ApplicationStateManager
from src.context.context_manager import ContextManager
from src.tools.system_control.window_tools import WindowManager

class TestContextSynchronizationRegression:
    def setup_method(self):
        self.parser_mock = MagicMock(spec=CommandParser)
        self.resolver_mock = MagicMock(spec=CommandResolver)
        self.task_planner_mock = MagicMock(spec=TaskPlanner)
        self.history_manager_mock = MagicMock(spec=HistoryManager)
        
        self.registry_mock = MagicMock(spec=ToolRegistry)
        self.registry_mock.execute_tool.return_value = {"status": "success", "message": "Simulated tool execution"}
        
        self.state_manager = ApplicationStateManager()
        self.context_manager = ContextManager()
        
        self.executor = Executor(
            registry=self.registry_mock,
            state_manager=self.state_manager,
            context_manager=self.context_manager
        )
        
        self.engine = AutomationEngine(
            parser=self.parser_mock,
            resolver=self.resolver_mock,
            task_planner=self.task_planner_mock,
            executor=self.executor,
            history_manager=self.history_manager_mock,
            context_manager=self.context_manager
        )

    @patch("src.context.application_state_manager.WindowManager")
    def test_focus_typo_stores_canonical_name(self, mock_wm):
        mock_wm.find_windows.return_value = [{"title": "WhatsApp", "hwnd": 123}]
        # First check returns Discord (so it executes), second check returns WhatsApp (after focus)
        mock_wm.get_current_window.side_effect = [
            {"hwnd": 456, "title": "Discord", "app_name": "discord"},
            {"hwnd": 123, "title": "WhatsApp", "app_name": "whatsapp"},
            {"hwnd": 123, "title": "WhatsApp", "app_name": "whatsapp"}
        ]
        
        self.engine.process_command("focus whatsap")
        self.executor.execute({"action": "get_focused_history"})
        history = self.context_manager.get_focus_history()
        
        assert "whatsapp" in history
        assert "whatsap" not in history
        assert self.context_manager.get_context_snapshot()["current_active_app"] == "whatsapp"

    @patch("src.context.application_state_manager.WindowManager")
    def test_current_and_previous_app_sync(self, mock_wm):
        self.engine.process_command("focus steam")
        self.engine.process_command("focus discord")
        
        mock_wm.get_current_window.return_value = {"title": "Discord", "app_name": "discord", "hwnd": 123}
        
        result_current = self.executor.execute({"action": "get_current_app"})
        assert "discord" in result_current["message"]
        
        result_previous = self.executor.execute({"action": "get_previous_app"})
        assert "steam" in result_previous["message"]

    def test_context_action_tracking(self):
        self.registry_mock.execute_tool.return_value = {"status": "failed", "message": "Simulated failure"}
        res1 = self.executor.execute({"action": "open_application", "parameters": {"application_name": "unknown_app"}})
        assert res1.get("status") == "failed"
        assert self.context_manager.state["last_failed_action"] == "open_application"
        assert self.context_manager.state.get("last_successful_action") is None
        
        self.registry_mock.execute_tool.return_value = {"status": "success", "message": "Worked"}
        res2 = self.executor.execute({"action": "dummy_action", "parameters": {}})
        assert res2.get("status") == "success"
        
        assert self.context_manager.state["last_successful_action"] == "dummy_action"
        assert self.context_manager.state.get("last_failed_action") is None
