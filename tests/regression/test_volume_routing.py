import pytest
from unittest.mock import MagicMock

from src.automation.engine import AutomationEngine

@pytest.fixture
def mock_engine():
    parser = MagicMock()
    resolver = MagicMock()
    task_planner = MagicMock()
    executor = MagicMock()
    history_manager = MagicMock()
    context_manager = MagicMock()
    context_manager.state = {}
    
    reference_resolver = MagicMock()

    # The parser shouldn't be called, so mock parse_command to return something
    # but we'll assert it's not called.
    parser.parse_command.return_value = None
    
    # Task planner shouldn't be called
    task_planner.plan_tasks.return_value = []
    
    # We just want to inspect what goes into executor
    def dummy_execute(parsed_commands):
        return {"status": "success", "message": "Executed"}
        
    executor.execute.side_effect = dummy_execute

    engine = AutomationEngine(
        parser=parser,
        resolver=resolver,
        task_planner=task_planner,
        executor=executor,
        history_manager=history_manager,
        context_manager=context_manager,
        reference_resolver=reference_resolver
    )
    return engine, parser, task_planner, executor

@pytest.mark.parametrize("command, expected_action", [
    ("mute", "mute_volume"),
    ("mute volume", "mute_volume"),
    ("mute pc", "mute_volume"),
    ("mute sound", "mute_volume"),
    ("unmute", "unmute_volume"),
    ("unmute pc", "unmute_volume"),
    ("unmute sound", "unmute_volume"),
    ("volume up", "increase_volume"),
    ("sound up", "increase_volume"),
    ("increase volume", "increase_volume"),
    ("decrease volume", "decrease_volume"),
    ("volume down", "decrease_volume"),
    ("sound down", "decrease_volume"),
    ("volume status", "volume_status"),
    ("current volume", "volume_status"),
    ("what is my volume", "volume_status"),
])
def test_volume_routing_bypasses_planner(mock_engine, command, expected_action):
    engine, parser, task_planner, executor = mock_engine
    
    engine.process_command(command)
    
    # Assert planners were not called
    assert task_planner.plan_tasks.call_count == 0
    assert parser.parse_command.call_count == 0
    
    # Assert correct action was routed to executor
    executor.execute.assert_called_once()
    called_args = executor.execute.call_args[0][0]
    
    if isinstance(called_args, list):
        assert called_args[0]["action"] == expected_action
    else:
        assert called_args["action"] == expected_action


@pytest.mark.parametrize("command, expected_level", [
    ("set volume 50", 50),
    ("set volume to 75", 75),
    ("set volume 0", 0),
    ("set volume 100", 100),
    ("set volume 25 percent", 25),
    ("set volume to 10%", 10),
    ("set pc volume to 25", 25)
])
def test_set_volume_routing(mock_engine, command, expected_level):
    engine, parser, task_planner, executor = mock_engine
    
    engine.process_command(command)
    
    assert task_planner.plan_tasks.call_count == 0
    assert parser.parse_command.call_count == 0
    
    executor.execute.assert_called_once()
    called_args = executor.execute.call_args[0][0]
    
    if isinstance(called_args, list):
        cmd_obj = called_args[0]
    else:
        cmd_obj = called_args
        
    assert cmd_obj["action"] == "set_volume"
    assert cmd_obj["parameters"]["level"] == expected_level
