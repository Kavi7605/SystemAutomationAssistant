import logging
import subprocess
import re
from typing import Dict, Any

from src.tools.base import BaseTool

logger = logging.getLogger(__name__)

class WifiManager:
    """
    Centralized manager for Windows WiFi controls.
    Bypasses admin restrictions by using connection/disconnection instead of adapter toggling.
    """
    
    @staticmethod
    def get_wifi_status() -> Dict[str, Any]:
        """
        Parses 'netsh wlan show interfaces' to get WiFi status.
        Returns:
            {"enabled": bool, "connected": bool, "ssid": str or None}
        """
        try:
            # We use netsh wlan show interfaces
            # If no interface, output contains "There is no wireless interface on the system"
            # Or "The Wireless AutoConfig Service (wlansvc) is not running"
            result = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True, check=False)
            output = result.stdout
            
            if "There is no wireless interface on the system" in output or "wlansvc" in output:
                return {"enabled": False, "connected": False, "ssid": None}
                
            # If there's an interface, it's enabled.
            enabled = True
            connected = False
            ssid = None
            
            # Check connection state
            state_match = re.search(r"^\s*State\s*:\s*(.+)$", output, re.MULTILINE)
            if state_match:
                state = state_match.group(1).strip().lower()
                if state == "connected":
                    connected = True
            
            if connected:
                ssid_match = re.search(r"^\s*SSID\s*:\s*(.+)$", output, re.MULTILINE)
                if ssid_match:
                    ssid = ssid_match.group(1).strip()
                    
            return {"enabled": enabled, "connected": connected, "ssid": ssid}
            
        except Exception as e:
            logger.error(f"Failed to get WiFi status: {e}", exc_info=True)
            return {"enabled": False, "connected": False, "ssid": None}

    @staticmethod
    def disable_wifi() -> bool:
        """
        Disconnects the WiFi interface. 
        Does not physically disable the adapter to avoid needing Admin rights.
        Returns True if successful, False otherwise.
        """
        try:
            result = subprocess.run(["netsh", "wlan", "disconnect"], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to disconnect WiFi: {e}", exc_info=True)
            return False

    @staticmethod
    def enable_wifi(last_ssid: str = None) -> str:
        """
        Attempts to connect to WiFi using priority rules:
        1. last_ssid
        2. preferred profile from netsh
        
        Returns an error message if failed, or empty string if successful.
        """
        try:
            # Priority 1: last_ssid
            if last_ssid:
                logger.info(f"Attempting Priority 1 reconnect to: {last_ssid}")
                res = subprocess.run(["netsh", "wlan", "connect", f"name={last_ssid}"], capture_output=True, text=True, check=False)
                if res.returncode == 0:
                    return ""
                logger.info(f"Priority 1 reconnect failed. Output: {res.stdout.strip()}")
            
            # Get list of profiles for Priority 2
            result = subprocess.run(["netsh", "wlan", "show", "profiles"], capture_output=True, text=True, check=False)
            if result.returncode != 0:
                return "No known WiFi network is available for automatic reconnection."
                
            profiles = []
            for line in result.stdout.splitlines():
                if "All User Profile" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        profiles.append(parts[1].strip())
                        
            if not profiles:
                return "No known WiFi network is available for automatic reconnection."
                
            # Priority 2: Try to connect to the preferred profile
            profile = profiles[0]
            if profile == last_ssid:
                # We already tried this in Priority 1 and it failed
                if len(profiles) > 1:
                    profile = profiles[1]
                else:
                    return "No known WiFi network is available for automatic reconnection."
                    
            logger.info(f"Attempting Priority 2 reconnect to: {profile}")
            connect_res = subprocess.run(["netsh", "wlan", "connect", f"name={profile}"], capture_output=True, text=True, check=False)
            
            if connect_res.returncode == 0:
                return ""
            else:
                logger.info(f"Priority 2 reconnect failed. Output: {connect_res.stdout.strip()}")
                return "No known WiFi network is available for automatic reconnection."
                
        except Exception as e:
            logger.error(f"Failed to enable WiFi: {e}", exc_info=True)
            return "No known WiFi network is available for automatic reconnection."

    @staticmethod
    def get_wifi_debug(last_ssid: str = None) -> str:
        """
        Gathers diagnostic information about WiFi.
        """
        # 1. netsh wlan show interfaces
        interfaces_res = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True, check=False)
        interfaces_out = interfaces_res.stdout
        
        # 2. netsh wlan show profiles
        profiles_res = subprocess.run(["netsh", "wlan", "show", "profiles"], capture_output=True, text=True, check=False)
        
        # 3. Parsed profile list
        profiles = []
        if profiles_res.returncode == 0:
            for line in profiles_res.stdout.splitlines():
                if "All User Profile" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        profiles.append(parts[1].strip())
                        
        # 5. Chosen reconnect target
        chosen_target = "None"
        if last_ssid:
            chosen_target = last_ssid
        elif profiles:
            chosen_target = profiles[0]
            
        lines = [
            "WiFi Debug",
            "----------",
            f"Last SSID: {last_ssid}",
            "",
            "Saved Profiles:"
        ]
        
        if profiles:
            for p in profiles:
                lines.append(f"- {p}")
        else:
            lines.append("- None")
            
        lines.append("")
        lines.append("Chosen Target:")
        lines.append(chosen_target)
        lines.append("")
        lines.append("Current Interface State:")
        lines.append(interfaces_out.strip())
        
        return "\n".join(lines)


