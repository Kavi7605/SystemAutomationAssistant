import pytest
from unittest.mock import MagicMock
from src.automation.engine import AutomationEngine

@pytest.fixture
def engine():
    parser = MagicMock()
    # Mock parser to return dummy json for non-deterministic stuff like 'wait until it opens'
    parser.parse_command.side_effect = lambda x: {"action": "dummy", "parameters": {"cmd": x}}
    
    resolver = MagicMock()
    resolver.resolve.side_effect = lambda x: x
    
    task_planner = MagicMock()
    executor = MagicMock()
    executor.execute.return_value = {"status": "success", "message": "Success"}
    history_manager = MagicMock()
    nlp_preprocessor = MagicMock()
    nlp_preprocessor.process.side_effect = lambda x: x
    
    engine = AutomationEngine(
        parser=parser,
        resolver=resolver,
        task_planner=task_planner,
        executor=executor,
        history_manager=history_manager,
        nlp_preprocessor=nlp_preprocessor
    )
    return engine

def test_open_steam_then_discord(engine):
    engine.process_command("Open Steam then Discord")
    called_args = engine.executor.execute.call_args[0][0]
    assert len(called_args) == 2
    assert called_args[0]["action"] == "open_application"
    assert called_args[0]["parameters"]["application_name"].lower() == "steam"
    assert called_args[1]["action"] == "open_application"
    assert called_args[1]["parameters"]["application_name"].lower() == "discord"

def test_open_chrome_discord_github(engine):
    engine.process_command("Open Steam, Discord and GitHub")
    called_args = engine.executor.execute.call_args[0][0]
    assert len(called_args) == 3
    assert called_args[0]["action"] == "open_application"
    assert called_args[0]["parameters"]["application_name"].lower() == "steam"
    assert called_args[1]["action"] == "open_application"
    assert called_args[1]["parameters"]["application_name"].lower() == "discord"
    assert called_args[2]["action"] == "open_application"
    assert called_args[2]["parameters"]["application_name"].lower() == "github"

def test_open_steam_wait_focus(engine):
    engine.process_command("Open Steam and wait until it opens then focus it")
    called_args = engine.executor.execute.call_args[0][0]
    assert len(called_args) == 3
    assert called_args[0]["action"] == "open_application"
    assert called_args[1]["action"] == "wait"
    assert called_args[2]["action"] == "focus_window"
    assert called_args[2]["parameters"]["window_name"].lower() == "steam"

def test_wait_discord_maximize(engine):
    engine.process_command("Wait until Discord opens then maximize it")
    called_args = engine.executor.execute.call_args[0][0]
    assert len(called_args) == 2
    assert called_args[0]["action"] == "wait"
    assert called_args[1]["action"] == "maximize_window"
    assert called_args[1]["parameters"]["window_name"].lower() == "discord"

def test_if_discord_running(engine):
    engine.process_command("If Discord is running focus it")
    engine.executor.execute.assert_not_called()

def test_if_not_running(engine):
    engine.process_command("If Discord is not running open Discord")
    engine.executor.execute.assert_not_called()

def test_open_chrome_after_discord(engine):
    engine.process_command("Open Steam after Discord")
    called_args = engine.executor.execute.call_args[0][0]
    assert len(called_args) == 2
    assert called_args[0]["action"] == "dummy"
    assert called_args[1]["action"] == "open_application"
    assert called_args[1]["parameters"]["application_name"].lower() == "steam"

def test_open_four_apps(engine):
    engine.process_command("Open Steam, then Discord, then GitHub, then WhatsApp")
    called_args = engine.executor.execute.call_args[0][0]
    assert len(called_args) == 4
    assert called_args[0]["parameters"]["application_name"].lower() == "steam"
    assert called_args[1]["parameters"]["application_name"].lower() == "discord"
    assert called_args[2]["parameters"]["application_name"].lower() == "github"
    assert called_args[3]["parameters"]["application_name"].lower() == "whatsapp"

def test_while_opening(engine):
    engine.process_command("Open Discord while opening Steam")
    called_args = engine.executor.execute.call_args[0][0]
    assert len(called_args) == 2
    # opening steam, open discord -> Y, X
    assert "steam" in called_args[0]["parameters"].get("cmd", "").lower()

def test_followed_by(engine):
    engine.process_command("Open Steam followed by VS Code")
    called_args = engine.executor.execute.call_args[0][0]
    assert len(called_args) == 2
    assert called_args[0]["parameters"]["application_name"].lower() == "steam"
    assert called_args[1]["action"] == "search_web"

def test_open_steam_discord_focus_it(engine):
    engine.process_command("open steam then open discord then focus it")
    called_args = engine.executor.execute.call_args[0][0]
    assert len(called_args) == 3
    assert called_args[2]["action"] == "focus_window"
    assert called_args[2]["parameters"]["window_name"].lower() == "discord"

def test_open_steam_discord_focus_previous(engine):
    engine.process_command("open steam then open discord then focus previous app")
    called_args = engine.executor.execute.call_args[0][0]
    assert len(called_args) == 3
    assert called_args[2]["action"] == "focus_window"
    assert called_args[2]["parameters"]["window_name"].lower() == "steam"

def test_debug_commands_bypass(engine):
    engine.process_command("show context")
    called_args = engine.executor.execute.call_args[0][0]
    assert called_args["action"] == "debug_context"

    engine.executor.execute.reset_mock()
    engine.process_command("debug context")
    called_args = engine.executor.execute.call_args[0][0]
    assert called_args["action"] == "debug_context"
