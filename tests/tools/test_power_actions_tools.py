import pytest
from unittest.mock import patch, MagicMock
from src.tools.system_control.power_actions_tools import ShutdownTool, RestartTool, SleepTool, LockScreenTool, ConfirmPowerActionTool, CancelPowerActionTool

def test_shutdown_tool_initiates_confirmation():
    tool = ShutdownTool()
    result = tool.execute()
    assert result["status"] == "success"
    assert "confirm shutdown" in result["message"]
    assert result["pending_power_action"] == "shutdown"

def test_restart_tool_initiates_confirmation():
    tool = RestartTool()
    result = tool.execute()
    assert result["status"] == "success"
    assert "confirm restart" in result["message"]
    assert result["pending_power_action"] == "restart"

@patch('src.tools.system_control.power_actions_tools.subprocess.run')
def test_sleep_tool_success(mock_run):
    # Mock powercfg /a
    mock_res = MagicMock()
    mock_res.stdout = "The following sleep states are available:\nStandby (S3)"
    
    # Mock powershell success
    mock_run.side_effect = [mock_res, None]
    
    tool = SleepTool()
    result = tool.execute()
    
    assert mock_run.call_count == 2
    assert result["status"] == "success"
    assert result["last_power_action"] == "sleep"

@patch('src.tools.system_control.power_actions_tools.subprocess.run')
def test_sleep_tool_fails_gracefully(mock_run):
    # Mock powercfg /a with no S3 support
    mock_res = MagicMock()
    mock_res.stdout = "The following sleep states are not available:\nStandby (S3)"
    mock_run.return_value = mock_res
    
    tool = SleepTool()
    result = tool.execute()
    
    assert mock_run.call_count == 1
    assert result["status"] == "error"
    assert "True Sleep (S3 or S0) is not supported" in result["message"]

@patch('src.tools.system_control.power_actions_tools.subprocess.run')
def test_lock_screen_tool(mock_run):
    tool = LockScreenTool()
    result = tool.execute()
    
    mock_run.assert_called_once()
    assert result["status"] == "success"
    assert result["last_power_action"] == "lock"

@patch('src.tools.system_control.power_actions_tools.subprocess.run')
def test_confirm_power_action_tool_success(mock_run):
    tool = ConfirmPowerActionTool()
    result = tool.execute(action_type="shutdown", pending_action="shutdown")
    
    mock_run.assert_called_once_with(["shutdown", "/s", "/t", "0"], check=True)
    assert result["status"] == "success"
    assert result["last_power_action"] == "shutdown"
    assert result["clear_pending"] is True

def test_confirm_power_action_tool_mismatch():
    tool = ConfirmPowerActionTool()
    result = tool.execute(action_type="shutdown", pending_action="restart")
    
    assert result["status"] == "error"
    assert "No pending shutdown confirmation exists" in result["message"]

def test_cancel_power_action_tool():
    tool = CancelPowerActionTool()
    result = tool.execute()
    
    assert result["status"] == "success"
    assert result["clear_pending"] is True
