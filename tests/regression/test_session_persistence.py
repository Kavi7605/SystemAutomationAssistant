import pytest
import os
import shutil
from unittest.mock import MagicMock, patch
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.automation.engine import AutomationEngine
from src.core.command_parser import CommandParser
from src.core.history_manager import HistoryManager
from src.planner.resolver import CommandResolver
from src.planner.task_planner import TaskPlanner
from src.automation.executor import Executor
from src.tools.registry import ToolRegistry
from src.context.application_state_manager import ApplicationStateManager
from src.context.context_manager import ContextManager
from src.context.persistence_manager import PersistenceManager

class TestSessionPersistenceRegression:
    def setup_method(self):
        self.test_dir = "tests/data_tmp_reg"
        self.context_file = os.path.join(self.test_dir, "context.json")
        self.state_file = os.path.join(self.test_dir, "state.json")
        
        # Patch WindowManager so we don't need real APIs during test
        self.wm_patcher = patch("src.context.application_state_manager.WindowManager")
        self.mock_wm = self.wm_patcher.start()
        self.mock_wm.get_current_window.return_value = {"hwnd": 123}
        self.mock_wm.find_windows.return_value = []
        
    def teardown_method(self):
        if hasattr(self, 'patcher'):
            self.patcher.stop()
        if hasattr(self, 'wm_patcher'):
            self.wm_patcher.stop()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _create_engine(self):
        parser_mock = MagicMock(spec=CommandParser)
        resolver_mock = MagicMock(spec=CommandResolver)
        task_planner_mock = MagicMock(spec=TaskPlanner)
        history_manager_mock = MagicMock(spec=HistoryManager)
        
        registry_mock = MagicMock(spec=ToolRegistry)
        registry_mock.execute_tool.return_value = {"status": "success", "message": "Simulated tool execution"}
        
        self.patcher = patch("src.tools.application_finder.ApplicationFinder.find_application")
        self.mock_find_app = self.patcher.start()
        self.mock_find_app.return_value = True

        pm = PersistenceManager(context_file=self.context_file, state_file=self.state_file)
        
        state_manager = ApplicationStateManager(pm)
        state_manager.is_running = MagicMock(return_value=False)
        state_manager.is_focused = MagicMock(return_value=False)
        context_manager = ContextManager(pm)
        
        state_manager.load()
        context_manager.load()
        
        executor = Executor(
            registry=registry_mock,
            state_manager=state_manager,
            context_manager=context_manager
        )
        
        engine = AutomationEngine(
            parser=parser_mock,
            resolver=resolver_mock,
            task_planner=task_planner_mock,
            executor=executor,
            history_manager=history_manager_mock,
            context_manager=context_manager
        )
        return engine, context_manager, state_manager

    def test_session_restart_retains_history(self):
        # Session 1
        engine1, context_manager1, _ = self._create_engine()
        engine1.process_command("open steam")
        engine1.process_command("focus steam")
        engine1.process_command("open discord")
        
        assert context_manager1.get_open_history() == ["steam", "discord"]
        
        # Simulate restart: Destroy everything and create Session 2
        engine2, context_manager2, _ = self._create_engine()
        
        # Verify state is restored
        assert context_manager2.get_open_history() == ["steam", "discord"]
        
        # Further mutations in Session 2
        engine2.process_command("open spotify")
        assert context_manager2.get_open_history() == ["steam", "discord", "spotify"]
        
        # Simulate restart: Session 3
        _, context_manager3, _ = self._create_engine()
        assert context_manager3.get_open_history() == ["steam", "discord", "spotify"]
