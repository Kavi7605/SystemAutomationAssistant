import sys
import os
import unittest
from unittest.mock import MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.automation.engine import AutomationEngine
from src.core.command_parser import CommandParser
from src.core.history_manager import HistoryManager
from src.planner.resolver import CommandResolver
from src.planner.task_planner import TaskPlanner
from src.automation.executor import Executor
from src.tools.application_finder import ApplicationFinder

class TestDay8Part4(unittest.TestCase):
    def _mock_find_app(self, name):
        name_lower = name.lower()
        if name_lower in ["github", "vscode", "steam", "discord", "whatsapp", "lively wallpaper"]:
            return {"path": f"C:\\Program Files\\{name_lower}.exe", "arguments": ""}
        return None

    def assertExecute(self, expected_action, expected_params=None, cmd_idx=0):
        self.executor_mock.execute.assert_called()
        cmd = self.executor_mock.execute.call_args[0][0]
        if isinstance(cmd, list):
            cmd = cmd[cmd_idx]
        self.assertEqual(cmd["action"], expected_action)
        if expected_params:
            for k, v in expected_params.items():
                self.assertEqual(cmd["parameters"][k], v)

    def test_bug1_github_classification_inconsistency(self):
        from src.tools.application_finder import ApplicationFinder
        original_find = ApplicationFinder.find_application
        ApplicationFinder.find_application = self._mock_find_app
        
        try:
            # Single command
            self.engine.process_command("open github")
            self.assertExecute("open_application", {"application_name": "github"})
            self.executor_mock.reset_mock()
            
            # Multi-step command
            # The planner outputs the exact names. Engine must route them consistently.
            self.task_planner_mock.plan_tasks.return_value = ["close whatsapp", "open github"]
            
            # Parser should NOT be called if semantic router successfully handles the individual tasks
            self.parser_mock.parse_command.side_effect = AssertionError("Parser should be bypassed by Router for standalone tasks")
            
            self.engine.process_command("close whatsapp and open github")
            
            cmds = self.executor_mock.execute.call_args[0][0]
            self.assertEqual(len(cmds), 2)
            self.assertEqual(cmds[0]["action"], "close_application")
            self.assertEqual(cmds[0]["parameters"]["application_name"], "whatsapp")
            self.assertEqual(cmds[1]["action"], "open_application")
            self.assertEqual(cmds[1]["parameters"]["application_name"], "github")
            self.executor_mock.reset_mock()
            
            # Reversed order
            self.task_planner_mock.plan_tasks.return_value = ["open github", "close whatsapp"]
            self.engine.process_command("open github and close whatsapp")
            cmds = self.executor_mock.execute.call_args[0][0]
            self.assertEqual(len(cmds), 2)
            self.assertEqual(cmds[0]["action"], "open_application")
            self.assertEqual(cmds[0]["parameters"]["application_name"], "github")
            self.assertEqual(cmds[1]["action"], "close_application")
            self.assertEqual(cmds[1]["parameters"]["application_name"], "whatsapp")
            
        finally:
            ApplicationFinder.find_application = original_find

    def test_bug2_close_command_inconsistency(self):
        from src.tools.application_finder import ApplicationFinder
        original_find = ApplicationFinder.find_application
        ApplicationFinder.find_application = self._mock_find_app
        
        try:
            # Single command
            self.engine.process_command("close lively wallpaper")
            self.assertExecute("close_application", {"application_name": "lively wallpaper"})
            self.executor_mock.reset_mock()
            
            # Multi-step command
            self.task_planner_mock.plan_tasks.return_value = ["open whatsapp", "close lively wallpaper"]
            
            # Parser should NOT be called
            self.parser_mock.parse_command.side_effect = AssertionError("Parser should be bypassed")
            
            self.engine.process_command("open whatsapp and close lively wallpaper")
            cmds = self.executor_mock.execute.call_args[0][0]
            self.assertEqual(len(cmds), 2)
            self.assertEqual(cmds[0]["action"], "open_application")
            self.assertEqual(cmds[0]["parameters"]["application_name"], "whatsapp")
            self.assertEqual(cmds[1]["action"], "close_application")
            self.assertEqual(cmds[1]["parameters"]["application_name"], "lively wallpaper")
            
        finally:
            ApplicationFinder.find_application = original_find

if __name__ == "__main__":
    unittest.main()

import pytest
from unittest.mock import MagicMock
from src.automation.engine import AutomationEngine

def test_full_pipeline_routing():
    parser = MagicMock()
    resolver = MagicMock()
    planner = MagicMock()
    executor = MagicMock()
    history = MagicMock()
    
    engine = AutomationEngine(parser, resolver, planner, executor, history)
    
    # 1. open notepad bypasses planner
    engine.process_command("open notepad")
    planner.plan_tasks.assert_not_called()
    executor.execute.assert_called()
    cmd = executor.execute.call_args[0][0]
    if isinstance(cmd, list): cmd = cmd[0]
    assert cmd["action"] == "open_application"
    
    executor.reset_mock()
    planner.reset_mock()
    
    # 2. open github website bypasses planner
    engine.process_command("open github website")
    planner.plan_tasks.assert_not_called()
    executor.execute.assert_called()
    cmd = executor.execute.call_args[0][0]
    if isinstance(cmd, list): cmd = cmd[0]
    assert cmd["action"] == "open_url"
    
    executor.reset_mock()
    planner.reset_mock()
    
    # 3. open github and github website executes two actions
    engine.process_command("open github and github website")
    planner.plan_tasks.assert_not_called()
    executor.execute.assert_called_once()
    cmds = executor.execute.call_args[0][0]
    assert isinstance(cmds, list)
    assert len(cmds) == 2
    assert cmds[0]["action"] == "open_application"
    assert cmds[1]["action"] == "open_url"
    
    executor.reset_mock()
    planner.reset_mock()
    
    # 5. open vscode and close steam still goes through planner
    # Provide a mock plan so it doesn't fail
    planner.plan_tasks.return_value = ["open vscode", "close steam"]
    parser.parse_command.side_effect = [
        {"action": "open_application", "parameters": {"application_name": "vscode"}},
        {"action": "close_application", "parameters": {"application_name": "steam"}}
    ]
    resolver.resolve.side_effect = lambda x: x
    
    engine.process_command("open vscode and close steam")
    planner.plan_tasks.assert_called_once_with("open vscode and close steam")
    executor.execute.assert_called()
