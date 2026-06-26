import pytest
from src.nlp.canonicalizer import Canonicalizer

def test_canonicalizer():
    normalizer = Canonicalizer()
    
    cases = {
        "Open Steam": "open steam",
        "  Launch   Discord  ": "launch discord",
        "Focus Chrome!": "focus chrome",
        "Wait 5 seconds.": "wait 5 seconds",
        "Close   GitHub Desktop?": "close github desktop"
    }
    
    for input_text, expected in cases.items():
        assert normalizer.normalize(input_text) == expected
