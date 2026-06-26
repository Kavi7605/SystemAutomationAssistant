import re
from src.nlp.base_normalizer import BaseNormalizer
from src.nlp.data.number_words import WORD_TO_NUMBER, TIME_PHRASES_SORTED, TIME_PHRASES

class NumberNormalizer(BaseNormalizer):
    def normalize(self, text: str) -> str:
        result = text
        
        # Replace time phrases first (e.g., "half minute" -> "30 seconds")
        for phrase in TIME_PHRASES_SORTED:
            replacement = TIME_PHRASES[phrase]
            pattern = re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
            result = pattern.sub(replacement, result)
            
        # Replace word numbers with digits (e.g., "five" -> "5")
        for word, digit in WORD_TO_NUMBER.items():
            pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
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
