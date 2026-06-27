import re
from typing import List, Union, Dict

class ConditionParser:
    """
    Detects conditional commands and returns them as a structured intermediate representation.
    """
    
    def __init__(self):
        pass

    def parse(self, commands: List[str]) -> List[Union[str, Dict[str, str]]]:
        parsed = []
        action_verbs = ["open ", "close ", "focus ", "maximize ", "minimize ", "restore ", "wait ", "type ", "search ", "click "]
        
        for cmd in commands:
            cmd = cmd.strip()
            if not cmd:
                continue
                
            explicit_match = re.match(r'^(if\s+not|if|unless|when|once|after)\b\s+(.+?)(?:,|\s+then\s+)(.+)$', cmd, flags=re.IGNORECASE)
            if explicit_match:
                condition_keyword = explicit_match.group(1).lower()
                condition = explicit_match.group(2).strip()
                action = explicit_match.group(3).strip()
                
                if condition_keyword in ['if not', 'unless']:
                    condition = f"not {condition}"
                    
                parsed.append({
                    "type": "conditional",
                    "condition": condition,
                    "action": action
                })
                continue
                
            starts_with_cond = re.match(r'^(if\s+not|if|unless|when|once|after)\b\s+(.+)$', cmd, flags=re.IGNORECASE)
            if starts_with_cond:
                keyword = starts_with_cond.group(1).lower()
                rest = starts_with_cond.group(2).strip()
                
                action_idx = -1
                words = rest.split()
                for i, word in enumerate(words):
                    potential_verb = word.lower() + " "
                    if any(potential_verb.startswith(v) for v in action_verbs):
                        action_idx = i
                        break
                        
                if action_idx > 0:
                    condition = " ".join(words[:action_idx]).strip()
                    action = " ".join(words[action_idx:]).strip()
                    
                    if keyword in ['if not', 'unless']:
                        condition = f"not {condition}"
                        
                    parsed.append({
                        "type": "conditional",
                        "condition": condition,
                        "action": action
                    })
                    continue
            
            trailing_match = re.search(r'^(.+?)\s+(if\s+not|if|unless|when|once)\b\s+(.+)$', cmd, flags=re.IGNORECASE)
            if trailing_match:
                action = trailing_match.group(1).strip()
                keyword = trailing_match.group(2).lower()
                condition = trailing_match.group(3).strip()
                
                if keyword in ['if not', 'unless']:
                    condition = f"not {condition}"
                    
                parsed.append({
                    "type": "conditional",
                    "condition": condition,
                    "action": action
                })
                continue
                
            parsed.append(cmd)
            
        return parsed
