import re
from src.nlp.base_normalizer import BaseNormalizer

class NumberNormalizer(BaseNormalizer):
    def __init__(self):
        from src.nlp.data.number_words import WORD_TO_NUMBER, TIME_PHRASES_SORTED, TIME_PHRASES
        self.time_patterns = [(re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE), TIME_PHRASES[phrase]) for phrase in TIME_PHRASES_SORTED]
        self.word_patterns = [(re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE), str(digit)) for word, digit in WORD_TO_NUMBER.items()]

    def normalize(self, text: str) -> str:
        result = text
        
        # Replace time phrases first (e.g., "half minute" -> "30 seconds")
        for pattern, replacement in self.time_patterns:
            result = pattern.sub(replacement, result)
            
        # Replace word numbers with digits (e.g., "five" -> "5")
        for pattern, digit in self.word_patterns:
            result = pattern.sub(digit, result)
            
        # Convert minute/hour expressions into seconds
        def minute_replacer(match):
            val = int(match.group(1))
            return f"{val * 60} seconds"
            
        def hour_replacer(match):
            val = int(match.group(1))
            return f"{val * 3600} seconds"
            
        result = re.sub(r'\b(\d+)\s+minutes?\b', minute_replacer, result, flags=re.IGNORECASE)
        result = re.sub(r'\b(\d+)\s+hours?\b', hour_replacer, result, flags=re.IGNORECASE)
            
        return result
