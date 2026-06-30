import re
from src.nlp.base_normalizer import BaseNormalizer

class GrammarNormalizer(BaseNormalizer):
    def __init__(self):
        from src.nlp.data.grammar_phrases import GRAMMAR_PHRASES
        self.patterns = [re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE) for phrase in GRAMMAR_PHRASES]

    def normalize(self, text: str) -> str:
        # Pad with spaces to allow easy word boundary matching
        padded_text = f" {text} "
        
        for pattern in self.patterns:
            padded_text = pattern.sub(" ", padded_text)
            
        return padded_text.strip()
