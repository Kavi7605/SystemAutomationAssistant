import pytest
from unittest.mock import patch, MagicMock
from src.tools.system_control.hotspot_tools import HotspotManager, GetHotspotStatusTool

@patch('src.tools.system_control.hotspot_tools.subprocess.run')
def test_get_hotspot_status_on(mock_run):
    mock_res = MagicMock()
    mock_res.stdout = "On\n"
    mock_run.return_value = mock_res
    
    status = HotspotManager.get_hotspot_status()
    assert status["enabled"] is True

@patch('src.tools.system_control.hotspot_tools.subprocess.run')
def test_get_hotspot_status_off(mock_run):
    mock_res = MagicMock()
    mock_res.stdout = "Off\n"
    mock_run.return_value = mock_res
    
    status = HotspotManager.get_hotspot_status()
    assert status["enabled"] is False

@patch('src.tools.system_control.hotspot_tools.subprocess.run')
def test_get_hotspot_status_exception(mock_run):
    mock_run.side_effect = Exception("Crash")
    
    status = HotspotManager.get_hotspot_status()
    assert status["enabled"] is False

@patch('src.tools.system_control.hotspot_tools.HotspotManager.get_hotspot_status')
def test_get_hotspot_status_tool(mock_status):
    mock_status.return_value = {"enabled": True}
    
    tool = GetHotspotStatusTool()
    result = tool.execute()
    
    assert result["status"] == "success"
    assert "Enabled: Yes" in result["message"]
    assert result["hotspot_enabled"] is True
