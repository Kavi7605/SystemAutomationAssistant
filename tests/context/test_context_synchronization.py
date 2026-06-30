import pytest
from unittest.mock import patch
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.context.application_aliases import normalize_app_name
from src.context.context_manager import ContextManager
from src.context.application_state_manager import ApplicationStateManager

class TestContextSynchronization:
    
    @pytest.mark.parametrize("input_name, expected", [
        ("vscode", "vscode"),
        ("visual studio code", "vscode"),
        ("code", "vscode"),
        ("whatsap", "whatsapp"),  # Typo test
        ("steam", "steam"),
        ("discord", "discord"),
        ("google chrome", "chrome"),
        ("unknown_app", "unknown_app")
    ])
    def test_alias_and_typo_normalization(self, input_name, expected):
        assert normalize_app_name(input_name) == expected

    def test_context_manager_stores_normalized_names(self):
        cm = ContextManager()
        
        cm.mark_app_opened("whatsap")
        assert cm.get_last_opened_app() == "whatsapp"
        assert cm.get_open_history() == ["whatsapp"]
        
        cm.mark_app_focused("visual studio code")
        assert cm.get_last_focused_app() == "vscode"
        assert cm.get_focus_history() == ["vscode"]
        
        cm.mark_app_closed("google chrome")
        assert cm.get_last_closed_app() == "chrome"
        assert cm.get_close_history() == ["chrome"]

    @patch("src.context.application_state_manager.WindowManager")
    def test_state_manager_stores_normalized_names(self, mock_wm):
        mock_wm.find_windows.return_value = [{"title": "WhatsApp", "hwnd": 123}]
        mock_wm.get_current_window.return_value = {"hwnd": 123}
        
        sm = ApplicationStateManager()
        sm.refresh_app_state("whatsap")
        
        # State should be keyed by the normalized name
        assert "whatsapp" in sm.states
        assert sm.is_window_open("whatsap") == True

    def test_sync_active_apps(self):
        cm = ContextManager()
        
        cm.sync_active_apps("discord", "steam")
        
        snapshot = cm.get_context_snapshot()
        assert snapshot["current_active_app"] == "discord"
        assert snapshot["last_active_app"] == "steam"
