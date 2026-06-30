from unittest.mock import MagicMock
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.automation.executor import Executor
from src.tools.registry import ToolRegistry
from src.context.application_state_manager import ApplicationStateManager
from src.context.context_manager import ContextManager


class TestStateAwareExecution:
    def setup_method(self):
        self.registry_mock = MagicMock(spec=ToolRegistry)
        self.state_manager_mock = MagicMock(spec=ApplicationStateManager)
        self.context_manager_mock = MagicMock(spec=ContextManager)
        
        # Tools always return success if actually called
        self.registry_mock.execute_tool.return_value = {"status": "success", "message": "Action executed via ToolRegistry"}
        
        self.executor = Executor(
            registry=self.registry_mock,
            state_manager=self.state_manager_mock,
            context_manager=self.context_manager_mock
        )

    def test_open_validation(self):
        # First call is_running returns False (needs to launch)
        # Next two calls is_running returns True (already running)
        self.state_manager_mock.is_running.side_effect = [False, True, True]
        
        commands = [
            {"action": "open_application", "parameters": {"application_name": "steam"}},
            {"action": "open_application", "parameters": {"application_name": "steam"}},
            {"action": "open_application", "parameters": {"application_name": "steam"}}
        ]
        
        result = self.executor.execute(commands)
        
        # Should refresh state 4 times (1 before each of the 3 commands, plus 1 after the first successful execution)
        assert self.state_manager_mock.refresh_app_state.call_count == 4
        
        # The registry tool should only be executed ONCE (for the first command)
        assert self.registry_mock.execute_tool.call_count == 1
        
        # Check execution statuses
        assert result["status"] == "completed"
        assert result["successful"] == 3
        
        # Check specific messages
        assert "Action executed" in result["results"][0]["result"]["message"]
        assert "Steam is already running" in result["results"][1]["result"]["message"]
        assert "Steam is already running" in result["results"][2]["result"]["message"]

    def test_close_validation(self):
        # First call is_running returns True (needs to close)
        # Next two calls is_running returns False (already closed)
        self.state_manager_mock.is_running.side_effect = [True, False, False]
        
        commands = [
            {"action": "close_application", "parameters": {"application_name": "steam"}},
            {"action": "close_application", "parameters": {"application_name": "steam"}},
            {"action": "close_application", "parameters": {"application_name": "steam"}}
        ]
        
        result = self.executor.execute(commands)
        
        # Should refresh state 4 times (1 before each of the 3 commands, plus 1 after the first successful execution)
        assert self.state_manager_mock.refresh_app_state.call_count == 4
        
        # The registry tool should only be executed ONCE (for the first command)
        assert self.registry_mock.execute_tool.call_count == 1
        
        # Check execution statuses
        assert result["status"] == "completed"
        assert result["successful"] == 3
        
        # Check specific messages
        assert "Action executed" in result["results"][0]["result"]["message"]
        assert "Steam is already closed" in result["results"][1]["result"]["message"]
        assert "Steam is already closed" in result["results"][2]["result"]["message"]

    def test_focus_validation(self):
        # First call is_focused returns False (needs to focus)
        # Next two calls is_focused returns True (already focused)
        self.state_manager_mock.is_focused.side_effect = [False, True, True]
        
        commands = [
            {"action": "focus_window", "parameters": {"window_name": "steam"}},
            {"action": "focus_window", "parameters": {"window_name": "steam"}},
            {"action": "focus_window", "parameters": {"window_name": "steam"}}
        ]
        
        result = self.executor.execute(commands)
        
        assert self.state_manager_mock.refresh_app_state.call_count == 3
        
        # The registry tool should only be executed ONCE (for the first command)
        assert self.registry_mock.execute_tool.call_count == 1
        
        # Check execution statuses
        assert result["status"] == "completed"
        assert result["successful"] == 3
        
        # Check specific messages
        assert "Action executed" in result["results"][0]["result"]["message"]
        assert "Steam is already focused" in result["results"][1]["result"]["message"]
        assert "Steam is already focused" in result["results"][2]["result"]["message"]

    def test_history_validation(self):
        # Execute open steam 3 times, with it already being open after the first
        self.state_manager_mock.is_running.side_effect = [False, True, True]
        
        commands = [
            {"action": "open_application", "parameters": {"application_name": "steam"}},
            {"action": "open_application", "parameters": {"application_name": "steam"}},
            {"action": "open_application", "parameters": {"application_name": "steam"}}
        ]
        
        self.executor.execute(commands)
        
        # The context_manager.mark_app_opened should be called 3 times
        # because we now record user intent even if execution is skipped
        assert self.context_manager_mock.mark_app_opened.call_count == 3
        self.context_manager_mock.mark_app_opened.assert_called_with("steam")
