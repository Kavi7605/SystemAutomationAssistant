from src.context.context_manager import ContextManager

def test_multiple_open_operations():
    cm = ContextManager()
    cm.mark_app_opened("steam")
    cm.mark_app_opened("discord")
    cm.mark_app_opened("whatsapp")
    
    assert cm.get_open_history() == ["steam", "discord", "whatsapp"]
    assert cm.get_last_opened_app() == "whatsapp"
    assert cm.get_previous_opened_app() == "discord"

def test_multiple_close_operations():
    cm = ContextManager()
    cm.mark_app_closed("steam")
    cm.mark_app_closed("discord")
    
    assert cm.get_close_history() == ["steam", "discord"]
    assert cm.get_last_closed_app() == "discord"
    assert cm.get_previous_closed_app() == "steam"

def test_multiple_focus_operations():
    cm = ContextManager()
    cm.mark_app_focused("steam")
    cm.mark_app_focused("discord")
    cm.mark_app_focused("steam")
    
    assert cm.get_focus_history() == ["steam", "discord", "steam"]
    assert cm.get_last_focused_app() == "steam"
    assert cm.get_previous_focused_app() == "discord"
    
    snap = cm.get_context_snapshot()
    assert snap["current_active_app"] == "steam"
    assert snap["last_active_app"] == "discord"

def test_history_retrieval_empty():
    cm = ContextManager()
    assert cm.get_open_history() == []
    assert cm.get_last_opened_app() is None
    assert cm.get_previous_opened_app() is None

def test_snapshot_correctness():
    cm = ContextManager()
    cm.mark_app_opened("steam")
    cm.mark_app_focused("steam")
    cm.mark_app_closed("steam")
    
    snap = cm.get_context_snapshot()
    assert snap["opened_apps_history"] == ["steam"]
    assert snap["focused_apps_history"] == ["steam"]
    assert snap["closed_apps_history"] == ["steam"]
    
    # Verify deep copy works - modifying returned list should not affect original
    snap["opened_apps_history"].append("discord")
    assert cm.get_open_history() == ["steam"]
