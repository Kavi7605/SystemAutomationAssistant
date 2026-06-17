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

class TestDay8Part5(unittest.TestCase):
    def assertExecute(self, expected_action, expected_params=None):
        self.executor_mock.execute.assert_called()
        cmd = self.executor_mock.execute.call_args[0][0]
        if isinstance(cmd, list):
            cmd = cmd[0]
        self.assertEqual(cmd["action"], expected_action)
        if expected_params:
            for k, v in expected_params.items():
                self.assertEqual(cmd["parameters"][k], v)
        self.executor_mock.reset_mock()

    def test_open_file_routing_grammar(self):
        # 1. open test.txt
        self.engine.process_command("open test.txt")
        self.assertExecute("open_file", {"file_name": "test.txt"})

        # 2. open file test.txt
        self.engine.process_command("open file test.txt")
        self.assertExecute("open_file", {"file_name": "test.txt"})

        # 3. open test.txt file
        self.engine.process_command("open test.txt file")
        self.assertExecute("open_file", {"file_name": "test.txt"})

        # 4. open test.txt in desktop
        self.engine.process_command("open test.txt in desktop")
        self.assertExecute("open_file", {"file_name": "test.txt", "path": "desktop"})

        # 5. open file test.txt in desktop
        self.engine.process_command("open file test.txt in desktop")
        self.assertExecute("open_file", {"file_name": "test.txt", "path": "desktop"})

        # 6. open test.txt file in desktop
        self.engine.process_command("open test.txt file in desktop")
        self.assertExecute("open_file", {"file_name": "test.txt", "path": "desktop"})

if __name__ == "__main__":
    unittest.main()

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

    def test_open_test_txt_in_desktop(self):
        self.engine.process_command("open test.txt in desktop")
        self.assertExecute("open_file", {"file_name": "test.txt", "path": "desktop"})
        self.executor_mock.reset_mock()