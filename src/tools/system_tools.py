import os
import subprocess
import datetime
import time
import socket
import webbrowser
import logging
import pyautogui
import traceback
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
            # 1. Direct OS Native Dispatch for absolute paths and UWP Virtual Paths
            # os.startfile is perfect because it delegates directly to the OS shell,
            # avoids locking CMD popups, and natively processes shell:AppsFolder URIs.
            if os.path.isabs(target_path) or target_path.lower().startswith("shell:appsfolder"):
                logger.info(f"Verification method: OS Native Dispatch (os.startfile)")
                try:
                    if len(cmd_list) > 1:
                        # Fallback to subprocess.Popen for strict argument injection without shell=True
                        logger.info(f"Arguments detected, using subprocess.Popen(shell=False)")
                        process = subprocess.Popen(cmd_list)
                        logger.info(f"Launch success. PID: {process.pid}")
                    else:
                        os.startfile(target_path)
                        logger.info(f"Launch success via os.startfile.")
                        
                    return {"status": "success", "message": f"{original_name.capitalize()} opened successfully"}
                    
                except FileNotFoundError:
                    logger.error(f"Verification result: FAILED. File not found: {target_path}")
                    return {"status": "application_not_found", "message": f"Application {original_name} could not be found."}
                except OSError as e:
                    logger.error(f"Verification result: FAILED. OS Error: {e}")
                    return {"status": "failed", "message": f"Application {original_name} failed to launch: {str(e)}"}
            
            # 2. Subprocess execution for unresolved/relative PATH binaries
            else:
                logger.info(f"Verification method: Subprocess Direct Execution")
                try:
                    process = subprocess.Popen(cmd_list)
                    logger.info(f"Launch success. PID: {process.pid}")
                    return {"status": "success", "message": f"{original_name.capitalize()} opened successfully"}
                except FileNotFoundError:
                    logger.error(f"Verification result: FAILED. Unresolved application not in PATH: {target_path}")
                    return {"status": "application_not_found", "message": f"Application {original_name} could not be found in PATH."}
                except OSError as e:
                    logger.error(f"Verification result: FAILED. OS Error: {e}")
                    return {"status": "failed", "message": f"Application {original_name} failed to launch: {str(e)}"}
                    
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
                    "description": "The name of the application to open."
                },
                "fallback_url": {
                    "type": "string",
                    "description": "Optional fallback URL to open if the application is not found."
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
        search_name = application_name.lower().replace(".exe", "")
        
        # Common aliases for process names
        aliases = {
            "calculator": "calculator",
            "calc": "calculator",
            "whatsapp": "whatsapp",
            "discord": "discord",
            "steam": "steam",
            "vscode": "code",
            "code": "code",
            "vs code": "code",
            "visual studio code": "code",
            "visual studio": "devenv",
            "vs": "devenv",
            "github desktop": "githubdesktop",
            "edge": "msedge",
            "browser": "msedge"
        }
        
        target_match = aliases.get(search_name, search_name)
        closed_count = 0
        
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    proc_name = proc.info['name']
                    if proc_name:
                        proc_name_lower = proc_name.lower()
                        # Fuzzy match: e.g. 'whatsapp' in 'whatsapp.exe' or 'calculator' in 'calculatorapp.exe'
                        if target_match in proc_name_lower:
                            proc.kill() # kill() is safer to force close unresponsive apps, similar to /F in taskkill
                            closed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
                    
            if closed_count > 0:
                logger.info(f"{application_name.capitalize()} closed successfully ({closed_count} processes terminated)")
                return {"status": "success", "message": f"{application_name.capitalize()} closed successfully"}
            else:
                return {"status": "failed", "message": f"Could not find any running process matching '{application_name}'"}
                
        except Exception as e:
            logger.error(f"Error closing {application_name}: {e}")
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
            from src.tools.path_resolver import PathResolver
            import ctypes
            
            res = PathResolver.resolve(path)
            if res["status"] == "failed":
                return res
            elif res.get("status") == "ambiguous":
                return res
                
            resolved_base_path = res["resolved_path"].path
            
            full_path = os.path.join(resolved_base_path, folder_name)
            logger.info(f"Creating folder at: {full_path}")
            os.makedirs(full_path, exist_ok=True)
            
            if "desktop" in full_path.lower():
                try:
                    ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
                    logger.info("Triggered Desktop Shell Refresh")
                except Exception as e:
                    logger.warning(f"Failed to refresh desktop: {e}")
            
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





class OpenUrlTool(BaseTool):
    name = "open_url"
    description = "Opens a specified URL in the default web browser."

    def execute(self, url: str, **kwargs) -> Dict[str, Any]:
        if not url:
            return {"status": "failed", "message": "Missing url"}
            
        logger.info(f"Opening URL: {url}")
        
        try:
            # Ensure URL has a scheme
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url
                
            success = webbrowser.open(url)
            if success:
                return {"status": "success", "message": f"Opened URL: {url}"}
            else:
                return {"status": "failed", "message": f"Failed to open URL: {url}"}
        except Exception as e:
            logger.error(f"Failed to open URL {url}: {e}")
            return {"status": "failed", "message": f"Error opening URL: {str(e)}"}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "url": {
                    "type": "string",
                    "description": "The complete URL to open, e.g., 'https://youtube.com'."
                }
            },
            "required": ["url"]
        }


