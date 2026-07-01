import pytest
import os
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.automation.engine import AutomationEngine
from src.context.context_manager import ContextManager

def test_known_windows_folders(engine):
    e = engine
    
    # Mock PathResolver
    from src.tools.path_resolver import ResolvedPath
    with patch("src.tools.path_resolver.PathResolver.resolve") as mock_resolve:
        mock_resolve.return_value = {"status": "success", "resolved_path": ResolvedPath("C:\\Users\\MockUser\\Downloads")}
        
        cmd = e._route_semantic_command("open downloads")
        assert cmd["action"] == "open_item"
        assert cmd["parameters"]["item_name"] == "downloads"

def test_context_memory_priority(engine, tmp_path):
    e = engine
    ctx = e.context_manager
    notes_file = tmp_path / "notes.txt"
    notes_file.touch()
    
    ctx.update_filesystem_state("last_created_file", str(notes_file))
    
    with patch("src.tools.path_resolver.PathResolver.resolve") as mock_pr:
        mock_pr.return_value = {"status": "failed"}
        
        from src.tools.filesystem_tools import resolve_smart_item
        res = resolve_smart_item("it", context_manager=ctx)
        
        assert res["status"] == "success"
        assert res["resolved_name"] == "notes.txt"

def test_independent_memories(engine):
    e = engine
    ctx = e.context_manager
    ctx.mark_app_opened("Discord")
    assert ctx.state["last_interacted_app"] == "discord"
    
    ctx.update_filesystem_state("last_created_file", "C:\\notes.txt")
    
    assert ctx.state["last_interacted_app"] == "discord"
    assert ctx.state["last_interaction_type"] == "filesystem"

def test_cancel_pending_states(engine):
    e = engine
    ctx = e.context_manager
    
    # 1. Cancel Disambiguation
    ctx.state["pending_disambiguation"] = {"matches": ["a", "b"]}
    e.process_command("cancel")
    assert ctx.state.get("pending_disambiguation") is None
    
    # 2. Cancel Delete
    ctx.update_filesystem_state("pending_delete", "C:\\notes.txt")
    cmd = e._route_semantic_command("cancel")
    assert cmd["action"] == "cancel_delete"
    ctx.update_filesystem_state("pending_delete", None)
    
    # 3. Cancel Power Action
    ctx.update_system_state("pending_power_action", "shutdown")
    cmd2 = e._route_semantic_command("cancel")
    assert cmd2["action"] == "cancel_power_action"
    ctx.update_system_state("pending_power_action", None)
    
    # 4. Implicit cancel of disambiguation
    ctx.state["pending_disambiguation"] = {"matches": ["a", "b"]}
    e.process_command("create notes.txt")
    assert ctx.state.get("pending_disambiguation") is None
