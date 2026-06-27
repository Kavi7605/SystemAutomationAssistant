import re
from typing import List

class AdvancedCommandSplitter:
    """
    Splits complex command strings into sequential atomic instructions.
    Supports advanced connectors and implicit verb carry-over.
    Respects quotes to prevent false splits.
    """
    
    CONNECTORS = [
        r"\band\s+after\s+that\b",
        r"\band\s+then\b",
        r"\bafter\s+that\b",
        r"\bafterwards\b",
        r"\bfollowed\s+by\b",
        r"\band\b",
        r"\bthen\b",
        r"\bnext\b",
        r"\bmeanwhile\b",
        r","
    ]
    
    # Verbs that can carry over to subsequent parts
    CARRY_OVER_VERBS = ["open ", "close ", "minimize ", "maximize ", "restore "]
    
    # All action verbs to detect if a part starts with a verb
    ACTION_VERBS = CARRY_OVER_VERBS + [
        "create ", "delete ", "move ", "copy ", "rename ", "search ", 
        "wait ", "pause ", "sleep ", "click", "double click", "right click", 
        "type ", "write ", "press ", "scroll ", "focus ", "is ", "what ", 
        "which ", "tell ", "if ", "unless ", "when ", "once ", "after "
    ]

    def __init__(self):
        pattern = "|".join(self.CONNECTORS)
        self.split_regex = re.compile(rf'\s*(?:{pattern})\s*', flags=re.IGNORECASE)

    def split(self, text: str) -> List[str]:
        text = text.strip()
        if not text:
            return []

        # Temporarily protect quoted strings and "and search"
        protected_items = []
        def repl(match):
            ph = f"__PROT_{len(protected_items)}__"
            protected_items.append(match.group(0))
            return ph
            
        safe_text = re.sub(r'(["\'])(.*?)\1', repl, text)
        safe_text = re.sub(r'\band\s+search\b', repl, safe_text, flags=re.IGNORECASE)
        
        parts = self.split_regex.split(safe_text)
        
        normalized_parts = []
        carry_over = None
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            # Restore protected items
            for i, original in enumerate(protected_items):
                ph = f"__PROT_{i}__"
                if ph in part:
                    part = part.replace(ph, original)
                    
            part_lower = part.lower()
            
            starts_with_verb = any(part_lower.startswith(v) for v in self.ACTION_VERBS)
            
            if starts_with_verb:
                normalized_parts.append(part)
                carry_over = None
                for verb in self.CARRY_OVER_VERBS:
                    if part_lower.startswith(verb):
                        carry_over = verb
                        break
            else:
                if carry_over:
                    normalized_parts.append(f"{carry_over.strip()} {part}")
                else:
                    normalized_parts.append(part)
                    carry_over = None
                    
        return normalized_parts
