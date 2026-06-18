from unittest.mock import MagicMock
import pytest
from src.automation.engine import AutomationEngine

@pytest.fixture
def engine():
    parser = MagicMock()
    resolver = MagicMock()
    task_planner = MagicMock()
    executor = MagicMock()
    history_manager = MagicMock()
    return AutomationEngine(parser, resolver, task_planner, executor, history_manager)

def test_route_click(engine):
    result = engine._route_semantic_command("click")
    assert result == {"action": "click", "parameters": {}}

def test_route_click_with_coords(engine):
    result = engine._route_semantic_command("click 500 300")
    assert result == {"action": "click", "parameters": {"x": 500, "y": 300}}

def test_route_double_click(engine):
    result = engine._route_semantic_command("double click")
    assert result == {"action": "double_click", "parameters": {}}

def test_route_right_click(engine):
    result = engine._route_semantic_command("right click 10 20")
    assert result == {"action": "right_click", "parameters": {"x": 10, "y": 20}}

def test_route_type_text(engine):
    result = engine._route_semantic_command("type hello world")
    assert result == {"action": "type_text", "parameters": {"text": "hello world"}}

def test_route_write_text(engine):
    result = engine._route_semantic_command("write hello world")
    assert result == {"action": "type_text", "parameters": {"text": "hello world"}}

def test_route_press_hotkey(engine):
    result = engine._route_semantic_command("press ctrl c")
    assert result == {"action": "hotkey", "parameters": {"keys": ["ctrl", "c"]}}

def test_route_press_complex_hotkey(engine):
    result = engine._route_semantic_command("press ctrl shift esc")
    assert result == {"action": "hotkey", "parameters": {"keys": ["ctrl", "shift", "esc"]}}

def test_route_scroll_down(engine):
    result = engine._route_semantic_command("scroll down")
    assert result == {"action": "scroll", "parameters": {"direction": "down"}}

def test_route_scroll_up(engine):
    result = engine._route_semantic_command("scroll up")
    assert result == {"action": "scroll", "parameters": {"direction": "up"}}

def test_route_move_mouse(engine):
    result = engine._route_semantic_command("move mouse 500 300")
    assert result == {"action": "move_mouse", "parameters": {"x": 500, "y": 300}}

def test_route_move_mouse_to(engine):
    result = engine._route_semantic_command("move mouse to 500 300")
    assert result == {"action": "move_mouse", "parameters": {"x": 500, "y": 300}}
