import logging
import time
from typing import Dict, Any, List
from src.tools.base import BaseTool

logger = logging.getLogger(__name__)

class WindowManager:
    """
    Centralized manager for deterministic Windows window control via native APIs.
    Bypasses UI automation dependencies.
    """
    @staticmethod
    def _import_win32():
        try:
            import win32gui
            import win32process
            import win32con
            import psutil
            return win32gui, win32process, win32con, psutil
        except ImportError as e:
            logger.error(f"WindowManager dependencies missing: {e}")
            raise

    @staticmethod
    def _get_process_name(pid, psutil_mod) -> str:
        try:
            return psutil_mod.Process(pid).name()
        except (psutil_mod.NoSuchProcess, psutil_mod.AccessDenied):
            return "Unknown"

    @staticmethod
    def _is_valid_window(hwnd, win32gui, check_visible=True) -> bool:
        """Filters out hidden and invalid windows."""
        if not win32gui.IsWindow(hwnd):
            return False
        if check_visible and not win32gui.IsWindowVisible(hwnd):
            return False
        title = win32gui.GetWindowText(hwnd)
        if not title.strip():
            return False
        return True

    @staticmethod
    def _get_window_info(hwnd) -> Dict[str, Any]:
        win32gui, win32process, win32con, psutil_mod = WindowManager._import_win32()
        title = win32gui.GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        app_name = WindowManager._get_process_name(pid, psutil_mod)
        
        placement = win32gui.GetWindowPlacement(hwnd)[1]
        state = "Normal"
        if placement == win32con.SW_SHOWMAXIMIZED:
            state = "Maximized"
        elif placement == win32con.SW_SHOWMINIMIZED or win32gui.IsIconic(hwnd):
            state = "Minimized"
            
        return {
            "title": title,
            "app_name": app_name,
            "state": state,
            "pid": pid,
            "hwnd": hwnd
        }

    @staticmethod
    def get_current_window() -> Dict[str, Any]:
        """Returns info about the active foreground window."""
        win32gui, _, _, _ = WindowManager._import_win32()
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd or not win32gui.IsWindow(hwnd):
            return {
                "title": "Unknown",
                "app_name": "Unknown",
                "state": "Unknown",
                "pid": 0,
                "hwnd": 0
            }
        return WindowManager._get_window_info(hwnd)

    @staticmethod
    def list_open_windows() -> List[Dict[str, Any]]:
        """Lists all visible top-level windows with non-empty titles."""
        win32gui, _, _, _ = WindowManager._import_win32()
        windows = []
        
        def callback(hwnd, extra):
            if WindowManager._is_valid_window(hwnd, win32gui, check_visible=True):
                windows.append(WindowManager._get_window_info(hwnd))
            return True
            
        win32gui.EnumWindows(callback, None)
        return windows

    @staticmethod
    def find_windows(target: str) -> List[Dict[str, Any]]:
        """Finds windows matching the target by exact app name or partial title."""
        target_lower = target.lower().strip()
        all_windows = WindowManager.list_open_windows()
        matches = []
        
        # 1. Check for exact app name match (e.g. 'chrome.exe' or 'chrome')
        for win in all_windows:
            app_lower = win["app_name"].lower()
            if target_lower == app_lower or target_lower + ".exe" == app_lower:
                matches.append(win)
                
        if matches:
            return matches
            
        # 2. Check for partial title match
        for win in all_windows:
            if target_lower in win["title"].lower():
                matches.append(win)
                
        return matches

    @staticmethod
    def set_window_state(hwnd: int, action: str) -> bool:
        """Minimizes, maximizes, or restores a window."""
        win32gui, _, win32con, _ = WindowManager._import_win32()
        if not win32gui.IsWindow(hwnd):
            return False
            
        cmd = win32con.SW_RESTORE
        if action == "minimize":
            cmd = win32con.SW_MINIMIZE
        elif action == "maximize":
            cmd = win32con.SW_MAXIMIZE
        elif action == "restore":
            cmd = win32con.SW_RESTORE
            
        win32gui.ShowWindow(hwnd, cmd)
        return True

    @staticmethod
    def focus_window(hwnd: int) -> str:
        """Focuses a window. Returns success or partial_success if Windows blocked foreground."""
        win32gui, _, win32con, _ = WindowManager._import_win32()
        if not win32gui.IsWindow(hwnd):
            return "failed"
            
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            
        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception as e:
            logger.warning(f"WindowManager.focus_window SetForegroundWindow failed: {e}")
            
        time.sleep(0.1) # Brief pause to let Windows process
        
        active_hwnd = win32gui.GetForegroundWindow()
        if active_hwnd == hwnd:
            return "success"
        else:
            return "partial_success"


