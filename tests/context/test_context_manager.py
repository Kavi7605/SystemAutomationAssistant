import pytest
from src.context.context_manager import ContextManager

def test_mark_app_opened():
    cm = ContextManager()
    cm.mark_app_opened("steam")
    
    snapshot = cm.get_context_snapshot()
    assert snapshot["last_opened_app"] == "steam"
    assert snapshot["last_successful_action"] == "open_application"

def test_mark_app_closed():
    cm = ContextManager()
    cm.mark_app_closed("discord")
    
    snapshot = cm.get_context_snapshot()
    assert snapshot["last_closed_app"] == "discord"
    assert snapshot["last_successful_action"] == "close_application"

def test_mark_app_focused():
    cm = ContextManager()
    
    cm.mark_app_focused("steam")
    snapshot = cm.get_context_snapshot()
    assert snapshot["last_focused_app"] == "steam"
    assert snapshot["current_active_app"] == "steam"
    assert snapshot["last_active_app"] is None
    assert snapshot["last_successful_action"] == "focus_window"
    
    cm.mark_app_focused("discord")
    snapshot = cm.get_context_snapshot()
    assert snapshot["last_focused_app"] == "discord"
    assert snapshot["current_active_app"] == "discord"
    assert snapshot["last_active_app"] == "steam"

def test_update_last_command():
    cm = ContextManager()
    cm.update_last_command("open steam and focus discord")
    
    snapshot = cm.get_context_snapshot()
    assert snapshot["last_command"] == "open steam and focus discord"

def test_get_context_snapshot():
    cm = ContextManager()
    cm.mark_app_opened("vscode")
    cm.mark_app_focused("vscode")
    cm.update_last_command("open vscode")
    cm.update_active_window("Visual Studio Code")
    cm.mark_action_failed("click")
    
    snapshot = cm.get_context_snapshot()
    
    assert snapshot == {
        "last_command": "open vscode",
        "last_opened_app": "vscode",
        "last_closed_app": None,
        "last_focused_app": "vscode",
        "current_active_app": "vscode",
        "last_active_app": None,
        "last_window_title": "Visual Studio Code",
        "last_successful_action": "focus_window",
        "last_failed_action": "click",
        "opened_apps_history": ["vscode"],
        "closed_apps_history": [],
        "focused_apps_history": ["vscode"],
        "pending_disambiguation": None
    }

def test_update_active_window_synchronization():
    cm = ContextManager()
    
    # Simulate window with known alias
    cm.update_active_window("Visual Studio Code")
    assert cm.get_context_snapshot()["current_active_app"] == "vscode"
    assert cm.get_context_snapshot()["last_active_app"] is None
    
    # Simulate window with another known alias
    cm.update_active_window("Discord - #general")
    assert cm.get_context_snapshot()["current_active_app"] == "discord"
    assert cm.get_context_snapshot()["last_active_app"] == "vscode"
    
    # Simulate unknown window
    cm.update_active_window("Unknown Custom App")
    assert cm.get_context_snapshot()["current_active_app"] is None
    assert cm.get_context_snapshot()["last_active_app"] == "discord"
