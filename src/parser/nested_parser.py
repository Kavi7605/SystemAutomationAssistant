import re
from typing import List

class NestedParser:
    """
    Extracts nested clauses and flattens them into explicitly ordered steps.
    e.g. "Wait until X opens then focus it" -> handled by splitter.
    "Close Chrome after saving the document" -> "save the document", "close chrome"
    "Open Discord and wait until it opens before focusing it" -> "open discord", "wait until discord opens", "focus it"
    """

    def __init__(self):
        pass

    def parse(self, commands: List[str]) -> List[str]:
        flattened = []
        for cmd in commands:
            cmd = cmd.strip()
            if not cmd:
                continue
                
            # Check for "X before Y"
            before_match = re.search(r'\s+before\s+', cmd, flags=re.IGNORECASE)
            # Check for "X after Y" but avoid triggering on just "after" if it's conditional like "After WhatsApp opens, focus it"
            # ConditionParser handles "after X, Y". Here we handle "X after Y".
            after_match = re.search(r'^(.+?)\s+after\s+(.+)$', cmd, flags=re.IGNORECASE)
            
            # check if it starts with 'after' or conditional
            starts_with_cond = re.match(r'^(if|unless|when|once|after)\b', cmd, flags=re.IGNORECASE)
            
            if before_match and not starts_with_cond:
                x = cmd[:before_match.start()].strip()
                y = cmd[before_match.end():].strip()
                flattened.append(x)
                flattened.append(y)
            elif after_match and not starts_with_cond:
                x = after_match.group(1).strip()
                y = after_match.group(2).strip()
                flattened.append(y)
                flattened.append(x)
            else:
                # check for "while"
                while_match = re.search(r'^(.+?)\s+while\s+(.+)$', cmd, flags=re.IGNORECASE)
                if while_match and not starts_with_cond:
                    x = while_match.group(1).strip()
                    y = while_match.group(2).strip()
                    # For sequential, we can just do Y then X or X then Y. Let's do Y then X
                    flattened.append(y)
                    flattened.append(x)
                else:
                    flattened.append(cmd)
        return flattened
