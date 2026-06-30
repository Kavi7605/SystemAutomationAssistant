import re
from src.nlp.base_normalizer import BaseNormalizer

class ReferenceNormalizer(BaseNormalizer):
    def __init__(self):
        # We replace the longest matches first
        self.replacements = {
            r"\bboth of them\b": "both",
            r"\bboth applications\b": "both",
            r"\bboth apps\b": "both",
            r"\ball of them\b": "all",
            r"\bevery application\b": "all",
            r"\bevery app\b": "all",
            r"\bevery one\b": "all",
            r"\ball apps\b": "all",
            r"\ball app\b": "all",
            r"\bthese apps\b": "all",
            r"\bthose apps\b": "all",
            r"\bthem\b": "all",
            r"\bthe remaining app\b": "other",
            r"\bwhichever app is still open\b": "other",
            r"\bthe other app\b": "other",
            r"\bthe other one\b": "other",
            r"\bevery other app\b": "other_all",
            r"\bthe next app\b": "next",
            r"\bswitch back\b": "focus previous",
            r"\bthe previous one\b": "previous",
            r"\bthe one i opened earlier\b": "previous",
            r"\bthe same app\b": "it",
            r"\bthe app i opened first\b": "first",
            r"\bthe app i opened last\b": "newest",
            r"\bthe app i closed most recently\b": "last_closed",
            r"\brecently opened\b": "newest",
            r"\brecently focused\b": "last_focused"
        }
        self.patterns = [(re.compile(pattern, flags=re.IGNORECASE), replacement) for pattern, replacement in self.replacements.items()]

    def normalize(self, text: str) -> str:
        result = text
        for pattern, replacement in self.patterns:
            result = pattern.sub(replacement, result)
        return result
