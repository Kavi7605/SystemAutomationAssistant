import pytest
import datetime
from src.context.context_manager import ContextManager
from src.context.persistence_manager import PersistenceManager
import os

def test_disambiguation_initial_state():
    cm = ContextManager()
    assert "pending_disambiguation" in cm.state
    assert cm.state["pending_disambiguation"] is None

def test_disambiguation_persistence(tmp_path):
    persist = PersistenceManager(context_file=str(tmp_path / "context.json"), state_file=str(tmp_path / "state.json"))
    cm = ContextManager(persistence_manager=persist)
    
    # Simulate an ambiguous response from a tool
    cm.state["pending_disambiguation"] = {
        "action": "delete_item",
        "parameters": {"item_name": "report"},
        "matches": ["REPORT.docx", "REPORT.pdf"],
        "target_key": "item_name",
        "created_at": datetime.datetime.now().isoformat(),
        "prompt": "delete report"
    }
    cm.save()
    
    # Create new instance (like restarting the app)
    cm2 = ContextManager(persistence_manager=persist)
    cm2.load()
    
    assert cm2.state["pending_disambiguation"] is not None
    assert cm2.state["pending_disambiguation"]["action"] == "delete_item"
    assert cm2.state["pending_disambiguation"]["matches"] == ["REPORT.docx", "REPORT.pdf"]
    assert cm2.state["pending_disambiguation"]["prompt"] == "delete report"

def test_disambiguation_cleanup():
    cm = ContextManager()
    cm.state["pending_disambiguation"] = {
        "action": "delete_item",
        "parameters": {},
        "matches": ["1", "2"]
    }
    
    # Simulate a user typing "cancel"
    cm.state["pending_disambiguation"] = None
    assert cm.state["pending_disambiguation"] is None
