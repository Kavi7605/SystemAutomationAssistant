import logging
import subprocess
import re
from typing import Dict, Any

from src.tools.base import BaseTool

logger = logging.getLogger(__name__)

class PowerManager:
    """
    Manager for Windows Power settings and Battery Saver.
    """
    
    @staticmethod
    def get_battery_saver_status() -> Dict[str, Any]:
        """
        Parses PowerShell PowerManager to get EnergySaverStatus.
        Returns:
            {"enabled": bool}
        """
        ps_script = (
            "Add-Type -AssemblyName System.Runtime.WindowsRuntime; "
            "[Windows.System.Power.PowerManager,Windows.System.Power,ContentType=WindowsRuntime] | Out-Null; "
            "Write-Output [Windows.System.Power.PowerManager]::EnergySaverStatus"
        )
        try:
            result = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True, check=False)
            output = result.stdout.strip()
            
            enabled = False
            if "On" in output:
                enabled = True
                
            return {"enabled": enabled}
            
        except Exception as e:
            logger.error(f"Failed to get Battery Saver status: {e}")
            return {"enabled": False}

    @staticmethod
    def get_power_profiles() -> Dict[str, Any]:
        """
        Parses powercfg /list to find all available power schemes and the active one.
        Returns:
            {
                "active_profile": str,
                "profiles": {
                    "balanced": {"name": "Balanced", "guid": "xxx"},
                    ...
                }
            }
        """
        try:
            result = subprocess.run(["powercfg", "/list"], capture_output=True, text=True, check=False)
            output = result.stdout
            
            profiles = {}
            active_profile = None
            
            for line in output.splitlines():
                # Expected format: Power Scheme GUID: 1e318514-32c7-4aff-8a27-e3967a8213a8  (ASUS Recommended) *
                match = re.search(r"Power Scheme GUID:\s+([a-f0-9\-]+)\s+\((.+?)\)(\s+\*)?", line)
                if match:
                    guid = match.group(1)
                    name = match.group(2)
                    is_active = match.group(3) is not None
                    
                    key = name.lower()
                    profiles[key] = {
                        "name": name,
                        "guid": guid
                    }
                    
                    if is_active:
                        active_profile = name
                        
            return {
                "active_profile": active_profile,
                "profiles": profiles
            }
            
        except Exception as e:
            logger.error(f"Failed to get Power Profiles: {e}")
            return {
                "active_profile": None,
                "profiles": {}
            }

    @staticmethod
    def set_power_profile(guid: str) -> bool:
        """
        Sets the active power scheme using powercfg.
        """
        try:
            subprocess.run(["powercfg", "/setactive", guid], capture_output=True, text=True, check=True)
            return True
        except Exception as e:
            logger.error(f"Failed to set Power Profile {guid}: {e}")
            return False


class GetBatterySaverStatusTool(BaseTool):
    name = "battery_saver_status"
    description = "Gets the current Battery Saver status."
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        status = PowerManager.get_battery_saver_status()
        
        message = (
            "Battery Saver Status\n"
            "--------------------\n"
            f"Enabled: {'Yes' if status['enabled'] else 'No'}"
        )
        
        return {
            "status": "success", 
            "message": message,
            "battery_saver_enabled": status["enabled"]
        }


class ListPowerProfilesTool(BaseTool):
    name = "list_power_profiles"
    description = "Lists all available power profiles and shows the current active one."
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        data = PowerManager.get_power_profiles()
        active = data.get("active_profile", "Unknown")
        profiles = data.get("profiles", {})
        
        profile_names = [p["name"] for p in profiles.values()]
        
        if not profile_names:
            return {
                "status": "error",
                "message": "Failed to retrieve available power profiles."
            }
            
        message = (
            "Power Profiles\n"
            "--------------\n"
            f"Active Profile: {active}\n\n"
            "Available Profiles:\n"
            + "\n".join([f"- {name}" for name in profile_names])
        )
        
        return {
            "status": "success", 
            "message": message,
            "power_plan": active,
            "available_power_profiles": profile_names
        }


class GetPowerModeStatusTool(BaseTool):
    name = "power_status"
    description = "Gets the current active power profile."
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        data = PowerManager.get_power_profiles()
        active = data.get("active_profile", "Unknown")
        profiles = data.get("profiles", {})
        
        profile_names = [p["name"] for p in profiles.values()]
        
        message = (
            "Power Status\n"
            "------------\n"
            f"Current Mode: {active}"
        )
        
        return {
            "status": "success", 
            "message": message,
            "power_plan": active,
            "available_power_profiles": profile_names
        }


class SetPowerModeTool(BaseTool):
    name = "set_power_mode"
    description = "Switches to a specified power profile (e.g., Performance, Balanced, Silent, Turbo)."
    
    def execute(self, mode: str, **kwargs) -> Dict[str, Any]:
        mode_lower = mode.lower()
        data = PowerManager.get_power_profiles()
        profiles = data.get("profiles", {})
        
        # Exact match or substring match
        matched_profile = None
        for key, p in profiles.items():
            if mode_lower in key:
                matched_profile = p
                break
                
        if not matched_profile:
            return {
                "status": "error",
                "message": f"{mode.title()} power profile was not found on this system."
            }
            
        success = PowerManager.set_power_profile(matched_profile["guid"])
        
        if success:
            # Query again to get the true active status
            new_data = PowerManager.get_power_profiles()
            new_active = new_data.get("active_profile", "Unknown")
            all_names = [p["name"] for p in new_data.get("profiles", {}).values()]
            
            return {
                "status": "success",
                "message": f"Successfully switched to {new_active} mode.",
                "power_plan": new_active,
                "available_power_profiles": all_names
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to switch to {matched_profile['name']} mode."
            }