class MinimizeWindowTool(BaseTool):
    name = "minimize_window"
    description = "Minimizes a specified window or the current window."
    
    def get_schema(self) -> Dict[str, Any]:
        schema = super().get_schema()
        schema["parameters"] = {
            "window_name": {
                "type": "string",
                "description": "Name of the window to minimize (or 'current window')"
            }
        }
        return schema
        
    def execute(self, **kwargs) -> Dict[str, Any]:
        target = kwargs.get("window_name", "current window")
        if target in ["current window", "active window", ""]:
            win_info = WindowManager.get_current_window()
            if win_info["hwnd"] == 0:
                return {"status": "failed", "message": "No active window found."}
            
            if win_info["state"] == "Minimized":
                return {"status": "success", "message": f"{win_info['title']} is already minimized.", "window": win_info}
                
            WindowManager.set_window_state(win_info["hwnd"], "minimize")
            logger.info(f"Minimizing window: {win_info['title']}")
            win_info["state"] = "Minimized"
            return {"status": "success", "message": f"Minimized window: {win_info['title']}", "window": win_info}
            
        matches = WindowManager.find_windows(target)
        if not matches:
            return {"status": "failed", "message": f"Window not found: {target}"}
            
        if len(matches) > 1:
            titles = []
            for m in matches:
                if m["title"] not in titles:
                    titles.append(m["title"])
            if len(titles) > 1:
                return {
                    "status": "ambiguous",
                    "matches": titles,
                    "target_key": "window_name"
                }
            
        target_win = matches[0]
        if target_win["state"] == "Minimized":
            return {"status": "success", "message": f"{target_win['title']} is already minimized.", "window": target_win}
            
        WindowManager.set_window_state(target_win["hwnd"], "minimize")
        logger.info(f"Minimizing window: {target_win['title']}")
        target_win["state"] = "Minimized"
        return {"status": "success", "message": f"Minimized window: {target_win['title']}", "window": target_win}


class MaximizeWindowTool(BaseTool):
    name = "maximize_window"
    description = "Maximizes a specified window or the current window."
    
    def get_schema(self) -> Dict[str, Any]:
        schema = super().get_schema()
        schema["parameters"] = {
            "window_name": {
                "type": "string",
                "description": "Name of the window to maximize (or 'current window')"
            }
        }
        return schema
        
    def execute(self, **kwargs) -> Dict[str, Any]:
        target = kwargs.get("window_name", "current window")
        if target in ["current window", "active window", ""]:
            win_info = WindowManager.get_current_window()
            if win_info["hwnd"] == 0:
                return {"status": "failed", "message": "No active window found."}
            
            if win_info["state"] == "Maximized":
                return {"status": "success", "message": f"{win_info['title']} is already maximized.", "window": win_info}
                
            WindowManager.set_window_state(win_info["hwnd"], "maximize")
            logger.info(f"Maximizing window: {win_info['title']}")
            win_info["state"] = "Maximized"
            return {"status": "success", "message": f"Maximizing window: {win_info['title']}", "window": win_info}
            
        matches = WindowManager.find_windows(target)
        if not matches:
            return {"status": "failed", "message": f"Window not found: {target}"}
            
        if len(matches) > 1:
            titles = []
            for m in matches:
                if m["title"] not in titles:
                    titles.append(m["title"])
            if len(titles) > 1:
                return {
                    "status": "ambiguous",
                    "matches": titles,
                    "target_key": "window_name"
                }
            
        target_win = matches[0]
        if target_win["state"] == "Maximized":
            return {"status": "success", "message": f"{target_win['title']} is already maximized.", "window": target_win}
            
        WindowManager.set_window_state(target_win["hwnd"], "maximize")
        logger.info(f"Maximizing window: {target_win['title']}")
        target_win["state"] = "Maximized"
        return {"status": "success", "message": f"Maximizing window: {target_win['title']}", "window": target_win}


