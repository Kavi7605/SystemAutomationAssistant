import pytest
from src.nlp.number_normalizer import NumberNormalizer

def test_number_normalizer():
    normalizer = NumberNormalizer()
    
    cases = {
        "five seconds": "5 seconds",
        "ten": "10",
        "half minute": "30 seconds",
        "one minute": "60 seconds",
        "two minutes": "120 seconds",
        "quarter hour": "900 seconds",
        "wait for two minutes and ten seconds": "wait for 120 seconds and 10 seconds",
        "open steam": "open steam"
    }
    
    for input_text, expected in cases.items():
        assert normalizer.normalize(input_text).strip() == expected
