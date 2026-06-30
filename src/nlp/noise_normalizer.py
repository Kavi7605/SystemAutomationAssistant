import re
from src.nlp.base_normalizer import BaseNormalizer

class NoiseNormalizer(BaseNormalizer):
    def __init__(self):
        self.pattern = re.compile(r'(?i)\b(?:i think|maybe|actually|basically|kind of|sort of|probably|you know|well)\b')

    def normalize(self, text: str) -> str:
        result = self.pattern.sub('', text)
        return re.sub(r'\s+', ' ', result).strip()
