"""Placeholder backend. Replace with the real automation engine later.

The real backend should expose the same `execute(command: str) -> str` interface
so main_window.py does not need to change when swapped in.
"""
import random


class FakeBackend:
    _RESPONSES = {
        "open chrome": "Opened Chrome successfully.",
        "open steam": "Opened Steam successfully.",
        "open whatsapp": "Opened WhatsApp successfully.",
        "take screenshot": "Screenshot captured and saved.",
        "increase brightness": "Brightness increased to 80%.",
        "turn wifi on": "WiFi turned on.",
    }

    def execute(self, command: str) -> str:
        """Simulate processing a natural language command. Always succeeds here."""
        key = command.strip().lower()
        if key in self._RESPONSES:
            return self._RESPONSES[key]
        if key.startswith("create"):
            return f"Created file as requested: '{command}'."
        if key.startswith("delete"):
            return f"Deleted file as requested: '{command}'."
        if key.startswith("move"):
            return f"Moved file as requested: '{command}'."
        return random.choice([
            f"Done: {command}",
            f"Command executed: {command}",
            f"'{command}' completed successfully.",
        ])
