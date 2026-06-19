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
    return AutomationEngine(parser, resolver, task_planner, executor, history_manager)

def test_multi_action_open_and_focus_steam(engine):
    normalized = engine._normalize_app_chains("open steam and focus steam")
    expanded = engine._expand_multi_actions(normalized)
    assert expanded == ["open steam", "focus steam"]

def test_multi_action_open_and_focus_whatsapp(engine):
    normalized = engine._normalize_app_chains("open whatsapp and focus whatsapp")
    expanded = engine._expand_multi_actions(normalized)
    assert expanded == ["open whatsapp", "focus whatsapp"]
    
def test_multi_action_open_discord_and_active_window(engine):
    normalized = engine._normalize_app_chains("open discord and what window is active")
    expanded = engine._expand_multi_actions(normalized)
    assert expanded == ["open discord", "what window is active"]

def test_route_focus_nonexistentapp(engine):
    result = engine._route_semantic_command("focus nonexistentapp")
    assert result == {"action": "focus_window", "parameters": {"window_name": "nonexistentapp"}}

def test_route_active_window_aliases(engine):
    aliases = [
        "what app is active",
        "what window is focused",
        "what is visible on screen",
        "what app is open",
        "what application is open",
        "what window is open",
        "which app is open",
        "which application is open",
        "which window is open",
        "tell me what app is open",
        "tell me what window is open",
        "tell me which app is open"
    ]
    for alias in aliases:
        result = engine._route_semantic_command(alias)
        assert result == {"action": "get_active_window", "parameters": {}}, f"Failed on alias: {alias}"

def test_multi_action_three_chain(engine):
    normalized = engine._normalize_app_chains("open discord and focus discord and what window is active")
    expanded = engine._expand_multi_actions(normalized)
    assert expanded == ["open discord", "focus discord", "what window is active"]

def test_multi_action_open_and_active_aliases(engine):
    test_cases = [
        ("open steam and what app is open", ["open steam", "what app is open"]),
        ("open discord and what window is open", ["open discord", "what window is open"]),
        ("open whatsapp and what application is open", ["open whatsapp", "what application is open"]),
        ("open steam and tell me what app is open", ["open steam", "tell me what app is open"])
    ]
    for cmd, expected in test_cases:
        normalized = engine._normalize_app_chains(cmd)
        expanded = engine._expand_multi_actions(normalized)
        assert expanded == expected, f"Failed on command: {cmd}"

def test_wait_routing_grammar(engine):
    # Test wait for seconds
    result = engine._route_semantic_command("wait 5 seconds")
    assert result == {"action": "wait", "parameters": {"wait_type": "seconds", "seconds": 5}}

    result = engine._route_semantic_command("pause for 10 seconds")
    assert result == {"action": "wait", "parameters": {"wait_type": "seconds", "seconds": 10}}
    
    # Test wait until window
    result = engine._route_semantic_command("wait until steam opens")
    assert result == {"action": "wait", "parameters": {"wait_type": "window", "window_name": "steam"}}

    result = engine._route_semantic_command("wait until discord launches")
    assert result == {"action": "wait", "parameters": {"wait_type": "window", "window_name": "discord"}}

def test_multi_action_wait_sequences(engine):
    test_cases = [
        ("open steam and wait for 5 seconds and focus steam", ["open steam", "wait for 5 seconds", "focus steam"]),
        ("open steam and wait until steam opens and focus steam", ["open steam", "wait until steam opens", "focus steam"]),
        ("open discord and wait until discord launches and focus discord", ["open discord", "wait until discord launches", "focus discord"]),
        ("close steam and wait until steam is closed and open discord", ["close steam", "wait until steam is closed", "open discord"]),
        ("close vscode and wait until vscode disappears and open whatsapp", ["close vscode", "wait until vscode disappears", "open whatsapp"])
    ]
    for cmd, expected in test_cases:
        normalized = engine._normalize_app_chains(cmd)
        expanded = engine._expand_multi_actions(normalized)
        assert expanded == expected, f"Failed on command: {cmd}"

def test_wait_closed_routing_grammar(engine):
    result = engine._route_semantic_command("wait until steam closes")
    assert result == {"action": "wait", "parameters": {"wait_type": "window_closed", "window_name": "steam"}}

    result = engine._route_semantic_command("wait until steam is closed")
    assert result == {"action": "wait", "parameters": {"wait_type": "window_closed", "window_name": "steam"}}

    result = engine._route_semantic_command("wait until vscode disappears")
    assert result == {"action": "wait", "parameters": {"wait_type": "window_closed", "window_name": "vscode"}}
