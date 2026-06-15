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

7. FOLDER CREATION: Extract ONLY the folder's name into the `folder_name` parameter. The `path` parameter must contain the target drive or directory exactly as the user specified it (e.g., `C drive Projects`).
8. NEVER INVENT WINDOWS PATHS: You must NEVER generate paths with backslashes like `C:\\Projects`. Output natural language paths exactly as provided by the user (e.g., `C drive Projects`). Backslashes cause JSON parsing errors.
9. WEBSITE SEARCHES: For website-specific searches (e.g., "search youtube for X", "search github website for Y"), you MUST use the `open_url` action with the appropriately constructed search URL. Do NOT use `search_web` for website-specific searches. Use `search_web` ONLY for general google/web searches.
10. CLOSING WEBSITES: Closing browser tabs or websites is NOT supported. If a user asks to close a website (e.g., "close youtube website"), you MUST return the `unsupported` action with a message parameter explaining that closing websites is not supported.

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

Input: wait 5 seconds

Output:
{{
    "action": "wait",
    "parameters": {{
        "seconds": 5
    }}
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

Input: create folder reports in C drive Projects

Output:
{{
    "action": "create_folder",
    "parameters": {{
        "folder_name": "reports",
        "path": "C drive Projects"
    }}
}}

Input: create folder named testing in c drive

Output:
{{
    "action": "create_folder",
    "parameters": {{
        "folder_name": "testing",
        "path": "c drive"
    }}
}}

Input: create folder work inside d drive

Output:
{{
    "action": "create_folder",
    "parameters": {{
        "folder_name": "work",
        "path": "d drive"
    }}
}}

Input: create folder testing day 5 in c drive

Output:
{{
    "action": "create_folder",
    "parameters": {{
        "folder_name": "testing day 5",
        "path": "c drive"
    }}
}}

Input: create file notes.txt

Output:
{{
    "action": "create_file",
    "parameters": {{
        "file_name": "notes.txt"
    }}
}}

Input: create notes.txt in C drive Kavi Work Degree Charusat SEM 7 Internship

Output:
{{
    "action": "create_file",
    "parameters": {{
        "file_name": "notes.txt",
        "path": "C drive Kavi Work Degree Charusat SEM 7 Internship"
    }}
}}

Input: create report.docx in desktop

Output:
{{
    "action": "create_file",
    "parameters": {{
        "file_name": "report.docx",
        "path": "desktop"
    }}
}}

Input: create notes.txt in downloads

Output:
{{
    "action": "create_file",
    "parameters": {{
        "file_name": "notes.txt",
        "path": "Downloads"
    }}
}}

Input: create file report.md inside documents

Output:
{{
    "action": "create_file",
    "parameters": {{
        "file_name": "report.md",
        "path": "Documents"
    }}
}}

Input: create file notes.txt in c drive

Output:
{{
    "action": "create_file",
    "parameters": {{
        "file_name": "notes.txt",
        "path": "c drive"
    }}
}}

Input: open downloads

Output:
{{
    "action": "open_folder",
    "parameters": {{
        "folder_path": "downloads"
    }}
}}

Input: open documents

Output:
{{
    "action": "open_folder",
    "parameters": {{
        "folder_path": "documents"
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

Input: open youtube

Output:
{{
    "action": "open_url",
    "parameters": {{
        "url": "https://youtube.com"
    }}
}}

Input: close youtube website

Output:
{{
    "action": "unsupported",
    "parameters": {{
        "message": "Closing browser tabs/websites is not currently supported."
    }}
}}

Input: open github

Output:
{{
    "action": "open_application",
    "parameters": {{
        "application_name": "github"
    }}
}}

Input: open github desktop

Output:
{{
    "action": "open_application",
    "parameters": {{
        "application_name": "github desktop"
    }}
}}

Input: open github website

Output:
{{
    "action": "open_url",
    "parameters": {{
        "url": "https://github.com"
    }}
}}

Input: open chatgpt

Output:
{{
    "action": "open_url",
    "parameters": {{
        "url": "https://chatgpt.com"
    }}
}}

Input: search youtube for ghost of yotei

Output:
{{
    "action": "open_url",
    "parameters": {{
        "url": "https://www.youtube.com/results?search_query=ghost+of+yotei"
    }}
}}

Input: search github website for python automation projects

Output:
{{
    "action": "open_url",
    "parameters": {{
        "url": "https://github.com/search?q=python+automation+projects"
    }}
}}

Input: search github python automation projects

Output:
{{
    "action": "search_web",
    "parameters": {{
        "query": "python automation projects"
    }}
}}

Input: open linkedin website

Output:
{{
    "action": "open_url",
    "parameters": {{
        "url": "https://www.linkedin.com"
    }}
}}

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
