import sys
import logging
import json
from src.llm.ollama_client import OllamaClient
from src.core.command_parser import CommandParser
from src.core.history_manager import HistoryManager
from src.planner.resolver import CommandResolver
from src.automation.executor import Executor
from src.utils.logger import setup_logger
from src.tools.registry import ToolRegistry
from src.tools.application_finder import ApplicationFinder
from src.tools.system_tools import (
    OpenApplicationTool,
    CloseApplicationTool,
    TakeScreenshotTool,
    CreateFolderTool,
    SearchWebTool
)

logger = setup_logger("system_assistant")

def main():
    print("Initializing System Automation Assistant...")
    
    try:
        # 0. Initialize Foundations (Tool Registry & Application Finder)
        registry = ToolRegistry()
        app_finder = ApplicationFinder()
        
        # Register Tools
        registry.register(OpenApplicationTool(app_finder))
        registry.register(CloseApplicationTool())
        registry.register(TakeScreenshotTool())
        registry.register(CreateFolderTool())
        registry.register(SearchWebTool())
        
        # 1. Create Ollama client connecting to localhost:11434 with gemma3:4b
        client = OllamaClient(host="http://localhost:11434", model="gemma3:4b")
        
        # 2. Initialize Command Parser with dynamic tool registry
        parser = CommandParser(client=client, registry=registry)
        
        # 3. Initialize Planner Layer (Resolves vague entities)
        resolver = CommandResolver()
        
        # 4. Initialize Executor Engine (Executes system actions dynamically)
        executor = Executor(registry=registry)

        # 5. Initialize Command History Manager
        history_manager = HistoryManager()
        
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
                parsed_json = parser.parse_command(user_input)
                
                if parsed_json:
                    print("\nGenerated JSON (Raw):")
                    print(json.dumps(parsed_json, indent=4))
                    
                    print("\nPlanning / Resolving...")
                    resolved_json = resolver.resolve(parsed_json)
                    
                    if resolved_json != parsed_json:
                        print("Resolved JSON:")
                        print(json.dumps(resolved_json, indent=4))
                    
                    print("\nExecuting command...")
                    exec_result = executor.execute(resolved_json)
                    
                    # Record history
                    history_manager.add_entry(
                        user_command=user_input,
                        generated_json=parsed_json,
                        resolved_json=resolved_json,
                        execution_result=exec_result
                    )
                    
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
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
