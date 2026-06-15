import sys
import os
import unittest
from unittest.mock import MagicMock

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.automation.engine import AutomationEngine
from src.core.command_parser import CommandParser
from src.core.history_manager import HistoryManager
from src.planner.resolver import CommandResolver
from src.planner.task_planner import TaskPlanner
from src.automation.executor import Executor

class TestFilesystemBypass(unittest.TestCase):
    def setUp(self):
        # Mock components to isolate the engine router logic
        self.parser_mock = MagicMock(spec=CommandParser)
        self.resolver_mock = MagicMock(spec=CommandResolver)
        self.task_planner_mock = MagicMock(spec=TaskPlanner)
        self.executor_mock = MagicMock(spec=Executor)
        self.history_mock = MagicMock(spec=HistoryManager)

        # Setup default mock behaviors
        self.resolver_mock.resolve.side_effect = lambda x: x
        
        self.engine = AutomationEngine(
            parser=self.parser_mock,
            resolver=self.resolver_mock,
            task_planner=self.task_planner_mock,
            executor=self.executor_mock,
            history_manager=self.history_mock
        )

    def test_1_create_folder_bypasses_planner(self):
        input_cmd = "create folder testing in C drive Kavi Work Degree Charusat Sem 7 Internship"
        self.parser_mock.parse_command.return_value = {
            "action": "create_folder",
            "parameters": {"folder_name": "testing", "path": "C drive Kavi Work Degree Charusat Sem 7 Internship"}
        }
        self.executor_mock.execute.return_value = {"status": "success", "message": "Success"}
        
        self.engine.process_command(input_cmd)
        
        # Verify TaskPlanner was NOT called
        self.task_planner_mock.plan_tasks.assert_not_called()
        
        # Verify CommandParser received the exact original string
        self.parser_mock.parse_command.assert_called_once_with(input_cmd)

    def test_2_create_file_bypasses_planner(self):
        input_cmd = "create file notes.txt in desktop"
        self.parser_mock.parse_command.return_value = {
            "action": "create_file",
            "parameters": {"file_name": "notes.txt", "path": "desktop"}
        }
        self.executor_mock.execute.return_value = {"status": "success", "message": "Success"}
        
        self.engine.process_command(input_cmd)
        
        # Verify TaskPlanner was NOT called
        self.task_planner_mock.plan_tasks.assert_not_called()

    def test_2b_create_filename_ext_bypasses_planner(self):
        input_cmd = "create notes.txt in C drive Kavi Work Degree Charusat SEM 7 Internship"
        self.parser_mock.parse_command.return_value = {
            "action": "create_file",
            "parameters": {"file_name": "notes.txt", "path": "C drive Kavi Work Degree Charusat SEM 7 Internship"}
        }
        self.executor_mock.execute.return_value = {"status": "success", "message": "Success"}
        self.engine.process_command(input_cmd)
        self.task_planner_mock.plan_tasks.assert_not_called()

    def test_2c_create_report_docx_bypasses_planner(self):
        input_cmd = "create report.docx in desktop"
        self.parser_mock.parse_command.return_value = {
            "action": "create_file",
            "parameters": {"file_name": "report.docx", "path": "desktop"}
        }
        self.executor_mock.execute.return_value = {"status": "success", "message": "Success"}
        self.engine.process_command(input_cmd)
        self.task_planner_mock.plan_tasks.assert_not_called()

    def test_2d_create_demo_py_bypasses_planner(self):
        input_cmd = "create demo.py in downloads"
        self.parser_mock.parse_command.return_value = {
            "action": "create_file",
            "parameters": {"file_name": "demo.py", "path": "downloads"}
        }
        self.executor_mock.execute.return_value = {"status": "success", "message": "Success"}
        self.engine.process_command(input_cmd)
        self.task_planner_mock.plan_tasks.assert_not_called()

    def test_2e_open_file_bypasses_parser_and_planner(self):
        input_cmd = "open file report.docx in desktop"
        # We don't mock parser return value, because it shouldn't be called at all!
        self.executor_mock.execute.return_value = {"status": "success", "message": "Success"}
        self.engine.process_command(input_cmd)
        self.task_planner_mock.plan_tasks.assert_not_called()
        self.parser_mock.parse_command.assert_not_called()
        
        # Verify executor received the synthesized JSON
        call_args = self.executor_mock.execute.call_args[0][0]
        assert call_args["action"] == "open_file"
        assert call_args["parameters"]["file_name"] == "report.docx"
        assert call_args["parameters"]["path"] == "desktop"

    def test_2f_open_filename_ext_bypasses_parser_and_planner(self):
        input_cmd = "open notes.txt in C drive Kavi Work Degree Charusat SEM 7 Internship"
        self.executor_mock.execute.return_value = {"status": "success", "message": "Success"}
        self.engine.process_command(input_cmd)
        self.task_planner_mock.plan_tasks.assert_not_called()
        self.parser_mock.parse_command.assert_not_called()
        
        call_args = self.executor_mock.execute.call_args[0][0]
        assert call_args["action"] == "open_file"
        assert call_args["parameters"]["file_name"] == "notes.txt"
        assert call_args["parameters"]["path"] == "C drive Kavi Work Degree Charusat SEM 7 Internship"

    def test_2g_open_filename_only_bypasses_parser_and_planner(self):
        input_cmd = "open report.docx"
        self.executor_mock.execute.return_value = {"status": "success", "message": "Success"}
        self.engine.process_command(input_cmd)
        self.task_planner_mock.plan_tasks.assert_not_called()
        self.parser_mock.parse_command.assert_not_called()
        
        call_args = self.executor_mock.execute.call_args[0][0]
        assert call_args["action"] == "open_file"
        assert call_args["parameters"]["file_name"] == "report.docx"
        assert "path" not in call_args["parameters"]

    def test_3_open_steam_uses_planner(self):
        input_cmd = "open steam and discord"
        self.task_planner_mock.plan_tasks.return_value = ["open steam", "open discord"]
        self.parser_mock.parse_command.side_effect = [
            {"action": "open_application", "parameters": {"application_name": "steam"}},
            {"action": "open_application", "parameters": {"application_name": "discord"}}
        ]
        self.executor_mock.execute.return_value = {"status": "success", "message": "Success"}
        
        self.engine.process_command(input_cmd)
        
        # Verify TaskPlanner WAS called
        self.task_planner_mock.plan_tasks.assert_called_once_with(input_cmd)

    def test_4_open_calculator_uses_planner(self):
        input_cmd = "open calculator and close it after 5 seconds"
        self.task_planner_mock.plan_tasks.return_value = ["open calculator", "wait 5 seconds", "close calculator"]
        self.parser_mock.parse_command.side_effect = [
            {"action": "open_application", "parameters": {"application_name": "calculator"}},
            {"action": "wait", "parameters": {"seconds": 5}},
            {"action": "close_application", "parameters": {"application_name": "calculator"}}
        ]
        self.executor_mock.execute.return_value = {"status": "success", "message": "Success"}
        
        self.engine.process_command(input_cmd)
        
        # Verify TaskPlanner WAS called
        self.task_planner_mock.plan_tasks.assert_called_once_with(input_cmd)

    def test_5_close_youtube_website_fails(self):
        input_cmd = "close youtube website"
        # Not a filesystem command, so it uses planner
        self.task_planner_mock.plan_tasks.return_value = [input_cmd]
        
        # CommandParser should return unsupported
        self.parser_mock.parse_command.return_value = {
            "action": "unsupported",
            "parameters": {
                "message": "Closing browser tabs/websites is not currently supported."
            }
        }
        
        # Using a real executor instance to test the logic handles unsupported properly
        from src.tools.registry import ToolRegistry
        real_executor = Executor(registry=ToolRegistry())
        self.engine.executor = real_executor
        
        # Capture stdout for verification if needed, but we can just check the executor result
        # To intercept the result, we can mock history manager which receives the result
        self.engine.process_command(input_cmd)
        
        # The history manager receives the execution result
        call_args = self.history_mock.add_entry.call_args[1]
        exec_result = call_args['execution_result']
        
        assert exec_result["status"] == "failed"
        assert "Closing browser tabs/websites is not currently supported." in exec_result["message"]

if __name__ == "__main__":
    unittest.main()
