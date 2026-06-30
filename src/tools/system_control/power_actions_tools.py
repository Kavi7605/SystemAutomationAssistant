import subprocess
import logging
from typing import Dict, Any

from src.tools.base import BaseTool

logger = logging.getLogger(__name__)

class ShutdownTool(BaseTool):
    name = "shutdown_pc"
    description = "Initiates a shutdown request (requires confirmation)."
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        return {
            "status": "success",
            "message": "Are you sure you want to shut down the PC?\nType:\nconfirm shutdown",
            "pending_power_action": "shutdown"
        }

class RestartTool(BaseTool):
    name = "restart_pc"
    description = "Initiates a restart request (requires confirmation)."
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        return {
            "status": "success",
            "message": "Are you sure you want to restart the PC?\nType:\nconfirm restart",
            "pending_power_action": "restart"
        }

class SleepTool(BaseTool):
    name = "sleep_pc"
    description = "Puts the PC to sleep."
    
    def _is_sleep_supported(self) -> bool:
        try:
            result = subprocess.run(["powercfg", "/a"], capture_output=True, text=True, check=False)
            output = result.stdout.lower()
            # Look for S3 or S0 Low Power Idle in the supported states section
            if "standby (s3)" in output or "standby (s0 low power idle)" in output:
                # Also check if it's in the "not available" section
                # But powercfg /a output structure usually lists available ones first.
                # A simple check: if "standby (s3)" is reported as supported, we can try.
                # To be safer, we can just look for the literal string indicating availability.
                lines = output.splitlines()
                supported = False
                in_supported_section = False
                for line in lines:
                    line = line.strip()
                    if line.startswith("the following sleep states are available"):
                        in_supported_section = True
                    elif line.startswith("the following sleep states are not available"):
                        in_supported_section = False
                        
                    if in_supported_section and ("standby (s3)" in line or "standby (s0 low power idle)" in line):
                        supported = True
                        break
                return supported
        except Exception as e:
            logger.error(f"Error checking sleep support: {e}", exc_info=True)
        # Default to True to attempt it if parsing fails
        return True

    def execute(self, **kwargs) -> Dict[str, Any]:
        if not self._is_sleep_supported():
            return {
                "status": "error",
                "message": "True Sleep (S3 or S0) is not supported or currently disabled on this system's configuration. Falling back to Hibernate is prevented by design."
            }
            
        ps_command = "Add-Type -Assembly System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState([System.Windows.Forms.PowerState]::Suspend, $false, $false)"
        try:
            subprocess.run(["powershell", "-Command", ps_command], check=True)
            return {
                "status": "success",
                "message": "System is going to sleep.",
                "last_power_action": "sleep"
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to sleep PC: {e}", exc_info=True)
            return {
                "status": "error",
                "message": "Failed to execute sleep command."
            }

class LockScreenTool(BaseTool):
    name = "lock_screen"
    description = "Locks the Windows screen."
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=True)
            return {
                "status": "success",
                "message": "Screen locked.",
                "last_power_action": "lock"
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to lock screen: {e}", exc_info=True)
            return {
                "status": "error",
                "message": "Failed to lock screen."
            }

class ConfirmPowerActionTool(BaseTool):
    name = "confirm_power_action"
    description = "Confirms a pending power action (shutdown or restart)."
    
    def execute(self, action_type: str, pending_action: str, **kwargs) -> Dict[str, Any]:
        if not pending_action or pending_action != action_type:
            return {
                "status": "error",
                "message": f"No pending {action_type} confirmation exists."
            }
            
        try:
            if action_type == "shutdown":
                subprocess.run(["shutdown", "/s", "/t", "0"], check=True)
                msg = "Shutting down..."
            elif action_type == "restart":
                subprocess.run(["shutdown", "/r", "/t", "0"], check=True)
                msg = "Restarting..."
            else:
                return {"status": "error", "message": "Unknown action type."}
                
            return {
                "status": "success",
                "message": msg,
                "last_power_action": action_type,
                "clear_pending": True
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to execute {action_type}: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to execute {action_type}."
            }

class CancelPowerActionTool(BaseTool):
    name = "cancel_power_action"
    description = "Cancels any pending power action."
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        return {
            "status": "success",
            "message": "Pending power action cancelled.",
            "clear_pending": True
        }
