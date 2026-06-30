import re
from src.nlp.base_normalizer import BaseNormalizer

class SimplificationNormalizer(BaseNormalizer):
    def __init__(self):
        self.patterns = [
            (re.compile(r'(?i)\bi want you to\s+'), ''),
            (re.compile(r'(?i)\bi\'d (?:really )?like (?:you )?to\s+'), ''),
            (re.compile(r'(?i)\bi would (?:really )?like (?:you )?to\s+'), ''),
            (re.compile(r'(?i)\bi\'d like if you could\s+'), ''),
            (re.compile(r'(?i)\btry to\s+'), ''),
            (re.compile(r'(?i)\btry\s+([a-zA-Z]+)ing\b'), r'\1'),
            (re.compile(r'(?i)\bfor me\b'), ''),
            (re.compile(r'(?i)^opening\b'), 'open'),
            (re.compile(r'(?i)^closing\b'), 'close'),
            (re.compile(r'(?i)^maximizing\b'), 'maximize'),
            (re.compile(r'(?i)^minimizing\b'), 'minimize'),
            (re.compile(r'(?i)^focusing\b'), 'focus'),
            (re.compile(r'(?i)\band\s+opening\b'), 'and open'),
            (re.compile(r'(?i)\band\s+closing\b'), 'and close'),
            (re.compile(r'(?i)\band\s+maximizing\b'), 'and maximize'),
            (re.compile(r'(?i)\band\s+minimizing\b'), 'and minimize'),
            (re.compile(r'(?i)\band\s+focusing\b'), 'and focus'),
        ]

    def normalize(self, text: str) -> str:
        result = text
        for pattern, repl in self.patterns:
            result = pattern.sub(repl, result)
            
        # Clean up extra spaces
        return re.sub(r'\s+', ' ', result).strip()
