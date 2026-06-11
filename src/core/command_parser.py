import logging
import json
from typing import Dict, Any, Optional
from src.llm.ollama_client import OllamaClient
from src.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

class CommandParser:
    """
    Parses natural language commands into structured JSON representations 
    using the Ollama LLM client and dynamically loaded tool schemas.
    """
    def __init__(self, client: OllamaClient, registry: ToolRegistry):
        self.client = client
        self.registry = registry
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        schemas = self.registry.get_all_schemas()
        schemas_json = json.dumps(schemas, indent=4)
        
        return f"""You are a system automation assistant command parser. Your task is to interpret user input and convert it into a structured JSON command.

Supported actions are described by the following tool schemas:
{schemas_json}

You must ALWAYS output strictly valid JSON and nothing else. Do not include any explanations, conversational text, or markdown formatting (like ```json).

Format your response exactly like this:
{{
    "action": "action_name",
    "parameters": {{
        "parameter_key": "parameter_value"
    }}
}}

If the command cannot be understood or maps to an unsupported action, return an action of "unknown" and an empty parameters object:
{{
    "action": "unknown",
    "parameters": {{}}
}}
"""

    def parse_command(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Parses the user input into a structured JSON command using the LLM.
        
        Args:
            user_input: Natural language string provided by the user.
            
        Returns:
            A dictionary containing the parsed 'action' and 'parameters', 
            or None if parsing failed.
        """
        prompt = f"User input: {user_input}\nConvert this into the specified JSON format."
        
        try:
            result = self.client.generate(prompt=prompt, system=self.system_prompt)
            return result
        except Exception as e:
            logger.error(f"Failed to parse command: {e}")
            return None
