import pytest
from unittest.mock import patch

from src.tools.system_control.brightness_tools import (
    BrightnessManager,
    IncreaseBrightnessTool,
    DecreaseBrightnessTool,
    SetBrightnessTool,
    GetBrightnessStatusTool
)

@patch('src.tools.system_control.brightness_tools.sbc.list_monitors', return_value=['Monitor 1', 'Monitor 2'])
@patch('src.tools.system_control.brightness_tools.sbc.get_brightness', return_value=[50, 60])
@patch('src.tools.system_control.brightness_tools.sbc.set_brightness')
def test_increase_brightness_tool(mock_set, mock_get, mock_list):
    tool = IncreaseBrightnessTool()
    
    # Test normal increase
    result = tool.execute()
    mock_set.assert_called_with(60, display=0)
    assert result["old_brightness"] == 50
    assert result["new_brightness"] == 50 # Wait, get_brightness returns [50, 60] which means our mock always returns 50 for the primary.
    # The set_brightness returns the mocked get_brightness, which is 50. 
    # Let's mock differently to test logic better.

@patch('src.tools.system_control.brightness_tools.BrightnessManager.set_brightness')
@patch('src.tools.system_control.brightness_tools.BrightnessManager.get_brightness')
def test_increase_brightness_tool_logic(mock_get, mock_set):
    tool = IncreaseBrightnessTool()
    
    # Normal
    mock_get.return_value = 50
    mock_set.return_value = 60
    result = tool.execute()
    mock_set.assert_called_with(60)
    assert result["old_brightness"] == 50
    assert result["new_brightness"] == 60
    
    # Clamping
    mock_get.return_value = 95
    mock_set.return_value = 100
    result = tool.execute()
    mock_set.assert_called_with(105) # Manager will clamp it

@patch('src.tools.system_control.brightness_tools.BrightnessManager.set_brightness')
@patch('src.tools.system_control.brightness_tools.BrightnessManager.get_brightness')
def test_decrease_brightness_tool_logic(mock_get, mock_set):
    tool = DecreaseBrightnessTool()
    
    # Normal
    mock_get.return_value = 50
    mock_set.return_value = 40
    tool.execute()
    mock_set.assert_called_with(40)
    
    # Clamping
    mock_get.return_value = 5
    mock_set.return_value = 0
    tool.execute()
    mock_set.assert_called_with(-5)

@patch('src.tools.system_control.brightness_tools.BrightnessManager.set_brightness', return_value=50)
def test_set_brightness_tool(mock_set):
    tool = SetBrightnessTool()
    
    # Valid
    result = tool.execute(level=50)
    assert result["status"] == "success"
    assert result["brightness_level"] == 50
    
    # Invalid: > 100
    result = tool.execute(level=101)
    assert result["status"] == "failed"
    assert "Brightness must be a number between 0 and 100." in result["message"]
    
    # Invalid: < 0
    result = tool.execute(level=-1)
    assert result["status"] == "failed"
    assert "Brightness must be a number between 0 and 100." in result["message"]
    
    # Invalid: not a number
    result = tool.execute(level="abc")
    assert result["status"] == "failed"
    assert "Brightness must be a number between 0 and 100." in result["message"]

@patch('src.tools.system_control.brightness_tools.BrightnessManager.get_brightness', return_value=75)
def test_get_brightness_status(mock_get):
    tool = GetBrightnessStatusTool()
    result = tool.execute()
    
    assert result["status"] == "success"
    assert result["brightness_level"] == 75
    assert "Brightness Status" in result["message"]
    assert "Brightness: 75%" in result["message"]

def test_brightness_manager_clamping():
    with patch('src.tools.system_control.brightness_tools.sbc.set_brightness') as mock_set, \
         patch('src.tools.system_control.brightness_tools.BrightnessManager.get_brightness') as mock_get, \
         patch('src.tools.system_control.brightness_tools.BrightnessManager._get_display', return_value=0):
        
        mock_get.return_value = 100
        vol = BrightnessManager.set_brightness(150)
        assert vol == 100
        mock_set.assert_called_with(100, display=0)
        
        mock_get.return_value = 0
        vol = BrightnessManager.set_brightness(-50)
        assert vol == 0
        mock_set.assert_called_with(0, display=0)

def test_brightness_manager_multi_monitor():
    with patch('src.tools.system_control.brightness_tools.sbc.list_monitors') as mock_list, \
         patch('src.tools.system_control.brightness_tools.sbc.get_brightness') as mock_get:
         
        # Multiple monitors detected
        mock_list.return_value = ['Display1', 'Display2']
        
        # When called without arguments, returns list for all monitors
        # We need to make it return different things depending on kwargs
        def mock_get_bright(**kwargs):
            if 'display' in kwargs:
                if kwargs['display'] == 0:
                    return [75]
                elif kwargs['display'] == 1:
                    return [50]
            return [75, 50]
            
        mock_get.side_effect = mock_get_bright
        
        val = BrightnessManager.get_brightness()
        assert val == 75

def test_brightness_manager_no_monitors():
    with patch('src.tools.system_control.brightness_tools.sbc.list_monitors', return_value=[]):
        with pytest.raises(RuntimeError, match="No controllable displays detected."):
            BrightnessManager._get_display()

@pytest.mark.integration
def test_brightness_manager_initialization_integration():
    """Integration test to verify BrightnessManager successfully interacts with sbc."""
    try:
        display = BrightnessManager._get_display()
        assert isinstance(display, int)
    except RuntimeError:
        pytest.skip("No controllable displays detected on this machine.")

@pytest.mark.integration
def test_startup_self_test_brightness():
    """Startup self-test executing get_brightness() directly."""
    try:
        brightness = BrightnessManager.get_brightness()
        assert isinstance(brightness, int)
        assert 0 <= brightness <= 100
    except RuntimeError:
        pytest.skip("No controllable displays detected on this machine.")
