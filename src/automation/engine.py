import logging
import re
from typing import Dict, Any, List, Optional

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

    def get_history(self) -> List[Dict[str, Any]]:
        return self.history_manager.get_history()

    def _route_semantic_command(self, user_input_lower: str) -> Optional[Dict[str, Any]]:
        # 1. Domain Name Routing
        domain_match = re.match(r"^open\s+([\w\-]+\.(?:com|org|net|io|ai|dev|app))$", user_input_lower)
        if domain_match:
            domain = domain_match.group(1)
            return {
                "action": "open_url",
                "parameters": {"url": f"https://{domain}"}
            }
            
        # 2. Website & Search Routing
        from src.core.website_registry import WEBSITE_REGISTRY
        from src.core.url_builder import build_search_url, build_base_url
        
        website_match = re.match(r"^open\s+(.+?)\s+website(?:\s+(?:and\s+)?(?:search\s+)?(.+))?$", user_input_lower)
        if website_match:
            site_key_candidate = website_match.group(1).strip()
            query = website_match.group(2)
            
            if site_key_candidate in WEBSITE_REGISTRY:
                if query:
                    search_url = build_search_url(site_key_candidate, query)
                    return {
                        "action": "open_url",
                        "parameters": {"url": search_url}
                    }
                else:
                    base_url = build_base_url(site_key_candidate)
                    return {
                        "action": "open_url",
                        "parameters": {"url": base_url}
                    }
                    
        # 3. Application vs Website Routing
        app_match = re.match(r"^open\s+(.+)$", user_input_lower)
        if app_match:
            alias = app_match.group(1).strip()
            
            for site_key, site_info in WEBSITE_REGISTRY.items():
                if alias in site_info.get("application_aliases", []):
                    return {
                        "action": "open_application",
                        "parameters": {
                            "application_name": alias,
                            "fallback_url": site_info.get("website")
                        }
                    }
                    
        # 4. File Creation Misclassification
        create_file_match = re.match(r"^create\s+([\w\-\.]+\.(?:txt|docx|pdf|py|java|js|json|csv|md))(?:\s+(?:in|inside)\s+(.+))?$", user_input_lower)
        if create_file_match:
            file_name = create_file_match.group(1)
            path = create_file_match.group(2)
            parsed = {
                "action": "create_file",
                "parameters": {"file_name": file_name}
            }
            if path:
                parsed["parameters"]["path"] = path.strip()
            return parsed
            
        return None

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

    def process_command(self, user_input: str) -> None:
        """
        Main entry point for processing a natural language command.
        """
        logger.info(f"--- New Command Received ---")
        logger.info(f"User Input: {user_input}")
        
        user_input_lower = user_input.lower().strip()
        
        # 1. Check for deterministic semantic routing
        semantic_json = self._route_semantic_command(user_input_lower)
        if semantic_json:
            logger.info("Router matched deterministic semantic pattern. Bypassing TaskPlanner and CommandParser.")
            parsed_commands = [semantic_json]
            tasks = [user_input]
            logger.info("Bypassing TaskPlanner for deterministic semantic operation.")
            self._execute_parsed_commands(user_input, tasks, parsed_commands)
            return
        
        filesystem_keywords = [
            "create file", "create folder", "open folder", "open file",
            "delete file", "delete folder", "move file",
            "move folder", "copy file", "copy folder",
            "rename file", "rename folder"
        ]
        
        # Check standard keywords
        is_filesystem_command = any(user_input_lower.startswith(kw) for kw in filesystem_keywords)
        
        # Check specific Pattern 1: create <filename.ext>
        if not is_filesystem_command:
            # Matches 'create ' followed by a word with a dot and an extension
            if re.match(r"^create\s+[\w\-\.]+\.[a-z0-9]+\b", user_input_lower):
                is_filesystem_command = True
                logger.info("Router matched filesystem pattern:\ncreate <filename.ext>")
            # Matches 'open ' followed by a word with a dot and an extension
            elif re.match(r"^open\s+[\w\-\.]+\.[a-z0-9]+\b", user_input_lower):
                is_filesystem_command = True
                logger.info("Router matched filesystem pattern:\nopen <filename.ext>")
                
        # Must not be a multi-step operation combined with 'and'
        if is_filesystem_command and " and " in user_input_lower:
            is_filesystem_command = False
            
        logger.info(f"Router Decision:\nFilesystem Command = {is_filesystem_command}")
        logger.info(f"TaskPlanner skipped:\n{is_filesystem_command}")
            
        if is_filesystem_command:
            tasks = [user_input]
            logger.info("Bypassing TaskPlanner for filesystem operation.")
        else:
            tasks = self.task_planner.plan_tasks(user_input)
            
            if not tasks:
                logger.warning("Planner failed completely. Falling back to single-task mode.")
                tasks = [user_input]
            else:
                logger.info(f"Generated plan: {tasks}")
                for i, task in enumerate(tasks, 1):
                    logger.info(f"Plan Step {i}: {task}")
                
        parsed_commands = []
        for task in tasks:
            logger.info(f"Parsing command: {task}")
            
            # Direct parser bypass for Open File operations
            open_file_match = re.match(r"^open\s+(?:file\s+)?([\w\-\.]+\.[a-zA-Z0-9]+)(?:\s+(?:in|inside)\s+(.+))?\s*$", task, re.IGNORECASE)
            
            if open_file_match:
                logger.info("Router matched open file operation, bypassing CommandParser.")
                file_name = open_file_match.group(1)
                path = open_file_match.group(2)
                
                parsed_json = {
                    "action": "open_file",
                    "parameters": {
                        "file_name": file_name
                    }
                }
                if path:
                    parsed_json["parameters"]["path"] = path.strip()
                    
                logger.info(f"Router Direct Output:\n{parsed_json}")
            else:
                logger.info(f"CommandParser Input:\n{task}")
                parsed_json = self.parser.parse_command(task)
                logger.info(f"CommandParser Output:\n{parsed_json}")
            
            if parsed_json:
                resolved_json = self.resolver.resolve(parsed_json)
                if isinstance(resolved_json, list):
                    parsed_commands.extend(resolved_json)
                else:
                    parsed_commands.append(resolved_json)
            else:
                logger.error(f"Failed to parse task: {task}")
        
        self._execute_parsed_commands(user_input, tasks, parsed_commands)

    def _execute_parsed_commands(self, user_input: str, tasks: list, parsed_commands: list) -> None:
        if not parsed_commands:
            logger.error("Failed to generate any valid JSON commands. Please check the logs.")
            return
            
        logger.info("Executing command(s)...")
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
        
        logger.info("Execution Result:")
        if exec_result.get("status") == "success":
            logger.info(f"[OK] {exec_result.get('message')}")
        elif exec_result.get("status") == "completed":
            logger.info("Execution Summary:")
            logger.info(f"Successful: {exec_result.get('successful')}")
            logger.info(f"Failed: {exec_result.get('failed')}")
        else:
            logger.error(f"[FAIL] Failed: {exec_result.get('message')}")
