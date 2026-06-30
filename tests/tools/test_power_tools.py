from unittest.mock import patch, MagicMock
from src.tools.system_control.power_tools import PowerManager, SetPowerModeTool

@patch('src.tools.system_control.power_tools.subprocess.run')
def test_get_battery_saver_on(mock_run):
    mock_res = MagicMock()
    mock_res.stdout = "On\n"
    mock_run.return_value = mock_res
    
    status = PowerManager.get_battery_saver_status()
    assert status["enabled"] is True

@patch('src.tools.system_control.power_tools.subprocess.run')
def test_get_battery_saver_off(mock_run):
    mock_res = MagicMock()
    mock_res.stdout = "Disabled\n"
    mock_run.return_value = mock_res
    
    status = PowerManager.get_battery_saver_status()
    assert status["enabled"] is False

@patch('src.tools.system_control.power_tools.subprocess.run')
def test_get_power_profiles(mock_run):
    mock_res = MagicMock()
    mock_res.stdout = """
Existing Power Schemes (* Active)
-----------------------------------
Power Scheme GUID: 11111111-1111  (Balanced)
Power Scheme GUID: 22222222-2222  (Performance) *
Power Scheme GUID: 33333333-3333  (Turbo)
"""
    mock_run.return_value = mock_res
    
    data = PowerManager.get_power_profiles()
    assert data["active_profile"] == "Performance"
    assert "balanced" in data["profiles"]
    assert "performance" in data["profiles"]
    assert "turbo" in data["profiles"]
    assert data["profiles"]["balanced"]["guid"] == "11111111-1111"

@patch('src.tools.system_control.power_tools.PowerManager.get_power_profiles')
@patch('src.tools.system_control.power_tools.PowerManager.set_power_profile')
def test_set_power_mode_success(mock_set, mock_get):
    # Initial state
    mock_get.side_effect = [
        {
            "active_profile": "Balanced",
            "profiles": {
                "balanced": {"name": "Balanced", "guid": "111"},
                "performance": {"name": "Performance", "guid": "222"}
            }
        },
        # After switch
        {
            "active_profile": "Performance",
            "profiles": {
                "balanced": {"name": "Balanced", "guid": "111"},
                "performance": {"name": "Performance", "guid": "222"}
            }
        }
    ]
    mock_set.return_value = True
    
    tool = SetPowerModeTool()
    result = tool.execute(mode="performance")
    
    mock_set.assert_called_with("222")
    assert result["status"] == "success"
    assert result["power_plan"] == "Performance"
    assert "Balanced" in result["available_power_profiles"]

@patch('src.tools.system_control.power_tools.PowerManager.get_power_profiles')
def test_set_power_mode_graceful_failure_not_found(mock_get):
    mock_get.return_value = {
        "active_profile": "Balanced",
        "profiles": {
            "balanced": {"name": "Balanced", "guid": "111"},
            "performance": {"name": "Performance", "guid": "222"}
        }
    }
    
    tool = SetPowerModeTool()
    result = tool.execute(mode="turbo")
    
    assert result["status"] == "error"
    assert "Turbo power profile was not found on this system" in result["message"]
