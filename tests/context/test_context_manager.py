import pytest
from src.core.context_manager import ContextManager

def test_context_manager_singleton():
    cm1 = ContextManager()
    cm2 = ContextManager()
    assert cm1 is cm2

def test_context_manager_properties():
    cm = ContextManager()
    
    # Test setting and getting
    cm.last_application = "vscode"
    assert cm.last_application == "vscode"
    
    cm.last_website = "github.com"
    assert cm.last_website == "github.com"
    
    cm.last_url = "https://github.com"
    assert cm.last_url == "https://github.com"
    
    cm.last_file = "test.txt"
    assert cm.last_file == "test.txt"
    
    cm.last_folder = "reports"
    assert cm.last_folder == "reports"
    
    cm.last_action = "open_application"
    assert cm.last_action == "open_application"
    
    payload = {"action": "open_application", "parameters": {"application_name": "vscode"}}
    cm.last_action_payload = payload
    assert cm.last_action_payload == payload
