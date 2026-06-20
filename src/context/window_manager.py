import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class WindowManager:
    """
    Provides a deterministic layer for interacting with application windows.
    """
    def __init__(self):
        try:
            import pygetwindow as gw
            import psutil
            import win32process
            import win32gui
            import win32con
            self.gw = gw
            self.psutil = psutil
            self.win32process = win32process
            self.win32gui = win32gui
            self.win32con = win32con
        except ImportError as e:
            logger.warning(f"WindowManager: Could not import dependencies. Some features may not work. Error: {e}")

    def get_active_window(self) -> Optional[Dict[str, Any]]:
        """Returns metadata about the currently active foreground window."""
        try:
            hwnd = self.win32gui.GetForegroundWindow()
            if not hwnd:
                return None
            
            title = self.win32gui.GetWindowText(hwnd)
            _, pid = self.win32process.GetWindowThreadProcessId(hwnd)
            
            process_name = "unknown"
            try:
                process_name = self.psutil.Process(pid).name()
            except (self.psutil.NoSuchProcess, self.psutil.AccessDenied):
                pass
                
            is_minimized = self.win32gui.IsIconic(hwnd) != 0
            
            return {
                "title": title,
                "process_name": process_name,
                "is_minimized": is_minimized
            }
        except Exception as e:
            logger.error(f"WindowManager: Error getting active window: {e}")
            return None

    def _get_aliases(self, window_name: str) -> list:
        try:
            from src.context.application_aliases import APP_WINDOW_ALIASES
            name_lower = window_name.lower()
            return APP_WINDOW_ALIASES.get(name_lower, [name_lower])
        except ImportError:
            return [window_name.lower()]

    def find_window(self, window_name: str) -> Optional[Dict[str, Any]]:
        """Finds a window by a case-insensitive partial match of its title."""
        logger.info(f"WindowManager: Searching for {window_name}")
        aliases = self._get_aliases(window_name)
        try:
            windows = self.gw.getAllWindows()
            for win in windows:
                if win.title and any(alias in win.title.lower() for alias in aliases):
                    logger.info(f"WindowManager: {window_name} found")
                    hwnd = win._hWnd
                    if not self.win32gui.IsWindow(hwnd):
                        continue
                    active_hwnd = self.win32gui.GetForegroundWindow()
                    is_active = (hwnd == active_hwnd)
                    return {
                        "title": win.title,
                        "matched_name": window_name,
                        "is_active": is_active,
                        "is_minimized": win.isMinimized
                    }
            logger.info(f"WindowManager: {window_name} not found")
            return None
        except Exception as e:
            logger.error(f"WindowManager: Error finding window '{window_name}': {e}")
            return None

    def is_window_open(self, window_name: str) -> bool:
        """Checks if a window with the given name is open."""
        return self.find_window(window_name) is not None

    def focus_window(self, window_name: str) -> Dict[str, str]:
        """Brings the matching window to the foreground."""
        logger.info(f"WindowManager: Focusing {window_name}")
        aliases = self._get_aliases(window_name)
        try:
            windows = self.gw.getAllWindows()
            for win in windows:
                if win.title and any(alias in win.title.lower() for alias in aliases):
                    hwnd = win._hWnd
                    if not self.win32gui.IsWindow(hwnd):
                        continue
                        
                    _, pid = self.win32process.GetWindowThreadProcessId(hwnd)
                    process_name = "unknown"
                    try:
                        process_name = self.psutil.Process(pid).name()
                    except (self.psutil.NoSuchProcess, self.psutil.AccessDenied):
                        pass
                        
                    is_minimized = self.win32gui.IsIconic(hwnd) != 0
                    logger.info(f"WindowManager: Found '{win.title}' (hwnd: {hwnd}, process: {process_name}, minimized: {is_minimized})")
                    
                    if is_minimized:
                        self.win32gui.ShowWindow(hwnd, self.win32con.SW_RESTORE)
                    
                    try:
                        win.activate()
                    except Exception as ex:
                        logger.warning(f"WindowManager: pygetwindow activate() failed: {ex}")
                        
                    try:
                        self.win32gui.BringWindowToTop(hwnd)
                        self.win32gui.SetForegroundWindow(hwnd)
                    except Exception as ex:
                        logger.warning(f"WindowManager: SetForegroundWindow failed: {ex}")
                        
                    import time
                    time.sleep(0.1)
                    active_win = self.get_active_window()
                    if active_win and active_win.get("title") == win.title:
                        logger.info(f"WindowManager: {window_name} focused successfully")
                        return {"status": "success", "message": f"Focused window: {win.title}"}
                    else:
                        logger.warning(f"WindowManager: {window_name} focus partial (Windows prevented foreground)")
                        return {"status": "partial_success", "message": f"{win.title} found but Windows prevented foreground activation."}
            
            logger.info(f"WindowManager: Focus failed. {window_name} not found.")
            return {"status": "failed", "message": "Window not found"}
        except Exception as e:
            logger.error(f"WindowManager: Error focusing window '{window_name}': {e}")
            return {"status": "failed", "message": str(e)}
