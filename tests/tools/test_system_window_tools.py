import pytest
from unittest.mock import MagicMock, patch
from src.tools.system_control.window_tools import (
    WindowManager,
    MinimizeWindowTool,
    MaximizeWindowTool,
    RestoreWindowTool,
    FocusWindowTool,
    GetCurrentWindowTool,
    ListOpenWindowsTool
)

@pytest.fixture
def mock_win32():
    with patch('src.tools.system_control.window_tools.WindowManager._import_win32') as mock:
        win32gui = MagicMock()
        win32process = MagicMock()
        win32con = MagicMock()
        win32con.SW_MINIMIZE = 6
        win32con.SW_MAXIMIZE = 3
        win32con.SW_RESTORE = 9
        win32con.SW_SHOWMAXIMIZED = 3
        win32con.SW_SHOWMINIMIZED = 2
        psutil = MagicMock()
        mock.return_value = (win32gui, win32process, win32con, psutil)
        yield win32gui, win32process, win32con, psutil

def test_get_current_window_tool(mock_win32):
    win32gui, win32process, win32con, psutil = mock_win32
    win32gui.GetForegroundWindow.return_value = 1234
    win32gui.IsWindow.return_value = True
    win32gui.GetWindowText.return_value = "Test Window"
    win32process.GetWindowThreadProcessId.return_value = (0, 999)
    psutil.Process().name.return_value = "test.exe"
    win32gui.GetWindowPlacement.return_value = (0, win32con.SW_RESTORE)
    win32gui.IsIconic.return_value = False
    
    tool = GetCurrentWindowTool()
    result = tool.execute()
    
    assert result["status"] == "success"
    assert result["window"]["title"] == "Test Window"
    assert result["window"]["app_name"] == "test.exe"
    assert result["window"]["state"] == "Normal"

def test_minimize_window_tool_current(mock_win32):
    win32gui, win32process, win32con, psutil = mock_win32
    win32gui.GetForegroundWindow.return_value = 1234
    win32gui.IsWindow.return_value = True
    win32gui.GetWindowText.return_value = "Notepad"
    win32process.GetWindowThreadProcessId.return_value = (0, 999)
    psutil.Process().name.return_value = "notepad.exe"
    win32gui.GetWindowPlacement.return_value = (0, win32con.SW_RESTORE)
    win32gui.IsIconic.return_value = False
    
    tool = MinimizeWindowTool()
    result = tool.execute(window_name="current window")
    
    assert result["status"] == "success"
    win32gui.ShowWindow.assert_called_with(1234, win32con.SW_MINIMIZE)

def test_focus_window_tool_multiple_matches(mock_win32):
    # Setup mock to return multiple windows via list_open_windows
    with patch('src.tools.system_control.window_tools.WindowManager.list_open_windows') as mock_list:
        mock_list.return_value = [
            {"title": "Chrome - Google", "app_name": "chrome.exe", "state": "Normal", "pid": 1, "hwnd": 1},
            {"title": "Chrome - YouTube", "app_name": "chrome.exe", "state": "Normal", "pid": 2, "hwnd": 2}
        ]
        
        tool = FocusWindowTool()
        result = tool.execute(window_name="chrome")
        
        assert result["status"] == "ambiguous"
        assert len(result["matches"]) == 2
        assert "Chrome - Google" in result["matches"]

def test_focus_window_tool_single_match(mock_win32):
    win32gui, _, win32con, _ = mock_win32
    win32gui.GetForegroundWindow.return_value = 1
    
    with patch('src.tools.system_control.window_tools.WindowManager.list_open_windows') as mock_list:
        mock_list.return_value = [
            {"title": "Discord", "app_name": "discord.exe", "state": "Normal", "pid": 1, "hwnd": 1}
        ]
        
        tool = FocusWindowTool()
        result = tool.execute(window_name="discord")
        
        assert result["status"] == "success"
        win32gui.SetForegroundWindow.assert_called_with(1)

def test_list_open_windows_tool(mock_win32):
    with patch('src.tools.system_control.window_tools.WindowManager.list_open_windows') as mock_list:
        mock_list.return_value = [
            {"title": "Window 1", "app_name": "app1.exe", "state": "Normal", "pid": 1, "hwnd": 1},
            {"title": "Window 2", "app_name": "app2.exe", "state": "Minimized", "pid": 2, "hwnd": 2}
        ]
        
        tool = ListOpenWindowsTool()
        result = tool.execute()
        
        assert result["status"] == "success"
        assert result["count"] == 2
        assert len(result["windows"]) == 2
