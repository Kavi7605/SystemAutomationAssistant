import logging
import re
from typing import Dict, Any, List, Optional, Union

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

    SEQUENCE_SEPARATORS = [
        r"\band\b",
        r"\bthen\b",
        ","
    ]

    def _normalize_app_chains(self, command: str) -> str:
        """
        Rewrites application chains like 'open discord and whatsapp and steam' 
        to 'open discord and open whatsapp and open steam'.
        """
        separator_pattern = "|".join(self.SEQUENCE_SEPARATORS)
        regex = rf'\s*(?:{separator_pattern})\s*'
        
        type_match = re.search(rf'\s*(?:{separator_pattern})\s*(type\s+|write\s+)', command, flags=re.IGNORECASE)
        type_suffix = ""
        if type_match:
            idx = type_match.start(1)
            type_suffix = command[idx:]
            command = command[:type_match.start()]
            
        if not command.strip():
            return type_suffix
            
        parts = re.split(regex, command, flags=re.IGNORECASE)
        action_verbs = ("open ", "close ", "create ", "delete ", "move ", "copy ", "rename ", "search ", "wait ", "click", "double click", "right click", "type ", "write ", "press ", "scroll ")
        
        normalized_parts = []
        carry_over = None
        
        for part in parts:
            part_lower = part.strip().lower()
            if not part_lower:
                continue
                
            starts_with_verb = any(part_lower.startswith(v) for v in action_verbs)
            
            if starts_with_verb:
                normalized_parts.append(part.strip())
                if part_lower.startswith("open "):
                    carry_over = "open "
                elif part_lower.startswith("close "):
                    carry_over = "close "
                else:
                    carry_over = None
            else:
                if carry_over:
                    normalized_parts.append(f"{carry_over}{part.strip()}")
                else:
                    normalized_parts.append(part.strip())
                    carry_over = None
                    
        normalized_cmd = " and ".join(normalized_parts)
        if type_suffix:
            normalized_cmd += " and " + type_suffix
            
        return normalized_cmd

    def _expand_multi_actions(self, command: str) -> list[str]:
        """Splits deterministic action chains into individual tasks."""
        if command.lower().startswith("type ") or command.lower().startswith("write "):
            return [command]
            
        separator_pattern = "|".join(self.SEQUENCE_SEPARATORS)
        type_match = re.search(rf'\s*(?:{separator_pattern})\s*(type\s+|write\s+)', command, flags=re.IGNORECASE)
        
        type_task = None
        if type_match:
            type_task = command[type_match.start(1):].strip()
            command = command[:type_match.start()].strip()
            
        if not command:
            return [type_task] if type_task else []
            
        regex = rf'\s*(?:{separator_pattern})\s*'
        parts = [p.strip() for p in re.split(regex, command, flags=re.IGNORECASE) if p.strip()]
        
        if type_task:
            parts.append(type_task)
            
        return parts

    def _classify_target(self, target: str) -> Dict[str, Any]:
        """
        Classifies a target into Website, Application, or SearchWeb using the exact approved hierarchy.
        """
        target = target.strip()
        
        # Rule 1: Explicit Website
        if target.endswith(" website"):
            base_name = target[:-8].strip()
            from src.core.url_builder import build_base_url
            url = build_base_url(base_name) or f"https://{base_name}.com"
            return {"action": "open_url", "parameters": {"url": url}}

        # Rule 2: Installed Application
        from src.tools.application_finder import ApplicationFinder
        app_finder = ApplicationFinder()
        if app_finder.find_application(target):
            return {"action": "open_application", "parameters": {"application_name": target}}

        # Rule 3: Website Registry Entry
        from src.core.website_registry import WEBSITE_REGISTRY
        if target in WEBSITE_REGISTRY:
            from src.core.url_builder import build_base_url
            url = build_base_url(target)
            return {"action": "open_url", "parameters": {"url": url}}

        # Rule 4: Unknown Target
        return {"action": "search_web", "parameters": {"query": target}}

    def _extract_query_and_mode(self, site_key: str, full_query: str) -> tuple[str, Optional[str]]:
        from src.core.website_registry import WEBSITE_REGISTRY
        site_info = WEBSITE_REGISTRY.get(site_key.lower(), {})
        valid_modes = site_info.get("search_modes", [])
        
        # Exact match (query is JUST the mode)
        for mode in valid_modes:
            if full_query.lower() == mode.lower():
                return "", mode.lower()
                
        # Suffix match
        valid_modes_sorted = sorted(valid_modes, key=len, reverse=True)
        for mode in valid_modes_sorted:
            if full_query.lower().endswith(f" {mode.lower()}"):
                query = full_query[:-len(mode)-1].strip()
                return query, mode.lower()
                
        return full_query, None

    def _route_semantic_command(self, user_input_lower: str) -> Optional[Dict[str, Any] | List[Dict[str, Any]]]:
        from src.core.website_registry import WEBSITE_REGISTRY
        from src.core.url_builder import build_search_url, build_base_url
        
        # 0. Desktop Interaction Toolkit Routing
        # click [x y]
        click_match = re.match(r"^click(?:\s+(\d+)\s+(\d+))?$", user_input_lower)
        if click_match:
            params = {}
            if click_match.group(1) and click_match.group(2):
                params["x"] = int(click_match.group(1))
                params["y"] = int(click_match.group(2))
            return {"action": "click", "parameters": params}

        # double click [x y]
        double_click_match = re.match(r"^double\s+click(?:\s+(\d+)\s+(\d+))?$", user_input_lower)
        if double_click_match:
            params = {}
            if double_click_match.group(1) and double_click_match.group(2):
                params["x"] = int(double_click_match.group(1))
                params["y"] = int(double_click_match.group(2))
            return {"action": "double_click", "parameters": params}

        # right click [x y]
        right_click_match = re.match(r"^right\s+click(?:\s+(\d+)\s+(\d+))?$", user_input_lower)
        if right_click_match:
            params = {}
            if right_click_match.group(1) and right_click_match.group(2):
                params["x"] = int(right_click_match.group(1))
                params["y"] = int(right_click_match.group(2))
            return {"action": "right_click", "parameters": params}

        # type / write <text>
        type_match = re.match(r"^(?:type|write)\s+(.+)$", user_input_lower)
        if type_match:
            return {"action": "type_text", "parameters": {"text": type_match.group(1)}}

        # press <keys>
        press_match = re.match(r"^press\s+(.+)$", user_input_lower)
        if press_match:
            keys = press_match.group(1).split()
            return {"action": "hotkey", "parameters": {"keys": keys}}

        # scroll down / up
        scroll_match = re.match(r"^scroll\s+(down|up)$", user_input_lower)
        if scroll_match:
            return {"action": "scroll", "parameters": {"direction": scroll_match.group(1)}}

        # move mouse [to] <x> <y>
        move_match = re.match(r"^move\s+mouse(?:\s+to)?\s+(\d+)\s+(\d+)$", user_input_lower)
        if move_match:
            return {"action": "move_mouse", "parameters": {"x": int(move_match.group(1)), "y": int(move_match.group(2))}}
        
        # 1.0 Search Intent Bypass
        search_intent_match = re.match(r"^open\s+(.+?)\s+and\s+search(?:\s+for)?\s+(.+)$", user_input_lower)
        if search_intent_match:
            site_key_candidate = search_intent_match.group(1).strip()
            full_query = search_intent_match.group(2).strip()
            
            if site_key_candidate.endswith(" website"):
                site_key_candidate = site_key_candidate[:-8].strip()
                
            query, mode = self._extract_query_and_mode(site_key_candidate, full_query)
            search_url = build_search_url(site_key_candidate, query, mode)
            if search_url:
                return {"action": "open_url", "parameters": {"url": search_url}}
                
        # The old multi-match block has been removed to rely completely on the Multi-Action Sequencer
        # This allows mixed deterministic/non-deterministic sequences to properly fall through to the planner.

        # 2. Website & Search Routing (Normalizations)
        website_match = re.match(r"^open\s+(.+?)\s+website(?:\s+(.*))?$", user_input_lower)
        if website_match:
            site_key_candidate = website_match.group(1).strip()
            remainder = website_match.group(2)
            
            if not remainder:
                url = build_base_url(site_key_candidate) or f"https://{site_key_candidate}.com"
                return {"action": "open_url", "parameters": {"url": url}}
                
            remainder = remainder.strip()
            
            if remainder.startswith("and search for "):
                full_query = remainder[15:].strip()
            elif remainder.startswith("and search "):
                full_query = remainder[11:].strip()
            elif remainder.startswith("search for "):
                full_query = remainder[11:].strip()
            elif remainder.startswith("search "):
                full_query = remainder[7:].strip()
            else:
                full_query = remainder
                
            query, mode = self._extract_query_and_mode(site_key_candidate, full_query)
                
            # Validation: Missing query
            if not query and not mode:
                return {
                    "action": "unsupported",
                    "parameters": {"message": "Validation error: Search query is missing."}
                }
            elif not query and mode:
                return {
                    "action": "unsupported",
                    "parameters": {
                        "message": f"Validation error:\nSearch query is missing before search mode '{mode}'."
                    }
                }
                    
            search_url = build_search_url(site_key_candidate, query, mode)
            if not search_url:
                search_url = f"https://{site_key_candidate}.com"
            return {"action": "open_url", "parameters": {"url": search_url}}

        # 3. Domain Name Routing
        domain_match = re.match(r"^open\s+([\w\-]+\.(?:com|org|net|io|ai|dev|app))$", user_input_lower)
        if domain_match:
            domain = domain_match.group(1)
            return {
                "action": "open_url",
                "parameters": {"url": f"https://{domain}"}
            }

        # 4. Open Folder Routing (Grammar A & B)
        # Grammar A: open <name> folder [in <path>]
        open_folder_suffix_match = re.match(r"^open\s+(.+?)\s+(?:folder|directory)(?:\s+(?:in|inside)\s+(.+))?$", user_input_lower)
        if open_folder_suffix_match:
            folder_name = open_folder_suffix_match.group(1).strip()
            path = open_folder_suffix_match.group(2)
            parsed = {"action": "open_folder", "parameters": {"folder_name": folder_name}}
            if path: parsed["parameters"]["base_path"] = path.strip()
            return parsed

        # Grammar B: open folder <name> [in <path>]
        open_folder_prefix_match = re.match(r"^open\s+(?:folder|directory)\s+(.+?)(?:\s+(?:in|inside)\s+(.+))?$", user_input_lower)
        if open_folder_prefix_match:
            folder_name = open_folder_prefix_match.group(1).strip()
            path = open_folder_prefix_match.group(2)
            parsed = {"action": "open_folder", "parameters": {"folder_name": folder_name}}
            if path: parsed["parameters"]["base_path"] = path.strip()
            return parsed

        # 5. Close Application
        close_match = re.match(r"^close\s+(.+)$", user_input_lower)
        if close_match:
            app_name = close_match.group(1).strip()
            if " and " in app_name: return None
            return {"action": "close_application", "parameters": {"application_name": app_name}}

        # 6. Create Folder
        create_folder_match = re.match(r"^create\s+folder\s+(.+)$", user_input_lower)
        if create_folder_match:
            return {"action": "create_folder", "parameters": {"folder_name": create_folder_match.group(1).strip()}}

        # 7. Open File
        open_file_match = re.match(r"^open\s+(?:file\s+)?([\w\-\.]+\.[a-zA-Z0-9]+)(?:\s+file)?(?:\s+(?:in|inside)\s+(.+))?\s*$", user_input_lower, re.IGNORECASE)
        if open_file_match:
            file_name = open_file_match.group(1)
            path = open_file_match.group(2)
            parsed = {"action": "open_file", "parameters": {"file_name": file_name}}
            if path: parsed["parameters"]["path"] = path.strip()
            return parsed

        # 8. Create File
        create_file_match = re.match(r"^create\s+([\w\-\.]+\.(?:txt|docx|pdf|py|java|js|json|csv|md))(?:\s+(?:in|inside)\s+(.+))?$", user_input_lower)
        if create_file_match:
            file_name = create_file_match.group(1)
            path = create_file_match.group(2)
            parsed = {"action": "create_file", "parameters": {"file_name": file_name}}
            if path: parsed["parameters"]["path"] = path.strip()
            return parsed

        # 9. General 'open' target classification
        app_match = re.match(r"^open\s+(.+)$", user_input_lower)
        if app_match:
            target = app_match.group(1).strip()
            if " and " in target: return None
            return self._classify_target(target)
            
        return None

    def start(self):
        """Starts the interactive CLI loop."""
        print("Assistant ready! Type 'exit' or 'quit' to stop.")
        print("-" * 50)
        
        voice_listener = None
        
        while True:
            try:
                print("\n[T] Type Command | [V] Voice Command | [Q] Quit")
                mode = input("Select mode: ").strip().upper()
                
                if mode in ['Q', 'QUIT', 'EXIT']:
                    print("Exiting...")
                    break
                elif mode == 'V':
                    if not voice_listener:
                        try:
                            from src.voice.voice_listener import VoiceListener
                            voice_listener = VoiceListener()
                        except FileNotFoundError as e:
                            print(f"\nVoice initialization failed: {e}")
                            continue
                            
                    result = voice_listener.listen()
                    if not result or not result.get("transcript"):
                        print("\nNo speech detected.")
                        continue
                        
                    transcript = result["transcript"]
                    model_used = result.get("model", "unknown")
                    device_used = result.get("device", "unknown")
                    duration = result.get("duration", 0)
                    
                    print(f"\nRaw Transcript:\n{transcript}\n")
                    
                    logger.info("Voice Engine: Faster-Whisper")
                    logger.info(f"Model: {model_used}")
                    logger.info(f"Device: {device_used}")
                    logger.info(f"Recognition Time: {duration}s")
                    logger.info(f"Transcript: {transcript}")
                    
                    proceed = input("Proceed? [Y/N]: ").strip().upper()
                    if proceed == 'Y':
                        print("Executing...")
                        self.process_command(transcript, source="voice")
                    else:
                        print("Command cancelled.")
                        continue
                elif mode == 'T':
                    user_input = input("Enter command: ").strip()
                    if user_input.lower() in ['exit', 'quit']:
                        print("Exiting...")
                        break
                    if not user_input:
                        continue
                    self.process_command(user_input, source="keyboard")
                else:
                    # Fallback for old behavior if user directly types the command
                    user_input = mode
                    if user_input.lower() in ['exit', 'quit']:
                        print("Exiting...")
                        break
                    if not user_input:
                        continue
                    self.process_command(user_input, source="keyboard")
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
                print(f"\nAn unexpected error occurred: {e}. Please try again.")

    def process_command(self, user_input: str, source: str = "keyboard") -> None:
        """
        Main entry point for processing a natural language command.
        """
        logger.info(f"--- New Command Received ---")
        logger.info(f"User Input: {user_input}")
        
        user_input_lower = user_input.lower().strip()
                
        # 0. Deterministic Multi-Action Sequencing
        normalized_input = self._normalize_app_chains(user_input_lower)
        expanded_tasks = self._expand_multi_actions(normalized_input)
        
        if len(expanded_tasks) > 1:
            all_deterministic = True
            parsed_commands = []
            
            for task in expanded_tasks:
                semantic_json = self._route_semantic_command(task)
                if not semantic_json:
                    all_deterministic = False
                    break
                    
                if isinstance(semantic_json, list):
                    parsed_commands.extend(semantic_json)
                else:
                    parsed_commands.append(semantic_json)
                    
            if all_deterministic:
                logger.info("Multi-action detected.")
                logger.info(f"Expanded into {len(expanded_tasks)} tasks.")
                for i, task in enumerate(expanded_tasks, 1):
                    logger.info(f"Sequence Task {i}: {task}")
                logger.info("Executing deterministic sequence.")
                self._execute_parsed_commands(user_input, expanded_tasks, parsed_commands, source)
                return

        # 1. Check for deterministic semantic routing
        semantic_json = self._route_semantic_command(user_input_lower)
        if semantic_json:
            logger.info("Router matched deterministic semantic pattern. Bypassing TaskPlanner and CommandParser.")
            
            if isinstance(semantic_json, list):
                parsed_commands = semantic_json
                tasks = [user_input]
            else:
                parsed_commands = [semantic_json]
                tasks = [user_input]
                
            logger.info("Bypassing TaskPlanner for deterministic semantic operation.")
            self._execute_parsed_commands(user_input, tasks, parsed_commands, source)
            return
        
        filesystem_keywords = [
            "create file", "create folder", "open folder", "open file",
            "delete file", "delete folder", "move file",
            "move folder", "copy file", "copy folder",
            "rename file", "rename folder"
        ]
        
        is_filesystem_command = any(user_input_lower.startswith(kw) for kw in filesystem_keywords)
        
        if not is_filesystem_command:
            if re.match(r"^create\s+[\w\-\.]+\.[a-z0-9]+\b", user_input_lower):
                is_filesystem_command = True
                logger.info("Router matched filesystem pattern:\ncreate <filename.ext>")
            elif re.match(r"^open\s+[\w\-\.]+\.[a-z0-9]+\b", user_input_lower):
                is_filesystem_command = True
                logger.info("Router matched filesystem pattern:\nopen <filename.ext>")
                
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
            
            # Check if router can handle the individual task natively
            semantic_json = self._route_semantic_command(task.lower())
            if semantic_json:
                logger.info("Router matched individual task natively, bypassing CommandParser.")
                if isinstance(semantic_json, list):
                    parsed_commands.extend(semantic_json)
                else:
                    parsed_commands.append(semantic_json)
                continue
            
            open_file_match = re.match(r"^open\s+(?:file\s+)?([\w\-\.]+\.[a-zA-Z0-9]+)(?:\s+file)?(?:\s+(?:in|inside)\s+(.+))?\s*$", task, re.IGNORECASE)
            
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
        
        self._execute_parsed_commands(user_input, tasks, parsed_commands, source)

    def _execute_parsed_commands(self, user_input: str, tasks: list, parsed_commands: list, source: str = "keyboard") -> None:
        if not parsed_commands:
            logger.error("Failed to generate any valid JSON commands. Please check the logs.")
            return
            
        logger.info("Executing command(s)...")
        if len(parsed_commands) == 1:
            exec_result = self.executor.execute(parsed_commands[0])
        else:
            exec_result = self.executor.execute(parsed_commands)
            
        logger.info(f"Execution results: {exec_result}")
        
        self.history_manager.add_entry(
            user_command=user_input,
            generated_plan=tasks,
            generated_json=parsed_commands,
            resolved_json=parsed_commands,
            execution_result=exec_result,
            source=source
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
