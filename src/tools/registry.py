from typing import Dict, Any, List
import logging
from src.tools.base import BaseTool

logger = logging.getLogger(__name__)

class ToolRegistry:
    """
    Manages all available tools, handles registration, schema generation, 
    and routing execution.
    """
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        """Registers a tool with the registry."""
        self.tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    def get_tool(self, name: str) -> BaseTool:
        """Retrieves a tool by name."""
        return self.tools.get(name)

    def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """Executes a tool by name with the given arguments."""
        tool = self.get_tool(name)
        if not tool:
            return {"status": "failed", "message": f"Tool '{name}' not found in registry."}
        
        try:
            return tool.execute(**kwargs)
        except Exception as e:
            logger.error(f"Error executing tool '{name}': {e}", exc_info=True)
            return {"status": "failed", "message": str(e)}

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Returns the schemas of all registered tools."""
        return [tool.get_schema() for tool in self.tools.values()]
    
    def get_tools_description(self) -> str:
        """Returns a formatted string describing all available tools."""
        desc = []
        for tool in self.tools.values():
            desc.append(f"- {tool.name}: {tool.description}")
        return "\n".join(desc)
