import os
import subprocess
import datetime
import socket
import webbrowser
import logging
import pyautogui
import traceback

from src.tools.registry import ToolRegistry

logger = logging.getLogger("system_assistant")

class Executor:
    """
    Executes automation actions based on parsed JSON commands dynamically 
    using the ToolRegistry.
    """
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def execute(self, command_json: dict) -> dict:
        """
        Routes the parsed JSON command to the appropriate Tool in the registry.
        """
        action = command_json.get("action")
        parameters = command_json.get("parameters", {})

        if not action or action == "unknown":
            return {"status": "failed", "message": "Unknown or unsupported action."}

        try:
            if action == "clarify":
                # The Planner has requested clarification from the user
                message = parameters.get("message", "Could you please clarify your request?")
                return {"status": "success", "message": f"Clarification needed: {message}"}
                
            # Execute dynamically via Tool Registry
            result = self.registry.execute_tool(action, **parameters)
            return result
        except Exception as e:
            logger.error(f"Error executing {action}: {e}", exc_info=True)
            return {"status": "failed", "message": str(e)}
