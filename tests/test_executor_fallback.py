import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.automation.executor import Executor
from src.tools.registry import ToolRegistry

class TestExecutorFallback(unittest.TestCase):
    def test_executor_fallback_when_app_not_found(self):
        registry_mock = MagicMock(spec=ToolRegistry)
        # Mock execute_tool: First call returns application_not_found
        # Second call returns success
        registry_mock.execute_tool.side_effect = [
            {"status": "application_not_found", "message": "App not found"},
            {"status": "success", "message": "Website opened"}
        ]
        
        executor = Executor(registry=registry_mock)
        
        result = executor.execute({
            "action": "open_application",
            "parameters": {
                "application_name": "unknown_app",
                "fallback_url": "https://fallback.com"
            }
        })
        
        # Verify execute_tool was called twice
        self.assertEqual(registry_mock.execute_tool.call_count, 2)
        
        # Check first call
        first_call_args = registry_mock.execute_tool.call_args_list[0]
        self.assertEqual(first_call_args[0][0], "open_application")
        self.assertEqual(first_call_args[1]["application_name"], "unknown_app")
        
        # Check second call (fallback)
        second_call_args = registry_mock.execute_tool.call_args_list[1]
        self.assertEqual(second_call_args[0][0], "open_url")
        self.assertEqual(second_call_args[1]["url"], "https://fallback.com")
        
        # Check result message
        self.assertEqual(result["status"], "success")
        self.assertTrue("Opened fallback website" in result["message"])

if __name__ == "__main__":
    unittest.main()
