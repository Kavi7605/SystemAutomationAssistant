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

class TestDay8Part3(unittest.TestCase):
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

    def test_priority1_search_intent_bypass_planner(self):
        commands = [
            ("open github and search kavi7605 user", "github.com", "kavi7605"),
            ("open github and search python repositories", "github.com", "python"),
            ("open youtube and search avengers", "youtube.com", "avengers"),
            ("open reddit and search python", "reddit", "python"),
        ]
        
        from src.tools.application_finder import ApplicationFinder
        original_find = ApplicationFinder.find_application
        ApplicationFinder.find_application = self._mock_find_app
        
        try:
            for cmd, domain_hint, query_hint in commands:
                self.engine.process_command(cmd)
                self.task_planner_mock.plan_tasks.assert_not_called()
                self.assertExecute("open_url")
                url = self.executor_mock.execute.call_args[0][0]["parameters"]["url"]
                self.assertIn(domain_hint, url)
                self.assertIn(query_hint, url)
                self.executor_mock.reset_mock()
        finally:
            ApplicationFinder.find_application = original_find

    def test_priority2_natural_website_search_grammar(self):
        commands = [
            ("open youtube website avengers", "avengers"),
            ("open youtube website shorts", "shorts"),
            ("open github website kavi7605", "kavi7605"),
            ("open github website kavi7605 user", "kavi7605"),
            ("open github website kavi7605 users", "kavi7605"),
            ("open github website python repositories", "python")
        ]
        
        for cmd, query_hint in commands:
            self.engine.process_command(cmd)
            self.task_planner_mock.plan_tasks.assert_not_called()
            self.assertExecute("open_url")
            url = self.executor_mock.execute.call_args[0][0]["parameters"]["url"]
            self.assertIn(query_hint, url)
            self.executor_mock.reset_mock()

    def test_priority3_close_application_classification(self):
        from src.tools.application_finder import ApplicationFinder
        original_find = ApplicationFinder.find_application
        ApplicationFinder.find_application = self._mock_find_app
        
        try:
            commands = [
                ("close lively wallpaper", "lively wallpaper"),
                ("close steam", "steam"),
                ("close whatsapp", "whatsapp")
            ]
            
            for cmd, app_name in commands:
                self.engine.process_command(cmd)
                self.task_planner_mock.plan_tasks.assert_not_called()
                self.assertExecute("close_application", {"application_name": app_name})
                self.executor_mock.reset_mock()
        finally:
            ApplicationFinder.find_application = original_find

if __name__ == "__main__":
    unittest.main()

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

