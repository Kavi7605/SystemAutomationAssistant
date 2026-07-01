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
            "last_interacted_app": None,
            "current_active_app": None,
            "last_active_app": None,
            "last_window_title": None,
            "last_successful_action": None,
            "last_failed_action": None,
            "last_interaction_type": None,
            "opened_apps_history": [],
            "closed_apps_history": [],
            "focused_apps_history": [],
            "active_opened_apps": [],
            "pending_disambiguation": None,
            "filesystem_state": {
                "last_opened_folder": None,
                "last_created_folder": None,
                "last_created_file": None,
                "last_found_file": None,
                "last_found_folder": None,
                "pending_delete": None
            },
            "system_state": {
                "volume_level": None,
                "is_muted": False,
                "brightness_level": None,
                "wifi_enabled": None,
                "wifi_connected": None,
                "wifi_name": None,
                "hotspot_enabled": None,
                "bluetooth_enabled": None,
                "power_mode": None,
                "battery_saver_enabled": None,
                "power_plan": None,
                "available_power_profiles": [],
                "last_power_action": None,
                "pending_power_action": None,
                "display_monitor_count": None,
                "primary_resolution": None,
                "primary_refresh_rate": None,
                "current_window_title": None,
                "current_window_app": None,
                "current_window_handle": None,
                "last_window_action": None,
                "open_windows_count": None
            }
        }

    def update_last_command(self, command: str) -> None:
        self.state["last_command"] = command
        self.save()

    def mark_app_opened(self, app_name: str) -> None:
        from src.context.application_aliases import normalize_app_name
        app_name = normalize_app_name(app_name)
        self.state["last_opened_app"] = app_name
        self.state["last_successful_action"] = "open_application"
        self.state["last_interacted_app"] = app_name
        self.state["last_interaction_type"] = "application"
        
        # Suppress consecutive duplicates
        if not self.state["opened_apps_history"] or self.state["opened_apps_history"][-1] != app_name:
            self.state["opened_apps_history"].append(app_name)
            
        if app_name not in self.state["active_opened_apps"]:
            self.state["active_opened_apps"].append(app_name)
            
        # Synchronize current_active_app
        if self.state["current_active_app"] != app_name:
            self.state["last_active_app"] = self.state["current_active_app"]
            self.state["current_active_app"] = app_name
            
        self.save()

    def mark_app_closed(self, app_name: str) -> None:
        from src.context.application_aliases import normalize_app_name
        app_name = normalize_app_name(app_name)
        self.state["last_closed_app"] = app_name
        self.state["last_successful_action"] = "close_application"
        self.state["last_interacted_app"] = app_name
        self.state["last_interaction_type"] = "application"
        
        # Suppress consecutive duplicates
        if not self.state["closed_apps_history"] or self.state["closed_apps_history"][-1] != app_name:
            self.state["closed_apps_history"].append(app_name)
            
        if app_name in self.state["active_opened_apps"]:
            self.state["active_opened_apps"].remove(app_name)
            
        # Synchronize current_active_app if the active app was closed
        if self.state["current_active_app"] == app_name:
            self.state["last_active_app"] = self.state["current_active_app"]
            self.state["current_active_app"] = self.state["active_opened_apps"][-1] if self.state["active_opened_apps"] else None
            
        self.save()

    def mark_app_focused(self, app_name: str) -> None:
        from src.context.application_aliases import normalize_app_name
        app_name = normalize_app_name(app_name)
        self.state["last_focused_app"] = app_name
        self.state["last_successful_action"] = "focus_window"
        self.state["last_interacted_app"] = app_name
        self.state["last_interaction_type"] = "application"
        
        # Suppress consecutive duplicates
        if not self.state["focused_apps_history"] or self.state["focused_apps_history"][-1] != app_name:
            self.state["focused_apps_history"].append(app_name)
        
        # Synchronize current_active_app
        if self.state["current_active_app"] != app_name:
            self.state["last_active_app"] = self.state["current_active_app"]
            self.state["current_active_app"] = app_name
            
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
        self.state["last_failed_action"] = None
        self.save()

    def mark_action_failed(self, action: str) -> None:
        self.state["last_failed_action"] = action
        self.save()

    def update_system_state(self, key: str, value: Any) -> None:
        """Updates a specific property within the system_state block."""
        if "system_state" not in self.state:
            self.state["system_state"] = {}
        self.state["system_state"][key] = value
        self.save()

    def update_filesystem_state(self, key: str, value: Any) -> None:
        """Updates a specific property within the filesystem_state block."""
        if "filesystem_state" not in self.state:
            self.state["filesystem_state"] = {
                "last_opened_folder": None,
                "last_created_folder": None,
                "last_created_file": None,
                "last_found_file": None,
                "last_found_folder": None,
                "pending_delete": None
            }
        self.state["filesystem_state"][key] = value
        self.state["last_interaction_type"] = "filesystem"
        self.save()
        
    def get_filesystem_context(self) -> Dict[str, Any]:
        return self.state.get("filesystem_state", {})

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
                default_system_state = self.state.get("system_state", {}).copy()
                
                # Exclude session-specific histories from being loaded to prevent pollution
                for history_key in ["opened_apps_history", "closed_apps_history", "focused_apps_history", "active_opened_apps", "last_interacted_app"]:
                    if history_key in loaded:
                        del loaded[history_key]
                        
                self.state.update(loaded)
                
                if "filesystem_state" not in self.state:
                    self.state["filesystem_state"] = {
                        "last_opened_folder": None,
                        "last_created_folder": None,
                        "last_created_file": None,
                        "last_found_file": None,
                        "last_found_folder": None,
                        "pending_delete": None
                    }
                
                # Ensure all default keys exist in system_state even if loading an old save
                if "system_state" in loaded:
                    for key, value in default_system_state.items():
                        if key not in self.state["system_state"]:
                            self.state["system_state"][key] = value
