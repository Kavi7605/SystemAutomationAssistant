import sys
import logging
import json
from src.llm.ollama_client import OllamaClient
from src.core.command_parser import CommandParser

from src.utils.logger import setup_logger
from src.automation.executor import Executor

logger = setup_logger("system_assistant")

def main():
    print("Initializing System Automation Assistant...")
    
    try:
        # 1. Create Ollama client connecting to localhost:11434 with gemma3:4b
        client = OllamaClient(host="http://localhost:11434", model="gemma3:4b")
        
        # 2. Initialize Command Parser
        parser = CommandParser(client=client)
        
        # 3. Initialize Executor
        executor = Executor()
        
        print("Assistant ready! Type 'exit' or 'quit' to stop.")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("\nEnter command: ").strip()
                
                if user_input.lower() in ['exit', 'quit']:
                    print("Exiting...")
                    break
                    
                if not user_input:
                    continue
                    
                print("Parsing command...")
                result = parser.parse_command(user_input)
                
                if result:
                    print("\nGenerated JSON:")
                    print(json.dumps(result, indent=4))
                    
                    print("\nExecuting command...")
                    exec_result = executor.execute(result)
                    
                    print("\nExecution Result:")
                    if exec_result.get("status") == "success":
                        print(f"✓ {exec_result.get('message')}")
                    else:
                        print(f"✗ Failed: {exec_result.get('message')}")
                else:
                    print("\nFailed to generate a valid JSON command. Please check the logs.")
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                break
                
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
