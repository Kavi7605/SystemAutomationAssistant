import pytest
from unittest.mock import MagicMock
from src.tools.window_tools import GetActiveWindowTool, IsWindowOpenTool, FocusWindowTool

@pytest.fixture
def mock_wm():
    return MagicMock()

def test_get_active_window_tool(mock_wm):
    mock_wm.get_active_window.return_value = {"title": "Test Window", "process_name": "test.exe", "is_minimized": False}
    tool = GetActiveWindowTool(window_manager=mock_wm)
    result = tool.execute()
    
    assert result["status"] == "success"
    assert result["window"]["title"] == "Test Window"
    mock_wm.get_active_window.assert_called_once()

def test_get_active_window_tool_fail(mock_wm):
    mock_wm.get_active_window.return_value = None
    tool = GetActiveWindowTool(window_manager=mock_wm)
    result = tool.execute()
    
    assert result["status"] == "failed"

def test_is_window_open_tool_true(mock_wm):
    mock_wm.is_window_open.return_value = True
    tool = IsWindowOpenTool(window_manager=mock_wm)
    result = tool.execute(window_name="steam")
    
    assert result["status"] == "success"
    assert result["is_open"] is True
    mock_wm.is_window_open.assert_called_once_with("steam")

def test_is_window_open_tool_false(mock_wm):
    mock_wm.is_window_open.return_value = False
    tool = IsWindowOpenTool(window_manager=mock_wm)
    result = tool.execute(window_name="steam")
    
    assert result["status"] == "success"
    assert result["is_open"] is False

def test_focus_window_tool_success(mock_wm):
    mock_wm.focus_window.return_value = {"status": "success"}
    tool = FocusWindowTool(window_manager=mock_wm)
    result = tool.execute(window_name="discord")
    
    assert result["status"] == "success"
    mock_wm.focus_window.assert_called_once_with("discord")
