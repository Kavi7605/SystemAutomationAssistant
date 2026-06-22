import json
import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PersistenceManager:
    """
    Handles saving and loading of system state and context to local JSON files.
    """
    def __init__(self, context_file: str = "data/context.json", state_file: str = "data/state.json"):
        self.context_file = context_file
        self.state_file = state_file
        
        # Ensure the directories exist
        os.makedirs(os.path.dirname(os.path.abspath(self.context_file)), exist_ok=True)
        os.makedirs(os.path.dirname(os.path.abspath(self.state_file)), exist_ok=True)

    def _serialize(self, obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        return str(obj)

    def save_context(self, context_snapshot: Dict[str, Any]) -> None:
        try:
            with open(self.context_file, "w") as f:
                json.dump(context_snapshot, f, indent=2, default=self._serialize)
        except Exception as e:
            logger.error(f"Failed to save context to {self.context_file}: {e}")

    def load_context(self) -> Dict[str, Any]:
        if not os.path.exists(self.context_file):
            return {}
        try:
            with open(self.context_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.warning(f"Corrupted context JSON: {e}. Returning empty structure.")
            return {}
        except Exception as e:
            logger.error(f"Failed to load context: {e}")
            return {}

    def save_state(self, state_snapshot: Dict[str, Any]) -> None:
        try:
            with open(self.state_file, "w") as f:
                json.dump(state_snapshot, f, indent=2, default=self._serialize)
        except Exception as e:
            logger.error(f"Failed to save state to {self.state_file}: {e}")

    def load_state(self) -> Dict[str, Any]:
        if not os.path.exists(self.state_file):
            return {}
        try:
            with open(self.state_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.warning(f"Corrupted state JSON: {e}. Returning empty structure.")
            return {}
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return {}
