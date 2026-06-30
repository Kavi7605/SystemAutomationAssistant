import re
from src.nlp.base_normalizer import BaseNormalizer

class PolitenessNormalizer(BaseNormalizer):
    def __init__(self):
        self.pattern = re.compile(r'(?i)\b(?:could you please|could you|can you please|can you|would you mind|would you please|would you|hey assistant|please|just)\b')

    def normalize(self, text: str) -> str:
        result = self.pattern.sub('', text)
        return re.sub(r'\s+', ' ', result).strip()
