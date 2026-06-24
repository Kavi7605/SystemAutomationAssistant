from unittest.mock import MagicMock
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.automation.executor import Executor
from src.tools.registry import ToolRegistry
from src.context.context_manager import ContextManager

class TestExecutorContextUpdates:
    def test_executor_updates_context_for_power_status(self):
        registry_mock = MagicMock(spec=ToolRegistry)
        registry_mock.execute_tool.return_value = {
            "status": "success",
            "message": "Power status",
            "battery_saver_enabled": True,
            "power_plan": "Performance",
            "available_power_profiles": ["Balanced", "Performance", "Turbo"]
        }
        
        context_mock = MagicMock(spec=ContextManager)
        
        executor = Executor(registry=registry_mock, context_manager=context_mock)
        result = executor.execute({"action": "power_status", "parameters": {}})
        
        assert result["status"] == "success"
        
        # Verify update_system_state is called correctly instead of _update_system_state
        context_mock.update_system_state.assert_any_call("battery_saver_enabled", True)
        context_mock.update_system_state.assert_any_call("power_plan", "Performance")
        context_mock.update_system_state.assert_any_call("available_power_profiles", ["Balanced", "Performance", "Turbo"])
        
        # Verify no AttributeError occurred
        assert not hasattr(context_mock, "_update_system_state") or context_mock._update_system_state.call_count == 0

    def test_executor_updates_context_for_hotspot_status(self):
        registry_mock = MagicMock(spec=ToolRegistry)
        registry_mock.execute_tool.return_value = {
            "status": "success",
            "message": "Hotspot status",
            "hotspot_enabled": True
        }
        
        context_mock = MagicMock(spec=ContextManager)
        
        executor = Executor(registry=registry_mock, context_manager=context_mock)
        result = executor.execute({"action": "hotspot_status", "parameters": {}})
        
        assert result["status"] == "success"
        
        context_mock.update_system_state.assert_called_once_with("hotspot_enabled", True)
