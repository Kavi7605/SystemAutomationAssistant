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
    ("display status", "display_status"),
    ("show display settings", "display_status"),
    ("current display settings", "display_status"),
    ("current resolution", "display_status"),
    ("what is my resolution", "display_status"),
    ("current refresh rate", "display_status"),
    ("monitor count", "display_status"),
    ("connected monitors", "display_status"),
    ("display info", "display_status"),
    ("monitor info", "display_status"),
    ("primary monitor", "display_status"),
    ("monitor status", "display_status"),
    ("screen information", "display_status"),
])
def test_display_routing_bypasses_planner(mock_engine, command, expected_action):
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
