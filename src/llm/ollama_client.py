import requests
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class OllamaClient:
    """
    Client for interacting with a local Ollama instance.
    """
    def __init__(self, host: str = "http://localhost:11434", model: str = "gemma3:4b"):
        self.host = host.rstrip('/')
        self.model = model
        self.api_url = f"{self.host}/api/generate"

    def generate(self, prompt: str, system: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Sends a request to the Ollama API to generate a response based on the prompt.
        Expects a JSON response.
        
        Args:
            prompt: The user input or specific instruction.
            system: Optional system prompt to set the context and behavior.
            
        Returns:
            A parsed JSON dictionary, or None if the request/parsing fails.
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json"  # Enforce JSON output at the API level
        }
        
        if system:
            payload["system"] = system

        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            response_text = result.get("response", "")
            
            # Clean up potential markdown formatting that some models add despite prompt instructions
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            elif response_text.startswith("```"):
                response_text = response_text[3:]
            
            if response_text.endswith("```"):
                response_text = response_text[:-3]
                
            response_text = response_text.strip()
            
            try:
                parsed_json = json.loads(response_text)
                return parsed_json
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from response. Response text: {response_text}. Error: {e}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with Ollama API at {self.api_url}: {e}")
            return None
