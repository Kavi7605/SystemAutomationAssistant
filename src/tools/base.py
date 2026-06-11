from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTool(ABC):
    """
    Base class for all executable tools in the system.
    """
    name: str = "base_tool"
    description: str = "Base tool description."
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Executes the tool's action.
        Returns a dictionary with at least a 'status' (success/failed) and a 'message'.
        """
        pass
        
    def get_schema(self) -> Dict[str, Any]:
        """
        Returns the JSON schema describing this tool and its parameters.
        Must be implemented by subclasses if they take parameters.
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {}
        }
