import logging
from datetime import datetime
from typing import Dict, Any, Optional

try:
    import psutil
except ImportError:
    psutil = None

from src.context.window_manager import WindowManager
from src.context.application_aliases import APP_WINDOW_ALIASES, normalize_app_name

logger = logging.getLogger(__name__)

class ApplicationStateManager:
    """
    Maintains a real-time view of application states on the system.
    """
    def __init__(self, window_manager: WindowManager, persistence_manager=None):
        self.window_manager = window_manager
        self.persistence_manager = persistence_manager
        self.states: Dict[str, Dict[str, Any]] = {}
        self.current_active_app: Optional[str] = None
        self.last_active_app: Optional[str] = None

    def _init_app_state(self, app_name: str) -> None:
        if app_name not in self.states:
            self.states[app_name] = {
                "running": False,
                "window_open": False,
                "focused": False,
                "last_seen": None,
                "window_title": None
            }
            self.save()

    def get_app_state(self, app_name: str) -> Dict[str, Any]:
        app_name = normalize_app_name(app_name)
        self._init_app_state(app_name)
        return self.states[app_name]

    def is_running(self, app_name: str) -> bool:
        app_name = normalize_app_name(app_name)
        return self.states.get(app_name, {}).get("running", False)

    def is_window_open(self, app_name: str) -> bool:
        app_name = normalize_app_name(app_name)
        return self.states.get(app_name, {}).get("window_open", False)

    def is_focused(self, app_name: str) -> bool:
        app_name = normalize_app_name(app_name)
        return self.states.get(app_name, {}).get("focused", False)

    def get_current_active_app(self) -> Optional[str]:
        return self.current_active_app

    def get_last_active_app(self) -> Optional[str]:
        return self.last_active_app

    def mark_focused(self, app_name: str) -> None:
        app_name = normalize_app_name(app_name)
        self._init_app_state(app_name)
        
        for name in self.states:
            self.states[name]["focused"] = False
            
        self.states[app_name]["focused"] = True
        self.states[app_name]["last_seen"] = datetime.now()
        
        if self.current_active_app != app_name:
            self.last_active_app = self.current_active_app
            self.current_active_app = app_name
            
        self.save()

    def refresh_active_window(self) -> None:
        active_win = self.window_manager.get_active_window()
        if not active_win:
            return
            
        title = active_win.get("title", "").lower()
        process_name = active_win.get("process_name", "").lower().replace(".exe", "")
        
        matched_app = None
        for app, aliases in APP_WINDOW_ALIASES.items():
            if any(alias in title or alias in process_name for alias in aliases):
                matched_app = app
                break
                
        if not matched_app:
            matched_app = process_name if process_name and process_name != "unknown" else "unknown"
            
        if self.current_active_app != matched_app:
            self.last_active_app = self.current_active_app
            self.current_active_app = matched_app
            
        if matched_app != "unknown":
            self._init_app_state(matched_app)
            self.states[matched_app]["focused"] = True
            
        for name in self.states:
            if name != matched_app:
                self.states[name]["focused"] = False
                
        self.save()

    def refresh_app_state(self, app_name: str) -> None:
        app_name = normalize_app_name(app_name)
        self._init_app_state(app_name)
        state = self.states[app_name]
        
        win_info = self.window_manager.find_window(app_name)
        if win_info:
            state["window_open"] = True
            state["window_title"] = win_info.get("title")
            state["focused"] = win_info.get("is_active", False)
            state["last_seen"] = datetime.now()
        else:
            state["window_open"] = False
            state["window_title"] = None
            state["focused"] = False
            
        state["running"] = False
        if psutil:
            aliases = APP_WINDOW_ALIASES.get(app_name, [app_name])
            for proc in psutil.process_iter(['name']):
                try:
                    proc_name = proc.info['name']
                    if proc_name and any(alias in proc_name.lower() for alias in aliases):
                        state["running"] = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
                    
        if state["focused"]:
            if self.current_active_app != app_name:
                self.last_active_app = self.current_active_app
                self.current_active_app = app_name
                
        self.save()

    def refresh_all(self) -> None:
        apps_to_scan = set(APP_WINDOW_ALIASES.keys()).union(self.states.keys())
        for app_name in apps_to_scan:
            self.refresh_app_state(app_name)
        self.refresh_active_window()
        self.save()

    def save(self):
        if self.persistence_manager:
            self.persistence_manager.save_state({
                "states": self.states,
                "current_active_app": self.current_active_app,
                "last_active_app": self.last_active_app
            })

    def load(self):
        if self.persistence_manager:
            loaded = self.persistence_manager.load_state()
            if loaded:
                self.states = loaded.get("states", {})
                self.current_active_app = loaded.get("current_active_app")
                self.last_active_app = loaded.get("last_active_app")
