import re
from typing import List, Optional
from src.context.context_manager import ContextManager

class ReferenceResolver:
    def __init__(self, context_manager: ContextManager):
        self.context_manager = context_manager
        
        self.singular_tokens = [
            "the first app", "the second app", "the third app",
            "the first one", "the second one", "the third one",
            "the latest app", "the newest app", "the oldest app",
            "the last opened app", "the last closed app", "the last focused app",
            "the currently focused app",
            "previous app", "current app", "last app", "that", "this", "it",
            "first", "second", "third", "previous", "latest", "newest", "oldest",
            "other", "next", "last_closed", "last_focused"
        ]
        
        self.plural_tokens = [
            "both", "both apps", "all", "all apps", "all of them", "every app",
            "other_all"
        ]
        
        self.tokens = self.singular_tokens + self.plural_tokens

    def is_reference(self, token: str) -> bool:
        token = token.lower().strip()
        if token in self.tokens:
            return True
        if token.startswith("all except "):
            return True
        return False

    def _resolve_token(self, token: str) -> Optional[List[str]]:
        token = token.lower().strip()
        snap = self.context_manager.get_context_snapshot()
        
        opened_history = snap.get("opened_apps_history", [])
        closed_history = snap.get("closed_apps_history", [])
        focused_history = snap.get("focused_apps_history", [])
        active_opened_apps = snap.get("active_opened_apps", [])
        
        unique_opened_all = list(dict.fromkeys(opened_history))
        
        if token in ["it", "that", "this"]:
            if snap.get("last_interaction_type") == "filesystem":
                return [token]
            res = snap.get("last_interacted_app") or snap.get("current_active_app") or snap.get("last_focused_app") or snap.get("last_opened_app") or snap.get("last_closed_app")
            return [res] if res else None
        elif token in ["previous app", "last app", "previous"]:
            res = snap.get("last_active_app") or (unique_opened_all[-2] if len(unique_opened_all) >= 2 else None)
            return [res] if res else None
        elif token in ["current app", "the currently focused app"]:
            res = snap.get("current_active_app")
            return [res] if res else None
        elif token in ["the first app", "the first one", "first"]:
            return [active_opened_apps[0]] if len(active_opened_apps) >= 1 else None
        elif token in ["the second app", "the second one", "second"]:
            return [active_opened_apps[1]] if len(active_opened_apps) >= 2 else None
        elif token in ["the third app", "the third one", "third"]:
            return [active_opened_apps[2]] if len(active_opened_apps) >= 3 else None
        elif token in ["the latest app", "the newest app", "latest", "newest", "the last opened app"]:
            return [active_opened_apps[-1]] if active_opened_apps else None
        elif token in ["the oldest app", "oldest"]:
            return [active_opened_apps[0]] if active_opened_apps else None
        elif token in ["the last closed app", "last_closed"]:
            return [closed_history[-1]] if closed_history else None
        elif token in ["the last focused app", "last_focused"]:
            return [focused_history[-1]] if focused_history else None
        elif token == "other":
            exclude = snap.get("last_interacted_app") or snap.get("current_active_app")
            others = [app for app in active_opened_apps if app != exclude]
            return [others[0]] if others else None
        elif token == "next":
            curr = snap.get("current_active_app")
            if not curr or curr not in active_opened_apps or len(active_opened_apps) < 2:
                return None
            idx = active_opened_apps.index(curr)
            return [active_opened_apps[(idx + 1) % len(active_opened_apps)]]
        elif token in ["both", "both apps"]:
            if len(active_opened_apps) >= 2:
                return active_opened_apps[-2:]
            return None
        elif token in ["all", "all apps", "all of them", "every app"]:
            if active_opened_apps:
                return active_opened_apps
            return None
        elif token == "other_all":
            exclude = snap.get("last_interacted_app") or snap.get("current_active_app")
            others = [app for app in active_opened_apps if app != exclude]
            return others if others else None
        elif token.startswith("all except "):
            exclude = token.replace("all except ", "").strip()
            from src.context.application_aliases import normalize_app_name
            exclude = normalize_app_name(exclude)
            others = [app for app in active_opened_apps if app != exclude]
            return others if others else None
            
        return None

    def resolve(self, target: str) -> List[str]:
        """
        Resolves a target string into a list of strings representing 
        the underlying referenced objects.
        Returns the original string as a 1-element list if it's not a reference.
        Raises ValueError if it is a reference but cannot be resolved.
        """
        text_lower = target.lower().strip()
        
        def strip_article(name: str) -> str:
            name_lower = name.strip().lower()
            for article in ["the ", "a ", "an "]:
                if name_lower.startswith(article):
                    return name[len(article):].strip()
            return name.strip()
        
        if self.is_reference(text_lower):
            resolved = self._resolve_token(text_lower)
            if not resolved:
                raise ValueError("No application reference available in context.")
            return [strip_article(r) for r in resolved]
            
        sorted_tokens = sorted(self.tokens, key=len, reverse=True)
        pattern = r'\b(' + '|'.join(re.escape(t) for t in sorted_tokens) + r')\b'
        
        if re.search(pattern, target, flags=re.IGNORECASE):
            def replacer(match):
                token_match = match.group(1)
                res = self._resolve_token(token_match)
                if not res:
                    raise ValueError("No application reference available in context.")
                return " and ".join(strip_article(r) for r in res)
                
            try:
                resolved_text = re.sub(pattern, replacer, target, flags=re.IGNORECASE)
                return [resolved_text]
            except ValueError as e:
                raise e
                
        return [target]

    def resolve_command(self, command_text: str) -> str:
        """
        Legacy fallback method to preserve any unmigrated usages.
        Returns the joined string instead of a list.
        """
        resolved_list = self.resolve(command_text)
        return " and ".join(resolved_list)
