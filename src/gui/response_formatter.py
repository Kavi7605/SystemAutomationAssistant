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
        status = result.get("status", "unknown")
        raw_msg = result.get("message", "Executed.")
        title = result.get("title", action.replace('_', ' ').title())
        metadata = result.get("metadata", {})
        suggestions = result.get("suggestions", [])
        
        # 1. Handle Failures
        if status not in ["success", "completed", "partial_success"]:
            summary = f"Failed: {title}"
            rich_error = f"### ❌ {title} Failed\n\n**Reason:**\n{raw_msg}\n"
            if suggestions:
                rich_error += "\n**Suggestions:**\n"
                for sug in suggestions:
                    rich_error += f"- {sug}\n"
            return rich_error.strip(), summary
            
        # 2. Extract standard properties from result if available
        item_name = result.get("item_name") or result.get("path")
        source = result.get("source_name")
        target = result.get("target_name") or result.get("target_path")
        
        # 3. Action-Specific Formatting
        rich_text = f"### ✓ {title}\n\n"
        
        if "volume" in action or "mute" in action:
            rich_text += f"**Status:** {raw_msg}\n"
            if "volume_level" in result:
                rich_text += f"\n**Level:** {result['volume_level']}%\n"
            summary = raw_msg
            
        elif "brightness" in action:
            rich_text += f"**Status:** {raw_msg}\n"
            if "brightness_level" in result:
                rich_text += f"\n**Level:** {result['brightness_level']}%\n"
            summary = raw_msg
            
        elif action in ["open_application", "close_application"]:
            app_name = item_name or "Application"
            state = "Running" if "open" in action else "Closed"
            rich_text = f"### ✓ {app_name.title()} {state}\n\n**Application:** {app_name.title()}\n**Status:** {state}\n\n{raw_msg}"
            summary = raw_msg
            
        elif action in ["create_folder", "create_file", "delete_item"]:
            item_type = "Folder" if "folder" in action else "File"
            if action == "delete_item": item_type = "Item"
            name = os.path.basename(item_name) if item_name else "Unknown"
            
            rich_text = f"### ✓ {item_type} {'Created' if 'create' in action else 'Deleted'}\n\n"
            rich_text += f"{raw_msg}\n\n"
            if item_name:
                rich_text += f"**Target:**\n`{item_name}`\n"
            summary = raw_msg
            
        elif action in ["move_file", "copy_file"]:
            op = "Moved" if "move" in action else "Copied"
            rich_text = f"### ✓ File {op}\n\n"
            if source:
                rich_text += f"**From:**\n`{source}`\n\n"
            if target:
                rich_text += f"**To:**\n`{target}`\n\n"
            rich_text += f"**Status:** {raw_msg}"
            summary = raw_msg
            
        elif action == "search_web":
            rich_text = f"### ✓ Web Search\n\n{raw_msg}"
            summary = "Performed web search"
            
        elif action == "list_open_windows":
            lines = raw_msg.split('\n')
            rich_text = "### ✓ Open Windows\n\n"
            for line in lines:
                if line.strip() and not line.startswith("Found"):
                    rich_text += f"- {line.strip()}\n"
            summary = "Listed open windows"
            
        elif action == "execute_queue":
            results = result.get("results", [])
            successful = result.get('successful', 0)
            failed = result.get('failed', 0)
            
            rich_text = f"### Execution Summary\n\n"
            rich_text += f"**Completed:** {successful} | **Failed:** {failed}\n\n"
            for r in results:
                step_status = "✓" if r.get('result', {}).get('status') in ['success', 'completed'] else "❌"
                step_title = r.get('action').replace('_', ' ').title()
                rich_text += f"- {step_status} **Step {r.get('step')}**: {step_title}\n"
            summary = "Executed task queue"
            
        elif metadata:
            rich_text = f"### ✓ {title}\n\n{raw_msg}\n\n"
            for key, val in metadata.items():
                rich_text += f"**{key}:** {val}\n"
            summary = raw_msg[:40] + "..." if len(raw_msg) > 40 else raw_msg
            
        else:
            # Fallback for generic actions
            rich_text = f"### ✓ {title}\n\n{raw_msg}"
            summary = raw_msg[:40] + "..." if len(raw_msg) > 40 else raw_msg
            
        return rich_text.strip(), summary.strip()
