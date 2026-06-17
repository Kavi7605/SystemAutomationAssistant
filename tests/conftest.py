import sys
import os
import unittest
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

@pytest.fixture(autouse=True)
def inject_mocks_into_unittest(request, monkeypatch):
    """
    Automatically injects standardized mocks and an initialized AutomationEngine
    into any unittest.TestCase class within the tests directory.
    This centralized fixture eliminates duplicated setUp logic across historical files.
    """
    if request.cls and issubclass(request.cls, unittest.TestCase):
        # 1. Standard Mocks
        request.instance.parser_mock = MagicMock(spec=CommandParser)
        request.instance.resolver_mock = MagicMock(spec=CommandResolver)
        request.instance.task_planner_mock = MagicMock(spec=TaskPlanner)
        request.instance.executor_mock = MagicMock(spec=Executor)
        request.instance.history_manager_mock = MagicMock(spec=HistoryManager)
        
        # Alias for history_mock used in some files
        request.instance.history_mock = request.instance.history_manager_mock
        
        request.instance.resolver_mock.resolve.side_effect = lambda x: x
        
        # 2. Automation Engine
        request.instance.engine = AutomationEngine(
            parser=request.instance.parser_mock,
            resolver=request.instance.resolver_mock,
            task_planner=request.instance.task_planner_mock,
            executor=request.instance.executor_mock,
            history_manager=request.instance.history_manager_mock
        )

        # 3. Application Finder (Shared mock)
        def _mock_find_app(*args):
            name = args[-1]
            name_lower = name.lower()
            if name_lower in ["github", "vscode", "steam", "discord", "whatsapp", "lively wallpaper"]:
                return {"path": f"C:\\Program Files\\{name_lower}.exe", "arguments": ""}
            return None
            
        request.instance._mock_find_app = _mock_find_app
        request.instance.app_finder = ApplicationFinder()
        request.instance.app_finder.find_application = MagicMock(side_effect=_mock_find_app)
        
        # Monkeypatch globally for code calling ApplicationFinder() internally
        monkeypatch.setattr(ApplicationFinder, 'find_application', _mock_find_app)
