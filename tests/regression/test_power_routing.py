import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_engine():
    parser = MagicMock()
    task_planner = MagicMock()
    executor = MagicMock()
    
    resolver = MagicMock()
    history_manager = MagicMock()
    
    from src.automation.engine import AutomationEngine
    engine = AutomationEngine(
        parser=parser, 
        task_planner=task_planner, 
        executor=executor,
        resolver=resolver,
        history_manager=history_manager
    )
    
    return engine, parser, task_planner, executor

@pytest.mark.parametrize("command, expected_action, expected_mode", [
    ("battery saver status", "battery_saver_status", None),
    ("current battery saver status", "battery_saver_status", None),
    
    ("available power modes", "list_power_profiles", None),
    ("list power profiles", "list_power_profiles", None),
    
    ("current power mode", "power_status", None),
    ("power status", "power_status", None),
    
    ("switch to performance mode", "set_power_mode", "performance"),
    ("switch to silent mode", "set_power_mode", "silent"),
    ("switch to turbo", "set_power_mode", "turbo"),
    ("balanced mode", "set_power_mode", "balanced")
])
def test_power_routing_bypasses_planner(mock_engine, command, expected_action, expected_mode):
    engine, parser, task_planner, executor = mock_engine
    
    engine.process_command(command)
    
    # Assert bypass
    assert task_planner.plan_tasks.call_count == 0
    assert parser.parse_command.call_count == 0
    
    # Assert exact execution json
    executor.execute.assert_called_once()
    executed_command = executor.execute.call_args[0][0]
    
    assert executed_command["action"] == expected_action
    
    if expected_mode:
        assert executed_command["parameters"]["mode"] == expected_mode
    else:
        assert executed_command["parameters"] == {}
