import copy
from typing import Dict, List, Any
from src.context.reference_resolver import ReferenceResolver

class CommandExpander:
    """
    Responsible for accepting parsed JSON commands, detecting parameters 
    that contain plural references, and expanding one logical command 
    into multiple deterministic commands while preserving execution order.
    """
    def __init__(self, reference_resolver: ReferenceResolver):
        self.reference_resolver = reference_resolver

    def expand(self, parsed_commands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        expanded_commands = []
        
        ctx_manager = getattr(self.reference_resolver, 'context_manager', None)
        original_state = None
        if ctx_manager:
            original_state = copy.deepcopy(ctx_manager.__dict__)
            
        def simulate_context_update(action: str, target: str):
            if not ctx_manager or not target:
                return
            if action == "open_application":
                ctx_manager.mark_app_opened(target)
                ctx_manager.sync_active_apps(current_app=target, last_app=None)
            elif action == "close_application":
                ctx_manager.mark_app_closed(target)
                if ctx_manager.state.get('current_active_app') == target:
                    ctx_manager.sync_active_apps(current_app=None, last_app=target)
            elif action in ["focus_window", "minimize_window", "maximize_window", "restore_window"]:
                current = ctx_manager.state.get('current_active_app')
                ctx_manager.mark_app_focused(target)
                ctx_manager.sync_active_apps(current_app=target, last_app=current)
            elif action == "create_file":
                ctx_manager.update_filesystem_state("last_created_file", target)
            elif action == "create_folder":
                ctx_manager.update_filesystem_state("last_created_folder", target)
            elif action == "rename_item":
                ctx_manager.update_filesystem_state("last_renamed_file", target)
            elif action in ["move_file", "copy_file"]:
                ctx_manager.update_filesystem_state("last_found_file", target)
                
        try:
            for cmd in parsed_commands:
                if not isinstance(cmd, dict) or "parameters" not in cmd:
                    expanded_commands.append(cmd)
                    continue
                    
                has_list = False
                list_key = None
                list_values = []
                
                cmd_copy = copy.deepcopy(cmd)
                error_occurred = False
                
                for key, value in cmd_copy.get("parameters", {}).items():
                    if isinstance(value, str):
                        try:
                            resolved = self.reference_resolver.resolve(value)
                            if isinstance(resolved, list) and len(resolved) > 1:
                                has_list = True
                                list_key = key
                                list_values = resolved
                            elif isinstance(resolved, list) and len(resolved) == 1:
                                cmd_copy["parameters"][key] = resolved[0]
                        except ValueError as e:
                            expanded_commands.append({
                                "action": "unsupported",
                                "parameters": {"message": str(e)}
                            })
                            error_occurred = True
                            break
                            
                if error_occurred:
                    continue
                    
                if has_list:
                    for val in list_values:
                        new_cmd = {
                            "action": cmd_copy["action"],
                            "parameters": cmd_copy["parameters"].copy()
                        }
                        new_cmd["parameters"][list_key] = val
                        expanded_commands.append(new_cmd)
                        simulate_context_update(new_cmd["action"], val)
                else:
                    expanded_commands.append(cmd_copy)
                    
                    # Extract the primary target of the action
                    target = None
                    params = cmd_copy.get("parameters", {})
                    if "application_name" in params: target = params["application_name"]
                    elif "window_name" in params: target = params["window_name"]
                    elif "file_name" in params: target = params["file_name"]
                    elif "folder_name" in params: target = params["folder_name"]
                    elif "target_name" in params: target = params["target_name"]
                    elif "target_path" in params: target = params["target_path"]
                    
                    simulate_context_update(cmd_copy.get("action"), target)
                    
        finally:
            if ctx_manager and original_state is not None:
                ctx_manager.__dict__.update(original_state)
                
        return expanded_commands
