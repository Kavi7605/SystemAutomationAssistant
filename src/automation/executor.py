import logging
from typing import Dict, Any, Union, List

from src.tools.registry import ToolRegistry

logger = logging.getLogger("system_assistant")

class Executor:
    """
    Executes automation actions based on parsed JSON commands dynamically 
    using the ToolRegistry.
    """
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def execute(self, command_json: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Routes the parsed JSON command(s) to the appropriate Tool in the registry.
        """
        if isinstance(command_json, list):
            return self._execute_queue(command_json)
        return self._execute_single(command_json)

    def _execute_single(self, command_json: Dict[str, Any]) -> Dict[str, Any]:
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

    def _get_action_description(self, cmd: Dict[str, Any]) -> str:
        action = cmd.get("action", "unknown")
        params = cmd.get("parameters", {})
        
        if action == "open_application":
            app_name = params.get("application_name", "Application")
            return f"Opening {app_name.title()}"
        elif action == "close_application":
            app_name = params.get("application_name", "Application")
            return f"Closing {app_name.title()}"
        elif action == "search_web":
            return f"Searching web for '{params.get('query', '')}'"
        else:
            return f"Executing {action.replace('_', ' ').title()}"

    def _execute_queue(self, commands: List[Dict[str, Any]]) -> Dict[str, Any]:
        total_steps = len(commands)
        successful = 0
        failed = 0
        results = []

        print("")
        for i, cmd in enumerate(commands, 1):
            desc = self._get_action_description(cmd)
            print(f"[{i}/{total_steps}] {desc}")
            logger.info(f"Queue step {i}/{total_steps}: {desc}")
            
            result = self._execute_single(cmd)
            
            if result.get("status") in ["success", "completed"]:
                print("✓ Success\n")
                logger.info(f"Queue step {i} success.")
                successful += 1
            else:
                error_msg = result.get('message', 'Unknown error')
                print(f"✗ Failed: {error_msg}\n")
                logger.error(f"Queue step {i} failed: {error_msg}")
                failed += 1
                
            results.append({
                "step": i,
                "action": cmd.get("action", "unknown"),
                "result": result
            })

        return {
            "status": "completed",
            "total_steps": total_steps,
            "successful": successful,
            "failed": failed,
            "results": results
        }
