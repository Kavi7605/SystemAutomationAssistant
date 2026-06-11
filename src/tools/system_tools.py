import os
import subprocess
import datetime
import socket
import webbrowser
import logging
import pyautogui
import traceback
import time
import psutil
import shlex
from typing import Dict, Any

from src.tools.base import BaseTool
from src.tools.application_finder import ApplicationFinder

logger = logging.getLogger(__name__)

class OpenApplicationTool(BaseTool):
    name = "open_application"
    description = "Opens an application by its name or path."

    def __init__(self, application_finder: ApplicationFinder):
        self.application_finder = application_finder

    def execute(self, application_name: str, **kwargs) -> Dict[str, Any]:
        if not application_name:
            return {"status": "failed", "message": "Missing application_name"}
            
        logger.info(f"\n--- Application Launch Request ---")
        logger.info(f"Requested app: {application_name}")
        
        resolved_app_data = self.application_finder.find_application(application_name)
        
        if resolved_app_data:
            target_app = resolved_app_data.get("path")
            arguments = resolved_app_data.get("arguments", "")
        else:
            target_app = application_name
            arguments = ""
            
        logger.info(f"Resolved executable: {target_app}")
        logger.info(f"Arguments: {arguments}")
        
        # Construct the safe list-based command
        cmd_list = [target_app]
        if arguments:
            cmd_list.extend(shlex.split(arguments))
            
        logger.info(f"Final command: {cmd_list}")
        logger.info("----------------------------------\n")
        
        return self._launch_and_verify(cmd_list, application_name, target_app)

    def _launch_and_verify(self, cmd_list: list, original_name: str, target_path: str) -> Dict[str, Any]:
        try:
            try:
                # We use a list to Popen directly (safer and handles quotes intrinsically)
                process = subprocess.Popen(cmd_list)
                logger.info(f"PID: {process.pid}")
            except OSError:
                # Fallback for UWP apps or system commands (like 'calc')
                fallback_cmd = f"start {target_path}"
                logger.info(f"Popen failed. Attempting fallback: {fallback_cmd}")
                process = subprocess.Popen(fallback_cmd, shell=True)
                logger.info(f"Fallback PID (shell): {process.pid}")
            
            # Wait for application to spin up
            time.sleep(2.5)
            
            basename = os.path.basename(target_path).lower()
            if basename.endswith(".exe"):
                basename = basename[:-4]
            original_clean = original_name.lower().replace(".exe", "")
            
            if "discord" in target_path.lower() or "discord" in original_clean:
                search_names = ["discord.exe", "discord"]
            else:
                search_names = [f"{basename}.exe", basename, f"{original_clean}.exe", original_clean]
                
            found = False
            for proc in psutil.process_iter(['name']):
                try:
                    p_name = proc.info.get('name', '').lower()
                    if p_name in search_names:
                        found = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
                    
            if found:
                logger.info(f"Verification result: SUCCESS. Found running process for {original_name}.")
                return {"status": "success", "message": f"{original_name.capitalize()} opened successfully"}
            else:
                logger.error(f"Verification result: FAILED. Process for {original_name} not found in process list.")
                return {"status": "failed", "message": f"Application {original_name} failed to launch or verify."}
                
        except Exception as e:
            logger.error(f"Exception while opening application {original_name}: {e}")
            return {"status": "failed", "message": str(e)}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "application_name": {
                    "type": "string",
                    "description": "The name of the application to open, e.g., 'discord' or 'calc'."
                }
            },
            "required": ["application_name"]
        }


class CloseApplicationTool(BaseTool):
    name = "close_application"
    description = "Closes a running application by its name."

    def execute(self, application_name: str, **kwargs) -> Dict[str, Any]:
        if not application_name:
            return {"status": "failed", "message": "Missing application_name"}
            
        logger.info(f"Attempting to close application: {application_name}")
        
        # Ensure we have the .exe suffix for taskkill
        target_exe = application_name if application_name.lower().endswith(".exe") else f"{application_name}.exe"
        
        try:
            result = subprocess.run(f"taskkill /IM {target_exe} /F", shell=True, capture_output=True, text=True)
            if result.returncode == 0 or "SUCCESS" in result.stdout:
                logger.info(f"{application_name.capitalize()} closed successfully")
                return {"status": "success", "message": f"{application_name.capitalize()} closed successfully"}
            else:
                return {"status": "failed", "message": f"Failed to close {application_name}. Output: {result.stderr}"}
        except Exception as e:
            return {"status": "failed", "message": str(e)}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "application_name": {
                    "type": "string",
                    "description": "The name of the application to close, e.g., 'discord' or 'calculator'."
                }
            },
            "required": ["application_name"]
        }


class TakeScreenshotTool(BaseTool):
    name = "take_screenshot"
    description = "Takes a screenshot of the main screen and saves it to a file."

    def execute(self, **kwargs) -> Dict[str, Any]:
        logger.info("Screenshot started")
        try:
            screenshots_dir = "screenshots"
            if not os.path.exists(screenshots_dir):
                os.makedirs(screenshots_dir)
                
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(screenshots_dir, filename)
            
            img = pyautogui.screenshot()
            img.save(filepath)
            
            logger.info("Screenshot saved")
            return {
                "status": "success", 
                "message": "Screenshot captured successfully", 
                "file_path": filepath
            }
        except Exception as e:
            tb_str = traceback.format_exc()
            logger.error(f"Screenshot failed: {e}\nTraceback:\n{tb_str}")
            return {"status": "failed", "message": "Screenshot failed"}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {}
        }


class CreateFolderTool(BaseTool):
    name = "create_folder"
    description = "Creates a new folder at a specified path."

    def execute(self, folder_name: str, path: str = ".", **kwargs) -> Dict[str, Any]:
        if not folder_name:
            return {"status": "failed", "message": "Missing folder_name"}
            
        try:
            full_path = os.path.join(path, folder_name)
            logger.info(f"Creating folder at: {full_path}")
            os.makedirs(full_path, exist_ok=True)
            
            logger.info(f"Folder '{folder_name}' created successfully")
            return {"status": "success", "message": f"Folder '{folder_name}' created successfully", "path": full_path}
        except Exception as e:
            logger.error(f"Failed to create folder: {e}")
            return {"status": "failed", "message": f"Failed to create folder: {str(e)}"}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "folder_name": {
                    "type": "string",
                    "description": "The name of the new folder."
                },
                "path": {
                    "type": "string",
                    "description": "The optional base path where the folder should be created. Default is current directory."
                }
            },
            "required": ["folder_name"]
        }


class SearchWebTool(BaseTool):
    name = "search_web"
    description = "Performs a Google search using the default web browser."

    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
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
            logger.info(f"Web search initiated for: {query}")
            return {"status": "success", "message": f"Searched web for '{query}'"}
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return {"status": "failed", "message": f"Web search failed: {str(e)}"}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "query": {
                    "type": "string",
                    "description": "The search term or phrase to look up."
                }
            },
            "required": ["query"]
        }
