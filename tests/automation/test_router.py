import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.automation.engine import AutomationEngine
from src.core.command_parser import CommandParser
from src.core.history_manager import HistoryManager
from src.planner.resolver import CommandResolver
from src.planner.task_planner import TaskPlanner
from src.automation.executor import Executor

class TestSemanticRouting(unittest.TestCase):
    def test_1_open_github_bypasses_parser_and_planner(self):
        self.executor_mock.execute.return_value = {"status": "success", "message": "Success"}
        self.engine.process_command("open github")
        
        self.task_planner_mock.plan_tasks.assert_not_called()
        self.parser_mock.parse_command.assert_not_called()
        
        call_args = self.executor_mock.execute.call_args[0][0]
        self.assertEqual(call_args["action"], "open_application")
        self.assertEqual(call_args["parameters"]["application_name"], "github")

    def test_2_open_github_website_routes_to_url(self):
        self.executor_mock.execute.return_value = {"status": "success", "message": "Success"}
        self.engine.process_command("open github website")
        
        self.task_planner_mock.plan_tasks.assert_not_called()
        self.parser_mock.parse_command.assert_not_called()
        
        call_args = self.executor_mock.execute.call_args[0][0]
        self.assertEqual(call_args["action"], "open_url")
        self.assertEqual(call_args["parameters"]["url"], "https://github.com")

    def test_3_open_github_website_python_projects_single_url(self):
        self.executor_mock.execute.return_value = {"status": "success", "message": "Success"}
        self.engine.process_command("open github website python projects")
        
        self.task_planner_mock.plan_tasks.assert_not_called()
        self.parser_mock.parse_command.assert_not_called()
        
        call_args = self.executor_mock.execute.call_args[0][0]
        self.assertEqual(call_args["action"], "open_url")
        self.assertEqual(call_args["parameters"]["url"], "https://github.com/search?q=python+projects&type=repositories")

    def test_4_open_youtube_website_ghost_of_yotei_single_url(self):
        self.executor_mock.execute.return_value = {"status": "success", "message": "Success"}
        self.engine.process_command("open youtube website ghost of yotei")
        
        self.task_planner_mock.plan_tasks.assert_not_called()
        self.parser_mock.parse_command.assert_not_called()
        
        call_args = self.executor_mock.execute.call_args[0][0]
        self.assertEqual(call_args["action"], "open_url")
        self.assertEqual(call_args["parameters"]["url"], "https://www.youtube.com/results?search_query=ghost+of+yotei")

    def test_5_open_domain_name_routes_to_url(self):
        self.executor_mock.execute.return_value = {"status": "success", "message": "Success"}
        self.engine.process_command("open github.com")
        
        self.task_planner_mock.plan_tasks.assert_not_called()
        self.parser_mock.parse_command.assert_not_called()
        
        call_args = self.executor_mock.execute.call_args[0][0]
        self.assertEqual(call_args["action"], "open_url")
        self.assertEqual(call_args["parameters"]["url"], "https://github.com")

    def test_6_create_test_txt_routes_to_create_file(self):
        self.executor_mock.execute.return_value = {"status": "success", "message": "Success"}
        self.engine.process_command("create test.txt")
        
        self.task_planner_mock.plan_tasks.assert_not_called()
        self.parser_mock.parse_command.assert_not_called()
        
        call_args = self.executor_mock.execute.call_args[0][0]
        self.assertEqual(call_args["action"], "create_file")
        self.assertEqual(call_args["parameters"]["file_name"], "test.txt")

if __name__ == "__main__":
    unittest.main()
