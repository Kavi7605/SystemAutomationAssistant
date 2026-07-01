import sys
import os
import pytest
from unittest.mock import MagicMock

# Ensure the root directory is accessible for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.automation.engine import AutomationEngine
from src.core.command_parser import CommandParser
from src.core.history_manager import HistoryManager
from src.planner.resolver import CommandResolver
from src.planner.task_planner import TaskPlanner
from src.automation.executor import Executor
from src.tools.application_finder import ApplicationFinder

@pytest.fixture
def _mock_find_app():
    def _mock(*args):
        name = args[-1] if args else ""
        name_lower = name.lower()
        if name_lower in ["github", "vscode", "steam", "discord", "whatsapp", "lively wallpaper", "notepad", "calculator"]:
            return {"path": f"C:\\Program Files\\{name_lower}.exe", "arguments": ""}
        return None
    return _mock

@pytest.fixture(autouse=True)
def mock_application_finder(monkeypatch, _mock_find_app):
    monkeypatch.setattr(ApplicationFinder, 'find_application', _mock_find_app)

@pytest.fixture
def _mock_resolve_smart_item():
    def _mock(target, preferred_extension=None, **kwargs):
        target_lower = target.lower()
        workspace_items = ["report", "notes.txt", "test.txt", "demo.py"]
        if any(item in target_lower for item in workspace_items):
            return {"status": "success", "resolved_name": target, "path": "mock"}
        return {"status": "not_found"}
    return _mock

@pytest.fixture(autouse=True)
def mock_filesystem_tools(request, monkeypatch, _mock_resolve_smart_item):
    if any(name in str(request.node.fspath) for name in ["test_filesystem_tools.py", "test_smart_discovery.py", "test_interactive_disambiguation.py", "test_filesystem_stabilization.py", "test_day23_intelligent_filesystem.py", "test_day23_final.py"]):
        return
    try:
        import src.tools.filesystem_tools as ft
        monkeypatch.setattr(ft, 'resolve_smart_item', _mock_resolve_smart_item)
    except ImportError:
        pass

@pytest.fixture
def parser_mock():
    return MagicMock(spec=CommandParser)

@pytest.fixture
def resolver_mock():
    mock = MagicMock(spec=CommandResolver)
    mock.resolve.side_effect = lambda x: x
    return mock

@pytest.fixture
def task_planner_mock():
    return MagicMock(spec=TaskPlanner)

@pytest.fixture
def executor_mock():
    return MagicMock(spec=Executor)

@pytest.fixture
def history_manager_mock():
    return MagicMock(spec=HistoryManager)

@pytest.fixture
def engine(request, parser_mock, resolver_mock, task_planner_mock, executor_mock, history_manager_mock):
    from src.context.context_manager import ContextManager
    from src.context.reference_resolver import ReferenceResolver
    
    cm = ContextManager()
    rr = ReferenceResolver(cm)

    return AutomationEngine(
        parser=parser_mock,
        resolver=resolver_mock,
        task_planner=task_planner_mock,
        executor=executor_mock,
        history_manager=history_manager_mock,
        context_manager=cm,
        reference_resolver=rr
    )

@pytest.fixture(autouse=True)
def inject_mocks_into_class(request, engine, parser_mock, resolver_mock, task_planner_mock, executor_mock, history_manager_mock):
    """Injects standardized mocks and AutomationEngine into any test class automatically."""
    if request.cls:
        request.cls.engine = engine
        request.cls.parser_mock = parser_mock
        request.cls.resolver_mock = resolver_mock
        request.cls.task_planner_mock = task_planner_mock
        request.cls.executor_mock = executor_mock
        request.cls.history_manager_mock = history_manager_mock
        request.cls.history_mock = history_manager_mock
