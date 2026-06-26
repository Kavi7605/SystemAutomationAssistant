import re
from src.nlp.base_normalizer import BaseNormalizer
from src.nlp.data.grammar_phrases import GRAMMAR_PHRASES

class GrammarNormalizer(BaseNormalizer):
    def normalize(self, text: str) -> str:
        # Pad with spaces to allow easy word boundary matching
        padded_text = f" {text} "
        
        for phrase in GRAMMAR_PHRASES:
            # Create a regex to match the phrase with word boundaries, case-insensitive
            pattern = re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
            padded_text = pattern.sub(" ", padded_text)
            
        return padded_text.strip()
