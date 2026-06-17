import pytest
from unittest.mock import MagicMock
from src.automation.engine import AutomationEngine

def test_multi_action_routing_github():
    parser = MagicMock()
    resolver = MagicMock()
    planner = MagicMock()
    executor = MagicMock()
    history = MagicMock()
    
    engine = AutomationEngine(parser, resolver, planner, executor, history)
    
    engine.process_command("open github and github website")
    planner.plan_tasks.assert_not_called()
    executor.execute.assert_called_once()
    
    cmds = executor.execute.call_args[0][0]
    assert isinstance(cmds, list)
    assert len(cmds) == 2
    assert cmds[0]["action"] == "open_application"
    assert cmds[0]["parameters"]["application_name"] == "github"
    assert cmds[1]["action"] == "open_url"
    assert cmds[1]["parameters"]["url"] == "https://github.com"

def test_multi_action_routing_vscode():
    parser = MagicMock()
    resolver = MagicMock()
    planner = MagicMock()
    executor = MagicMock()
    history = MagicMock()
    
    engine = AutomationEngine(parser, resolver, planner, executor, history)
    
    engine.process_command("open vscode and github website")
    planner.plan_tasks.assert_not_called()
    executor.execute.assert_called_once()
    
    cmds = executor.execute.call_args[0][0]
    assert isinstance(cmds, list)
    assert len(cmds) == 2
    assert cmds[0]["action"] == "open_application"
    assert cmds[0]["parameters"]["application_name"] == "vscode"
    assert cmds[1]["action"] == "open_url"
    assert cmds[1]["parameters"]["url"] == "https://github.com"

def test_multi_action_routing_github_desktop():
    parser = MagicMock()
    resolver = MagicMock()
    planner = MagicMock()
    executor = MagicMock()
    history = MagicMock()
    
    engine = AutomationEngine(parser, resolver, planner, executor, history)
    
    engine.process_command("open github desktop and github website")
    planner.plan_tasks.assert_not_called()
    executor.execute.assert_called_once()
    
    cmds = executor.execute.call_args[0][0]
    assert isinstance(cmds, list)
    assert len(cmds) == 2
    assert cmds[0]["action"] == "open_application"
    assert cmds[0]["parameters"]["application_name"] == "github desktop"
    assert cmds[1]["action"] == "open_url"
    assert cmds[1]["parameters"]["url"] == "https://github.com"

def test_multi_action_planner_fallback():
    parser = MagicMock()
    resolver = MagicMock()
    planner = MagicMock()
    executor = MagicMock()
    history = MagicMock()
    
    engine = AutomationEngine(parser, resolver, planner, executor, history)
    
    # Needs planner stub so it doesn't fail parsing
    planner.plan_tasks.return_value = ["open vscode", "close steam"]
    parser.parse_command.side_effect = [
        {"action": "open_application", "parameters": {"application_name": "vscode"}},
        {"action": "close_application", "parameters": {"application_name": "steam"}}
    ]
    resolver.resolve.side_effect = lambda x: x
    
    engine.process_command("open vscode and close steam")
    planner.plan_tasks.assert_called_once_with("open vscode and close steam")
    executor.execute.assert_called()

def test_website_grammar_search():
    parser = MagicMock()
    resolver = MagicMock()
    planner = MagicMock()
    executor = MagicMock()
    history = MagicMock()
    
    engine = AutomationEngine(parser, resolver, planner, executor, history)
    
    engine.process_command("open github website and search python repositories")
    planner.plan_tasks.assert_not_called()
    executor.execute.assert_called_once()
    
    cmd = executor.execute.call_args[0][0]
    if isinstance(cmd, list): cmd = cmd[0]
    assert cmd["action"] == "open_url"
    assert "search?q=python" in cmd["parameters"]["url"]
    assert "repositories" in cmd["parameters"]["url"]

def test_website_grammar_validation_error():
    parser = MagicMock()
    resolver = MagicMock()
    planner = MagicMock()
    executor = MagicMock()
    history = MagicMock()

    engine = AutomationEngine(parser, resolver, planner, executor, history)

    # Now "open github website user" is the invalid one
    engine.process_command("open github website user")
    planner.plan_tasks.assert_not_called()
    executor.execute.assert_called_once()

    cmd = executor.execute.call_args[0][0]
    if isinstance(cmd, list): cmd = cmd[0]
    assert cmd["action"] == "unsupported"
    assert "Search query is missing" in cmd["parameters"]["message"]
