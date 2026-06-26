import re
from src.nlp.base_normalizer import BaseNormalizer
from src.nlp.data.intent_synonyms import SYNONYM_TO_INTENT

class IntentNormalizer(BaseNormalizer):
    def normalize(self, text: str) -> str:
        result = text
        
        # We want to replace longest synonyms first to avoid partial matches
        sorted_synonyms = sorted(SYNONYM_TO_INTENT.keys(), key=len, reverse=True)
        
        for syn in sorted_synonyms:
            canonical_intent = SYNONYM_TO_INTENT[syn]
            # Replace synonym with canonical intent if matched as a whole word
            pattern = re.compile(rf"\b{re.escape(syn)}\b", re.IGNORECASE)
            result = pattern.sub(canonical_intent, result)
            
        return result
