from unittest.mock import patch
import pytest

import pyautogui
from src.tools.desktop_tools import (
    ClickTool,
    DoubleClickTool,
    RightClickTool,
    TypeTextTool,
    HotkeyTool,
    ScrollTool,
    MoveMouseTool
)

@pytest.fixture
def click_tool():
    return ClickTool()

@pytest.fixture
def double_click_tool():
    return DoubleClickTool()

@pytest.fixture
def right_click_tool():
    return RightClickTool()

@pytest.fixture
def type_text_tool():
    return TypeTextTool()

@pytest.fixture
def hotkey_tool():
    return HotkeyTool()

@pytest.fixture
def scroll_tool():
    return ScrollTool()

@pytest.fixture
def move_mouse_tool():
    return MoveMouseTool()

@patch('pyautogui.click')
def test_click_tool_no_coords(mock_click, click_tool):
    result = click_tool.execute()
    mock_click.assert_called_once_with()
    assert result["status"] == "success"

@patch('pyautogui.click')
def test_click_tool_with_coords(mock_click, click_tool):
    result = click_tool.execute(x=100, y=200)
    mock_click.assert_called_once_with(x=100, y=200)
    assert result["status"] == "success"

@patch('pyautogui.click')
def test_click_tool_failsafe(mock_click, click_tool):
    mock_click.side_effect = pyautogui.FailSafeException("Fail-safe triggered")
    result = click_tool.execute()
    assert result["status"] == "failed"
    assert "Fail-safe" in result["message"]

@patch('pyautogui.doubleClick')
def test_double_click_tool(mock_double_click, double_click_tool):
    result = double_click_tool.execute(x=50, y=60)
    mock_double_click.assert_called_once_with(x=50, y=60)
    assert result["status"] == "success"

@patch('pyautogui.rightClick')
def test_right_click_tool(mock_right_click, right_click_tool):
    result = right_click_tool.execute(x=10, y=20)
    mock_right_click.assert_called_once_with(x=10, y=20)
    assert result["status"] == "success"

@patch('pyautogui.write')
def test_type_text_tool(mock_write, type_text_tool):
    result = type_text_tool.execute(text="hello world")
    mock_write.assert_called_once_with("hello world")
    assert result["status"] == "success"

def test_type_text_tool_missing_param(type_text_tool):
    result = type_text_tool.execute(text="")
    assert result["status"] == "failed"

@patch('pyautogui.hotkey')
def test_hotkey_tool(mock_hotkey, hotkey_tool):
    result = hotkey_tool.execute(keys=["ctrl", "c"])
    mock_hotkey.assert_called_once_with("ctrl", "c")
    assert result["status"] == "success"

def test_hotkey_tool_missing_param(hotkey_tool):
    result = hotkey_tool.execute(keys=[])
    assert result["status"] == "failed"

@patch('pyautogui.scroll')
def test_scroll_tool_up(mock_scroll, scroll_tool):
    result = scroll_tool.execute(direction="up")
    mock_scroll.assert_called_once_with(500)
    assert result["status"] == "success"

@patch('pyautogui.scroll')
def test_scroll_tool_down(mock_scroll, scroll_tool):
    result = scroll_tool.execute(direction="down")
    mock_scroll.assert_called_once_with(-500)
    assert result["status"] == "success"

def test_scroll_tool_missing_param(scroll_tool):
    result = scroll_tool.execute(direction="")
    assert result["status"] == "failed"

@patch('pyautogui.moveTo')
def test_move_mouse_tool(mock_move, move_mouse_tool):
    result = move_mouse_tool.execute(x=500, y=300)
    mock_move.assert_called_once_with(500, 300)
    assert result["status"] == "success"

def test_move_mouse_tool_missing_param(move_mouse_tool):
    result = move_mouse_tool.execute(x=None, y=300)
    assert result["status"] == "failed"

@patch('pyautogui.moveTo')
def test_move_mouse_tool_failsafe(mock_move, move_mouse_tool):
    mock_move.side_effect = pyautogui.FailSafeException("Fail-safe")
    result = move_mouse_tool.execute(x=0, y=0)
    assert result["status"] == "failed"
    assert "Fail-safe" in result["message"]
