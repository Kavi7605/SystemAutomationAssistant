import pytest
from unittest.mock import MagicMock
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
from src.context.window_manager import WindowManager

class TestContextSynchronizationRegression:
    def setup_method(self):
        self.parser_mock = MagicMock(spec=CommandParser)
        self.resolver_mock = MagicMock(spec=CommandResolver)
        self.task_planner_mock = MagicMock(spec=TaskPlanner)
        self.history_manager_mock = MagicMock(spec=HistoryManager)
        
        self.registry_mock = MagicMock(spec=ToolRegistry)
        self.registry_mock.execute_tool.return_value = {"status": "success", "message": "Simulated tool execution"}
        
        self.window_manager_mock = MagicMock(spec=WindowManager)
        self.window_manager_mock.find_window.return_value = None
        self.window_manager_mock.get_active_window.return_value = None
        
        self.state_manager = ApplicationStateManager(self.window_manager_mock)
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

    def test_focus_typo_stores_canonical_name(self):
        # User focuses 'whatsap'
        self.engine.process_command("focus whatsap")
        
        # Check history via command
        self.executor.execute({"action": "get_focused_history"})
        history = self.context_manager.get_focus_history()
        
        # It must be whatsapp, not whatsap
        assert "whatsapp" in history
        assert "whatsap" not in history
        
        # Current app should be whatsapp
        assert self.context_manager.get_context_snapshot()["current_active_app"] == "whatsapp"

    def test_current_and_previous_app_sync(self):
        # Focus steam
        self.engine.process_command("focus steam")
        
        # Focus discord
        self.engine.process_command("focus discord")
        
        # The ApplicationStateManager is the source of truth for current app retrieval.
        # It asks window_manager.get_active_window(). We mock it so it returns discord.
        self.window_manager_mock.get_active_window.return_value = {"title": "Discord", "process_name": "discord.exe"}
        
        result_current = self.executor.execute({"action": "get_current_app"})
        assert "discord" in result_current["message"]
        
        # Previous app retrieval
        # Since last active app was steam according to ContextManager's focused_apps logic?
        # Actually ApplicationStateManager tracks current_active_app and last_active_app through mark_focused
        # and refresh_active_window.
        result_previous = self.executor.execute({"action": "get_previous_app"})
        assert "steam" in result_previous["message"]
