import json
import logging
from typing import Dict, Any, Optional

from src.core.memory import MemoryManager
from src.tools.registry import ToolRegistry
from src.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class Agent:
    """
    The reasoning engine that uses the LLM to process user requests, 
    decide on tool usage, and maintain a multi-step loop.
    """
    def __init__(self, llm_client: OllamaClient, memory: MemoryManager, tool_registry: ToolRegistry):
        self.llm = llm_client
        self.memory = memory
        self.registry = tool_registry
        self.max_steps = 5

    def _build_system_prompt(self) -> str:
        tools_schema = json.dumps(self.registry.get_all_schemas(), indent=2)
        
        return f"""You are a helpful, intelligent System Automation Assistant.
You have access to the following tools:
{tools_schema}

You operate in a loop of Thought, Action, and Observation.
At each step, you must output strictly valid JSON in one of the two formats below.

Format 1 - Use a Tool:
{{
    "thought": "Explain why you are taking this action",
    "action": "tool_name",
    "parameters": {{"key": "value"}}
}}

Format 2 - Final Answer or Asking the User:
{{
    "thought": "Explain your reasoning",
    "response": "The text to show to the user"
}}

IMPORTANT RULES:
1. ONLY return JSON. Do not include markdown code blocks (like ```json).
2. If you need information from the user (like what to name a folder), use Format 2 to ask them.
3. If you have completed the request, use Format 2 to tell the user what you did.
"""

    def run(self, user_input: str) -> str:
        """
        Runs the ReAct loop for a single user input.
        """
        self.memory.add_message("user", user_input)
        
        system_prompt = self._build_system_prompt()
        
        for step in range(self.max_steps):
            logger.info(f"Agent loop step {step + 1}/{self.max_steps}")
            
            context_string = self.memory.get_context_string()
            prompt = f"Conversation History:\n{context_string}\n\nWhat is your next action?"
            
            try:
                # Expecting JSON dict back from llm client generate
                response_json = self.llm.generate(prompt=prompt, system=system_prompt)
                
                if not response_json:
                    return "Error: Failed to generate a response from the LLM."
                    
                # Add assistant thought to memory for tracing (optional, but good for context)
                # self.memory.add_message("assistant", json.dumps(response_json))
                
                if "response" in response_json:
                    final_answer = response_json["response"]
                    self.memory.add_message("assistant", final_answer)
                    return final_answer
                    
                if "action" in response_json:
                    action_name = response_json["action"]
                    parameters = response_json.get("parameters", {})
                    
                    logger.info(f"Agent decided to execute tool: {action_name} with params: {parameters}")
                    
                    # Execute tool
                    tool_result = self.registry.execute_tool(action_name, **parameters)
                    
                    # Add observation to memory
                    observation = f"Tool '{action_name}' returned: {json.dumps(tool_result)}"
                    self.memory.add_message("tool", observation)
                    
                else:
                    return "Error: LLM returned invalid format (neither response nor action)."
                    
            except Exception as e:
                logger.error(f"Error in agent loop: {e}", exc_info=True)
                return f"An internal error occurred: {str(e)}"
                
        return "Error: Agent reached maximum steps without finding a final answer."
