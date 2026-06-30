from unittest.mock import MagicMock
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.automation.executor import Executor
from src.tools.registry import ToolRegistry
from src.context.application_state_manager import ApplicationStateManager
from src.context.context_manager import ContextManager

class TestContextInspection:
    def setup_method(self):
        self.registry_mock = MagicMock(spec=ToolRegistry)
        self.state_manager_mock = MagicMock(spec=ApplicationStateManager)
        self.context_manager_mock = MagicMock(spec=ContextManager)
        
        self.executor = Executor(
            registry=self.registry_mock,
            state_manager=self.state_manager_mock,
            context_manager=self.context_manager_mock
        )

    def test_get_current_app(self):
        self.state_manager_mock.get_current_active_app.return_value = "discord"
        result = self.executor.execute({"action": "get_current_app"})
        
        self.state_manager_mock.refresh_active_window.assert_called_once()
        assert result["status"] == "success"
        assert "discord" in result["message"]

    def test_get_current_app_none(self):
        self.state_manager_mock.get_current_active_app.return_value = None
        result = self.executor.execute({"action": "get_current_app"})
        
        assert result["status"] == "success"
        assert "No active application tracked" in result["message"]

    def test_get_previous_app(self):
        self.state_manager_mock.get_last_active_app.return_value = "steam"
        result = self.executor.execute({"action": "get_previous_app"})
        
        assert result["status"] == "success"
        assert "steam" in result["message"]

    def test_get_previous_app_none(self):
        self.state_manager_mock.get_last_active_app.return_value = None
        result = self.executor.execute({"action": "get_previous_app"})
        
        assert result["status"] == "success"
        assert "No previous application available" in result["message"]

    def test_get_opened_history(self):
        self.context_manager_mock.get_open_history.return_value = ["steam", "discord"]
        result = self.executor.execute({"action": "get_opened_history"})
        
        assert result["status"] == "success"
        assert "1. steam" in result["message"]
        assert "2. discord" in result["message"]

    def test_get_opened_history_empty(self):
        self.context_manager_mock.get_open_history.return_value = []
        result = self.executor.execute({"action": "get_opened_history"})
        
        assert result["status"] == "success"
        assert "No apps have been opened yet" in result["message"]

    def test_get_focused_history(self):
        self.context_manager_mock.get_focus_history.return_value = ["whatsapp"]
        result = self.executor.execute({"action": "get_focused_history"})
        
        assert result["status"] == "success"
        assert "1. whatsapp" in result["message"]

    def test_get_closed_history(self):
        self.context_manager_mock.get_close_history.return_value = ["calculator"]
        result = self.executor.execute({"action": "get_closed_history"})
        
        assert result["status"] == "success"
        assert "1. calculator" in result["message"]

    def test_debug_state(self):
        self.state_manager_mock.states = {
            "steam": {"running": True, "window_open": True, "focused": False}
        }
        result = self.executor.execute({"action": "debug_state"})
        
        self.state_manager_mock.refresh_all.assert_called_once()
        assert result["status"] == "success"
        assert "State Snapshot:" in result["message"]
        assert "steam" in result["message"]
        assert "true" in result["message"].lower()
