from src.parser.nested_parser import NestedParser

def test_nested_before():
    parser = NestedParser()
    assert parser.parse(["wait until it opens before focusing it"]) == ["wait until it opens", "focusing it"]
    
def test_nested_before_real():
    parser = NestedParser()
    assert parser.parse(["wait until discord opens before focusing it"]) == ["wait until discord opens", "focusing it"]

def test_nested_after():
    parser = NestedParser()
    assert parser.parse(["close chrome after saving the document"]) == ["saving the document", "close chrome"]

def test_nested_while():
    parser = NestedParser()
    assert parser.parse(["open discord while opening steam"]) == ["opening steam", "open discord"]

def test_nested_no_match():
    parser = NestedParser()
    assert parser.parse(["open discord"]) == ["open discord"]
