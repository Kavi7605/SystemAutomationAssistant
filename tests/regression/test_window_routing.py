import pytest
from unittest.mock import MagicMock
from src.automation.engine import AutomationEngine

@pytest.fixture
def engine():
    parser = MagicMock()
    resolver = MagicMock()
    task_planner = MagicMock()
    executor = MagicMock()
    history_manager = MagicMock()
    engine_instance = AutomationEngine(parser, resolver, task_planner, executor, history_manager)
    return engine_instance

def test_route_minimize_aliases(engine):
    aliases = [
        "minimize chrome",
        "minimize vscode",
        "minimize current window",
        "minimize active window",
        "minimize notepad"
    ]
    for alias in aliases:
        result = engine._route_semantic_command(alias)
        assert result["action"] == "minimize_window"
        # Extract target from the alias, e.g. "minimize chrome" -> "chrome"
        expected_target = alias.replace("minimize ", "")
        assert result["parameters"]["window_name"] == expected_target

def test_route_maximize_aliases(engine):
    aliases = [
        "maximize chrome",
        "maximize current window",
        "maximize active window"
    ]
    for alias in aliases:
        result = engine._route_semantic_command(alias)
        assert result["action"] == "maximize_window"
        expected_target = alias.replace("maximize ", "")
        assert result["parameters"]["window_name"] == expected_target

def test_route_restore_aliases(engine):
    aliases = [
        "restore chrome",
        "restore current window",
        "restore active window"
    ]
    for alias in aliases:
        result = engine._route_semantic_command(alias)
        assert result["action"] == "restore_window"
        expected_target = alias.replace("restore ", "")
        assert result["parameters"]["window_name"] == expected_target

def test_route_focus_aliases(engine):
    aliases = [
        ("focus chrome", "chrome"),
        ("switch to chrome", "chrome"),
        ("bring chrome to front", "chrome"),
        ("activate chrome", "chrome"),
        ("focus previous window", "previous window")
    ]
    for alias, expected in aliases:
        result = engine._route_semantic_command(alias)
        assert result["action"] == "focus_window"
        assert result["parameters"]["window_name"] == expected

def test_route_current_window_aliases(engine):
    aliases = [
        "current window",
        "active window",
        "window status",
        "show current window",
        "what window is active"
    ]
    for alias in aliases:
        result = engine._route_semantic_command(alias)
        assert result["action"] == "get_current_window"

def test_route_list_windows_aliases(engine):
    aliases = [
        "list open windows",
        "show open windows",
        "what windows are open",
        "window list"
    ]
    for alias in aliases:
        result = engine._route_semantic_command(alias)
        assert result["action"] == "list_open_windows"

def test_deterministic_bypass(engine):
    engine.parser.parse_command = MagicMock()
    engine.task_planner.plan_task = MagicMock()
    
    # We use execute_command directly
    engine.process_command("minimize chrome", source="USER_EXPLICIT")
    
    # Assert neither parser nor planner were called because it was caught deterministically
    engine.parser.parse_command.assert_not_called()
    engine.task_planner.plan_task.assert_not_called()
