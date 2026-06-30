from src.parser.command_splitter import AdvancedCommandSplitter

def test_split_simple_and():
    splitter = AdvancedCommandSplitter()
    assert splitter.split("open steam and discord") == ["open steam", "open discord"]

def test_split_multiple_and():
    splitter = AdvancedCommandSplitter()
    assert splitter.split("open chrome, discord and github") == ["open chrome", "open discord", "open github"]

def test_split_then():
    splitter = AdvancedCommandSplitter()
    assert splitter.split("open steam then discord") == ["open steam", "open discord"]

def test_split_mixed_connectors():
    splitter = AdvancedCommandSplitter()
    assert splitter.split("open chrome, discord, github and whatsapp") == ["open chrome", "open discord", "open github", "open whatsapp"]

def test_split_after_that():
    splitter = AdvancedCommandSplitter()
    assert splitter.split("open chrome and after that open vscode") == ["open chrome", "open vscode"]

def test_split_quotes():
    splitter = AdvancedCommandSplitter()
    assert splitter.split('type "hello and welcome" and close chrome') == ['type "hello and welcome"', "close chrome"]
