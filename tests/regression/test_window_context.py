import pytest
from unittest.mock import MagicMock
from src.automation.executor import Executor
from src.context.context_manager import ContextManager
from src.tools.registry import ToolRegistry

@pytest.fixture
def executor():
    registry = ToolRegistry()
    registry.execute_tool = MagicMock()
    
    context_manager = ContextManager()
    # Mock saving to avoid disk IO
    context_manager.save = MagicMock()
    
    return Executor(registry=registry, state_manager=MagicMock(), context_manager=context_manager, reference_resolver=MagicMock())

def test_context_sync_minimize(executor):
    executor.registry.execute_tool.return_value = {
        "status": "success",
        "window": {
            "title": "Notepad",
            "app_name": "notepad.exe",
            "hwnd": 1234,
            "state": "Minimized",
            "pid": 5678
        }
    }
    
    cmd = {"action": "minimize_window", "parameters": {"window_name": "notepad"}}
    executor._execute_single(cmd)
    
    state = executor.context_manager.state["system_state"]
    assert state["current_window_title"] == "Notepad"
    assert state["current_window_app"] == "notepad.exe"
    assert state["current_window_handle"] == 1234
    assert state["last_window_action"] == "minimize"

def test_context_sync_list_windows(executor):
    executor.registry.execute_tool.return_value = {
        "status": "success",
        "count": 5,
        "windows": []
    }
    
    cmd = {"action": "list_open_windows", "parameters": {}}
    executor._execute_single(cmd)
    
    state = executor.context_manager.state["system_state"]
    assert state["open_windows_count"] == 5

def test_context_sync_current_window(executor):
    executor.registry.execute_tool.return_value = {
        "status": "success",
        "window": {
            "title": "Chrome",
            "app_name": "chrome.exe",
            "hwnd": 9999,
            "state": "Normal",
            "pid": 1000
        }
    }
    
    cmd = {"action": "get_current_window", "parameters": {}}
    executor._execute_single(cmd)
    
    state = executor.context_manager.state["system_state"]
    assert state["current_window_title"] == "Chrome"
    assert state["current_window_app"] == "chrome.exe"
    assert state["current_window_handle"] == 9999
    # Ensure it doesn't accidentally set last_window_action
    assert state.get("last_window_action") is None
