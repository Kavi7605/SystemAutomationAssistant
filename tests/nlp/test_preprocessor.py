import pytest
from src.nlp.preprocessor import NLPPreprocessor

def test_nlp_preprocessor():
    preprocessor = NLPPreprocessor()
    
    # E2E basic tests in isolation
    cases = {
        "Could you please launch steam for me": "open steam",
        "Can u focus vs code": "focus vscode",
        "Wait half minute": "wait 30 seconds"
    }
    
    for input_text, expected in cases.items():
        assert preprocessor.process(input_text) == expected
