import logging
from typing import Dict, Any, Union, List

from src.tools.registry import ToolRegistry

# Type hinting
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.context.application_state_manager import ApplicationStateManager
    from src.context.context_manager import ContextManager

logger = logging.getLogger("system_assistant")

class Executor:
    """
    Executes automation actions based on parsed JSON commands dynamically 
    using the ToolRegistry.
    """
    def __init__(self, registry: ToolRegistry, state_manager: 'ApplicationStateManager' = None, context_manager: 'ContextManager' = None, reference_resolver: 'ReferenceResolver' = None):
        self.registry = registry
        self.state_manager = state_manager
        self.context_manager = context_manager
        self.reference_resolver = reference_resolver

    def _sync_active_apps(self) -> None:
        if self.state_manager and self.context_manager:
            self.context_manager.sync_active_apps(
                self.state_manager.get_current_active_app(),
                self.state_manager.get_last_active_app()
            )

    def execute(self, command_json: Union[Dict[str, Any], List[Dict[str, Any]]], stop_on_failure: bool = True) -> Dict[str, Any]:
        """
        Routes the parsed JSON command(s) to the appropriate Tool in the registry.
        """
        if isinstance(command_json, list):
            return self._execute_queue(command_json, stop_on_failure)
            
        # Resolve references for single commands before execution
        if self.reference_resolver:
            for key, value in command_json.get("parameters", {}).items():
                if isinstance(value, str):
                    try:
                        command_json["parameters"][key] = self.reference_resolver.resolve_command(value)
                    except ValueError as e:
                        return {"status": "failed", "message": str(e)}
                        
        return self._execute_single(command_json)

    def _execute_single(self, command_json: Dict[str, Any]) -> Dict[str, Any]:
        action = command_json.get("action")
        parameters = command_json.get("parameters", {})

        if not action or action == "unknown":
            return {"status": "failed", "message": "Unknown or unsupported action."}
            
        if action == "unsupported":
            msg = parameters.get("message", "This action is not supported.")
            return {"status": "failed", "message": msg}

        try:
            if action == "clarify":
                # The Planner has requested clarification from the user
                message = parameters.get("message", "Could you please clarify your request?")
                return {"status": "success", "message": f"Clarification needed: {message}"}
                
            if action == "debug_context":
                if self.context_manager:
                    import json
                    snapshot = self.context_manager.get_context_snapshot()
                    def _serialize(obj):
                        if hasattr(obj, 'isoformat'): return obj.isoformat()
                        return str(obj)
                    formatted = json.dumps(snapshot, indent=2, default=_serialize)
                    print(f"\n[DEBUG] Context Snapshot:\n{formatted}\n")
                    return {"status": "success", "message": f"Context Snapshot:\n{formatted}"}
                else:
                    return {"status": "failed", "message": "ContextManager not initialized."}
                    
            if action == "debug_state":
                if self.state_manager:
                    import json
                    self.state_manager.refresh_all()
                    self._sync_active_apps()
                    snapshot = self.state_manager.states
                    def _serialize(obj):
                        if hasattr(obj, 'isoformat'): return obj.isoformat()
                        return str(obj)
                    formatted = json.dumps(snapshot, indent=2, default=_serialize)
                    return {"status": "success", "message": f"State Snapshot:\n{formatted}"}
                else:
                    return {"status": "failed", "message": "ApplicationStateManager not initialized."}
                    
            if action == "get_current_app":
                if self.state_manager:
                    self.state_manager.refresh_active_window()
                    self._sync_active_apps()
                    current = self.state_manager.get_current_active_app()
                    if current:
                        return {"status": "success", "message": f"Current app: {current}"}
                    return {"status": "success", "message": "No active application tracked."}
                return {"status": "failed", "message": "ApplicationStateManager not initialized."}
                
            if action == "get_previous_app":
                if self.state_manager:
                    self.state_manager.refresh_active_window()
                    self._sync_active_apps()
                    prev = self.state_manager.get_last_active_app()
                    if prev:
                        return {"status": "success", "message": f"Previous app: {prev}"}
                    return {"status": "success", "message": "No previous application available."}
                return {"status": "failed", "message": "ApplicationStateManager not initialized."}
                
            if action == "get_opened_history":
                if self.context_manager:
                    history = self.context_manager.get_open_history()
                    if history:
                        msg = "Opened Apps History:\n" + "\n".join(f"{i+1}. {app}" for i, app in enumerate(history))
                        return {"status": "success", "message": msg}
                    return {"status": "success", "message": "Opened Apps History:\nNo apps have been opened yet."}
                return {"status": "failed", "message": "ContextManager not initialized."}
                
            if action == "get_focused_history":
                if self.context_manager:
                    history = self.context_manager.get_focus_history()
                    if history:
                        msg = "Focused Apps History:\n" + "\n".join(f"{i+1}. {app}" for i, app in enumerate(history))
                        return {"status": "success", "message": msg}
                    return {"status": "success", "message": "Focused Apps History:\nNo apps have been focused yet."}
                return {"status": "failed", "message": "ContextManager not initialized."}
                
            if action == "get_closed_history":
                if self.context_manager:
                    history = self.context_manager.get_close_history()
                    if history:
                        msg = "Closed Apps History:\n" + "\n".join(f"{i+1}. {app}" for i, app in enumerate(history))
                        return {"status": "success", "message": msg}
                    return {"status": "success", "message": "Closed Apps History:\nNo apps have been closed yet."}
                return {"status": "failed", "message": "ContextManager not initialized."}
                    
            # State-Aware Validation Intercepts
            if action == "open_application":
                app_name = parameters.get("application_name")
                if self.state_manager and app_name:
                    self.state_manager.refresh_app_state(app_name)
                    if self.state_manager.is_running(app_name):
                        logger.info(f"{app_name.title()} is already running. Skipping execution.")
                        return {"status": "success", "message": f"{app_name.title()} is already running."}
                        
            elif action == "close_application":
                app_name = parameters.get("application_name")
                if self.state_manager and app_name:
                    self.state_manager.refresh_app_state(app_name)
                    if not self.state_manager.is_running(app_name):
                        logger.info(f"{app_name.title()} is already closed. Skipping execution.")
                        return {"status": "success", "message": f"{app_name.title()} is already closed."}
                        
            elif action == "focus_window":
                window_name = parameters.get("window_name")
                if self.state_manager and window_name:
                    self.state_manager.refresh_app_state(window_name)
                    self._sync_active_apps()
                    if self.state_manager.is_focused(window_name):
                        logger.info(f"{window_name.title()} is already focused. Skipping execution.")
                        return {"status": "success", "message": f"{window_name.title()} is already focused."}
                
            # Execute dynamically via Tool Registry
            result = self.registry.execute_tool(action, **parameters)
            
            # Fallback logic for open_application
            if action == "open_application" and result.get("status") == "application_not_found":
                fallback_url = parameters.get("fallback_url")
                if fallback_url:
                    logger.info(f"Application not found. Executing fallback URL: {fallback_url}")
                    result = self.registry.execute_tool("open_url", url=fallback_url)
                    # Modify message to indicate fallback
                    if result.get("status") == "success":
                        result["message"] = f"Application not found. Opened fallback website: {fallback_url}"
                        # If we fallback, the action effectively becomes open_url
                        action = "open_url"
                        parameters = {"url": fallback_url}

            if result.get("status") == "success":
                # Handle fallback scenarios where open_application turns into open_url
                if action == "open_application" and "fallback" in result.get("message", "").lower():
                    action = "open_url"
                    
            if result.get("status") in ["success", "partial_success"]:
                if self.context_manager:
                    self.context_manager.mark_action_success(action)
                
                if action == "open_application":
                    app_name = parameters.get("application_name")
                    if self.state_manager:
                        self.state_manager.refresh_app_state(app_name)
                    if self.context_manager and app_name:
                        self.context_manager.mark_app_opened(app_name)
                elif action == "close_application":
                    app_name = parameters.get("application_name")
                    if self.state_manager:
                        self.state_manager.refresh_app_state(app_name)
                    if self.context_manager and app_name:
                        self.context_manager.mark_app_closed(app_name)
                elif action == "focus_window":
                    window_name = parameters.get("window_name")
                    if self.state_manager and window_name:
                        self.state_manager.mark_focused(window_name)
                        self._sync_active_apps()
                    if self.context_manager and window_name:
                        self.context_manager.mark_app_focused(window_name)
                
                elif action == "get_active_window":
                    if self.state_manager:
                        self.state_manager.refresh_active_window()
                        self._sync_active_apps()
                    title = result.get("window", {}).get("title")
                    if self.context_manager and title:
                        self.context_manager.update_active_window(title)
            
            if result.get("status") not in ["success", "completed", "partial_success"]:
                if self.context_manager:
                    self.context_manager.mark_action_failed(action)
            
            return result
        except Exception as e:
            if self.context_manager:
                self.context_manager.mark_action_failed(action)
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
        elif action == "get_active_window":
            return "Getting active window"
        elif action == "is_window_open":
            return f"Checking if {params.get('window_name', 'window')} is open"
        elif action == "focus_window":
            return f"Focusing {params.get('window_name', 'window').title()}"
        elif action == "wait":
            wait_type = params.get("wait_type", "seconds")
            if wait_type == "seconds":
                return f"Waiting {params.get('seconds', 0)} seconds..."
            elif wait_type == "window":
                window_name = params.get("window_name", "window").title()
                timeout = params.get("timeout", 30)
                return f"Waiting for {window_name} window (timeout {timeout}s)..."
            elif wait_type == "window_closed":
                window_name = params.get("window_name", "window").title()
                timeout = params.get("timeout", 30)
                return f"Waiting for {window_name} window to close (timeout {timeout}s)..."
            elif wait_type == "app":
                app_name = params.get("app_name", "app").title()
                timeout = params.get("timeout", 30)
                return f"Waiting for {app_name} application (timeout {timeout}s)..."
            elif wait_type == "app_closed":
                app_name = params.get("app_name", "app").title()
                timeout = params.get("timeout", 30)
                return f"Waiting for {app_name} application to close (timeout {timeout}s)..."
        else:
            return f"Executing {action.replace('_', ' ').title()}"

    def _execute_queue(self, commands: List[Dict[str, Any]], stop_on_failure: bool = True) -> Dict[str, Any]:
        total_steps = len(commands)
        successful = 0
        failed = 0
        results = []

        print("")
        for i, cmd in enumerate(commands, 1):
            if self.reference_resolver:
                try:
                    for key, value in cmd.get("parameters", {}).items():
                        if isinstance(value, str):
                            cmd["parameters"][key] = self.reference_resolver.resolve_command(value)
                except ValueError as e:
                    error_msg = str(e)
                    print(f"[{i}/{total_steps}] Failed: {error_msg}\n")
                    logger.error(f"Queue step {i} failed: {error_msg}")
                    failed += 1
                    results.append({"step": i, "action": cmd.get("action", "unknown"), "result": {"status": "failed", "message": error_msg}})
                    if stop_on_failure: 
                        print(f"Queue aborted due to failure at step {i}.")
                        logger.warning(f"Queue aborted at step {i} due to failure.")
                        break
                    continue
                    
            action = cmd.get("action", "unknown")
            desc = self._get_action_description(cmd)
            
            if action not in ["get_active_window", "is_window_open"]:
                print(f"[{i}/{total_steps}] {desc}")
                
            logger.info(f"Queue step {i}/{total_steps}: {desc}")
            
            result = self._execute_single(cmd)
            
            if result.get("status") in ["success", "completed", "partial_success"]:
                msg = result.get("message", "Success")
                if action in ["get_active_window", "is_window_open"]:
                    print(f"[{i}/{total_steps}] {msg}\n")
                else:
                    print(f"[OK] {msg}\n")
                logger.info(f"Queue step {i} success: {msg}")
                successful += 1
            else:
                error_msg = result.get('message', 'Unknown error')
                print(f"[FAIL] {error_msg}\n")
                logger.error(f"Queue step {i} failed: {error_msg}")
                failed += 1
                
            results.append({
                "step": i,
                "action": cmd.get("action", "unknown"),
                "result": result
            })
            
            if result.get("status") not in ["success", "completed", "partial_success"] and stop_on_failure:
                print(f"Queue aborted due to failure at step {i}.")
                logger.warning(f"Queue aborted at step {i} due to failure.")
                break

        return {
            "status": "completed" if failed == 0 else ("failed" if stop_on_failure else "partial_success"),
            "total_steps": total_steps,
            "successful": successful,
            "failed": failed,
            "results": results,
            "aborted": failed > 0 and stop_on_failure
        }
