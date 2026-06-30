import re
from src.nlp.base_normalizer import BaseNormalizer

class IntentNormalizer(BaseNormalizer):
    def __init__(self):
        from src.nlp.data.intent_synonyms import SYNONYM_TO_INTENT
        sorted_synonyms = sorted(SYNONYM_TO_INTENT.keys(), key=len, reverse=True)
        self.patterns = [(re.compile(rf"\b{re.escape(syn)}\b", re.IGNORECASE), SYNONYM_TO_INTENT[syn]) for syn in sorted_synonyms]

    def normalize(self, text: str) -> str:
        if text.lower().strip() in ["show context", "debug context", "show state", "debug state"]:
            return text
            
        result = text
        for pattern, canonical_intent in self.patterns:
            result = pattern.sub(canonical_intent, result)
            
        return result
