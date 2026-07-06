from typing import Dict, Any

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
        status = result.get("status", "info")
        title = result.get("title")
        message = result.get("message", "")
        metadata = result.get("metadata", {})
        suggestions = result.get("suggestions", [])
        action_name = result.get("action", "")
        
        icons = cls._get_icons()
        
        # 1. Map status to icon and determine fallback titles
        if status in ["success", "completed", "partial_success"]:
            icon = icons.get("success", "✓")
            fallback_title = "Success"
        elif status == "failed" or status == "error":
            icon = icons.get("error", "✗")
            fallback_title = "Error"
        elif status == "warning":
            icon = icons.get("warning", "⚠")
            fallback_title = "Warning"
        elif status == "info":
            icon = icons.get("info", "ℹ")
            fallback_title = "Information"
        elif status == "interactive":
            icon = icons.get("question", "?")
            fallback_title = "Interactive Selection"
        elif status == "cancelled":
            icon = icons.get("info", "ℹ")
            fallback_title = "Operation Cancelled"
        else:
            icon = icons.get("info", "ℹ")
            fallback_title = "Operation Result"
            
        # Title resolution chain: Provided Title -> Action derived -> Fallback
        if not title:
            if action_name:
                title = action_name.replace("_", " ").title()
            else:
                title = fallback_title
                
        # Handle specific confirmation override based on message content if status isn't already warning/interactive
        # (Legacy support, though Executor should ideally provide this explicitly now)
        if "delete" in message.lower() and "are you sure" in message.lower() and status != "warning":
            icon = icons.get("warning", "⚠")
            if not result.get("title"):
                title = "Delete Confirmation"
            
        # 2. Build the formatted string
        parts = [f"{icon} **{title}**\n"]
        
        # 3. Add Message
        if message:
            parts.append(f"{message}\n")
                
        # 4. Add Metadata
        if metadata:
            for key, value in metadata.items():
                parts.append(f"**{key}**")
                parts.append(f"{value}\n")
                
        # 5. Interactive Selection Specifics
        if status == "interactive" and result.get("matches"):
            matches = result.get("matches", [])
            for i, match in enumerate(matches, 1):
                parts.append(f"{i}. {match}")
            parts.append("\nReply with:")
            for i in range(1, len(matches) + 1):
                parts.append(str(i))
            parts.append("cancel\n")
            
        # 6. Add Suggestions
        if suggestions:
            parts.append("**Suggestions**\n")
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