class CreateFileTool(BaseTool):
    name = "create_file"
    description = "Creates a new empty file at a specified path."

    def execute(self, file_name: str, path: str = ".", **kwargs) -> Dict[str, Any]:
        if not file_name:
            return {"status": "failed", "message": "Missing file_name"}
            
        try:
            from src.tools.path_resolver import PathResolver
            import ctypes
            
            res = PathResolver.resolve(path)
            if res["status"] == "failed":
                return res
            elif res.get("status") == "ambiguous":
                return res
                
            resolved_base_path = res["resolved_path"].path
                
            full_path = os.path.join(resolved_base_path, file_name)
            logger.info(f"Creating file at: {full_path}")
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            if os.path.exists(full_path):
                logger.info(f"File '{file_name}' already exists. No changes made.")
                return {"status": "success", "message": f"File '{file_name}' already exists. No changes made.", "path": full_path}
            
            with open(full_path, 'w') as f:
                pass # Creates new empty file
                
            if "desktop" in full_path.lower():
                try:
                    ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
                    logger.info("Triggered Desktop Shell Refresh")
                except Exception as e:
                    logger.warning(f"Failed to refresh desktop: {e}")
                
            logger.info(f"File '{file_name}' created successfully")
            return {"status": "success", "message": f"File '{file_name}' created successfully", "path": full_path}
        except Exception as e:
            logger.error(f"Failed to create file: {e}")
            return {"status": "failed", "message": f"Failed to create file: {str(e)}"}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "file_name": {
                    "type": "string",
                    "description": "The name of the new file, including extension."
                },
                "path": {
                    "type": "string",
                    "description": "The optional base path where the file should be created. Default is current directory."
                }
            },
            "required": ["file_name"]
        }


