"""
Synonym mapping for intent normalization.
Maps various synonymous action verbs to their canonical representation.
"""

INTENT_SYNONYMS = {
    "open": ["launch", "start", "run", "fire up", "boot", "bring up", "execute", "reopen"],
    "close": ["exit", "terminate", "kill", "quit", "stop", "end"],
    "focus": ["activate", "switch to", "bring to front", "show", "jump to"],
    "wait": ["sleep", "pause", "hold", "delay"],
    "search": ["find", "look up", "google", "browse"]
}

# Reverse mapping for faster O(1) lookup during processing
SYNONYM_TO_INTENT = {}
for intent, synonyms in INTENT_SYNONYMS.items():
    for syn in synonyms:
        SYNONYM_TO_INTENT[syn.lower()] = intent
