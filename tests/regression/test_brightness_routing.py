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

    parser.parse_command.return_value = None
    task_planner.plan_tasks.return_value = []
    
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
    ("brightness up", "increase_brightness"),
    ("increase brightness", "increase_brightness"),
    ("raise brightness", "increase_brightness"),
    ("brightness down", "decrease_brightness"),
    ("decrease brightness", "decrease_brightness"),
    ("lower brightness", "decrease_brightness"),
    ("brightness status", "brightness_status"),
    ("current brightness", "brightness_status"),
    ("what is my brightness", "brightness_status"),
    ("show brightness", "brightness_status"),
])
def test_brightness_routing_bypasses_planner(mock_engine, command, expected_action):
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
    ("set brightness 50", 50),
    ("set brightness to 75", 75),
    ("set brightness 0", 0),
    ("set brightness 100", 100),
    ("set brightness 25 percent", 25),
    ("set screen brightness to 10%", 10),
    ("set screen brightness 25", 25)
])
def test_set_brightness_routing(mock_engine, command, expected_level):
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
        
    assert cmd_obj["action"] == "set_brightness"
    assert cmd_obj["parameters"]["level"] == expected_level
