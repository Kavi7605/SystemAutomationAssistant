import logging
from typing import Dict, Any
from src.utils.browser_utils import get_default_browser

logger = logging.getLogger(__name__)

class CommandResolver:
    """
    Planner Layer component responsible for resolving vague entities and enhancing 
    commands before execution.
    
    Future Extensibility:
    - Context memory integration
    - Multi-step planning (splitting one command into many)
    - Clarification requests (returning status to ask user for missing info)
    """
    def __init__(self):
        # Allow future addition of Context memory here
        self.context_memory = None
        
        self.browser_aliases = [
            "browser", "default browser", "my browser", "internet", "web browser"
        ]
        
        # Mapping of vague names to specific application names
        self.alias_map = {
            "editor": "notepad",
            "terminal": "cmd",
            "music": "spotify"
        }

    def resolve(self, command_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes a parsed JSON command from the LLM, resolves vague entities,
        and returns an enhanced/resolved JSON command for the Executor.
        """
        if not command_json or not isinstance(command_json, dict):
            return command_json

        # Create a copy to avoid mutating the original
        resolved_command = command_json.copy()
        
        action = resolved_command.get("action")
        parameters = resolved_command.get("parameters", {})

        # Handle 'search_web' clarification and intent correction
        if action == "search_web":
            query = parameters.get("query", "").strip()
            
            # Correction: "I want to search the web" -> open default browser
            if query.lower() in ["", "search", "the web", "internet"]:
                if query.lower() in ["the web", "internet"]:
                    resolved_command["action"] = "open_application"
                    resolved_command["parameters"] = {"application_name": "browser"}
                    # Re-route to standard open_application logic
                    action = "open_application"
                    parameters = resolved_command["parameters"]
                else:
                    # Missing query -> Clarification Request
                    return {
                        "action": "clarify",
                        "parameters": {
                            "message": "What would you like me to search for?"
                        }
                    }

        if action in ["open_application", "close_application"]:
            self._resolve_application_name(parameters)
            
        resolved_command["parameters"] = parameters
        return resolved_command

    def _resolve_application_name(self, parameters: Dict[str, Any]):
        """
        Resolves generic application names to specific executable names based on aliases.
        """
        app_name = parameters.get("application_name")
        if app_name:
            app_name_lower = app_name.lower().strip()
            
            # Browser Intelligence
            if app_name_lower in self.browser_aliases:
                default_browser = get_default_browser()
                if default_browser:
                    logger.info(f"Planner resolved '{app_name}' to system default browser: {default_browser}")
                    parameters["application_name"] = default_browser
                else:
                    logger.warning("Default browser detection failed, falling back to msedge.exe")
                    parameters["application_name"] = "msedge.exe"
                return
                
            if app_name_lower in self.alias_map:
                resolved_name = self.alias_map[app_name_lower]
                logger.info(f"Planner resolved vague application '{app_name}' -> '{resolved_name}'")
                parameters["application_name"] = resolved_name
