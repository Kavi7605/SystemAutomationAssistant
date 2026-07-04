import json
from typing import Dict, Any, Tuple
import os

class ResponseFormatter:
    """
    Formats raw execution results from the backend into rich, readable
    markdown text for the chat bubble, and a concise summary for the sidebar.
    """
    
    @staticmethod
    def format_result(action: str, result: Dict[str, Any]) -> Tuple[str, str]:
        status = result.get("status", "unknown").lower()
        raw_msg = result.get("message", "Executed.")
        title = result.get("title")
        
        # Priority 1: Never display Unknown
        if not title or title.lower() == "unknown":
            title = action.replace('_', ' ').title()
            if title.lower() == "unknown":
                title = "Operation Result"
            
        metadata = result.get("metadata", {})
        suggestions = result.get("suggestions", [])
        
        # Determine Icon and Summary based on Status
        if status in ["success", "completed", "partial_success"]:
            icon = "✓"
        elif status == "info":
            icon = "ℹ"
        else: # failed or error
            icon = "❌"
            
        # Extract a concise subtitle
        subtitle = "Just now"
        if metadata:
            # use the first metadata value if available
            first_key = list(metadata.keys())[0]
            val = metadata[first_key]
            # keep it short
            subtitle = str(val)[:50] + ("..." if len(str(val)) > 50 else "")
            
        summary = {
            "status": status,
            "title": title,
            "subtitle": subtitle
        }
            
        # Priority 3: Consistent Layout for everything
        # --- TITLE ---
        if status in ["success", "completed", "partial_success", "info"]:
            rich_text = f"### {icon} {title}\n\n"
        else:
            rich_text = f"### {icon} {title} Failed\n\n"

        # Special Action Overrides (e.g., list_open_windows, execute_queue)
        # Priority 4 & 5: Format specific output lists nicely
        if action == "list_open_windows":
            # Turn raw window string into a clean list
            lines = raw_msg.split('\n')
            clean_lines = []
            for line in lines:
                if line.strip() and not line.lower().startswith("found"):
                    clean_lines.append(f"1. {line.strip()}")
            if clean_lines:
                raw_msg = f"{len(clean_lines)} windows are currently open.\n\n" + "\n".join(clean_lines)
            else:
                raw_msg = "No open windows found."
                
        elif action == "execute_queue":
            results = result.get("results", [])
            successful = result.get('successful', 0)
            failed = result.get('failed', 0)
            raw_msg = f"**Completed:** {successful} | **Failed:** {failed}\n\n"
            for r in results:
                step_status = "✓" if r.get('result', {}).get('status') in ['success', 'completed'] else "❌"
                step_title = r.get('action', 'Unknown Action').replace('_', ' ').title()
                raw_msg += f"- {step_status} **Step {r.get('step')}**: {step_title}\n"
                
        elif action == "debug_context" or action == "debug_state":
            # Priority 4: Redesign Current Session
            state = result.get("state", {})
            rich_text = "### Current Session\n\n"
            
            # Application
            app_state = state.get('active_application', {})
            rich_text += "#### Application\n────────────────────\n\n"
            rich_text += f"**Active Window**\n{app_state.get('window_title', 'None')}\n\n"
            rich_text += f"**Last Opened**\n{state.get('recent_activity', {}).get('last_opened_app', 'None')}\n\n"
            rich_text += f"**Last Focused**\n{state.get('recent_activity', {}).get('last_focused_app', 'None')}\n\n"
            
            # Files
            fs_state = state.get('filesystem', {})
            rich_text += "#### Files\n────────────────────\n\n"
            rich_text += f"**Last Created File**\n{fs_state.get('last_created_file', 'None')}\n\n"
            rich_text += f"**Last Created Folder**\n{fs_state.get('last_created_folder', 'None')}\n\n"
            rich_text += f"**Last Found File**\n{fs_state.get('last_found_file', 'None')}\n\n"
            
            # System
            sys_state = state.get('system_state', {})
            rich_text += "#### System\n────────────────────\n\n"
            rich_text += f"**Volume**\n{sys_state.get('volume', 'Unknown')}%\n\n"
            rich_text += f"**Brightness**\n{sys_state.get('brightness', 'Unknown')}%\n\n"
            rich_text += f"**Wi-Fi**\n{sys_state.get('wifi_status', 'Unknown')}\n\n"
            
            summary = {
                "status": "success",
                "title": "Current session viewed",
                "subtitle": "Just now"
            }
            return rich_text.strip(), summary

        # --- MESSAGE ---
        if status not in ["success", "completed", "partial_success", "info"]:
            # It's an error, add "Reason" if no other message is provided
            rich_text += f"**Reason:**\n{raw_msg}\n\n"
        else:
            rich_text += f"{raw_msg}\n\n"
            
        # --- METADATA ---
        if metadata:
            for key, val in metadata.items():
                rich_text += f"**{key}**\n{val}\n\n"
                
        # --- SUGGESTIONS ---
        if suggestions:
            rich_text += "**Suggestions**\n\n"
            for sug in suggestions:
                rich_text += f"- {sug}\n"
                
        return rich_text.strip(), summary
