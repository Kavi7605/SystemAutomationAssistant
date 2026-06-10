import os
import subprocess
import datetime
import socket
import webbrowser
import logging
import pyautogui
import traceback

logger = logging.getLogger("system_assistant")

class Executor:
    """
    Executes automation actions based on parsed JSON commands.
    """
    def __init__(self):
        pass

    def execute(self, command_json: dict) -> dict:
        """
        Routes the parsed JSON command to the appropriate handler.
        """
        action = command_json.get("action")
        parameters = command_json.get("parameters", {})

        if not action or action == "unknown":
            return {"status": "failed", "message": "Unknown or unsupported action."}

        try:
            if action == "open_application":
                return self._open_application(parameters.get("application_name"))
            elif action == "close_application":
                return self._close_application(parameters.get("application_name"))
            elif action == "take_screenshot":
                return self._take_screenshot()
            elif action == "create_folder":
                return self._create_folder(parameters.get("folder_name"), parameters.get("path"))
            elif action == "search_web":
                return self._search_web(parameters.get("query"))
            else:
                return {"status": "failed", "message": f"Handler for {action} not implemented."}
        except Exception as e:
            logger.error(f"Error executing {action}: {e}", exc_info=True)
            return {"status": "failed", "message": str(e)}

    def _open_application(self, app_name: str) -> dict:
        if not app_name:
            return {"status": "failed", "message": "Missing application_name"}
            
        logger.info(f"Attempting to open application: {app_name}")
        
        try:
            # For Windows, 'start' can open registered apps
            result = subprocess.run(f"start {app_name}", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                logger.success(f"{app_name.capitalize()} opened successfully")
                return {"status": "success", "message": f"{app_name.capitalize()} opened successfully"}
            else:
                logger.error(f"Failed to open {app_name}: {result.stderr}")
                return {"status": "failed", "message": f"Application not found"}
        except Exception as e:
            logger.error(f"Exception while opening application {app_name}: {e}")
            return {"status": "failed", "message": "Application not found"}

    def _close_application(self, app_name: str) -> dict:
        if not app_name:
            return {"status": "failed", "message": "Missing application_name"}
            
        logger.info(f"Attempting to close application: {app_name}")
        try:
            result = subprocess.run(f"taskkill /IM {app_name}.exe /F", shell=True, capture_output=True, text=True)
            if result.returncode == 0 or "SUCCESS" in result.stdout:
                logger.success(f"{app_name.capitalize()} closed successfully")
                return {"status": "success", "message": f"{app_name.capitalize()} closed successfully"}
            else:
                return {"status": "failed", "message": f"Failed to close {app_name}"}
        except Exception as e:
            return {"status": "failed", "message": str(e)}

    def _take_screenshot(self) -> dict:
        logger.info("Screenshot started")
        try:
            screenshots_dir = "screenshots"
            if not os.path.exists(screenshots_dir):
                os.makedirs(screenshots_dir)
                
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(screenshots_dir, filename)
            
            # Using the working approach rather than passing filepath directly
            img = pyautogui.screenshot()
            img.save(filepath)
            
            logger.success("Screenshot saved")
            return {
                "status": "success", 
                "message": "Screenshot captured successfully", 
                "file_path": filepath
            }
        except Exception as e:
            tb_str = traceback.format_exc()
            logger.error(f"Screenshot failed: {e}\nTraceback:\n{tb_str}")
            return {"status": "failed", "message": "Screenshot failed"}

    def _create_folder(self, folder_name: str, path: str = None) -> dict:
        if not folder_name:
            return {"status": "failed", "message": "Missing folder_name"}
            
        try:
            target_path = path if path else "."
            full_path = os.path.join(target_path, folder_name)
            
            logger.info(f"Creating folder at: {full_path}")
            os.makedirs(full_path, exist_ok=True)
            
            logger.success(f"Folder '{folder_name}' created successfully")
            return {"status": "success", "message": f"Folder '{folder_name}' created successfully", "path": full_path}
        except Exception as e:
            logger.error(f"Failed to create folder: {e}")
            return {"status": "failed", "message": "Failed to create folder"}

    def _search_web(self, query: str) -> dict:
        if not query:
            return {"status": "failed", "message": "Missing query"}
            
        logger.info(f"Searching web for: {query}")
        
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
        except OSError:
            logger.error("Internet unavailable for web search")
            return {"status": "failed", "message": "Internet unavailable"}
            
        try:
            search_url = f"https://www.google.com/search?q={query}"
            webbrowser.open_new_tab(search_url)
            logger.success(f"Web search initiated for: {query}")
            return {"status": "success", "message": f"Searched web for '{query}'"}
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return {"status": "failed", "message": "Web search failed"}