class RestoreWindowTool(BaseTool):
    name = "restore_window"
    description = "Restores a specified window or the current window to normal size."
    
    def get_schema(self) -> Dict[str, Any]:
        schema = super().get_schema()
        schema["parameters"] = {
            "window_name": {
                "type": "string",
                "description": "Name of the window to restore (or 'current window')"
            }
        }
        return schema
        
    def execute(self, **kwargs) -> Dict[str, Any]:
        target = kwargs.get("window_name", "current window")
        if target in ["current window", "active window", ""]:
            win_info = WindowManager.get_current_window()
            if win_info["hwnd"] == 0:
                return {"status": "failed", "message": "No active window found."}
                
            WindowManager.set_window_state(win_info["hwnd"], "restore")
            logger.info(f"Restoring window: {win_info['title']}")
            win_info["state"] = "Normal"
            return {"status": "success", "message": f"Restored window: {win_info['title']}", "window": win_info}
            
        matches = WindowManager.find_windows(target)
        if not matches:
            return {"status": "failed", "message": f"Window not found: {target}"}
            
        if len(matches) > 1:
            titles = []
            for m in matches:
                if m["title"] not in titles:
                    titles.append(m["title"])
            if len(titles) > 1:
                return {
                    "status": "ambiguous",
                    "matches": titles,
                    "target_key": "window_name"
                }
            
        target_win = matches[0]
        WindowManager.set_window_state(target_win["hwnd"], "restore")
        logger.info(f"Restoring window: {target_win['title']}")
        target_win["state"] = "Normal"
        return {"status": "success", "message": f"Restored window: {target_win['title']}", "window": target_win}


class FocusWindowTool(BaseTool):
    name = "focus_window"
    description = "Brings a specific window to the foreground."
    
    def get_schema(self) -> Dict[str, Any]:
        schema = super().get_schema()
        schema["parameters"] = {
            "window_name": {
                "type": "string",
                "description": "Name of the window to focus"
            }
        }
        return schema
        
    def execute(self, **kwargs) -> Dict[str, Any]:
        target = kwargs.get("window_name", "")
        if not target:
            return {"status": "failed", "message": "Missing 'window_name' parameter."}
            
        matches = WindowManager.find_windows(target)
        if not matches:
            return {"status": "failed", "message": f"Window not found: {target}"}
            
        if len(matches) > 1:
            titles = []
            for m in matches:
                if m["title"] not in titles:
                    titles.append(m["title"])
            if len(titles) > 1:
                return {
                    "status": "ambiguous",
                    "matches": titles,
                    "target_key": "window_name"
                }
            
        target_win = matches[0]
        logger.info(f"Focusing window: {target_win['title']}")
        focus_status = WindowManager.focus_window(target_win["hwnd"])
        
        if focus_status == "success":
            return {"status": "success", "message": f"Focused window: {target_win['title']}", "window": target_win}
        else:
            return {"status": "success", "message": f"Found window '{target_win['title']}', but Windows prevented focus from being stolen.", "window": target_win}


class GetCurrentWindowTool(BaseTool):
    name = "get_current_window"
    description = "Retrieves information about the current active window."
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        win_info = WindowManager.get_current_window()
        if win_info["hwnd"] == 0:
            return {"status": "failed", "message": "No active window found."}
            
        logger.info("Retrieved current active window")
        
        msg = (
            f"Current Active Window:\n"
            f"Title: {win_info['title']}\n"
            f"App: {win_info['app_name']}\n"
            f"State: {win_info['state']}\n"
            f"PID: {win_info['pid']}"
        )
        return {"status": "success", "message": msg, "window": win_info}


class ListOpenWindowsTool(BaseTool):
    name = "list_open_windows"
    description = "Lists all currently visible top-level windows."
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        windows = WindowManager.list_open_windows()
        if not windows:
            return {"status": "success", "message": "No visible windows found.", "count": 0}
            
        lines = []
        for i, win in enumerate(windows):
            lines.append(f"{i+1}. {win['title']} ({win['app_name']}) - {win['state']}")
            
        msg = f"Found {len(windows)} open windows:\n\n" + "\n".join(lines)
        return {"status": "success", "message": msg, "count": len(windows), "windows": windows}


class IsWindowOpenTool(BaseTool):
    name = "is_window_open"
    description = "Checks if a specific window or application is currently open."
    
    def get_schema(self) -> Dict[str, Any]:
        schema = super().get_schema()
        schema["parameters"] = {
            "window_name": {
                "type": "string",
                "description": "Name of the window or app to check"
            }
        }
        return schema
        
    def execute(self, **kwargs) -> Dict[str, Any]:
        target = kwargs.get("window_name", "")
        if not target:
            return {"status": "failed", "message": "Missing 'window_name' parameter."}
            
        matches = WindowManager.find_windows(target)
        if not matches:
            return {"status": "success", "message": f"No, '{target}' is not open.", "is_open": False}
            
        return {"status": "success", "message": f"Yes, '{target}' is open.", "is_open": True, "matches": matches}
