import pytest
from unittest.mock import MagicMock
from src.context.window_manager import WindowManager

@pytest.fixture
def mock_wm():
    wm = WindowManager()
    wm.gw = MagicMock()
    wm.psutil = MagicMock()
    wm.win32gui = MagicMock()
    wm.win32process = MagicMock()
    return wm

def test_get_active_window(mock_wm):
    mock_wm.win32gui.GetForegroundWindow.return_value = 12345
    mock_wm.win32gui.GetWindowText.return_value = "Discord"
    mock_wm.win32process.GetWindowThreadProcessId.return_value = (0, 9999)
    
    mock_process = MagicMock()
    mock_process.name.return_value = "discord.exe"
    mock_wm.psutil.Process.return_value = mock_process
    mock_wm.win32gui.IsIconic.return_value = 0
    
    result = mock_wm.get_active_window()
    assert result == {
        "title": "Discord",
        "process_name": "discord.exe",
        "is_minimized": False
    }

def test_get_active_window_none(mock_wm):
    mock_wm.win32gui.GetForegroundWindow.return_value = 0
    assert mock_wm.get_active_window() is None

def test_find_window_found(mock_wm):
    mock_win = MagicMock()
    mock_win.title = "Steam - Library"
    mock_win.isMinimized = False
    mock_win._hWnd = 54321
    
    mock_wm.gw.getAllWindows.return_value = [mock_win]
    mock_wm.win32gui.GetForegroundWindow.return_value = 54321
    
    result = mock_wm.find_window("steam")
    assert result == {
        "title": "Steam - Library",
        "matched_name": "steam",
        "is_active": True,
        "is_minimized": False
    }

def test_find_window_not_found(mock_wm):
    mock_wm.gw.getAllWindows.return_value = []
    assert mock_wm.find_window("steam") is None

def test_is_window_open(mock_wm):
    mock_win = MagicMock()
    mock_win.title = "Google Chrome"
    mock_wm.gw.getAllWindows.return_value = [mock_win]
    
    assert mock_wm.is_window_open("chrome") is True
    assert mock_wm.is_window_open("discord") is False

def test_focus_window_success(mock_wm):
    mock_win = MagicMock()
    mock_win.title = "Discord"
    mock_win._hWnd = 1111
    mock_win.isMinimized = True
    mock_wm.gw.getAllWindows.return_value = [mock_win]
    mock_wm.win32gui.IsWindow.return_value = True
    mock_wm.win32process.GetWindowThreadProcessId.return_value = (0, 1234)
    mock_wm.get_active_window = MagicMock(return_value={"title": "Discord"})
    
    result = mock_wm.focus_window("discord")
    assert result["status"] == "success"

def test_focus_window_partial_success(mock_wm):
    mock_win = MagicMock()
    mock_win.title = "Discord"
    mock_win._hWnd = 1111
    mock_win.isMinimized = False
    mock_wm.gw.getAllWindows.return_value = [mock_win]
    mock_wm.win32gui.IsWindow.return_value = True
    mock_wm.win32process.GetWindowThreadProcessId.return_value = (0, 1234)
    mock_wm.get_active_window = MagicMock(return_value={"title": "Something Else"})
    
    result = mock_wm.focus_window("discord")
    assert result["status"] == "partial_success"

def test_focus_window_not_found(mock_wm):
    mock_wm.gw.getAllWindows.return_value = []
    result = mock_wm.focus_window("discord")
    assert result == {"status": "failed", "message": "Window not found"}

def test_focus_window_invalid_hwnd(mock_wm):
    mock_win = MagicMock()
    mock_win.title = "Discord"
    mock_win._hWnd = 9999
    mock_wm.gw.getAllWindows.return_value = [mock_win]
    mock_wm.win32gui.IsWindow.return_value = False # Invalid hwnd
    
    result = mock_wm.focus_window("discord")
    assert result == {"status": "failed", "message": "Window not found"}

def test_focus_window_minimized(mock_wm):
    mock_win = MagicMock()
    mock_win.title = "Discord"
    mock_win._hWnd = 1111
    mock_wm.gw.getAllWindows.return_value = [mock_win]
    mock_wm.win32gui.IsWindow.return_value = True
    mock_wm.win32process.GetWindowThreadProcessId.return_value = (0, 1234)
    mock_process = MagicMock()
    mock_process.name.return_value = "discord.exe"
    mock_wm.psutil.Process.return_value = mock_process
    mock_wm.win32gui.IsIconic.return_value = 1 # Minimized
    mock_wm.get_active_window = MagicMock(return_value={"title": "Discord"})
    
    result = mock_wm.focus_window("discord")
    assert result["status"] == "success"
    mock_wm.win32gui.ShowWindow.assert_called_once_with(1111, mock_wm.win32con.SW_RESTORE)
    mock_win.activate.assert_called_once()
    mock_wm.win32gui.BringWindowToTop.assert_called_once_with(1111)
    mock_wm.win32gui.SetForegroundWindow.assert_called_once_with(1111)

def test_find_window_with_alias(mock_wm):
    mock_win = MagicMock()
    mock_win.title = "Visual Studio Code"
    mock_win._hWnd = 1111
    mock_win.isMinimized = False
    mock_wm.gw.getAllWindows.return_value = [mock_win]
    mock_wm.win32gui.IsWindow.return_value = True
    mock_wm.win32gui.GetForegroundWindow.return_value = 2222

    result = mock_wm.find_window("vscode")
    assert result is not None
    assert result["title"] == "Visual Studio Code"
    assert result["matched_name"] == "vscode"

def test_focus_window_with_alias(mock_wm):
    mock_win = MagicMock()
    mock_win.title = "Visual Studio Code"
    mock_win._hWnd = 1111
    mock_win.isMinimized = False
    mock_wm.gw.getAllWindows.return_value = [mock_win]
    mock_wm.win32gui.IsWindow.return_value = True
    mock_wm.win32process.GetWindowThreadProcessId.return_value = (0, 1234)
    mock_wm.get_active_window = MagicMock(return_value={"title": "Visual Studio Code"})
    
    result = mock_wm.focus_window("vscode")
    assert result["status"] == "success"