class EnableWifiTool(BaseTool):
    name = "enable_wifi"
    description = "Enables/connects to WiFi."
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        last_ssid = None
        context_manager = getattr(self, "context_manager", None)
        if context_manager:
            system_state = context_manager.state.get("system_state", {})
            last_ssid = system_state.get("wifi_name")
            
        error = WifiManager.enable_wifi(last_ssid=last_ssid)
        
        # Always query actual status
        status = WifiManager.get_wifi_status()
        
        if error:
            return {
                "status": "failed", 
                "message": error,
                "wifi_enabled": status["enabled"],
                "wifi_connected": status["connected"],
                "wifi_name": status["ssid"]
            }
            
        return {
            "status": "success", 
            "message": "WiFi enabled successfully.",
            "wifi_enabled": status["enabled"],
            "wifi_connected": status["connected"],
            "wifi_name": status["ssid"]
        }


class DisableWifiTool(BaseTool):
    name = "disable_wifi"
    description = "Disables/disconnects from WiFi."
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        success = WifiManager.disable_wifi()
        
        # Always query actual status
        status = WifiManager.get_wifi_status()
        
        if not success:
            return {
                "status": "failed", 
                "message": "Failed to disconnect WiFi.",
                "wifi_enabled": status["enabled"],
                "wifi_connected": status["connected"],
                "wifi_name": status["ssid"]
            }
            
        return {
            "status": "success", 
            "message": "WiFi disabled successfully.",
            "wifi_enabled": status["enabled"],
            "wifi_connected": status["connected"],
            "wifi_name": status["ssid"]
        }


class GetWifiStatusTool(BaseTool):
    name = "wifi_status"
    description = "Gets the current WiFi status."
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        status = WifiManager.get_wifi_status()
        
        lines = [
            "WiFi Status",
            "-----------",
            f"Adapter Enabled: {'Yes' if status['enabled'] else 'No'}",
            f"Connected: {'Yes' if status['connected'] else 'No'}"
        ]
        
        if status['connected'] and status['ssid']:
            lines.append(f"Network: {status['ssid']}")
            
        message = "\n".join(lines)
        
        return {
            "status": "success", 
            "message": message,
            "wifi_enabled": status["enabled"],
            "wifi_connected": status["connected"],
            "wifi_name": status["ssid"]
        }


class WifiDebugTool(BaseTool):
    name = "wifi_debug"
    description = "Outputs raw diagnostics for WiFi."
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        last_ssid = None
        context_manager = getattr(self, "context_manager", None)
        if context_manager:
            system_state = context_manager.state.get("system_state", {})
            last_ssid = system_state.get("wifi_name")
            
        debug_output = WifiManager.get_wifi_debug(last_ssid)
        
        return {
            "status": "success",
            "message": debug_output
        }
