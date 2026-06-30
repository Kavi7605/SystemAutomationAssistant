from unittest.mock import patch, MagicMock

from src.tools.system_control.wifi_tools import (
    WifiManager,
    EnableWifiTool,
    DisableWifiTool,
    GetWifiStatusTool
)

def test_wifi_status_disconnected():
    output = """
There is 1 interface on the system:

    Name                   : Wi-Fi
    Description            : Intel(R) Wi-Fi 6 AX201 160MHz
    GUID                   : 44bf0952-4755-46b5-9232-bc34aa2cf479
    Physical address       : a4:6b:b6:33:78:d6
    Interface type         : Primary
    State                  : disconnected
    """
    mock_run = MagicMock()
    mock_run.stdout = output
    
    with patch('src.tools.system_control.wifi_tools.subprocess.run', return_value=mock_run):
        status = WifiManager.get_wifi_status()
        
    assert status["enabled"] is True
    assert status["connected"] is False
    assert status["ssid"] is None

def test_wifi_status_connected():
    output = """
There is 1 interface on the system:

    Name                   : Wi-Fi
    Description            : Intel(R) Wi-Fi 6 AX201 160MHz
    GUID                   : 44bf0952-4755-46b5-9232-bc34aa2cf479
    Physical address       : a4:6b:b6:33:78:d6
    Interface type         : Primary
    State                  : connected
    SSID                   : MyHomeWiFi
    BSSID                  : d8:4a:2b:2c:99:58
    """
    mock_run = MagicMock()
    mock_run.stdout = output
    
    with patch('src.tools.system_control.wifi_tools.subprocess.run', return_value=mock_run):
        status = WifiManager.get_wifi_status()
        
    assert status["enabled"] is True
    assert status["connected"] is True
    assert status["ssid"] == "MyHomeWiFi"

def test_wifi_status_disabled():
    output = "There is no wireless interface on the system."
    mock_run = MagicMock()
    mock_run.stdout = output
    
    with patch('src.tools.system_control.wifi_tools.subprocess.run', return_value=mock_run):
        status = WifiManager.get_wifi_status()
        
    assert status["enabled"] is False
    assert status["connected"] is False
    assert status["ssid"] is None

@patch('src.tools.system_control.wifi_tools.subprocess.run')
def test_disable_wifi(mock_run):
    mock_res = MagicMock()
    mock_res.returncode = 0
    mock_run.return_value = mock_res
    
    assert WifiManager.disable_wifi() is True
    mock_run.assert_called_with(["netsh", "wlan", "disconnect"], capture_output=True, text=True, check=False)

@patch('src.tools.system_control.wifi_tools.subprocess.run')
def test_enable_wifi_success_priority_1(mock_run):
    mock_connect = MagicMock()
    mock_connect.returncode = 0
    mock_run.return_value = mock_connect
    
    error = WifiManager.enable_wifi("Kavi's 5G Wifi")
    assert error == ""
    
    mock_run.assert_called_once_with(["netsh", "wlan", "connect", "name=Kavi's 5G Wifi"], capture_output=True, text=True, check=False)

@patch('src.tools.system_control.wifi_tools.subprocess.run')
def test_enable_wifi_priority_1_fails_priority_2_success(mock_run):
    # Priority 1 fails
    mock_connect_1 = MagicMock()
    mock_connect_1.returncode = 1
    mock_connect_1.stdout = "Failed"
    
    # Show profiles
    mock_profiles = MagicMock()
    mock_profiles.returncode = 0
    mock_profiles.stdout = "    All User Profile     : My Home WiFi\n    All User Profile     : GuestNetwork"
    
    # Priority 2 succeeds
    mock_connect_2 = MagicMock()
    mock_connect_2.returncode = 0
    
    mock_run.side_effect = [mock_connect_1, mock_profiles, mock_connect_2]
    
    error = WifiManager.enable_wifi("Old Network")
    assert error == ""
    
    assert mock_run.call_count == 3
    mock_run.assert_any_call(["netsh", "wlan", "connect", "name=Old Network"], capture_output=True, text=True, check=False)
    mock_run.assert_any_call(["netsh", "wlan", "connect", "name=My Home WiFi"], capture_output=True, text=True, check=False)

@patch('src.tools.system_control.wifi_tools.subprocess.run')
def test_enable_wifi_no_profiles(mock_run):
    mock_profiles = MagicMock()
    mock_profiles.returncode = 0
    mock_profiles.stdout = ""
    mock_run.return_value = mock_profiles
    
    error = WifiManager.enable_wifi()
    assert error == "No known WiFi network is available for automatic reconnection."

@patch('src.tools.system_control.wifi_tools.subprocess.run')
def test_enable_wifi_all_fail(mock_run):
    mock_profiles = MagicMock()
    mock_profiles.returncode = 0
    mock_profiles.stdout = "    All User Profile     : MyHomeWiFi"
    
    mock_connect = MagicMock()
    mock_connect.returncode = 1
    mock_connect.stdout = "Failed"
    
    mock_run.side_effect = [mock_profiles, mock_connect]
    
    error = WifiManager.enable_wifi()
    assert error == "No known WiFi network is available for automatic reconnection."

@patch('src.tools.system_control.wifi_tools.WifiManager.get_wifi_status')
@patch('src.tools.system_control.wifi_tools.WifiManager.disable_wifi')
def test_disable_wifi_tool(mock_disable, mock_status):
    mock_disable.return_value = True
    mock_status.return_value = {"enabled": True, "connected": False, "ssid": None}
    
    tool = DisableWifiTool()
    result = tool.execute()
    
    assert result["status"] == "success"
    assert result["wifi_connected"] is False
    assert "WiFi disabled successfully" in result["message"]

@patch('src.tools.system_control.wifi_tools.WifiManager.get_wifi_status')
@patch('src.tools.system_control.wifi_tools.WifiManager.enable_wifi')
def test_enable_wifi_tool(mock_enable, mock_status):
    mock_enable.return_value = ""
    mock_status.return_value = {"enabled": True, "connected": True, "ssid": "MyHomeWiFi"}
    
    tool = EnableWifiTool()
    result = tool.execute()
    
    assert result["status"] == "success"
    assert result["wifi_connected"] is True
    assert result["wifi_name"] == "MyHomeWiFi"
    assert "WiFi enabled successfully" in result["message"]

@patch('src.tools.system_control.wifi_tools.WifiManager.get_wifi_status')
def test_get_wifi_status_tool(mock_status):
    mock_status.return_value = {"enabled": True, "connected": True, "ssid": "MyHomeWiFi"}
    
    tool = GetWifiStatusTool()
    result = tool.execute()
    
    assert result["status"] == "success"
    assert "Enabled: Yes" in result["message"]
    assert "Connected: Yes" in result["message"]
    assert "Network: MyHomeWiFi" in result["message"]
