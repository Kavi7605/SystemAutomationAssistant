import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_engine():
    parser = MagicMock()
    task_planner = MagicMock()
    executor = MagicMock()
    
    resolver = MagicMock()
    history_manager = MagicMock()
    context_manager = MagicMock()
    context_manager.state = {}
    context_manager.get_context_snapshot.return_value = {"system_state": {}}
    
    from src.automation.engine import AutomationEngine
    engine = AutomationEngine(
        parser=parser, 
        task_planner=task_planner, 
        executor=executor,
        resolver=resolver,
        history_manager=history_manager,
        context_manager=context_manager
    )
    
    return engine, parser, task_planner, executor

@pytest.mark.parametrize("command, expected_action", [
    ("shutdown pc", "shutdown_pc"),
    ("turn off pc", "shutdown_pc"),
    ("shutdown the pc", "shutdown_pc"),
    ("restart pc", "restart_pc"),
    ("reboot computer", "restart_pc"),
    ("sleep pc", "sleep_pc"),
    ("put pc to sleep", "sleep_pc"),
    ("lock screen", "lock_screen"),
    ("lock the computer", "lock_screen"),
    ("confirm shutdown", "confirm_power_action"),
    ("confirm restart", "confirm_power_action"),
    ("cancel", "cancel_power_action"),
    ("cancel shutdown", "cancel_power_action")
])
def test_power_actions_routing_bypasses_planner(mock_engine, command, expected_action):
    engine, parser, task_planner, executor = mock_engine
    
    engine.process_command(command)
    
    assert task_planner.plan_tasks.call_count == 0
    assert parser.parse_command.call_count == 0
    
    executor.execute.assert_called_once()
    executed_command = executor.execute.call_args[0][0]
    
    assert executed_command["action"] == expected_action
