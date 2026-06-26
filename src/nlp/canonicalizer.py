import re
from src.nlp.base_normalizer import BaseNormalizer

class Canonicalizer(BaseNormalizer):
    def normalize(self, text: str) -> str:
        # Perform structural cleanup only
        # Lowercase
        result = text.lower()
        
        # Punctuation cleanup (remove trailing punctuation usually handled by AutomationEngine,
        # but good to clean up here too. Only trailing punctuation to avoid messing up domains like "github.com")
        result = re.sub(r'[\?!.]+$', '', result)
        
        # Collapse multiple spaces into one and strip
        result = re.sub(r'\s+', ' ', result).strip()
        
        return result
