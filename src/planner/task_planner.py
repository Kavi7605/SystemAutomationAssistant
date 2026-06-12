import logging
import json
from typing import List
from src.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class TaskPlanner:
    """
    Planner Layer that uses Llama3 to break down complex user requests 
    into a sequential list of simple, single-action natural language tasks.
    """
    def __init__(self, host: str = "http://localhost:11434"):
        # Explicitly initialize with llama3:latest as requested
        self.host = host.rstrip('/')
        self.client = OllamaClient(host=self.host, model="llama3:latest")
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        return """You are a Task Planner for a System Automation Assistant.
Your responsibility is to convert a complex user goal into a simple, sequential JSON array of individual executable tasks.
You must break down multi-step commands into single distinct actions.

CRITICAL RULES:
1. You must return ONLY a valid JSON array of strings.
2. Do not include any explanations, conversational text, or markdown formatting (like ```json).
3. If the input is already a single task, return an array with one element.
4. Keep the tasks in natural language, but simplify them to clear commands.

VALID:
[
"open steam",
"open discord"
]

INVALID:
{
"open steam":"",
"open discord":""
}

Examples:

Input: "Open Steam and Discord"
Output: [
"open steam",
"open discord"
]

Input: "Open Edge and take screenshot"
Output: [
"open edge",
"take screenshot"
]

Input: "Launch VS Code, open Discord and search ChatGPT"
Output: [
"launch vscode",
"open discord",
"search chatgpt"
]

Input: "Mute the volume and turn off screen"
Output: [
"mute volume",
"turn off screen"
]

Input: "Create folder work and open notepad"
Output: [
"create folder work",
"open notepad"
]

Input: "Close spotify and increase volume"
Output: [
"close spotify",
"increase volume"
]

Input: "Take a screenshot, save it, and open paint"
Output: [
"take screenshot",
"save screenshot",
"open paint"
]

Input: "Search for weather and open browser"
Output: [
"search weather",
"open browser"
]

Input: "Empty recycle bin and shutdown"
Output: [
"empty recycle bin",
"shutdown"
]

Input: "Open calculator"
Output: [
"open calculator"
]

Input: "Kill python process and launch word"
Output: [
"kill python",
"launch word"
]

Input: "Google python tutorials"
Output: [
"search python tutorials"
]

Input: "Stop music and open discord"
Output: [
"stop music",
"open discord"
]

Input: "Make directory projects and navigate to it"
Output: [
"create directory projects",
"navigate to projects"
]

Input: "Lock computer"
Output: [
"lock computer"
]

Input: "Fire up browser and go to youtube"
Output: [
"open browser",
"go to youtube"
]

Input: "Terminate excel and open notepad"
Output: [
"terminate excel",
"open notepad"
]

Input: "Capture screen"
Output: [
"take screenshot"
]

Input: "Pause video and increase volume to 50"
Output: [
"pause video",
"set volume to 50"
]

Input: "Run updates and restart computer"
Output: [
"run updates",
"restart computer"
]
"""

    def plan_tasks(self, user_input: str) -> List[str]:
        """
        Converts a user goal into a JSON list of executable tasks.
        
        Args:
            user_input: The natural language command from the user.
            
        Returns:
            A list of strings, where each string is a single distinct task.
        """
        prompt = f'Input: "{user_input}"\nOutput:'
        
        for attempt in range(2):
            try:
                # We use force_json=False because Llama3 handles raw arrays better without format restrictions
                result = self.client.generate(prompt=prompt, system=self.system_prompt, force_json=False)
                
                if isinstance(result, list):
                    tasks = [str(task) for task in result]
                    logger.info(f"TaskPlanner successfully generated {len(tasks)} tasks.")
                    return tasks
                elif isinstance(result, dict):
                    logger.error(f"TaskPlanner attempt {attempt+1}: Received JSON object instead of array. Retrying...")
                    continue
                else:
                    logger.warning(f"TaskPlanner attempt {attempt+1}: Unexpected response format {type(result)}. Retrying...")
                    
            except Exception as e:
                logger.error(f"Failed to plan tasks on attempt {attempt+1} due to an exception: {e}", exc_info=True)
                
        logger.error("TaskPlanner failed completely after 2 attempts.")
        return []