class TestDay8SearchPart2(unittest.TestCase):
    def _mock_find_app(self, name):
        name_lower = name.lower()
        if name_lower in ["github", "vscode", "steam", "discord"]:
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

    def test_baseline_github(self):
        # open github -> AppFinder says it's installed -> Application
        from src.tools.application_finder import ApplicationFinder
        original_find = ApplicationFinder.find_application
        ApplicationFinder.find_application = self._mock_find_app
        
        try:
            self.engine.process_command("open github")
            self.task_planner_mock.plan_tasks.assert_not_called()
            self.assertExecute("open_application", {"application_name": "github"})
            self.executor_mock.reset_mock()
            
            # open github website -> Website
            self.engine.process_command("open github website")
            self.task_planner_mock.plan_tasks.assert_not_called()
            self.assertExecute("open_url")
        finally:
            ApplicationFinder.find_application = original_find

    def test_baseline_youtube(self):
        from src.tools.application_finder import ApplicationFinder
        original_find = ApplicationFinder.find_application
        ApplicationFinder.find_application = self._mock_find_app
        
        try:
            # open youtube -> not installed, but in registry -> Website
            self.engine.process_command("open youtube")
            self.task_planner_mock.plan_tasks.assert_not_called()
            self.assertExecute("open_url")
            self.executor_mock.reset_mock()
            
            # open youtube website -> Website
            self.engine.process_command("open youtube website")
            self.task_planner_mock.plan_tasks.assert_not_called()
            self.assertExecute("open_url")
        finally:
            ApplicationFinder.find_application = original_find

    def test_multi_action_combinations(self):
        from src.tools.application_finder import ApplicationFinder
        original_find = ApplicationFinder.find_application
        ApplicationFinder.find_application = self._mock_find_app
        
        try:
            # open github and github website -> App + Website
            self.engine.process_command("open github and github website")
            cmds = self.executor_mock.execute.call_args[0][0]
            self.assertEqual(len(cmds), 2)
            self.assertEqual(cmds[0]["action"], "open_application")
            self.assertEqual(cmds[1]["action"], "open_url")
            self.executor_mock.reset_mock()
            
            # open github and youtube -> App + Website
            self.engine.process_command("open github and youtube")
            cmds = self.executor_mock.execute.call_args[0][0]
            self.assertEqual(len(cmds), 2)
            self.assertEqual(cmds[0]["action"], "open_application")
            self.assertEqual(cmds[1]["action"], "open_url")
            self.executor_mock.reset_mock()
            
            # open youtube and github -> Website + App
            self.engine.process_command("open youtube and github")
            cmds = self.executor_mock.execute.call_args[0][0]
            self.assertEqual(len(cmds), 2)
            self.assertEqual(cmds[0]["action"], "open_url")
            self.assertEqual(cmds[1]["action"], "open_application")
            self.executor_mock.reset_mock()
            
            # open vscode and steam -> App + App
            self.engine.process_command("open vscode and steam")
            cmds = self.executor_mock.execute.call_args[0][0]
            self.assertEqual(len(cmds), 2)
            self.assertEqual(cmds[0]["action"], "open_application")
            self.assertEqual(cmds[1]["action"], "open_application")
            self.executor_mock.reset_mock()
            
            # open vscode and github website -> App + Website
            self.engine.process_command("open vscode and github website")
            cmds = self.executor_mock.execute.call_args[0][0]
            self.assertEqual(len(cmds), 2)
            self.assertEqual(cmds[0]["action"], "open_application")
            self.assertEqual(cmds[1]["action"], "open_url")
        finally:
            ApplicationFinder.find_application = original_find

    def test_search_normalization(self):
        # open github website kavi7605 user
        self.engine.process_command("open github website kavi7605 user")
        self.assertExecute("open_url")
        url = self.executor_mock.execute.call_args[0][0]["parameters"]["url"]
        self.assertIn("kavi7605", url)
        self.assertIn("users", url)
        self.executor_mock.reset_mock()
        
        # open github website and search kavi7605 user
        self.engine.process_command("open github website and search kavi7605 user")
        self.assertExecute("open_url")
        url2 = self.executor_mock.execute.call_args[0][0]["parameters"]["url"]
        self.assertEqual(url, url2)
        self.executor_mock.reset_mock()
        
        # open youtube website shorts
        self.engine.process_command("open youtube website shorts")
        self.assertExecute("open_url")
        url = self.executor_mock.execute.call_args[0][0]["parameters"]["url"]
        self.assertIn("shorts", url)

    def test_search_validation_modes(self):
        invalid_queries = ["user", "repository", "issue"]
        for query in invalid_queries:
            self.engine.process_command(f"open github website {query}")
            cmd = self.executor_mock.execute.call_args[0][0]
            if isinstance(cmd, list): cmd = cmd[0]
            self.assertEqual(cmd["action"], "unsupported")
            self.assertIn("Validation error", cmd["parameters"]["message"])
            self.assertIn(f"before search mode '{query}'", cmd["parameters"]["message"])
            self.executor_mock.reset_mock()

    def test_folder_navigation(self):
        # open reports folder
        self.engine.process_command("open reports folder")
        self.assertExecute("open_folder", {"folder_name": "reports"})
        self.executor_mock.reset_mock()
        
        # open reports folder in c drive kavi work degree
        self.engine.process_command("open reports folder in c drive kavi work degree")
        self.assertExecute("open_folder", {"folder_name": "reports", "base_path": "c drive kavi work degree"})
        self.executor_mock.reset_mock()
        
        # open folder reports
        self.engine.process_command("open folder reports")
        self.assertExecute("open_folder", {"folder_name": "reports"})
        self.executor_mock.reset_mock()
        
        # open folder reports in c drive kavi work degree
        self.engine.process_command("open folder reports in c drive kavi work degree")
        self.assertExecute("open_folder", {"folder_name": "reports", "base_path": "c drive kavi work degree"})
        self.executor_mock.reset_mock()

    def test_unknown_target_search_fallback(self):
        from src.tools.application_finder import ApplicationFinder
        original_find = ApplicationFinder.find_application
        ApplicationFinder.find_application = self._mock_find_app
        
        try:
            self.engine.process_command("open quantum computing")
            self.assertExecute("search_web", {"query": "quantum computing"})
            self.executor_mock.reset_mock()
            
            self.engine.process_command("open kavi7605")
            self.assertExecute("search_web", {"query": "kavi7605"})
        finally:
            ApplicationFinder.find_application = original_find

    def test_open_test_txt_in_desktop(self):
        self.engine.process_command("open test.txt in desktop")
        self.assertExecute("open_file", {"file_name": "test.txt", "path": "desktop"})
        self.executor_mock.reset_mock()

    def test_open_vscode_and_close_steam(self):
        self.task_planner_mock.plan_tasks.return_value = ["open vscode", "close steam"]
        self.parser_mock.parse_command.side_effect = [
            {"action": "open_application", "parameters": {"application_name": "vscode"}},
            {"action": "close_application", "parameters": {"application_name": "steam"}}
        ]
        self.engine.process_command("open vscode and close steam")
        self.task_planner_mock.plan_tasks.assert_called_once()
        self.executor_mock.execute.assert_called()


