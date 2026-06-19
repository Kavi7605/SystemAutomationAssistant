from unittest.mock import MagicMock
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.automation.executor import Executor
from src.tools.registry import ToolRegistry

class TestExecutorFallback:
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
        assert registry_mock.execute_tool.call_count == 2
        
        # Check first call
        first_call_args = registry_mock.execute_tool.call_args_list[0]
        assert first_call_args[0][0] == "open_application"
        assert first_call_args[1]["application_name"] == "unknown_app"
        
        # Check second call (fallback)
        second_call_args = registry_mock.execute_tool.call_args_list[1]
        assert second_call_args[0][0] == "open_url"
        assert second_call_args[1]["url"] == "https://fallback.com"
        
        # Check result message
        assert result["status"] == "success"
        assert "Opened fallback website" in result["message"]

class TestExecutorQueueHandling:
    def test_executor_queue_success_path(self):
        registry_mock = MagicMock(spec=ToolRegistry)
        registry_mock.execute_tool.return_value = {"status": "success", "message": "Done"}
        
        executor = Executor(registry=registry_mock)
        commands = [
            {"action": "open_application", "parameters": {"application_name": "vscode"}},
            {"action": "focus_window", "parameters": {"window_name": "vscode"}}
        ]
        
        result = executor.execute(commands)
        
        assert registry_mock.execute_tool.call_count == 2
        assert result["status"] == "completed"
        assert result["successful"] == 2
        assert result["failed"] == 0
        assert not result["aborted"]

    def test_executor_queue_failure_path(self):
        registry_mock = MagicMock(spec=ToolRegistry)
        registry_mock.execute_tool.side_effect = [
            {"status": "success", "message": "Done"},
            {"status": "failed", "message": "Something went wrong"},
            {"status": "success", "message": "Done"}
        ]
        
        executor = Executor(registry=registry_mock)
        commands = [
            {"action": "open_application", "parameters": {"application_name": "vscode"}},
            {"action": "click", "parameters": {}},
            {"action": "focus_window", "parameters": {"window_name": "vscode"}}
        ]
        
        result = executor.execute(commands, stop_on_failure=True)
        
        assert registry_mock.execute_tool.call_count == 2 # Stopped at the second step
        assert result["status"] == "failed"
        assert result["successful"] == 1
        assert result["failed"] == 1
        assert result["aborted"] is True

    def test_executor_queue_timeout_path(self):
        registry_mock = MagicMock(spec=ToolRegistry)
        # First step succeeds, second step is a wait timeout (failed)
        registry_mock.execute_tool.side_effect = [
            {"status": "success", "message": "Done"},
            {"status": "failed", "message": "Timeout waiting for window 'vscode'"}
        ]
        
        executor = Executor(registry=registry_mock)
        commands = [
            {"action": "open_application", "parameters": {"application_name": "vscode"}},
            {"action": "wait", "parameters": {"wait_type": "window", "window_name": "vscode"}},
            {"action": "focus_window", "parameters": {"window_name": "vscode"}}
        ]
        
        result = executor.execute(commands)
        
        # Should stop after the timeout, not executing focus_window
        assert registry_mock.execute_tool.call_count == 2
        assert result["aborted"] is True

    def test_executor_queue_no_abort_on_failure(self):
        registry_mock = MagicMock(spec=ToolRegistry)
        registry_mock.execute_tool.side_effect = [
            {"status": "success", "message": "Done"},
            {"status": "failed", "message": "Something went wrong"},
            {"status": "success", "message": "Done"}
        ]
        
        executor = Executor(registry=registry_mock)
        commands = [
            {"action": "open_application", "parameters": {"application_name": "vscode"}},
            {"action": "click", "parameters": {}},
            {"action": "focus_window", "parameters": {"window_name": "vscode"}}
        ]
        
        result = executor.execute(commands, stop_on_failure=False)
        
        # Executes all steps despite failure
        assert registry_mock.execute_tool.call_count == 3
        assert result["status"] == "partial_success"
        assert result["successful"] == 2
        assert result["failed"] == 1
        assert result["aborted"] is False


