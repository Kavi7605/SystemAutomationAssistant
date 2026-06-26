import re
from src.nlp.base_normalizer import BaseNormalizer
from src.nlp.data.application_aliases import ALIAS_TO_APP

class ApplicationNormalizer(BaseNormalizer):
    def normalize(self, text: str) -> str:
        result = text
        
        # We want to replace longest aliases first to avoid partial matches
        # e.g., "visual studio code" before "code"
        sorted_aliases = sorted(ALIAS_TO_APP.keys(), key=len, reverse=True)
        
        for alias in sorted_aliases:
            canonical_app = ALIAS_TO_APP[alias]
            # Replace alias with canonical app name if matched as a whole word
            pattern = re.compile(rf"\b{re.escape(alias)}\b", re.IGNORECASE)
            result = pattern.sub(canonical_app, result)
            
        return result
