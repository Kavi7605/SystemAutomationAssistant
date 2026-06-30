import json
import os
import datetime
import logging
from typing import List, Dict, Any
from collections import Counter

logger = logging.getLogger(__name__)

class HistoryManager:
    """
    Manages user command history and execution results for future reference,
    analytics, and context-aware repetitions.
    """
    def __init__(self, history_file: str = "data/history.json"):
        self.history_file = os.path.abspath(history_file)
        self.history: List[Dict[str, Any]] = []
        self._load_history()

    def _load_history(self):
        """Loads command history from the disk cache."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
                logger.debug(f"Loaded {len(self.history)} history entries.")
            except Exception as e:
                logger.error(f"Failed to load history: {e}", exc_info=True)
                self.history = []
        else:
            self.history = []

    def _save_history(self):
        """Saves current command history to the disk cache."""
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save history: {e}", exc_info=True)

    def add_entry(self, user_command: str, generated_json: Dict[str, Any], resolved_json: Dict[str, Any], execution_result: Dict[str, Any], generated_plan: list = None, source: str = "keyboard"):
        """
        Records a completed execution cycle into the history.
        """
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "source": source,
            "user_command": user_command,
            "generated_plan": generated_plan,
            "generated_json": generated_json,
            "resolved_json": resolved_json,
            "execution_result": execution_result
        }
        self.history.append(entry)
        self._save_history()

    def get_recent_commands(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieves the most recent N commands."""
        return self.history[-limit:]

    def get_frequent_commands(self, limit: int = 5) -> List[str]:
        """
        Analyzes the history and returns the most frequently used natural language commands.
        """
        commands = [entry.get("user_command", "").lower().strip() for entry in self.history if entry.get("user_command")]
        counter = Counter(commands)
        return [cmd for cmd, count in counter.most_common(limit)]

    def search_history(self, query: str) -> List[Dict[str, Any]]:
        """
        Searches the command history for a specific substring within the user's input.
        """
        query_lower = query.lower().strip()
        results = []
        for entry in self.history:
            user_cmd = entry.get("user_command", "").lower()
            if query_lower in user_cmd:
                results.append(entry)
        return results
