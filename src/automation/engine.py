import logging
from typing import Optional

from src.core.command_parser import CommandParser
from src.core.history_manager import HistoryManager
from src.planner.resolver import CommandResolver
from src.planner.task_planner import TaskPlanner
from src.automation.executor import Executor

logger = logging.getLogger(__name__)

class AutomationEngine:
    """
    Core engine that drives the interactive CLI loop.
    It encapsulates the Task Planner, Command Parser, Resolver, and Executor.
    """
    def __init__(self, 
                 parser: CommandParser, 
                 resolver: CommandResolver, 
                 task_planner: TaskPlanner, 
                 executor: Executor, 
                 history_manager: HistoryManager):
        self.parser = parser
        self.resolver = resolver
        self.task_planner = task_planner
        self.executor = executor
        self.history_manager = history_manager

    def start(self):
        """Starts the interactive CLI loop."""
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
                
                self.process_command(user_input)
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
                print(f"\nAn unexpected error occurred: {e}. Please try again.")

    def process_command(self, user_input: str):
        """Processes a single natural language command through the entire pipeline."""
        logger.info(f"User goal: {user_input}")
            
        print("\nPlanning tasks...")
        tasks = self.task_planner.plan_tasks(user_input)
        
        if not tasks:
            logger.warning("Planner failed completely. Falling back to single-task mode.")
            tasks = [user_input]
        else:
            logger.info(f"Generated plan: {tasks}")
            print("\nGenerated Plan:\n")
            for i, task in enumerate(tasks, 1):
                print(f"{i}. {task}")
                
        parsed_commands = []
        for task in tasks:
            print(f"\nParsing command: {task}")
            parsed_json = self.parser.parse_command(task)
            
            if parsed_json:
                resolved_json = self.resolver.resolve(parsed_json)
                if isinstance(resolved_json, list):
                    parsed_commands.extend(resolved_json)
                else:
                    parsed_commands.append(resolved_json)
            else:
                print(f"Failed to parse task: {task}")
        
        if not parsed_commands:
            print("\nFailed to generate any valid JSON commands. Please check the logs.")
            return
            
        print("\nExecuting command(s)...")
        if len(parsed_commands) == 1:
            exec_result = self.executor.execute(parsed_commands[0])
        else:
            exec_result = self.executor.execute(parsed_commands)
            
        logger.info(f"Execution results: {exec_result}")
        
        # Record history
        self.history_manager.add_entry(
            user_command=user_input,
            generated_plan=tasks,
            generated_json=parsed_commands,
            resolved_json=parsed_commands,
            execution_result=exec_result
        )
        
        print("\nExecution Result:")
        if exec_result.get("status") == "success":
            print(f"✓ {exec_result.get('message')}")
        elif exec_result.get("status") == "completed":
            print("\nExecution Summary:")
            print(f"Successful: {exec_result.get('successful')}")
            print(f"Failed: {exec_result.get('failed')}")
        else:
            print(f"✗ Failed: {exec_result.get('message')}")
