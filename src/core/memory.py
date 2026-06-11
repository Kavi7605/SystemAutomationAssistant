from typing import List, Dict, Any

class MemoryManager:
    """
    Manages conversation history and short-term state for the Agent.
    """
    def __init__(self, max_history: int = 10):
        self.history: List[Dict[str, str]] = []
        self.max_history = max_history

    def add_message(self, role: str, content: str):
        """
        Adds a message to the conversation history.
        Role can be 'user', 'assistant', 'system', or 'tool'.
        """
        self.history.append({"role": role, "content": content})
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def get_history(self) -> List[Dict[str, str]]:
        """Returns the current conversation history."""
        return self.history

    def get_context_string(self) -> str:
        """Returns the conversation history formatted as a string for LLM injection."""
        context = ""
        for msg in self.history:
            context += f"{msg['role'].capitalize()}: {msg['content']}\n"
        return context

    def clear(self):
        """Clears the conversation history."""
        self.history = []
