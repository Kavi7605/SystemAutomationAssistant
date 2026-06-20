import pytest
from unittest.mock import MagicMock
from src.context.reference_resolver import ReferenceResolver
from src.context.context_manager import ContextManager

@pytest.fixture
def mock_cm():
    return MagicMock(spec=ContextManager)

@pytest.fixture
def resolver(mock_cm):
    return ReferenceResolver(mock_cm)

def test_resolve_it_to_last_opened(resolver, mock_cm):
    mock_cm.get_context_snapshot.return_value = {
        "last_opened_app": "steam",
        "last_focused_app": None,
        "current_active_app": None
    }
    
    assert resolver.resolve_command("focus it") == "focus steam"

def test_resolve_that_to_last_focused(resolver, mock_cm):
    mock_cm.get_context_snapshot.return_value = {
        "last_focused_app": "github",
        "last_opened_app": None,
        "current_active_app": None,
        "last_closed_app": None
    }
    
    assert resolver.resolve_command("close that") == "close github"

def test_resolve_priority_active_over_focused_over_opened(resolver, mock_cm):
    mock_cm.get_context_snapshot.return_value = {
        "current_active_app": "slack",
        "last_focused_app": "github",
        "last_opened_app": "steam",
        "last_closed_app": "whatsapp"
    }
    
    assert resolver.resolve_command("close that") == "close slack"

def test_resolve_priority_focused_over_opened(resolver, mock_cm):
    mock_cm.get_context_snapshot.return_value = {
        "current_active_app": None,
        "last_focused_app": "github",
        "last_opened_app": "steam",
        "last_closed_app": "whatsapp"
    }
    
    assert resolver.resolve_command("close that") == "close github"

def test_resolve_priority_last_closed(resolver, mock_cm):
    mock_cm.get_context_snapshot.return_value = {
        "last_focused_app": None,
        "last_opened_app": None,
        "current_active_app": None,
        "last_closed_app": "whatsapp"
    }
    
    assert resolver.resolve_command("reopen it") == "reopen whatsapp"

def test_resolve_current_app(resolver, mock_cm):
    mock_cm.get_context_snapshot.return_value = {
        "current_active_app": "discord"
    }
    
    assert resolver.resolve_command("focus current app") == "focus discord"

def test_resolve_previous_app(resolver, mock_cm):
    mock_cm.get_context_snapshot.return_value = {
        "last_active_app": "vscode"
    }
    
    assert resolver.resolve_command("focus previous app") == "focus vscode"

def test_missing_context_raises_error(resolver, mock_cm):
    mock_cm.get_context_snapshot.return_value = {
        "last_opened_app": None,
        "last_focused_app": None,
        "current_active_app": None,
        "last_closed_app": None
    }
    
    with pytest.raises(ValueError, match="No application reference available in context."):
        resolver.resolve_command("focus it")

def test_dynamic_re_evaluation(resolver, mock_cm):
    # Initial state
    mock_cm.get_context_snapshot.return_value = {
        "last_opened_app": "discord",
        "last_focused_app": None,
        "current_active_app": None,
        "last_closed_app": None
    }
    
    assert resolver.resolve_command("close it") == "close discord"
    
    # Context changes
    mock_cm.get_context_snapshot.return_value = {
        "last_opened_app": "whatsapp",
        "last_focused_app": None,
        "current_active_app": None,
        "last_closed_app": "discord"
    }
    
    assert resolver.resolve_command("close it") == "close whatsapp"
