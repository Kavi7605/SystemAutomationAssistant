import json
from typing import Dict, Any, Tuple

class ResponseFormatter:
    """
    Formats raw execution results from the backend into rich, readable
    text for the chat bubble, and a concise summary for the Recent Actions sidebar.
    """
    
    @staticmethod
    def format_result(action: str, result: Dict[str, Any]) -> Tuple[str, str]:
        """
        Returns (rich_text, summary_text)
        """
        status = result.get("status", "unknown")
        raw_msg = result.get("message", "Executed.")
        
        if status not in ["success", "completed", "partial_success"]:
            rich_error = f"### ❌ Failed\n\n**Reason:**\n{raw_msg}"
            summary = f"Failed: {action.replace('_', ' ').title()}"
            return rich_error, summary
            
        rich_text = f"### ✓ {raw_msg}\n\n"
        summary = raw_msg
        
        if action == "debug_context":
            try:
                if "{" in raw_msg:
                    json_str = raw_msg[raw_msg.find("{"):]
                    data = json.loads(json_str)
                    
                    rich_text = "### Context Snapshot\n\n"
                    rich_text += f"**Last Command:** {data.get('last_command', 'None')}\n\n"
                    rich_text += f"**Current Active App:** {data.get('current_active_app', 'None')}\n\n"
                    
                    opened_apps = data.get('opened_apps_history', [])
                    if opened_apps:
                        rich_text += "**Opened Applications**\n"
                        for app in opened_apps:
                            rich_text += f"- {app.title()}\n"
                        rich_text += "\n"
                        
                    sys_state = data.get('system_state', {})
                    if sys_state:
                        rich_text += "**System Information**\n"
                        rich_text += f"- **Volume:** {sys_state.get('volume_level', 'Unknown')}%\n"
                        rich_text += f"- **Power Plan:** {sys_state.get('power_plan', 'Unknown')}\n"
                        rich_text += f"- **Open Windows:** {sys_state.get('open_windows_count', 'Unknown')}\n"
                        
                    summary = "Displayed context snapshot"
            except Exception:
                pass
                
        elif action == "list_open_windows":
            lines = raw_msg.split('\n')
            rich_text = "### Open Windows\n\n"
            for line in lines:
                if line.strip() and not line.startswith("Found"):
                    rich_text += f"- {line.strip()}\n"
            summary = "Listed open windows"
            
        elif action in ["open_application", "close_application"]:
            summary = raw_msg
            app_name = result.get("item_name", "Application")
            rich_text = f"### {raw_msg}\n\n**Application:** {app_name.title()}\n**Status:** {'Running' if action == 'open_application' else 'Closed'}"
            
        elif action in ["create_folder", "create_file", "delete_item"]:
            summary = raw_msg
            path = result.get("path", result.get("item_name", "Unknown"))
            rich_text = f"### {raw_msg}\n\n**Location:**\n`{path}`\n\n**Status:** Completed"
            
        elif action in ["move_file", "copy_file"]:
            summary = raw_msg
            src = result.get("source_name", "Unknown")
            dest = result.get("target_path", result.get("target_name", "Unknown"))
            rich_text = f"### {raw_msg}\n\n**Source:**\n`{src}`\n\n**Destination:**\n`{dest}`\n\n**Status:** Completed"
            
        elif action == "execute_queue":
            results = result.get("results", [])
            rich_text = f"### Execution Summary\n\n**Successful:** {result.get('successful', 0)}\n**Failed:** {result.get('failed', 0)}\n\n"
            for r in results:
                step_status = "✓" if r.get('result', {}).get('status') in ['success', 'completed'] else "❌"
                rich_text += f"- {step_status} Step {r.get('step')}: {r.get('action').replace('_', ' ').title()}\n"
            summary = "Executed task queue"
            
        if rich_text == f"### ✓ {raw_msg}\n\n":
            rich_text = f"### ✓ {raw_msg}"
            summary = raw_msg[:40] + "..." if len(raw_msg) > 40 else raw_msg
            
        return rich_text.strip(), summary.strip()
