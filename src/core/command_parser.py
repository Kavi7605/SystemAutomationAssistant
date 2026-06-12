import logging
import json
from typing import Dict, Any, Optional, Union, List
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
        schemas_json = json.dumps(schemas, indent=2)

        return f"""
You are a system automation assistant command parser.

Your job is to convert user commands into STRICT JSON.

Supported tools:
{schemas_json}

IMPORTANT RULES:

1. Return ONLY valid JSON.
2. Never return explanations.
3. Never return markdown.
4. Never return text before or after JSON.
5. Use ONLY actions defined in the tool schemas above.
6. If the request is unsupported, return:

{{
    "action": "unknown",
    "parameters": {{}}
}}

Single Action Format:

{{
    "action": "action_name",
    "parameters": {{
        "key": "value"
    }}
}}

Multi-Step Format:

[
    {{
        "action": "action_name",
        "parameters": {{}}
    }},
    {{
        "action": "action_name",
        "parameters": {{}}
    }}
]

Examples:

Input: open steam

Output:
{{
    "action": "open_application",
    "parameters": {{
        "application_name": "steam"
    }}
}}

Input: launch discord

Output:
{{
    "action": "open_application",
    "parameters": {{
        "application_name": "discord"
    }}
}}

Input: start vscode

Output:
{{
    "action": "open_application",
    "parameters": {{
        "application_name": "vscode"
    }}
}}

Input: close steam

Output:
{{
    "action": "close_application",
    "parameters": {{
        "application_name": "steam"
    }}
}}

Input: terminate discord

Output:
{{
    "action": "close_application",
    "parameters": {{
        "application_name": "discord"
    }}
}}

Input: take screenshot

Output:
{{
    "action": "take_screenshot",
    "parameters": {{}}
}}

Input: capture screen

Output:
{{
    "action": "take_screenshot",
    "parameters": {{}}
}}

Input: search chatgpt

Output:
{{
    "action": "search_web",
    "parameters": {{
        "query": "chatgpt"
    }}
}}

Input: google python tutorials

Output:
{{
    "action": "search_web",
    "parameters": {{
        "query": "python tutorials"
    }}
}}

Input: create folder internship

Output:
{{
    "action": "create_folder",
    "parameters": {{
        "folder_name": "internship"
    }}
}}

Input: create folder reports in C:\\Projects

Output:
{{
    "action": "create_folder",
    "parameters": {{
        "folder_name": "reports",
        "path": "C:\\\\Projects"
    }}
}}

Input: open steam and discord

Output:
[
    {{
        "action": "open_application",
        "parameters": {{
            "application_name": "steam"
        }}
    }},
    {{
        "action": "open_application",
        "parameters": {{
            "application_name": "discord"
        }}
    }}
]

Input: take screenshot and open browser

Output:
[
    {{
        "action": "take_screenshot",
        "parameters": {{}}
    }},
    {{
        "action": "open_application",
        "parameters": {{
            "application_name": "browser"
        }}
    }}
]

Input: open fakeapp and take screenshot

Output:
[
    {{
        "action": "open_application",
        "parameters": {{
            "application_name": "fakeapp"
        }}
    }},
    {{
        "action": "take_screenshot",
        "parameters": {{}}
    }}
]
"""

    def parse_command(self, user_input: str) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        """
        Parses the user input into a structured JSON command or list of commands using the LLM.
        
        Args:
            user_input: Natural language string provided by the user.
            
        Returns:
            A dictionary or list of dictionaries containing the parsed 'action' and 'parameters', 
            or None if parsing failed.
        """
        prompt = f"User input: {user_input}\nConvert this into the specified JSON format."
        
        try:
            result = self.client.generate(prompt=prompt, system=self.system_prompt)
            return result
        except Exception as e:
            logger.error(f"Failed to parse command: {e}")
            return None
