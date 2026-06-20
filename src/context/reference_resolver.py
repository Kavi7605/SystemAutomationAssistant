import re
from src.context.context_manager import ContextManager

class ReferenceResolver:
    def __init__(self, context_manager: ContextManager):
        self.context_manager = context_manager
        self.tokens = ["previous app", "current app", "last app", "that", "this", "it"]

    def resolve_token(self, token: str) -> str:
        token = token.lower()
        snap = self.context_manager.get_context_snapshot()
        
        if token in ["it", "that", "this"]:
            return snap.get("current_active_app") or snap.get("last_focused_app") or snap.get("last_opened_app") or snap.get("last_closed_app")
        elif token in ["previous app", "last app"]:
            return snap.get("last_active_app")
        elif token in ["current app"]:
            return snap.get("current_active_app")
            
        return None

    def resolve_command(self, command_text: str) -> str:
        # Build regex to find any of the tokens as whole words.
        pattern = r'\b(' + '|'.join(self.tokens) + r')\b'
        
        def replacer(match):
            token = match.group(1)
            resolved = self.resolve_token(token)
            if not resolved:
                raise ValueError("No application reference available in context.")
            return resolved
            
        # Only replace if a reference is actually found and resolved
        try:
            resolved_text = re.sub(pattern, replacer, command_text, flags=re.IGNORECASE)
            return resolved_text
        except ValueError as e:
            raise e
