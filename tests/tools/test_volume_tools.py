import pytest
from unittest.mock import patch, MagicMock

from src.tools.system_control.volume_tools import (
    VolumeManager,
    MuteVolumeTool,
    UnmuteVolumeTool,
    IncreaseVolumeTool,
    DecreaseVolumeTool,
    SetVolumeTool,
    GetVolumeStatusTool
)

@patch('src.tools.system_control.volume_tools.VolumeManager.set_mute')
@patch('src.tools.system_control.volume_tools.VolumeManager.get_volume', return_value=50)
def test_mute_volume_tool(mock_get_vol, mock_set_mute):
    tool = MuteVolumeTool()
    result = tool.execute()
    
    mock_set_mute.assert_called_once_with(True)
    assert result["status"] == "success"
    assert result["is_muted"] is True
    assert result["volume_level"] == 50

@patch('src.tools.system_control.volume_tools.VolumeManager.set_mute')
@patch('src.tools.system_control.volume_tools.VolumeManager.get_volume', return_value=50)
def test_unmute_volume_tool(mock_get_vol, mock_set_mute):
    tool = UnmuteVolumeTool()
    result = tool.execute()
    
    mock_set_mute.assert_called_once_with(False)
    assert result["status"] == "success"
    assert result["is_muted"] is False

@patch('src.tools.system_control.volume_tools.VolumeManager.get_mute', return_value=False)
@patch('src.tools.system_control.volume_tools.VolumeManager.set_volume')
@patch('src.tools.system_control.volume_tools.VolumeManager.get_volume')
def test_increase_volume_tool(mock_get, mock_set, mock_mute):
    tool = IncreaseVolumeTool()
    
    # Test normal increase
    mock_get.return_value = 50
    mock_set.return_value = 55
    result = tool.execute()
    mock_set.assert_called_with(55)
    assert result["old_volume"] == 50
    assert result["new_volume"] == 55
    
    # Test clamping
    mock_get.return_value = 95
    mock_set.return_value = 100
    result = tool.execute()
    mock_set.assert_called_with(100)
    assert result["new_volume"] == 100
    
    # Test at max
    mock_get.return_value = 100
    mock_set.return_value = 100
    result = tool.execute()
    mock_set.assert_called_with(105) # Manager clamps it

@patch('src.tools.system_control.volume_tools.VolumeManager.get_mute', return_value=False)
@patch('src.tools.system_control.volume_tools.VolumeManager.set_volume')
@patch('src.tools.system_control.volume_tools.VolumeManager.get_volume')
def test_decrease_volume_tool(mock_get, mock_set, mock_mute):
    tool = DecreaseVolumeTool()
    
    # Test normal decrease
    mock_get.return_value = 50
    mock_set.return_value = 45
    result = tool.execute()
    mock_set.assert_called_with(45)
    
    # Test clamping
    mock_get.return_value = 5
    mock_set.return_value = 0
    result = tool.execute()
    mock_set.assert_called_with(0)
    
    # Test at min
    mock_get.return_value = 0
    mock_set.return_value = 0
    result = tool.execute()
    mock_set.assert_called_with(-5) # Manager clamps it

@patch('src.tools.system_control.volume_tools.VolumeManager.get_mute', return_value=False)
@patch('src.tools.system_control.volume_tools.VolumeManager.set_volume', return_value=50)
def test_set_volume_tool(mock_set, mock_mute):
    tool = SetVolumeTool()
    
    # Valid
    result = tool.execute(level=50)
    assert result["status"] == "success"
    assert result["volume_level"] == 50
    
    # Invalid: > 100
    result = tool.execute(level=101)
    assert result["status"] == "failed"
    assert "Volume must be a number between 0 and 100" in result["message"]
    
    # Invalid: < 0
    result = tool.execute(level=-1)
    assert result["status"] == "failed"
    assert "Volume must be a number between 0 and 100" in result["message"]
    
    # Invalid: not a number
    result = tool.execute(level="abc")
    assert result["status"] == "failed"

@patch('src.tools.system_control.volume_tools.VolumeManager.get_mute', return_value=False)
@patch('src.tools.system_control.volume_tools.VolumeManager.get_volume', return_value=75)
def test_get_volume_status(mock_get, mock_mute):
    tool = GetVolumeStatusTool()
    result = tool.execute()
    
    assert result["status"] == "success"
    assert result["volume_level"] == 75
    assert result["is_muted"] is False
    assert "Volume Status" in result["message"]
    assert "Volume: 75%" in result["message"]
    assert "Muted: No" in result["message"]

def test_volume_manager_clamping():
    with patch('src.tools.system_control.volume_tools.VolumeManager._get_volume_interface') as mock_int:
        interface = MagicMock()
        mock_int.return_value = interface
        
        # Test 150 clamps to 100
        vol = VolumeManager.set_volume(150)
        assert vol == 100
        interface.SetMasterVolumeLevelScalar.assert_called_with(1.0, None)
        
        # Test -50 clamps to 0
        vol = VolumeManager.set_volume(-50)
        assert vol == 0
        interface.SetMasterVolumeLevelScalar.assert_called_with(0.0, None)

@pytest.mark.integration
def test_volume_manager_initialization_integration():
    """Integration test to verify VolumeManager successfully initializes pycaw without mocking."""
    # This will fail if the pycaw initialization is incorrect.
    interface = VolumeManager._get_volume_interface()
    assert interface is not None
    assert hasattr(interface, 'GetMasterVolumeLevelScalar')

@pytest.mark.integration
def test_startup_self_test():
    """Startup self-test executing get_volume() directly to ensure real retrieval works."""
    volume = VolumeManager.get_volume()
    assert isinstance(volume, int)
    assert 0 <= volume <= 100
