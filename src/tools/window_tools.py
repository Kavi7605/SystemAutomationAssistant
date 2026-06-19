from typing import Dict, Any
from src.tools.base import BaseTool
from src.context.window_manager import WindowManager

class GetActiveWindowTool(BaseTool):
    name = "get_active_window"
    description = "Returns information about the currently active foreground window."

    def __init__(self, window_manager: WindowManager = None):
        self.wm = window_manager or WindowManager()

    def execute(self, **kwargs) -> Dict[str, Any]:
        result = self.wm.get_active_window()
        if result:
            return {"status": "success", "window": result, "message": f"Active window is {result.get('title')}"}
        return {"status": "failed", "message": "Could not determine active window"}

class IsWindowOpenTool(BaseTool):
    name = "is_window_open"
    description = "Checks if a specific window is open by name."

    def __init__(self, window_manager: WindowManager = None):
        self.wm = window_manager or WindowManager()

    def execute(self, window_name: str = "", **kwargs) -> Dict[str, Any]:
        if not window_name:
            return {"status": "failed", "message": "window_name parameter is required"}
            
        is_open = self.wm.is_window_open(window_name)
        return {
            "status": "success", 
            "is_open": is_open, 
            "message": f"Window '{window_name}' is {'open' if is_open else 'not open'}."
        }

    def get_schema(self) -> Dict[str, Any]:
        schema = super().get_schema()
        schema["parameters"] = {
            "window_name": "The name or partial title of the window to check"
        }
        return schema

class FocusWindowTool(BaseTool):
    name = "focus_window"
    description = "Brings the specified window to the foreground."

    def __init__(self, window_manager: WindowManager = None):
        self.wm = window_manager or WindowManager()

    def execute(self, window_name: str = "", **kwargs) -> Dict[str, Any]:
        if not window_name:
            return {"status": "failed", "message": "window_name parameter is required"}
            
        return self.wm.focus_window(window_name)

    def get_schema(self) -> Dict[str, Any]:
        schema = super().get_schema()
        schema["parameters"] = {
            "window_name": "The name or partial title of the window to focus"
        }
        return schema
