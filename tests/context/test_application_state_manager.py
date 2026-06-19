import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.context.application_state_manager import ApplicationStateManager
from src.context.window_manager import WindowManager

@pytest.fixture
def mock_wm():
    wm = MagicMock(spec=WindowManager)
    wm.find_window.return_value = None
    wm.get_active_window.return_value = None
    return wm

@pytest.fixture
def state_manager(mock_wm):
    return ApplicationStateManager(window_manager=mock_wm)

def test_initial_state(state_manager):
    assert state_manager.get_current_active_app() is None
    assert state_manager.get_last_active_app() is None
    assert state_manager.is_running("steam") is False
    assert state_manager.is_window_open("steam") is False
    assert state_manager.is_focused("steam") is False

@patch("src.context.application_state_manager.psutil")
def test_refresh_app_state_running_and_window(mock_psutil, state_manager, mock_wm):
    # Setup process
    mock_proc = MagicMock()
    mock_proc.info = {"name": "steam.exe"}
    mock_psutil.process_iter.return_value = [mock_proc]
    
    # Setup window
    mock_wm.find_window.return_value = {
        "title": "Steam",
        "is_active": False,
        "is_minimized": False
    }
    
    state_manager.refresh_app_state("steam")
    
    assert state_manager.is_running("steam") is True
    assert state_manager.is_window_open("steam") is True
    assert state_manager.is_focused("steam") is False
    assert state_manager.get_app_state("steam")["window_title"] == "Steam"
    assert isinstance(state_manager.get_app_state("steam")["last_seen"], datetime)

@patch("src.context.application_state_manager.psutil")
def test_refresh_app_state_focused(mock_psutil, state_manager, mock_wm):
    mock_proc = MagicMock()
    mock_proc.info = {"name": "discord.exe"}
    mock_psutil.process_iter.return_value = [mock_proc]
    
    mock_wm.find_window.return_value = {
        "title": "Discord",
        "is_active": True,
        "is_minimized": False
    }
    
    state_manager.refresh_app_state("discord")
    
    assert state_manager.is_focused("discord") is True
    assert state_manager.get_current_active_app() == "discord"

def test_mark_focused_shifts_active_apps(state_manager):
    state_manager.mark_focused("steam")
    assert state_manager.is_focused("steam") is True
    assert state_manager.get_current_active_app() == "steam"
    assert state_manager.get_last_active_app() is None
    
    state_manager.mark_focused("discord")
    assert state_manager.is_focused("steam") is False
    assert state_manager.is_focused("discord") is True
    assert state_manager.get_current_active_app() == "discord"
    assert state_manager.get_last_active_app() == "steam"

def test_refresh_active_window(state_manager, mock_wm):
    mock_wm.get_active_window.return_value = {
        "title": "Microsoft Word",
        "process_name": "winword.exe"
    }
    
    state_manager.refresh_active_window()
    
    assert state_manager.get_current_active_app() == "word"
    assert state_manager.is_focused("word") is True

@patch("src.context.application_state_manager.psutil")
def test_refresh_all(mock_psutil, state_manager, mock_wm):
    mock_proc = MagicMock()
    mock_proc.info = {"name": "code.exe"}
    mock_psutil.process_iter.return_value = [mock_proc]
    
    def side_effect(app_name):
        if app_name == "vscode":
            return {"title": "Visual Studio Code", "is_active": True, "is_minimized": False}
        return None
        
    mock_wm.find_window.side_effect = side_effect
    
    mock_wm.get_active_window.return_value = {
        "title": "Visual Studio Code",
        "process_name": "code.exe"
    }
    
    state_manager.refresh_all()
    
    # Should have scanned APP_WINDOW_ALIASES
    assert state_manager.is_running("vscode") is True
    assert state_manager.is_window_open("vscode") is True
    assert state_manager.is_focused("vscode") is True
    assert state_manager.get_current_active_app() == "vscode"
