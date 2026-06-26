import pytest
from src.nlp.grammar_normalizer import GrammarNormalizer

def test_grammar_normalizer():
    normalizer = GrammarNormalizer()
    
    cases = {
        "Could you please open steam": "open steam",
        "Can you launch discord": "launch discord",
        "Actually just close it for me right now": "close it",
        "Maybe at the moment could u focus teams": "focus teams",
        "open steam and calculator": "open steam and calculator"
    }
    
    for input_text, expected in cases.items():
        assert normalizer.normalize(input_text).strip() == expected
