import os
import json
import logging
import winreg
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class ApplicationFinder:
    """
    An Application Discovery Engine that scans the system for installed applications,
    builds an index, and caches it to avoid slow scans on every launch.
    """
    # Centralized Alias Mapping
    ALIASES = {
        "calc": "calculator",
        "vscode": "visual studio code",
        "code": "visual studio code",
        "vs code": "visual studio code",
        "browser": "msedge",
        "edge": "msedge",
        "chrome": "google chrome",
        "firefox": "firefox"
    }

    def __init__(self, index_file: str = "data/application_index.json"):
        # Make sure paths are absolute or relative to the project root
        self.index_file = os.path.abspath(index_file)
        self.app_index: Dict[str, Dict[str, str]] = {}
        self._load_index()

    def _load_index(self):
        """Loads the application index from the cache file."""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Handle backward compatibility: if old format (str), reset it
                    if data and isinstance(next(iter(data.values())), str):
                        logger.warning("Old cache format detected. Rebuilding index.")
                        self.app_index = {}
                        self.refresh_application_index()
                    else:
                        self.app_index = data
                        logger.info(f"Loaded {len(self.app_index)} applications from cache.")
            except Exception as e:
                logger.error(f"Failed to load application index: {e}")
                self.app_index = {}
        else:
            logger.info("Application index not found. Building for the first time...")
            self.refresh_application_index()

    def refresh_application_index(self):
        """Scans the system to build a fresh application index and saves it."""
        logger.info("Scanning system for applications...")
        index = {}
        
        # 1. Registry App Paths
        index.update(self._scan_registry_app_paths())
        
        # 2. Registry Uninstall DisplayIcon
        index.update(self._scan_registry_uninstall())
        
        # 3. Common Program Folders (Shallow Scan)
        index.update(self._scan_common_folders())
        
        # 4. Start Menu Shortcuts
        index.update(self._scan_start_menu())
        
        # 5. UWP / Windows Store Apps
        index.update(self._scan_uwp_apps())

        # Update instance index and save to disk
        self.app_index = index
        self._save_index()
        logger.info(f"Discovered and cached {len(self.app_index)} applications.")

    def _save_index(self):
        """Saves the application index to the cache file."""
        os.makedirs(os.path.dirname(self.index_file), exist_ok=True)
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.app_index, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save application index: {e}")

    def find_application(self, name: str) -> Optional[Dict[str, str]]:
        """
        Attempts to find the executable path and arguments for the given application name.
        """
        if not name:
            return None
            
        logger.info(f"Searching application: {name}")
        name_lower = name.lower()
        
        # 1. Alias Resolution Layer
        name_lower = self.ALIASES.get(name_lower, name_lower)
        
        target_app = None
        
        # 1. Exact match
        if name_lower in self.app_index:
            target_app = self.app_index[name_lower]
            
        # 2. Partial match (e.g., "discord" matching "discord ptb")
        if not target_app:
            for app_name, app_data in self.app_index.items():
                if name_lower == app_name or name_lower in app_name.split():
                    target_app = app_data
                    break
                    
        # 3. Handle cases where user input includes .exe
        if not target_app and name_lower.endswith(".exe"):
            base_name = name_lower[:-4]
            if base_name in self.app_index:
                target_app = self.app_index[base_name]
                
        if target_app:
            logger.info(f"Resolved target:\n{target_app.get('path')}\n\nArguments:\n{target_app.get('arguments')}")
            return target_app
            
        logger.info("Application not found")
        return None

    def list_installed_applications(self) -> List[str]:
        """Returns a list of all discovered application names."""
        return list(self.app_index.keys())

    def is_valid_application(self, path: str) -> bool:
        """Validates if a given path is an actual file and executable, or a virtual UWP path."""
        if not path:
            return False
            
        path_lower = path.lower()
        if path_lower.startswith("shell:appsfolder\\"):
            return True
            
        if not os.path.exists(path) or not os.path.isfile(path):
            return False
            
        return path_lower.endswith(".exe") or path_lower.endswith(".lnk") or path_lower.endswith(".bat")

    def _resolve_shortcut(self, path: str) -> Tuple[str, str]:
        """Resolves a .lnk shortcut to its actual executable target and arguments."""
        if not path.lower().endswith('.lnk'):
            return path, ""
            
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(path)
            target = shortcut.Targetpath
            arguments = shortcut.Arguments
            
            if target and self.is_valid_application(target):
                logger.info(f"Found shortcut:\n{path}\n\nResolved target:\n{target}\nArguments: {arguments}")
                return target, arguments
        except Exception as e:
            logger.debug(f"Failed to resolve shortcut {path}: {e}")
            
        return path, ""

    def _add_to_index(self, index: Dict[str, Dict[str, str]], name: str, path: str, arguments: str = ""):
        """Helper to cleanly add verified paths and arguments to the index."""
        if not name or not path:
            return
            
        # Resolve shortcuts to real executables
        resolved_path, resolved_args = self._resolve_shortcut(path)
        final_args = resolved_args if resolved_args else arguments
            
        # Only add to index if it's a valid application file
        if not self.is_valid_application(resolved_path):
            return
            
        name_clean = name.lower().replace(".exe", "").strip()
        # Avoid overriding exact short names with longer ones unless it's a better path
        if name_clean and name_clean not in index:
            index[name_clean] = {
                "path": resolved_path,
                "arguments": final_args
            }

    def _scan_registry_app_paths(self) -> Dict[str, str]:
        """Scans the Windows Registry 'App Paths' keys."""
        index = {}
        hives = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths")
        ]
        for hive, key_path in hives:
            try:
                with winreg.OpenKey(hive, key_path) as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            sub_key_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, sub_key_name) as sub_key:
                                val, _ = winreg.QueryValueEx(sub_key, "")
                                if val and isinstance(val, str):
                                    self._add_to_index(index, sub_key_name, val)
                        except OSError:
                            continue
            except OSError:
                continue
        return index

    def _scan_registry_uninstall(self) -> Dict[str, str]:
        """Scans the Uninstall registry keys for DisplayIcons."""
        index = {}
        hives = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
        ]
        for hive, key_path in hives:
            try:
                with winreg.OpenKey(hive, key_path) as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            sub_key_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, sub_key_name) as sub_key:
                                try:
                                    display_name, _ = winreg.QueryValueEx(sub_key, "DisplayName")
                                    display_icon, _ = winreg.QueryValueEx(sub_key, "DisplayIcon")
                                    if display_icon and isinstance(display_icon, str):
                                        icon_path = display_icon.split(',')[0].strip('"')
                                        if icon_path.lower().endswith('.exe'):
                                            self._add_to_index(index, display_name, icon_path)
                                except OSError:
                                    pass
                        except OSError:
                            continue
            except OSError:
                continue
        return index

    def _scan_common_folders(self) -> Dict[str, str]:
        """Shallow scans common installation directories."""
        index = {}
        folders = [
            os.environ.get('ProgramFiles'),
            os.environ.get('ProgramFiles(x86)'),
            os.environ.get('LOCALAPPDATA'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs'),
            os.environ.get('APPDATA')
        ]
        
        for folder in folders:
            if not folder or not os.path.exists(folder):
                continue
            try:
                for item in os.listdir(folder):
                    sub_path = os.path.join(folder, item)
                    if os.path.isdir(sub_path):
                        # 1. Check if an exe with same name as folder exists
                        exe_path = os.path.join(sub_path, f"{item}.exe")
                        if os.path.exists(exe_path):
                            self._add_to_index(index, item, exe_path)
                            continue
                        
                        # 2. Grab the first major .exe found
                        try:
                            for file in os.listdir(sub_path):
                                if file.lower().endswith('.exe'):
                                    file_lower = file.lower()
                                    if "uninstall" not in file_lower and "update" not in file_lower and "crash" not in file_lower:
                                        self._add_to_index(index, item, os.path.join(sub_path, file))
                                        break
                        except OSError:
                            pass
            except OSError:
                pass
        return index

    def _scan_start_menu(self) -> Dict[str, str]:
        """Scans Start Menu folders for shortcuts (.lnk)."""
        index = {}
        folders = [
            os.path.join(os.environ.get('APPDATA', ''), r'Microsoft\Windows\Start Menu\Programs'),
            os.path.join(os.environ.get('ALLUSERSPROFILE', ''), r'Microsoft\Windows\Start Menu\Programs')
        ]
        for folder in folders:
            if not folder or not os.path.exists(folder):
                continue
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith('.lnk'):
                        name = file[:-4]
                        self._add_to_index(index, name, os.path.join(root, file))
        return index

    def _scan_uwp_apps(self) -> Dict[str, Dict[str, str]]:
        """Scans installed UWP/Store Apps via PowerShell and returns virtual AppIDs."""
        index = {}
        try:
            import subprocess
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-StartApps | ConvertTo-Json"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0 and result.stdout:
                apps = json.loads(result.stdout)
                for app in apps:
                    name = app.get("Name", "")
                    appid = app.get("AppID", "")
                    if name and appid:
                        self._add_to_index(index, name, f"shell:AppsFolder\\{appid}")
        except Exception as e:
            logger.error(f"Failed to scan UWP apps: {e}")
            
        return index
