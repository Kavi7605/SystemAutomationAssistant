import logging
from typing import Dict, Any
import comtypes
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

from src.tools.base import BaseTool

logger = logging.getLogger(__name__)

class VolumeManager:
    """
    Centralized manager for Windows volume controls using pycaw.
    Ensures safe initialization and interaction with Core Audio APIs.
    """
    @staticmethod
    def _get_volume_interface() -> IAudioEndpointVolume:
        """Helper to get the Windows volume interface."""
        comtypes.CoInitialize()
        try:
            devices = AudioUtilities.GetSpeakers()
            return devices.EndpointVolume
        except Exception as e:
            logger.error(f"Failed to get audio endpoint: {e}", exc_info=True)
            raise
            
    @staticmethod
    def get_volume() -> int:
        """Gets current volume as a percentage (0-100)."""
        interface = VolumeManager._get_volume_interface()
        try:
            vol_scalar = interface.GetMasterVolumeLevelScalar()
            return round(vol_scalar * 100)
        finally:
            comtypes.CoUninitialize()
            
    @staticmethod
    def set_volume(level: int) -> int:
        """Sets the volume safely clamping between 0 and 100. Returns the newly set level."""
        level = max(0, min(100, level))
        interface = VolumeManager._get_volume_interface()
        try:
            interface.SetMasterVolumeLevelScalar(level / 100.0, None)
            return level
        finally:
            comtypes.CoUninitialize()
            
    @staticmethod
    def get_mute() -> bool:
        """Gets the current mute status."""
        interface = VolumeManager._get_volume_interface()
        try:
            return bool(interface.GetMute())
        finally:
            comtypes.CoUninitialize()
            
    @staticmethod
    def set_mute(state: bool) -> None:
        """Sets the mute status."""
        interface = VolumeManager._get_volume_interface()
        try:
            interface.SetMute(1 if state else 0, None)
        finally:
            comtypes.CoUninitialize()


class MuteVolumeTool(BaseTool):
    name = "mute_volume"
    description = "Mutes the system volume."
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            VolumeManager.set_mute(True)
            return {
                "status": "success", 
                "title": "Volume Muted",
                "message": "System volume has been muted.",
                "metadata": {
                    "Volume Level": f"{VolumeManager.get_volume()}%",
                    "Status": "Muted"
                },
                "is_muted": True,
                "volume_level": VolumeManager.get_volume()
            }
        except Exception as e:
            return {"status": "failed", "message": f"Failed to mute volume: {e}"}


class UnmuteVolumeTool(BaseTool):
    name = "unmute_volume"
    description = "Unmutes the system volume."
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            VolumeManager.set_mute(False)
            return {
                "status": "success", 
                "title": "Volume Unmuted",
                "message": "System volume has been unmuted.",
                "metadata": {
                    "Volume Level": f"{VolumeManager.get_volume()}%",
                    "Status": "Unmuted"
                },
                "is_muted": False,
                "volume_level": VolumeManager.get_volume()
            }
        except Exception as e:
            return {"status": "failed", "message": f"Failed to unmute volume: {e}"}


class IncreaseVolumeTool(BaseTool):
    name = "increase_volume"
    description = "Increases system volume by 5%."
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            old_vol = VolumeManager.get_volume()
            new_vol = VolumeManager.set_volume(old_vol + 5)
            return {
                "status": "success", 
                "title": "Volume Increased",
                "message": f"Volume increased from {old_vol}% to {new_vol}%.",
                "metadata": {
                    "New Volume": f"{new_vol}%",
                    "Muted": str(VolumeManager.get_mute())
                },
                "old_volume": old_vol,
                "new_volume": new_vol,
                "is_muted": VolumeManager.get_mute(),
                "volume_level": new_vol
            }
        except Exception as e:
            return {"status": "failed", "message": f"Failed to increase volume: {e}"}


class DecreaseVolumeTool(BaseTool):
    name = "decrease_volume"
    description = "Decreases system volume by 5%."
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            old_vol = VolumeManager.get_volume()
            new_vol = VolumeManager.set_volume(old_vol - 5)
            return {
                "status": "success", 
                "title": "Volume Decreased",
                "message": f"Volume decreased from {old_vol}% to {new_vol}%.",
                "metadata": {
                    "New Volume": f"{new_vol}%",
                    "Muted": str(VolumeManager.get_mute())
                },
                "old_volume": old_vol,
                "new_volume": new_vol,
                "is_muted": VolumeManager.get_mute(),
                "volume_level": new_vol
            }
        except Exception as e:
            return {"status": "failed", "message": f"Failed to decrease volume: {e}"}


class SetVolumeTool(BaseTool):
    name = "set_volume"
    description = "Sets system volume to a specific percentage."
    
    def get_schema(self) -> Dict[str, Any]:
        schema = super().get_schema()
        schema["parameters"] = {
            "level": {
                "type": "integer",
                "description": "The volume percentage to set (0-100)"
            }
        }
        return schema
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        level = kwargs.get("level")
        
        if level is None:
            return {"status": "failed", "message": "Missing 'level' parameter."}
            
        try:
            level = int(level)
        except ValueError:
            return {"status": "failed", "message": "Volume must be a number between 0 and 100."}
            
        if not (0 <= level <= 100):
            return {"status": "failed", "message": "Volume must be a number between 0 and 100."}
            
        try:
            new_vol = VolumeManager.set_volume(level)
            return {
                "status": "success", 
                "title": "Volume Set",
                "message": f"Volume was set to {new_vol}%.",
                "metadata": {
                    "Volume Level": f"{new_vol}%",
                    "Muted": str(VolumeManager.get_mute())
                },
                "volume_level": new_vol,
                "is_muted": VolumeManager.get_mute()
            }
        except Exception as e:
            return {"status": "failed", "message": f"Failed to set volume: {e}"}


class GetVolumeStatusTool(BaseTool):
    name = "volume_status"
    description = "Gets the current system volume status."
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            vol = VolumeManager.get_volume()
            muted = VolumeManager.get_mute()
            mute_str = "Yes" if muted else "No"
            return {
                "status": "success", 
                "title": "Volume Status",
                "message": "Current volume settings retrieved.",
                "metadata": {
                    "Volume Level": f"{vol}%",
                    "Muted": mute_str
                },
                "volume_level": vol,
                "is_muted": muted
            }
        except Exception as e:
            return {"status": "failed", "message": f"Failed to get volume status: {e}"}
