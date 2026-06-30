import logging
import subprocess
from typing import Dict, Any

from src.tools.base import BaseTool

logger = logging.getLogger(__name__)

class HotspotManager:
    """
    Manager for Windows Mobile Hotspot controls.
    """
    
    @staticmethod
    def get_hotspot_status() -> Dict[str, Any]:
        """
        Parses PowerShell TetheringManager to get hotspot status.
        Returns:
            {"enabled": bool}
        """
        ps_script = (
            "$connectionProfile = [Windows.Networking.Connectivity.NetworkInformation,Windows.Networking.Connectivity,ContentType=WindowsRuntime]::GetInternetConnectionProfile(); "
            "if ($connectionProfile -eq $null) { Write-Output 'Off'; exit }; "
            "$tetheringManager = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime]::CreateFromConnectionProfile($connectionProfile); "
            "Write-Output $tetheringManager.TetheringOperationalState"
        )
        try:
            result = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True, check=False)
            output = result.stdout.strip()
            
            enabled = False
            if output == "On":
                enabled = True
                
            return {"enabled": enabled}
            
        except Exception as e:
            logger.error(f"Failed to get Hotspot status: {e}", exc_info=True)
            return {"enabled": False}


class GetHotspotStatusTool(BaseTool):
    name = "hotspot_status"
    description = "Gets the current Mobile Hotspot status."
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        status = HotspotManager.get_hotspot_status()
        
        message = (
            "Mobile Hotspot Status\n"
            "---------------------\n"
            f"Enabled: {'Yes' if status['enabled'] else 'No'}"
        )
        
        return {
            "status": "success", 
            "message": message,
            "hotspot_enabled": status["enabled"]
        }