class OpenFolderTool(BaseTool):
    name = "open_folder"
    description = "Opens a standard Windows folder (e.g., Downloads, Documents, Desktop, etc.)."

    def execute(self, folder_name: str, base_path: str = None, **kwargs) -> Dict[str, Any]:
        if not folder_name:
            return {"status": "failed", "message": "Missing folder_name"}
            
        logger.info(f"Requested to open folder: {folder_name} in base_path: {base_path}")
        
        try:
            from src.tools.path_resolver import PathResolver
            
            if base_path and base_path != ".":
                res = PathResolver.resolve(base_path)
                if res["status"] == "failed":
                    return res
                elif res.get("status") == "ambiguous":
                    return res
                    
                resolved_base_path = res["resolved_path"].path
                full_path = os.path.join(resolved_base_path, folder_name)
                
                if os.path.exists(full_path) and os.path.isdir(full_path):
                    logger.info(f"Resolved path: {full_path}")
                    os.startfile(full_path)
                    return {"status": "success", "message": f"Opened folder: {full_path}", "path": full_path}
                else:
                    return {"status": "failed", "message": f"Resolved path is not a valid directory: {full_path}"}
            else:
                # Fallback search strategy if no base_path is provided
                from src.tools.system_tools import get_real_desktop_path
                cwd_path = os.getcwd()
                desktop_path = get_real_desktop_path()
                home_dir = os.path.expanduser("~")
                downloads_path = os.path.join(home_dir, "Downloads")
                documents_path = os.path.join(home_dir, "Documents")
                
                search_locations = [cwd_path, desktop_path, downloads_path, documents_path]
                
                found_path = None
                for loc in search_locations:
                    if not loc or not os.path.exists(loc): continue
                    test_path = os.path.join(loc, folder_name)
                    if os.path.exists(test_path) and os.path.isdir(test_path):
                        found_path = test_path
                        break
                        
                if not found_path:
                    # Let PathResolver try one last time in case folder_name is a known base location (like 'desktop' or 'reports' in cwd)
                    res = PathResolver.resolve(folder_name)
                    if res["status"] == "success" and res["resolved_path"].is_directory:
                        found_path = res["resolved_path"].path
                    else:
                        return {"status": "failed", "message": f"Folder does not exist: {folder_name} in default locations."}
                        
                logger.info(f"Resolved path: {found_path}")
                os.startfile(found_path)
                return {"status": "success", "message": f"Opened folder: {found_path}", "path": found_path}
                
        except Exception as e:
            logger.error(f"Failed to open folder: {e}")
            return {"status": "failed", "message": f"Error opening folder: {str(e)}"}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "folder_name": {
                    "type": "string",
                    "description": "The exact name of the folder to open."
                },
                "base_path": {
                    "type": "string",
                    "description": "The natural language location of the base path (e.g., 'C drive', 'desktop')."
                }
            },
            "required": ["folder_name"]
        }

class OpenFileTool(BaseTool):
    name = "open_file"
    description = "Opens a file using its default Windows application."

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "file_name": {
                    "type": "string",
                    "description": "The exact name of the file to open (e.g., notes.txt)."
                },
                "path": {
                    "type": "string",
                    "description": "The natural language location of the file (e.g., 'C drive Projects', 'desktop')."
                }
            },
            "required": ["file_name", "path"]
        }

    def execute(self, file_name: str, path: str = None, **kwargs) -> Dict[str, Any]:
        if not file_name:
            return {"status": "failed", "message": "Missing file_name"}
            
        logger.info(f"Requested to open file: {file_name} in {path}")
        
        import os
        from src.tools.path_resolver import PathResolver
        
        try:
            if not path or path == ".":
                # Fallback search strategy
                from src.tools.system_tools import get_real_desktop_path
                
                # Derive paths
                cwd_path = os.getcwd()
                desktop_path = get_real_desktop_path()
                home_dir = os.path.expanduser("~")
                downloads_path = os.path.join(home_dir, "Downloads")
                documents_path = os.path.join(home_dir, "Documents")
                
                search_locations = [cwd_path, desktop_path, downloads_path, documents_path]
                
                found_path = None
                for loc in search_locations:
                    if not loc or not os.path.exists(loc):
                        continue
                    test_path = os.path.join(loc, file_name)
                    if os.path.exists(test_path) and os.path.isfile(test_path):
                        found_path = test_path
                        break
                        
                if not found_path:
                    return {"status": "failed", "message": f"File does not exist: {file_name} in default locations."}
                    
                full_path = found_path
            else:
                res = PathResolver.resolve(path)
                if res["status"] == "failed":
                    return res
                elif res.get("status") == "ambiguous":
                    return res
                    
                resolved_base_path = res["resolved_path"].path
                full_path = os.path.join(resolved_base_path, file_name)
                
                if not os.path.exists(full_path):
                    return {"status": "failed", "message": f"File does not exist: {full_path}"}
                    
                if not os.path.isfile(full_path):
                    return {"status": "failed", "message": f"Path is not a file: {full_path}"}
                    
            logger.info(f"Resolved file path: {full_path}")
            os.startfile(full_path)
            return {"status": "success", "message": f"Opened file: {full_path}", "path": full_path}
                
        except Exception as e:
            logger.error(f"Failed to open file: {e}")
            return {"status": "failed", "message": f"Error opening file: {str(e)}"}
