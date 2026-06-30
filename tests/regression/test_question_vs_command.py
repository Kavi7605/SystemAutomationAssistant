import pytest
from src.core.command_parser import CommandParser
from src.automation.engine import AutomationEngine
from src.planner.resolver import CommandResolver
from src.planner.task_planner import TaskPlanner
from src.automation.executor import Executor
from src.core.history_manager import HistoryManager

@pytest.fixture
def engine():
    from src.tools.registry import ToolRegistry
    registry = ToolRegistry()
    parser = CommandParser(None, registry)
    resolver = CommandResolver()
    task_planner = TaskPlanner()
    executor = Executor(registry)
    history_manager = HistoryManager()
    
    return AutomationEngine(
        parser=parser,
        resolver=resolver,
        task_planner=task_planner,
        executor=executor,
        history_manager=history_manager
    )

def test_questions_vs_commands(engine):
    # Questions
    q1 = engine._route_semantic_command("What windows are open")
    assert q1["action"] == "list_open_windows"
    
    q2 = engine._route_semantic_command("Which applications are running")
    assert q2["action"] == "list_open_windows"
    
    q3 = engine._route_semantic_command("What is my volume")
    assert q3["action"] == "volume_status"
    
    q4 = engine._route_semantic_command("Is WiFi enabled")
    assert q4["action"] == "wifi_status"
    
    q5 = engine._route_semantic_command("What apps are running")
    assert q5["action"] == "list_open_windows"
    
    q6 = engine._route_semantic_command("What is the current volume")
    assert q6["action"] == "volume_status"

    # The normalizers handle politeness and simplification before routing
    # But since engine._route_semantic_command operates on the text *after* preprocessing,
    # let's assume the preprocessor has already cleaned them up.
    # We will test the full pipeline in another test if needed.
