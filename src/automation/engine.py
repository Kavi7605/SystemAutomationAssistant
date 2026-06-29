import logging
import re
from typing import Dict, Any, List, Optional

from src.core.command_parser import CommandParser
from src.core.history_manager import HistoryManager
from src.planner.resolver import CommandResolver
from src.planner.task_planner import TaskPlanner
from src.automation.executor import Executor
from src.context.context_manager import ContextManager
from src.context.reference_resolver import ReferenceResolver

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
                 history_manager: HistoryManager,
                 context_manager: ContextManager = None,
                 reference_resolver: ReferenceResolver = None,
                 nlp_preprocessor = None):
        self.parser = parser
        self.resolver = resolver
        self.task_planner = task_planner
        self.executor = executor
        self.history_manager = history_manager
        self.context_manager = context_manager
        self.reference_resolver = reference_resolver
        self.nlp_preprocessor = nlp_preprocessor
        
        from src.parser.parser_pipeline import ParserPipeline
        self.parser_pipeline = ParserPipeline()
        
        if self.reference_resolver:
            from src.automation.command_expander import CommandExpander
            self.command_expander = CommandExpander(self.reference_resolver)
        else:
            self.command_expander = None

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
        action_verbs = ("open ", "close ", "minimize ", "maximize ", "restore ", "create ", "delete ", "move ", "copy ", "rename ", "search ", "wait ", "pause ", "sleep ", "click", "double click", "right click", "type ", "write ", "press ", "scroll ", "focus ", "is ", "what ", "which ", "tell ")
        
        normalized_parts = []
        carry_over = None
        
        for part in parts:
            part_lower = part.strip().lower()
            if not part_lower:
                continue
                
            starts_with_verb = any(part_lower.startswith(v) for v in action_verbs)
            
            if starts_with_verb:
                normalized_parts.append(part.strip())
                carry_over = None
                for verb in ("open ", "close ", "minimize ", "maximize ", "restore "):
                    if part_lower.startswith(verb):
                        carry_over = verb
                        break
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
            
        protected_strings = []
        def repl(match):
            protected_strings.append(match.group(0))
            return f"__PROT_E_{len(protected_strings)-1}__"
            
        command = re.sub(r'\band\s+search\b', repl, command, flags=re.IGNORECASE)
            
        regex = rf'\s*(?:{separator_pattern})\s*'
        parts = [p.strip() for p in re.split(regex, command, flags=re.IGNORECASE) if p.strip()]
        
        final_parts = []
        for p in parts:
            for i, original in enumerate(protected_strings):
                ph = f"__PROT_E_{i}__"
                if ph in p:
                    p = p.replace(ph, original)
            final_parts.append(p)
        
        if type_task:
            final_parts.append(type_task)
            
        return final_parts

    def _classify_target(self, target: str) -> Dict[str, Any]:
        """
        Classifies a target into Website, Application, or SearchWeb using the exact approved hierarchy.
        """
        target = target.strip()
        
        from src.nlp.reference_normalizer import ReferenceNormalizer
        norm_target = ReferenceNormalizer().normalize(target.lower())
        
        # Rule 0: Reference Tokens
        is_ref = False
        if self.reference_resolver and hasattr(self.reference_resolver, 'is_reference'):
            is_ref = self.reference_resolver.is_reference(norm_target)
            
        if is_ref or norm_target in ["it", "that", "this", "previous app", "last app", "current app"]:
            return {"action": "open_application", "parameters": {"application_name": norm_target}}
            
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

    def _has_custom_path_intent(self, text: str) -> bool:
        """Detects if the user is trying to use custom locations not supported in Feature 9."""
        pattern = r"\s+(?:in|inside|into|under|to)\s+(?:the\s+)?(?:c\s+drive|d\s+drive|desktop|downloads|documents|home|root)\b"
        return bool(re.search(pattern, text, re.IGNORECASE))

    def _extract_type_hint(self, target: str) -> tuple[str, str]:
        """Extracts known document type aliases and returns the clean target and preferred extension."""
        target_lower = target.lower()
        hints = {
            "word document": ".docx",
            "word file": ".docx",
            "document": ".docx",
            "doc": ".docx",
            "docx": ".docx",
            "text file": ".txt",
            "text document": ".txt",
            "text": ".txt",
            "txt": ".txt",
            "pdf file": ".pdf",
            "pdf document": ".pdf",
            "pdf": ".pdf"
        }
        for hint, ext in hints.items():
            if target_lower.startswith(hint + " "):
                return target[len(hint)+1:].strip(), ext
            if target_lower.endswith(" " + hint):
                return target[:-len(hint)-1].strip(), ext
        return target, None

    def _route_semantic_command(self, user_input_mixed: str) -> Optional[Dict[str, Any] | List[Dict[str, Any]]]:
        from src.core.url_builder import build_search_url, build_base_url
        
        user_input_lower = user_input_mixed.lower().strip()
        user_input_clean = user_input_mixed.strip()
        
        # Check for path intent protection for filesystem commands
        fs_keywords = ["create", "make", "new", "move", "copy", "duplicate", "rename", "change", "delete", "remove"]
        if any(user_input_lower.startswith(kw + " ") for kw in fs_keywords) or any(user_input_lower == kw for kw in fs_keywords):
            if self._has_custom_path_intent(user_input_lower):
                return {"action": "reject_custom_path", "parameters": {}}

        
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

        # 0.5 Volume Controls Routing
        if user_input_lower in ["mute", "mute volume", "mute pc", "mute sound", "mute audio"]:
            return {"action": "mute_volume", "parameters": {}}
            
        if user_input_lower in ["unmute", "unmute volume", "unmute pc", "unmute sound", "unmute audio"]:
            return {"action": "unmute_volume", "parameters": {}}
            
        if user_input_lower in ["volume up", "sound up", "increase volume", "increase sound", "raise volume", "increase pc volume"]:
            return {"action": "increase_volume", "parameters": {}}
            
        if user_input_lower in ["volume down", "sound down", "decrease volume", "decrease sound", "lower volume", "decrease pc volume"]:
            return {"action": "decrease_volume", "parameters": {}}
            
        set_vol_match = re.match(r"^set\s+(?:pc\s+)?volume(?:\s+to)?\s+(\d+)(?:\s+percent|%)?$", user_input_lower)
        if set_vol_match:
            return {"action": "set_volume", "parameters": {"level": int(set_vol_match.group(1))}}
            
        if user_input_lower in ["volume status", "current volume", "what is my volume", "show volume"]:
            return {"action": "volume_status", "parameters": {}}

        # 0.6 Brightness Controls Routing
        if user_input_lower in ["brightness up", "increase brightness", "raise brightness"]:
            return {"action": "increase_brightness", "parameters": {}}
            
        if user_input_lower in ["brightness down", "decrease brightness", "lower brightness"]:
            return {"action": "decrease_brightness", "parameters": {}}
            
        set_bright_match = re.match(r"^set\s+(?:screen\s+)?brightness(?:\s+to)?\s+(\d+)(?:\s+percent|%)?$", user_input_lower)
        if set_bright_match:
            return {"action": "set_brightness", "parameters": {"level": int(set_bright_match.group(1))}}
            
        if user_input_lower in ["brightness status", "current brightness", "what is my brightness", "show brightness"]:
            return {"action": "brightness_status", "parameters": {}}

        # 0.6.5 Window Management Routing
        is_open_match = re.match(r"^is\s+(.+?)\s+(open|running|active)$", user_input_lower)
        if is_open_match:
            return {"action": "is_window_open", "parameters": {"window_name": is_open_match.group(1).strip()}}

        minimize_match = re.match(r"^minimize\s+(.+)$", user_input_lower)
        if minimize_match:
            return {"action": "minimize_window", "parameters": {"window_name": minimize_match.group(1).strip()}}
            
        maximize_match = re.match(r"^maximize\s+(.+)$", user_input_lower)
        if maximize_match:
            return {"action": "maximize_window", "parameters": {"window_name": maximize_match.group(1).strip()}}
            
        restore_match = re.match(r"^restore\s+(.+)$", user_input_lower)
        if restore_match:
            return {"action": "restore_window", "parameters": {"window_name": restore_match.group(1).strip()}}
            
        running_apps_aliases = [
            "list open windows", "show open windows", "focus open windows",
            "what windows are open", "window list",
            "show running apps", "list running apps", "focus running apps",
            "what apps are running", "running applications",
            "what applications are running", "what apps are open",
            "what applications are open", "list open applications", "list open apps",
            "focus open applications", "focus open apps"
        ]
        if user_input_lower in running_apps_aliases:
            user_input_lower = "list_running_apps"
            
        if user_input_lower == "list_running_apps":
            return {"action": "list_open_windows", "parameters": {}}
            
        focus_match = re.match(r"^(?:focus|switch to|bring|activate)\s+(.+?)(?:\s+to front)?$", user_input_lower)
        if focus_match:
            target = focus_match.group(1).strip()
            if target not in ["previous window", "performance mode", "silent mode", "turbo", "turbo mode", "balanced mode"]:
                return {"action": "focus_window", "parameters": {"window_name": target}}
                
        if user_input_lower == "focus previous window":
            return {"action": "focus_window", "parameters": {"window_name": "previous window"}}

        status_aliases = [
            "current window", "active window", "window status", 
            "show current window", "what window is active", "what app is active", 
            "what window is focused", "what is visible on screen", "what app is open", 
            "what application is open", "what window is open", "which app is open", 
            "which application is open", "which window is open", "tell me what app is open", 
            "tell me what window is open", "tell me which app is open"
        ]
        if user_input_lower in status_aliases:
            return {"action": "get_current_window", "parameters": {}}

        # 0.7 Display Controls Routing
        display_aliases = [
            "display status", "show display settings", "current display settings",
            "current resolution", "what is my resolution", "current refresh rate",
            "monitor count", "connected monitors", "display info", "monitor info",
            "primary monitor", "monitor status", "screen information"
        ]
        if user_input_lower in display_aliases:
            return {"action": "display_status", "parameters": {}}
        if user_input_lower == "wifi debug":
            return {"action": "wifi_debug", "parameters": {}}

        # 0.9.1 Unsupported Feature Routing
        unsupported_bluetooth_aliases = [
            "turn on bluetooth", "turn off bluetooth", 
            "turn on the bluetooth", "turn off the bluetooth",
            "bluetooth on", "bluetooth off",
            "bluetooth status", "show bluetooth status",
            "is bluetooth on", "bluetooth information"
        ]
        if user_input_lower in unsupported_bluetooth_aliases:
            return {"action": "unsupported_feature", "parameters": {"feature": "bluetooth"}}

        unsupported_hotspot_aliases = [
            "turn on hotspot", "turn off hotspot",
            "turn on mobile hotspot", "turn off mobile hotspot",
            "hotspot on", "hotspot off"
        ]
        if user_input_lower in unsupported_hotspot_aliases:
            return {"action": "unsupported_feature", "parameters": {"feature": "hotspot"}}

        unsupported_battery_saver_aliases = [
            "turn on battery saver mode", "turn off battery saver mode",
            "turn on the battery saver mode", "turn off the battery saver mode",
            "turn on battery saver", "turn off battery saver"
        ]
        if user_input_lower in unsupported_battery_saver_aliases:
            return {"action": "unsupported_feature", "parameters": {"feature": "battery_saver"}}

        if user_input_lower == "current fan mode":
            return {"action": "unsupported_feature", "parameters": {"feature": "fan_mode"}}

        unsupported_airplane_aliases = [
            "turn on airplane mode", "turn off airplane mode",
            "enable airplane mode", "disable airplane mode",
            "airplane mode on", "airplane mode off",
            "airplane mode status", "show airplane mode status", "is airplane mode enabled"
        ]
        if user_input_lower in unsupported_airplane_aliases:
            return {"action": "unsupported_feature", "parameters": {"feature": "airplane_mode"}}

        unsupported_night_light_aliases = [
            "turn on night light", "turn off night light",
            "enable night light", "disable night light",
            "night light on", "night light off",
            "turn on night mode", "turn off night mode",
            "enable night mode", "disable night mode"
        ]
        if user_input_lower in unsupported_night_light_aliases:
            return {"action": "unsupported_feature", "parameters": {"feature": "night_light"}}

        # 0.9.2 Hotspot Routing
        hotspot_status_aliases = [
            "hotspot status", "mobile hotspot status", "show hotspot status"
        ]
        if user_input_lower in hotspot_status_aliases:
            return {"action": "hotspot_status", "parameters": {}}

        # 0.9.3 Power Management Routing
        if user_input_lower in ["battery saver status", "current battery saver status"]:
            return {"action": "battery_saver_status", "parameters": {}}

        if user_input_lower in ["available power modes", "available power profiles", "list power modes", "list power profiles"]:
            return {"action": "list_power_profiles", "parameters": {}}

        if user_input_lower in ["current power mode", "power status"]:
            return {"action": "power_status", "parameters": {}}

        power_mode_match = re.match(r"^(?:switch\s+to\s+)?(performance|balanced|silent|turbo)(?:\s+mode)?$", user_input_lower)
        if power_mode_match:
            return {"action": "set_power_mode", "parameters": {"mode": power_mode_match.group(1)}}

        # 0.9.4 System Power Actions
        if user_input_lower in ["shutdown pc", "turn off pc", "shutdown the pc", "turn off the computer", "shutdown computer"]:
            return {"action": "shutdown_pc", "parameters": {}}
        if user_input_lower in ["restart pc", "restart the pc", "restart computer", "reboot pc", "reboot computer"]:
            return {"action": "restart_pc", "parameters": {}}
        if user_input_lower in ["sleep pc", "put pc to sleep", "make my pc sleep", "sleep computer"]:
            return {"action": "sleep_pc", "parameters": {}}
        if user_input_lower in ["lock screen", "lock the screen", "lock pc screen", "lock the pc screen", "lock computer", "lock the computer"]:
            return {"action": "lock_screen", "parameters": {}}
        if user_input_lower == "confirm shutdown":
            return {"action": "confirm_power_action", "parameters": {"action_type": "shutdown"}}
        if user_input_lower == "confirm restart":
            return {"action": "confirm_power_action", "parameters": {"action_type": "restart"}}
        if user_input_lower in ["cancel", "cancel shutdown", "cancel restart"]:
            return {"action": "cancel_power_action", "parameters": {}}

        # 0.9.5 WiFi Controls Routing
        if user_input_lower in ["turn on wifi", "enable wifi", "wifi on", "connect wifi"]:
            return {"action": "enable_wifi", "parameters": {}}
            
        if user_input_lower in ["turn off wifi", "disable wifi", "wifi off", "disconnect wifi"]:
            return {"action": "disable_wifi", "parameters": {}}
            
        wifi_status_aliases = [
            "wifi status", "show wifi status", "current wifi status",
            "am i connected to wifi", "am i connected to the internet",
            "wifi information", "network status",
            "wifi connection status", "network connection status"
        ]
        if user_input_lower in wifi_status_aliases:
            return {"action": "wifi_status", "parameters": {}}
            
        if user_input_lower == "wifi debug":
            return {"action": "wifi_debug", "parameters": {}}

        # 0.10 Wait Routing
        wait_seconds_match = re.match(r"^(wait|pause|sleep)(?:\s+for)?\s+(\d+)\s+seconds?$", user_input_lower)
        if wait_seconds_match:
            return {"action": "wait", "parameters": {"wait_type": "seconds", "seconds": int(wait_seconds_match.group(2))}}
            
        wait_until_match = re.match(r"^(?:wait|pause|sleep)\s+until\s+(.+?)\s+(opens|is\s+open|appears|loads|starts|launches|window\s+appears)$", user_input_lower)
        if wait_until_match:
            return {"action": "wait", "parameters": {"wait_type": "window", "window_name": wait_until_match.group(1).strip()}}
            
        wait_until_closed_match = re.match(r"^(?:wait|pause|sleep)\s+until\s+(.+?)\s+(closes|is\s+closed|disappears)$", user_input_lower)
        if wait_until_closed_match:
            return {"action": "wait", "parameters": {"wait_type": "window_closed", "window_name": wait_until_closed_match.group(1).strip()}}

        # scroll down / up
        scroll_match = re.match(r"^scroll\s+(down|up)$", user_input_lower)
        if scroll_match:
            return {"action": "scroll", "parameters": {"direction": scroll_match.group(1)}}

        # move mouse [to] <x> <y>
        move_match = re.match(r"^move\s+mouse(?:\s+to)?\s+(\d+)\s+(\d+)$", user_input_lower)
        if move_match:
            return {"action": "move_mouse", "parameters": {"x": int(move_match.group(1)), "y": int(move_match.group(2))}}


        if user_input_lower in ["show context", "debug context"]:
            return {"action": "debug_context", "parameters": {}}

        if user_input_lower in ["show state", "debug state"]:
            return {"action": "debug_state", "parameters": {}}

        if user_input_lower in ["what is my current app", "current app", "active app"]:
            return {"action": "get_current_app", "parameters": {}}

        if user_input_lower in ["what was my previous app", "previous app", "last app"]:
            return {"action": "get_previous_app", "parameters": {}}

        # History Inspections
        has_app_or_history = re.search(r'\b(app|apps|history)\b', user_input_lower)
        is_question_or_show = re.search(r'\b(what|which|show)\b', user_input_lower)
        is_bare_history = re.match(r'^(open|opened|focus|focused|close|closed)\s+(apps?|history|apps\s+history)$', user_input_lower)
        
        if has_app_or_history and (is_question_or_show or is_bare_history):
            if re.search(r'\b(open|opened)\b', user_input_lower):
                return {"action": "get_opened_history", "parameters": {}}
            if re.search(r'\b(focus|focused)\b', user_input_lower):
                return {"action": "get_focused_history", "parameters": {}}
            if re.search(r'\b(close|closed)\b', user_input_lower):
                return {"action": "get_closed_history", "parameters": {}}

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



        # 5. Close Application
        close_match = re.match(r"^close\s+(.+)$", user_input_lower)
        if close_match:
            app_name = close_match.group(1).strip()
            if " and " in app_name: return None
            return {"action": "close_application", "parameters": {"application_name": app_name}}

        # 6. Create Folder
        create_folder_patterns = [
            r"^(?:create|make|new)\s+(?:new\s+)?(?:a\s+)?folder(?:\s+(?:called|named))?\s+(.+)$",
            r"^(?:create|make|new)\s+(?:new\s+)?(.+?)\s+folder$"
        ]
        for pattern in create_folder_patterns:
            match = re.match(pattern, user_input_clean, re.IGNORECASE)
            if match:
                return {"action": "create_folder", "parameters": {"folder_name": match.group(1).strip()}}

        # 8. Create File
        create_file_patterns = [
            r"^(?:create|make|new)\s+(?:a\s+)?(?:file\s+)?(?:called|named)?\s*([\w\-\. ]+\.(?:txt|docx|pdf|py|java|js|json|csv|md))(?:\s+(?:in|inside|under)\s+(.+))?$",
            r"^(?:create|make|new)\s+([\w\-\. ]+\.(?:txt|docx|pdf|py|java|js|json|csv|md))\s+file(?:\s+(?:in|inside|under)\s+(.+))?$"
        ]
        for pattern in create_file_patterns:
            match = re.match(pattern, user_input_clean, re.IGNORECASE)
            if match:
                file_name = match.group(1).strip()
                path = match.group(2)
                parsed = {"action": "create_file", "parameters": {"file_name": file_name}}
                if path: parsed["parameters"]["target_folder"] = path.strip()
                return parsed

        # 8.a Smart Document/File Creation
        doc_patterns = [
            (r"^(?:create|make|new)\s+(?:a\s+)?(?:word\s+document|word\s+file|document|doc|docx)(?:\s+(?:called|named))?\s+(.+?)(?:\s+(?:in|inside|under)\s+(.+))?$", ".docx"),
            (r"^(?:create|make|new)\s+(?:a\s+)?text(?:\s+(?:file|document))?(?:\s+(?:called|named))?\s+(.+?)(?:\s+(?:in|inside|under)\s+(.+))?$", ".txt"),
            (r"^(?:create|make|new)\s+(?:a\s+)?pdf(?:\s+(?:file|document))?(?:\s+(?:called|named))?\s+(.+?)(?:\s+(?:in|inside|under)\s+(.+))?$", ".pdf"),
            (r"^(?:create|make|new)\s+(.+?)\s+(?:word\s+document|word\s+file|document|doc|docx)(?:\s+(?:in|inside|under)\s+(.+))?$", ".docx"),
            (r"^(?:create|make|new)\s+(.+?)\s+text(?:\s+(?:file|document))?(?:\s+(?:in|inside|under)\s+(.+))?$", ".txt"),
            (r"^(?:create|make|new)\s+(.+?)\s+pdf(?:\s+(?:file|document))?(?:\s+(?:in|inside|under)\s+(.+))?$", ".pdf")
        ]
        for pattern, ext in doc_patterns:
            match = re.match(pattern, user_input_clean, re.IGNORECASE)
            if match:
                base_name = match.group(1).strip()
                path = match.group(2)
                file_name = f"{base_name}{ext}" if not base_name.lower().endswith(ext) else base_name
                parsed = {"action": "create_file", "parameters": {"file_name": file_name}}
                if path: parsed["parameters"]["target_folder"] = path.strip()
                return parsed

        # 8.1 Filesystem Operations (Rename, Delete, Copy, Move)
        rename_match = re.match(r"^(?:rename|change)\s+(?:file\s+|folder\s+)?(.+?)(?:\s+(?:in|inside|under)\s+(.+?))?\s+to\s+(.+)$", user_input_clean, re.IGNORECASE)
        if rename_match:
            source = rename_match.group(1).strip()
            folder = rename_match.group(2)
            clean_source, pref_ext = self._extract_type_hint(source)
            parsed = {"action": "rename_item", "parameters": {"source_name": clean_source, "target_name": rename_match.group(3).strip()}}
            if pref_ext: parsed["parameters"]["preferred_extension"] = pref_ext
            if folder: parsed["parameters"]["target_folder"] = folder.strip()
            return parsed
            
        delete_match = re.match(r"^(?:delete|remove)\s+(?:file\s+|folder\s+)?(.+?)(?:\s+(?:file|folder))?(?:\s+(?:in|inside|under)\s+(.+))?$", user_input_clean, re.IGNORECASE)
        if delete_match:
            target = delete_match.group(1).strip()
            folder = delete_match.group(2)
            clean_target, pref_ext = self._extract_type_hint(target)
            parsed = {"action": "delete_item", "parameters": {"item_name": clean_target}}
            if pref_ext: parsed["parameters"]["preferred_extension"] = pref_ext
            if folder: parsed["parameters"]["target_folder"] = folder.strip()
            return parsed
            
        copy_match = re.match(r"^(?:copy|duplicate)\s+(?:file\s+|folder\s+)?(.+?)(?:\s+(?:in|inside|under)\s+(.+?))?\s+to\s+(.+)$", user_input_clean, re.IGNORECASE)
        if copy_match:
            source = copy_match.group(1).strip()
            folder = copy_match.group(2)
            clean_source, pref_ext = self._extract_type_hint(source)
            parsed = {"action": "copy_file", "parameters": {"source_name": clean_source, "target_name": copy_match.group(3).strip()}}
            if pref_ext: parsed["parameters"]["preferred_extension"] = pref_ext
            if folder: parsed["parameters"]["target_folder"] = folder.strip()
            return parsed
            
        move_match_full = re.match(r"^move\s+(?:file\s+|folder\s+)?(.+?)(?:\s+(?:in|inside|under)\s+(.+?))?\s+(?:to|into)\s+(.+)$", user_input_clean, re.IGNORECASE)
        move_match_simple = re.match(r"^move\s+(?:file\s+|folder\s+)?(.+?)\s+(?:to|in|into|inside)\s+(.+)$", user_input_clean, re.IGNORECASE)
        
        if move_match_full:
            source = move_match_full.group(1).strip()
            folder = move_match_full.group(2)
            clean_source, pref_ext = self._extract_type_hint(source)
            parsed = {"action": "move_file", "parameters": {"source_name": clean_source, "target_path": move_match_full.group(3).strip()}}
            if pref_ext: parsed["parameters"]["preferred_extension"] = pref_ext
            if folder: parsed["parameters"]["target_folder"] = folder.strip()
            return parsed
        elif move_match_simple:
            source = move_match_simple.group(1).strip()
            clean_source, pref_ext = self._extract_type_hint(source)
            parsed = {"action": "move_file", "parameters": {"source_name": clean_source, "target_path": move_match_simple.group(2).strip()}}
            if pref_ext: parsed["parameters"]["preferred_extension"] = pref_ext
            return parsed

        # 9. General 'open' target classification (Priority: Workspace -> App -> Web)
        app_match = re.match(r"^open\s+(?:file\s+|folder\s+|directory\s+)?(.+?)(?:\s+file|\s+folder|\s+directory)?(?:\s+(?:in|inside|under)\s+(.+))?$", user_input_clean, re.IGNORECASE)
        if app_match:
            target = app_match.group(1).strip()
            folder = app_match.group(2)
            if " and " in target.lower(): return None
            
            clean_target, pref_ext = self._extract_type_hint(target)
            
            from src.tools.filesystem_tools import resolve_smart_item
            res = resolve_smart_item(clean_target, preferred_extension=pref_ext, target_folder=folder.strip() if folder else None)
            
            user_input_lower = user_input_clean.lower()
            has_fs_intent = bool(folder) or bool(pref_ext) or any(user_input_lower.startswith(f"open {kw}") for kw in ["file", "folder", "directory"])
            
            if res["status"] in ["success", "ambiguous"] or has_fs_intent:
                parsed = {"action": "open_workspace_item", "parameters": {"item_name": clean_target}}
                if folder: parsed["parameters"]["target_folder"] = folder.strip()
                if pref_ext: parsed["parameters"]["preferred_extension"] = pref_ext
                return parsed
                
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
        if not user_input.strip():
            return
            
        user_input_clean = user_input.strip()
        
        # Intercept interactive disambiguation
        if self.context_manager and self.context_manager.state.get("pending_disambiguation"):
            if user_input_clean.lower() in ["cancel", "never mind", "stop"]:
                self.context_manager.state["pending_disambiguation"] = None
                self.context_manager.save()
                print("\n-> Selection cancelled.")
                return
                
            if user_input_clean.isdigit():
                parsed_json = {
                    "action": "resolve_disambiguation",
                    "parameters": {"selected_index": int(user_input_clean)}
                }
                self._execute_parsed_commands(user_input, ["resolve_disambiguation"], [parsed_json], source)
                return
                
            # Leave state active but return an error
            pending = self.context_manager.state["pending_disambiguation"]
            matches_str = "\n".join(f"{i+1}. {m}" for i, m in enumerate(pending.get("matches", [])))
            print(f"\n-> Please choose a valid option number or type 'cancel'.\n\n{matches_str}")
            return
            
        user_input_lower = re.sub(r'[\?!.]+$', '', user_input.lower().strip())
        user_input_lower = re.sub(r'\s+', ' ', user_input_lower).strip()
        
        if self.context_manager and user_input_lower not in ["show context", "debug context"]:
            self.context_manager.update_last_command(user_input)
            
        # Apply NLP Preprocessing Layer before routing/planning
        if self.nlp_preprocessor:
            user_input = self.nlp_preprocessor.process(user_input)
            # Update clean and lower variants after preprocessing
            user_input_clean = user_input.strip()
            user_input_lower = user_input.lower()
            
        logger.info("--- New Command Received ---")
        logger.info(f"Received input from {source}: {user_input}")
        logger.info(f"User Input: {user_input}")
                
        # 4. Parser Bypass for Simple and Debug Commands
        debug_commands = ["show context", "debug context", "debug state", "show state"]
        
        advanced_keywords = [
             " and ", " then ", " after ", " before ", " while ", 
             " if ", " unless ", " when ", " followed by ",
             "(", ")"
        ]
        
        requires_advanced_parsing = False
        if user_input_lower not in debug_commands:
            for kw in advanced_keywords:
                if kw in user_input_lower or user_input_lower.startswith(kw.strip() + " "):
                    requires_advanced_parsing = True
                    break

        # Apply ParserPipeline (Day 19)
        pipeline_tasks = []
        if hasattr(self, 'parser_pipeline') and requires_advanced_parsing:
            graph = self.parser_pipeline.parse(user_input)
            pipeline_tasks = graph.get_sequential_tasks()
        else:
            pipeline_tasks = [user_input]
            
        # 0. Deterministic Multi-Action Sequencing
        expanded_tasks = []
        for p_task in pipeline_tasks:
            if isinstance(p_task, dict):
                expanded_tasks.append(p_task)
            else:
                normalized_input = self._normalize_app_chains(p_task)
                expanded = self._expand_multi_actions(normalized_input)
                expanded_tasks.extend(expanded)
        
        if len(expanded_tasks) > 1:
            all_deterministic = True
            parsed_commands = []
            
            for task in expanded_tasks:
                if isinstance(task, dict):
                    parsed_commands.append(task)
                    continue
                    
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
        if len(expanded_tasks) == 1 and isinstance(expanded_tasks[0], dict):
            logger.info("Single conditional command detected. Bypassing Planner and routing directly.")
            self._execute_parsed_commands(user_input, [user_input], expanded_tasks, source)
            return
            
        semantic_json = None
        if len(expanded_tasks) == 1:
            semantic_json = self._route_semantic_command(user_input)
        
        # Power action confirmation expiration
        if self.context_manager and user_input_lower not in ["show context", "debug context", "debug state"]:
            state = self.context_manager.get_context_snapshot()["system_state"]
            pending = state.get("pending_power_action")
            if pending:
                is_confirm_or_cancel = False
                if semantic_json:
                    if isinstance(semantic_json, list):
                        is_confirm_or_cancel = any(c.get("action") in ["confirm_power_action", "cancel_power_action"] for c in semantic_json)
                    else:
                        is_confirm_or_cancel = semantic_json.get("action") in ["confirm_power_action", "cancel_power_action"]
                
                if not is_confirm_or_cancel:
                    self.context_manager.update_system_state("pending_power_action", None)
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
            
        if len(expanded_tasks) > 1:
            tasks = expanded_tasks
            logger.info("Bypassing TaskPlanner because ParserPipeline extracted explicit sequential tasks.")
        elif is_filesystem_command:
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
            if isinstance(task, dict):
                parsed_commands.append(task)
                continue
                
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
            
        if hasattr(self, 'command_expander') and self.command_expander:
            logger.info("Running Command Expander...")
            expanded_commands = self.command_expander.expand(parsed_commands)
        else:
            expanded_commands = parsed_commands
            
        logger.info("Executing command(s)...")
        executable_commands = []
        for cmd in expanded_commands:
            if isinstance(cmd, dict) and cmd.get("type") == "conditional":
                logger.info(f"Conditional commands are parsed successfully but execution is not implemented yet. Node: {cmd}")
                print("\n-> Conditional commands are parsed successfully but execution is not implemented yet.")
                continue
            if isinstance(cmd, dict) and cmd.get("action") == "conditional":
                logger.info(f"Conditional commands are parsed successfully but execution is not implemented yet. Node: {cmd}")
                print("\n-> Conditional commands are parsed successfully but execution is not implemented yet.")
                continue
            executable_commands.append(cmd)
            
        exec_result = {"status": "skipped", "message": "No executable commands."}
        if executable_commands:
            if len(executable_commands) == 1:
                exec_result = self.executor.execute(executable_commands[0])
            else:
                exec_result = self.executor.execute(executable_commands)
            
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
            msg = exec_result.get('message')
            logger.info(f"[OK] {msg}")
            print(f"\n-> {msg}")
        elif exec_result.get("status") == "completed":
            logger.info("Execution Summary:")
            logger.info(f"Successful: {exec_result.get('successful')}")
            logger.info(f"Failed: {exec_result.get('failed')}")
            print(f"\n-> Execution Summary:\n   Successful: {exec_result.get('successful')}\n   Failed: {exec_result.get('failed')}")
        else:
            msg = exec_result.get('message')
            logger.error(f"[FAIL] Failed: {msg}")
            print(f"\n-> Failed: {msg}")
