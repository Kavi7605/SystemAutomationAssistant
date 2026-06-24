import logging
from typing import Dict, Any
import screen_brightness_control as sbc

from src.tools.base import BaseTool

logger = logging.getLogger(__name__)

class BrightnessManager:
    """
    Centralized manager for Windows brightness controls using screen_brightness_control.
    """
    @staticmethod
    def _get_display() -> int:
        """
        Detects available displays and returns the primary display index.
        Raises an exception if brightness cannot be controlled.
        """
        monitors = sbc.list_monitors()
        if not monitors:
            raise RuntimeError("No controllable displays detected.")
        return 0  # Use the primary display (index 0) by default

    @staticmethod
    def get_brightness() -> int:
        """Gets the current brightness of the primary display as a percentage (0-100)."""
        display_idx = BrightnessManager._get_display()
        # sbc.get_brightness returns a list of integers corresponding to each monitor
        brightness_list = sbc.get_brightness()
        if not brightness_list:
            raise RuntimeError("Failed to read brightness from displays.")
        
        # If there's multiple values, we grab the primary one. 
        # But if we pass display=display_idx to get_brightness it returns a list of length 1
        val = sbc.get_brightness(display=display_idx)
        if not val:
            raise RuntimeError("Failed to read brightness for primary display.")
        return val[0]
        
    @staticmethod
    def set_brightness(level: int) -> int:
        """
        Sets the brightness on the primary display safely clamping between 0 and 100.
        Queries the actual brightness after setting and returns the new level.
        """
        level = max(0, min(100, level))
        display_idx = BrightnessManager._get_display()
        
        sbc.set_brightness(level, display=display_idx)
        
        # Query the actual value to ensure we return what the system applied
        return BrightnessManager.get_brightness()


class IncreaseBrightnessTool(BaseTool):
    name = "increase_brightness"
    description = "Increases system brightness by 10%."
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            old_bright = BrightnessManager.get_brightness()
            new_bright = BrightnessManager.set_brightness(old_bright + 10)
            return {
                "status": "success", 
                "message": f"Increasing brightness from {old_bright}% to {new_bright}%",
                "old_brightness": old_bright,
                "new_brightness": new_bright,
                "brightness_level": new_bright
            }
        except Exception as e:
            return {"status": "failed", "message": f"Failed to increase brightness: {e}"}


class DecreaseBrightnessTool(BaseTool):
    name = "decrease_brightness"
    description = "Decreases system brightness by 10%."
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            old_bright = BrightnessManager.get_brightness()
            new_bright = BrightnessManager.set_brightness(old_bright - 10)
            return {
                "status": "success", 
                "message": f"Decreasing brightness from {old_bright}% to {new_bright}%",
                "old_brightness": old_bright,
                "new_brightness": new_bright,
                "brightness_level": new_bright
            }
        except Exception as e:
            return {"status": "failed", "message": f"Failed to decrease brightness: {e}"}


class SetBrightnessTool(BaseTool):
    name = "set_brightness"
    description = "Sets system brightness to a specific percentage."
    
    def get_schema(self) -> Dict[str, Any]:
        schema = super().get_schema()
        schema["parameters"] = {
            "level": {
                "type": "integer",
                "description": "The brightness percentage to set (0-100)"
            }
        }
        return schema
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        level = kwargs.get("level")
        
        if level is None:
            return {"status": "failed", "message": "Brightness must be a number between 0 and 100."}
            
        try:
            level = int(level)
        except ValueError:
            return {"status": "failed", "message": "Brightness must be a number between 0 and 100."}
            
        if not (0 <= level <= 100):
            return {"status": "failed", "message": "Brightness must be a number between 0 and 100."}
            
        try:
            new_bright = BrightnessManager.set_brightness(level)
            return {
                "status": "success", 
                "message": f"Setting brightness to {new_bright}%",
                "brightness_level": new_bright
            }
        except Exception as e:
            return {"status": "failed", "message": f"Failed to set brightness: {e}"}


class GetBrightnessStatusTool(BaseTool):
    name = "brightness_status"
    description = "Gets the current system brightness status."
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            bright = BrightnessManager.get_brightness()
            message = f"Brightness Status\n----------------\nBrightness: {bright}%"
            
            return {
                "status": "success", 
                "message": message,
                "brightness_level": bright
            }
        except Exception as e:
            return {"status": "failed", "message": f"Failed to get brightness status: {e}"}
