import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ContextManager:
    """
    Centralized Context Tracking Engine that remembers recent user actions
    and application interactions.
    """
    def __init__(self, persistence_manager=None):
        self.persistence_manager = persistence_manager
        self.state = {
            "last_command": None,
            "last_opened_app": None,
            "last_closed_app": None,
            "last_focused_app": None,
            "current_active_app": None,
            "last_active_app": None,
            "last_window_title": None,
            "last_successful_action": None,
            "last_failed_action": None,
            "opened_apps_history": [],
            "closed_apps_history": [],
            "focused_apps_history": []
        }

    def update_last_command(self, command: str) -> None:
        self.state["last_command"] = command
        self.save()

    def mark_app_opened(self, app_name: str) -> None:
        from src.context.application_aliases import normalize_app_name
        app_name = normalize_app_name(app_name)
        self.state["last_opened_app"] = app_name
        self.state["last_successful_action"] = "open_application"
        self.state["opened_apps_history"].append(app_name)
        self.save()

    def mark_app_closed(self, app_name: str) -> None:
        from src.context.application_aliases import normalize_app_name
        app_name = normalize_app_name(app_name)
        self.state["last_closed_app"] = app_name
        self.state["last_successful_action"] = "close_application"
        self.state["closed_apps_history"].append(app_name)
        self.save()

    def mark_app_focused(self, app_name: str) -> None:
        from src.context.application_aliases import normalize_app_name
        app_name = normalize_app_name(app_name)
        self.state["last_focused_app"] = app_name
        self.state["focused_apps_history"].append(app_name)
        
        if self.state["current_active_app"] != app_name:
            self.state["last_active_app"] = self.state["current_active_app"]
            self.state["current_active_app"] = app_name
            
        self.state["last_successful_action"] = "focus_window"
        self.save()

    def update_active_window(self, window_title: str) -> None:
        self.state["last_window_title"] = window_title
        
        if not window_title:
            if self.state["current_active_app"] is not None:
                self.state["last_active_app"] = self.state["current_active_app"]
                self.state["current_active_app"] = None
                self.save()
            return
            
        from src.context.application_aliases import APP_WINDOW_ALIASES
        
        window_title_lower = window_title.lower()
        matched_app = None
        for app, aliases in APP_WINDOW_ALIASES.items():
            if any(alias in window_title_lower for alias in aliases):
                matched_app = app
                break
                
        if matched_app != self.state["current_active_app"]:
            self.state["last_active_app"] = self.state["current_active_app"]
            self.state["current_active_app"] = matched_app
            self.save()

    def sync_active_apps(self, current_app: str, last_app: str) -> None:
        """Synchronizes the active app state from ApplicationStateManager."""
        self.state["current_active_app"] = current_app
        self.state["last_active_app"] = last_app
        self.save()

    def mark_action_success(self, action: str) -> None:
        self.state["last_successful_action"] = action
        self.save()

    def mark_action_failed(self, action: str) -> None:
        self.state["last_failed_action"] = action
        self.save()

    def get_last_opened_app(self):
        history = self.state["opened_apps_history"]
        return history[-1] if history else None

    def get_last_closed_app(self):
        history = self.state["closed_apps_history"]
        return history[-1] if history else None

    def get_last_focused_app(self):
        history = self.state["focused_apps_history"]
        return history[-1] if history else None

    def get_previous_opened_app(self):
        history = self.state["opened_apps_history"]
        return history[-2] if len(history) >= 2 else None

    def get_previous_closed_app(self):
        history = self.state["closed_apps_history"]
        return history[-2] if len(history) >= 2 else None

    def get_previous_focused_app(self):
        history = self.state["focused_apps_history"]
        return history[-2] if len(history) >= 2 else None

    def get_open_history(self) -> list:
        return list(self.state["opened_apps_history"])

    def get_close_history(self) -> list:
        return list(self.state["closed_apps_history"])

    def get_focus_history(self) -> list:
        return list(self.state["focused_apps_history"])

    def get_context_snapshot(self) -> Dict[str, Any]:
        import copy
        return copy.deepcopy(self.state)
        
    def save(self):
        if self.persistence_manager:
            self.persistence_manager.save_context(self.get_context_snapshot())
            
    def load(self):
        if self.persistence_manager:
            loaded = self.persistence_manager.load_context()
            if loaded:
                self.state.update(loaded)
