import logging
import time
import psutil
from typing import Dict, Any

from src.tools.base import BaseTool
from src.context.window_manager import WindowManager

logger = logging.getLogger(__name__)

class WaitTool(BaseTool):
    name = "wait"
    description = "Smart waiting layer for the assistant with polling capabilities."

    def __init__(self, window_manager: WindowManager = None):
        self.window_manager = window_manager or WindowManager()

    def execute(self, wait_type: str = "seconds", seconds: int = None, window_name: str = None, app_name: str = None, timeout: int = 30, **kwargs) -> Dict[str, Any]:
        try:
            if wait_type == "seconds":
                if seconds is None:
                    return {"status": "failed", "message": "Missing 'seconds' parameter for wait_seconds"}
                return self.wait_seconds(seconds)
            elif wait_type == "window":
                if not window_name:
                    return {"status": "failed", "message": "Missing 'window_name' parameter for wait_until_window"}
                return self.wait_until_window(window_name, timeout)
            elif wait_type == "window_closed":
                if not window_name:
                    return {"status": "failed", "message": "Missing 'window_name' parameter for wait_until_window_closed"}
                return self.wait_until_window_closed(window_name, timeout)
            elif wait_type == "app":
                if not app_name:
                    return {"status": "failed", "message": "Missing 'app_name' parameter for wait_until_app_open"}
                return self.wait_until_app_open(app_name, timeout)
            elif wait_type == "app_closed":
                if not app_name:
                    return {"status": "failed", "message": "Missing 'app_name' parameter for wait_until_app_closed"}
                return self.wait_until_app_closed(app_name, timeout)
            else:
                return {"status": "failed", "message": f"Unknown wait_type: {wait_type}"}
        except Exception as e:
            logger.error(f"WaitTool error: {e}")
            return {"status": "failed", "message": str(e)}

    def wait_seconds(self, seconds: int) -> Dict[str, Any]:
        seconds = int(seconds)
        time.sleep(seconds)
        return {"status": "success", "message": f"Waited {seconds} seconds"}

    def wait_until_window(self, window_name: str, timeout: int = 30) -> Dict[str, Any]:
        start_time = time.time()
        while time.time() - start_time < timeout:
            win = self.window_manager.find_window(window_name)
            if win:
                return {"status": "success", "message": f"Window '{window_name}' appeared"}
            time.sleep(0.5)
        return {"status": "failed", "message": f"Timeout waiting for window '{window_name}'"}

    def wait_until_window_closed(self, window_name: str, timeout: int = 30) -> Dict[str, Any]:
        start_time = time.time()
        while time.time() - start_time < timeout:
            win = self.window_manager.find_window(window_name)
            if not win:
                return {"status": "success", "message": f"Window '{window_name}' closed"}
            time.sleep(0.5)
        return {"status": "failed", "message": f"Timeout waiting for window '{window_name}' to close"}

    def wait_until_app_open(self, app_name: str, timeout: int = 30) -> Dict[str, Any]:
        start_time = time.time()
        search_name = app_name.lower().replace(".exe", "")
        aliases = {
            "calculator": "calculator",
            "calc": "calculator",
            "whatsapp": "whatsapp",
            "discord": "discord",
            "steam": "steam",
            "vscode": "code",
            "code": "code",
            "edge": "msedge"
        }
        target_match = aliases.get(search_name, search_name)
        
        while time.time() - start_time < timeout:
            for proc in psutil.process_iter(['name']):
                try:
                    proc_name = proc.info['name']
                    if proc_name and target_match in proc_name.lower():
                        return {"status": "success", "message": f"Application '{app_name}' opened"}
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            time.sleep(0.5)
        return {"status": "failed", "message": f"Timeout waiting for application '{app_name}'"}

    def wait_until_app_closed(self, app_name: str, timeout: int = 30) -> Dict[str, Any]:
        start_time = time.time()
        search_name = app_name.lower().replace(".exe", "")
        aliases = {
            "calculator": "calculator",
            "calc": "calculator",
            "whatsapp": "whatsapp",
            "discord": "discord",
            "steam": "steam",
            "vscode": "code",
            "code": "code",
            "edge": "msedge"
        }
        target_match = aliases.get(search_name, search_name)
        
        while time.time() - start_time < timeout:
            found = False
            for proc in psutil.process_iter(['name']):
                try:
                    proc_name = proc.info['name']
                    if proc_name and target_match in proc_name.lower():
                        found = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            if not found:
                return {"status": "success", "message": f"Application '{app_name}' closed"}
            time.sleep(0.5)
        return {"status": "failed", "message": f"Timeout waiting for application '{app_name}' to close"}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "wait_type": {
                    "type": "string",
                    "description": "Type of wait: 'seconds', 'window', or 'app'"
                },
                "seconds": {
                    "type": "integer",
                    "description": "Number of seconds to wait"
                },
                "window_name": {
                    "type": "string",
                    "description": "Name of the window to wait for"
                },
                "app_name": {
                    "type": "string",
                    "description": "Name of the application to wait for"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default 30)"
                }
            },
            "required": ["wait_type"]
        }
