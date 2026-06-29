import pytest
from src.automation.command_expander import CommandExpander

class MockReferenceResolver:
    def resolve(self, target: str):
        if target == "both":
            return ["steam", "discord"]
        elif target == "all apps":
            return ["steam", "discord", "vscode"]
        elif target == "first app":
            return ["steam"]
        elif target == "unknown":
            raise ValueError("No application reference available in context.")
        return [target]

@pytest.fixture
def expander():
    resolver = MockReferenceResolver()
    return CommandExpander(reference_resolver=resolver)

def test_expand_singular_reference(expander):
    parsed = [{"action": "close_application", "parameters": {"application_name": "first app"}}]
    expanded = expander.expand(parsed)
    
    assert len(expanded) == 1
    assert expanded[0]["action"] == "close_application"
    assert expanded[0]["parameters"]["application_name"] == "steam"

def test_expand_plural_reference(expander):
    parsed = [{"action": "close_application", "parameters": {"application_name": "both"}}]
    expanded = expander.expand(parsed)
    
    assert len(expanded) == 2
    assert expanded[0]["action"] == "close_application"
    assert expanded[0]["parameters"]["application_name"] == "steam"
    
    assert expanded[1]["action"] == "close_application"
    assert expanded[1]["parameters"]["application_name"] == "discord"

def test_expand_all_reference(expander):
    parsed = [{"action": "minimize_window", "parameters": {"window_name": "all apps"}}]
    expanded = expander.expand(parsed)
    
    assert len(expanded) == 3
    assert expanded[0]["parameters"]["window_name"] == "steam"
    assert expanded[1]["parameters"]["window_name"] == "discord"
    assert expanded[2]["parameters"]["window_name"] == "vscode"

def test_expand_no_reference(expander):
    parsed = [{"action": "open_application", "parameters": {"application_name": "chrome"}}]
    expanded = expander.expand(parsed)
    
    assert len(expanded) == 1
    assert expanded[0]["parameters"]["application_name"] == "chrome"

def test_expand_unresolved_reference(expander):
    parsed = [{"action": "focus_window", "parameters": {"window_name": "unknown"}}]
    expanded = expander.expand(parsed)
    
    assert len(expanded) == 1
    assert expanded[0]["action"] == "unsupported"
    assert "No application reference available" in expanded[0]["parameters"]["message"]
