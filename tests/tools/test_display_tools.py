import pytest
from unittest.mock import patch, MagicMock

from src.tools.system_control.display_tools import (
    DisplayManager,
    GetDisplayStatusTool
)

@patch('src.tools.system_control.display_tools.win32api.EnumDisplayMonitors')
@patch('src.tools.system_control.display_tools.win32api.EnumDisplayDevices')
@patch('src.tools.system_control.display_tools.win32api.EnumDisplaySettings')
@patch('src.tools.system_control.display_tools.ctypes.windll.shcore.GetDpiForMonitor')
def test_get_all_monitors_info(mock_getdpi, mock_enum_settings, mock_enum_devices, mock_enum_monitors):
    # Setup mocks
    mock_monitor1 = MagicMock()
    mock_monitor1[0].handle = 123
    mock_enum_monitors.return_value = [mock_monitor1]
    
    mock_device = MagicMock()
    mock_device.DeviceName = "DISPLAY1"
    import win32con
    mock_device.StateFlags = win32con.DISPLAY_DEVICE_PRIMARY_DEVICE  # Primary device flag in win32con
    mock_enum_devices.return_value = mock_device
    
    mock_settings = MagicMock()
    mock_settings.PelsWidth = 1920
    mock_settings.PelsHeight = 1080
    mock_settings.DisplayFrequency = 60
    mock_settings.DisplayOrientation = 0 # Default/Landscape
    mock_enum_settings.return_value = mock_settings
    
    def dpi_side_effect(hmonitor, type, dpiX, dpiY):
        dpiX._obj.value = 96
        dpiY._obj.value = 96
        return 0
    mock_getdpi.side_effect = dpi_side_effect
    
    monitors = DisplayManager.get_all_monitors_info()
    assert len(monitors) == 1
    m = monitors[0]
    assert m["resolution"] == "1920x1080"
    assert m["refresh_rate"] == 60
    assert m["scaling"] == 100
    assert m["orientation"] == "Landscape"
    assert m["is_primary"] is True

@patch('src.tools.system_control.display_tools.DisplayManager.get_all_monitors_info')
def test_get_display_status_tool(mock_get_all):
    mock_get_all.return_value = [
        {
            "index": 1,
            "device_name": "DISPLAY1",
            "is_primary": True,
            "resolution": "2560x1440",
            "refresh_rate": 165,
            "scaling": 125,
            "orientation": "Landscape"
        },
        {
            "index": 2,
            "device_name": "DISPLAY2",
            "is_primary": False,
            "resolution": "1920x1080",
            "refresh_rate": 60,
            "scaling": 100,
            "orientation": "Portrait"
        }
    ]
    
    tool = GetDisplayStatusTool()
    result = tool.execute()
    
    assert result["status"] == "success"
    assert result["display_monitor_count"] == 2
    assert result["primary_resolution"] == "2560x1440"
    assert result["primary_refresh_rate"] == 165
    
    msg = result["message"]
    assert "Display Status" in msg
    assert "Monitor Count: 2" in msg
    assert "Primary Monitor" in msg
    assert "Resolution: 2560x1440" in msg
    assert "Refresh Rate: 165 Hz" in msg
    assert "Monitor 2" in msg
    assert "Orientation: Portrait" in msg
