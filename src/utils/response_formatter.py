import json
from typing import Dict, Any, List

class ResponseFormatter:
    """
    Formats raw execution results from the backend into a polished, user-friendly
    CLI format suitable for a desktop assistant.
    """
    
    ICONS = {
        "success": "✓",
        "error": "✗",
        "warning": "⚠",
        "info": "ℹ",
        "question": "?",
        "search": "🔍",
        "folder": "📁",
        "file": "📄",
        "app": "🖥"
    }
    
    ASCII_ICONS = {
        "success": "[OK]",
        "error": "[ERROR]",
        "warning": "[WARNING]",
        "info": "[INFO]",
        "question": "[?]",
        "search": "[SEARCH]",
        "folder": "Folder",
        "file": "File",
        "app": "App"
    }

    @classmethod
    def _get_icons(cls) -> Dict[str, str]:
        import sys
        try:
            if sys.stdout and hasattr(sys.stdout, 'encoding') and sys.stdout.encoding:
                "✓⚠✗ℹ📁".encode(sys.stdout.encoding)
            return cls.ICONS
        except UnicodeEncodeError:
            return cls.ASCII_ICONS
        except Exception:
            return cls.ICONS

    @classmethod
    def format_response(cls, result: Dict[str, Any]) -> str:
        """
        Formats a single result dictionary into a polished CLI string.
        """
        status = result.get("status", "unknown")
        title = result.get("title")
        message = result.get("message", "")
        metadata = result.get("metadata", {})
        suggestions = result.get("suggestions", [])
        
        icons = cls._get_icons()
        
        # Override for ambiguous (search results)
        if status == "ambiguous":
            icon = icons.get("question", "?")
            if not title:
                title = "Multiple matches were found"
            
            parts = [title, ""]
            matches = result.get("matches", [])
            for i, match in enumerate(matches, 1):
                # Basic parsing if match is just a path string
                # We expect the tool to pass better matches if possible, but fallback to strings
                match_str = str(match)
                import os
                name = os.path.basename(match_str)
                parent = os.path.basename(os.path.dirname(match_str)) if os.path.dirname(match_str) else "Unknown"
                
                parts.append(f"{i}.")
                parts.append(name)
                parts.append(parent)
                parts.append("")
                
            parts.append("Choose a number or type Cancel.")
            return "\n".join(parts)

        # 1. Map status to icon and default title
        if status in ["success", "completed", "partial_success"]:
            icon = icons.get("success", "")
            if not title:
                title = "Success"
        elif status == "failed":
            icon = icons.get("error", "")
            if not title:
                title = "Error"
        elif status == "info":
            icon = icons.get("info", "")
            if not title:
                title = "Information"
        else:
            icon = icons.get("info", "")
            if not title:
                title = "Result"
                
        # Handle specific confirmation override based on message content
        if "delete" in message.lower() and "are you sure" in message.lower():
            icon = icons.get("warning", "")
            title = "Delete Confirmation"
            
        # 2. Build the formatted string
        parts = [f"{icon} {title}\n"]
        
        # 3. Add Metadata
        if metadata:
            for key, value in metadata.items():
                parts.append(f"{key}:")
                parts.append(f"{value}\n")
                
        # 4. Add Message
        if message:
            # Clean up message for delete confirmation to avoid repeating the raw prompt
            if title == "Delete Confirmation":
                parts.append("This action cannot be undone.\n")
                parts.append("Type:\n\nyes\nno\ncancel")
            else:
                parts.append(f"{message}\n")
                
        # 5. Add Suggestions
        if suggestions:
            parts.append("Try:\n")
            for sug in suggestions:
                parts.append(f"• {sug}")
            parts.append("")
            
        return "\n".join(parts).strip()

    @classmethod
    def format_progress_start(cls, action_desc: str) -> str:
        """Formats the start of a progress message."""
        return f"{action_desc}"
        
    @classmethod
    def format_progress_step(cls, step_desc: str) -> str:
        """Formats an intermediate progress step."""
        return f"\n{step_desc}"
        
    @classmethod
    def format_progress_end(cls, success: bool = True) -> str:
        """Formats the end of a progress message."""
        icons = cls._get_icons()
        return f"\n\n{icons['success']} Completed" if success else f"\n\n{icons['error']} Failed"
        
    @classmethod
    def format_queue_summary(cls, successful: int, failed: int) -> str:
        """Formats a summary of a multi-step queue execution."""
        return (
            f"Summary\n\n"
            f"Completed: {successful}\n"
            f"Failed: {failed}"
        )
