import pytest
from src.context.context_manager import ContextManager
from src.context.reference_resolver import ReferenceResolver

@pytest.fixture
def empty_context():
    return ContextManager()

@pytest.fixture
def populated_context():
    cm = ContextManager()
    cm.mark_app_opened("steam")
    cm.mark_app_opened("discord")
    cm.mark_app_opened("vscode")
    
    cm.mark_app_closed("chrome")
    cm.mark_app_closed("edge")
    
    cm.mark_app_focused("notepad")
    
    cm.sync_active_apps(current_app="vscode", last_app="discord")
    return cm

@pytest.fixture
def resolver(populated_context):
    return ReferenceResolver(populated_context)

def test_singular_ordinal_resolution(resolver):
    assert resolver.resolve("the first app") == ["steam"]
    assert resolver.resolve("the second app") == ["discord"]
    assert resolver.resolve("the third app") == ["vscode"]
    assert resolver.resolve("first") == ["steam"]
    assert resolver.resolve("second") == ["discord"]
    assert resolver.resolve("third") == ["vscode"]
    
def test_newest_oldest_resolution(resolver):
    assert resolver.resolve("the newest app") == ["vscode"]
    assert resolver.resolve("latest") == ["vscode"]
    assert resolver.resolve("the oldest app") == ["steam"]
    assert resolver.resolve("oldest") == ["steam"]

def test_history_specific_resolution(resolver):
    assert resolver.resolve("the last closed app") == ["edge"]
    assert resolver.resolve("the last focused app") == ["notepad"]
    assert resolver.resolve("the currently focused app") == ["vscode"]

def test_plural_resolution(resolver):
    assert resolver.resolve("both") == ["discord", "vscode"]
    assert resolver.resolve("all apps") == ["steam", "discord", "vscode"]
    assert resolver.resolve("all of them") == ["steam", "discord", "vscode"]

def test_missing_history_failures():
    cm = ContextManager()
    res = ReferenceResolver(cm)
    
    with pytest.raises(ValueError):
        res.resolve("the first app")
        
    with pytest.raises(ValueError):
        res.resolve("both")
        
    with pytest.raises(ValueError):
        res.resolve("all apps")

def test_regression_existing_it(resolver):
    assert resolver.resolve("it") == ["notepad"]
    assert resolver.resolve("this") == ["notepad"]
    assert resolver.resolve("that") == ["notepad"]
    assert resolver.resolve("previous app") == ["discord"]
    assert resolver.resolve("current app") == ["vscode"]

def test_non_reference_passthrough(resolver):
    assert resolver.resolve("spotify") == ["spotify"]
    assert resolver.resolve("some random string") == ["some random string"]

def test_inline_substring_resolution(resolver):
    # This tests the legacy fallback replacer regex logic
    # "open it and that" -> should replace both "it" and "that" with "vscode" (current_active_app)
    # Wait, the fallback replacer does it and that?
    # Our regex replaces \b(it|that|...)\b with the resolved text
    result = resolver.resolve("close it and that")
    # Both "it" and "that" resolve to "vscode".
    # Output should be "close notepad and notepad" in a 1-element list
    assert result == ["close notepad and notepad"]
