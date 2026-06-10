import logging
from typing import Dict, Any, Optional
from src.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class CommandParser:
    """
    Parses natural language commands into structured JSON representations 
    using the Ollama LLM client.
    """
    def __init__(self, client: OllamaClient):
        self.client = client
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        return """You are a system automation assistant command parser. Your task is to interpret user input and convert it into a structured JSON command.

Supported actions:
1. "open_application" (requires "application_name" parameter)
2. "close_application" (requires "application_name" parameter)
3. "take_screenshot" (no parameters required)
4. "create_folder" (requires "folder_name" parameter and optional "path" parameter)
5. "search_web" (requires "query" parameter)

You must ALWAYS output strictly valid JSON and nothing else. Do not include any explanations, conversational text, or markdown formatting (like ```json).

Format your response exactly like this:
{
    "action": "action_name",
    "parameters": {
        "parameter_key": "parameter_value"
    }
}

If the command cannot be understood or maps to an unsupported action, return an action of "unknown" and an empty parameters object:
{
    "action": "unknown",
    "parameters": {}
}

Examples:
User: "open brave"
{"action": "open_application", "parameters": {"application_name": "brave"}}
User: "launch discord"
{"action": "open_application", "parameters": {"application_name": "discord"}}
User: "start notepad"
{"action": "open_application", "parameters": {"application_name": "notepad"}}
User: "close brave"
{"action": "close_application", "parameters": {"application_name": "brave"}}
User: "take screenshot"
{"action": "take_screenshot", "parameters": {}}
User: "capture screen"
{"action": "take_screenshot", "parameters": {}}
User: "screen capture"
{"action": "take_screenshot", "parameters": {}}
User: "find chatgpt"
{"action": "search_web", "parameters": {"query": "chatgpt"}}
User: "search chatgpt"
{"action": "search_web", "parameters": {"query": "chatgpt"}}
User: "look up weather in london"
{"action": "search_web", "parameters": {"query": "weather in london"}}
User: "create folder internship"
{"action": "create_folder", "parameters": {"folder_name": "internship"}}
User: "make folder internship"
{"action": "create_folder", "parameters": {"folder_name": "internship"}}
User: "create directory reports"
{"action": "create_folder", "parameters": {"folder_name": "reports"}}
User: "make directory assets"
{"action": "create_folder", "parameters": {"folder_name": "assets"}}
User: "create a new folder src"
{"action": "create_folder", "parameters": {"folder_name": "src"}}
User: "make a folder named backup"
{"action": "create_folder", "parameters": {"folder_name": "backup"}}
User: "Create folder Internship in C:\\Projects"
{"action": "create_folder", "parameters": {"folder_name": "Internship", "path": "C:\\Projects"}}
User: "Create folder Photos in D:\\Media"
{"action": "create_folder", "parameters": {"folder_name": "Photos", "path": "D:\\Media"}}
User: "Make directory Reports inside C:\\Users\\Kavi\\Documents"
{"action": "create_folder", "parameters": {"folder_name": "Reports", "path": "C:\\Users\\Kavi\\Documents"}}
User: "create directory reports in D:\\Work"
{"action": "create_folder", "parameters": {"folder_name": "reports", "path": "D:\\Work"}}
User: "make folder downloads in E:\\data"
{"action": "create_folder", "parameters": {"folder_name": "downloads", "path": "E:\\data"}}
User: "create a new folder called test in C:\\Temp"
{"action": "create_folder", "parameters": {"folder_name": "test", "path": "C:\\Temp"}}
User: "create folder docs at C:\\workspace"
{"action": "create_folder", "parameters": {"folder_name": "docs", "path": "C:\\workspace"}}
User: "make directory build in ./project"
{"action": "create_folder", "parameters": {"folder_name": "build", "path": "./project"}}
User: "create folder logs in /var/log"
{"action": "create_folder", "parameters": {"folder_name": "logs", "path": "/var/log"}}
User: "open calc"
{"action": "open_application", "parameters": {"application_name": "calc"}}
User: "what is the time"
{"action": "unknown", "parameters": {}}"""

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
