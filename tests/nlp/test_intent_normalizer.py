import pytest
from src.nlp.intent_normalizer import IntentNormalizer

def test_intent_normalizer():
    normalizer = IntentNormalizer()
    
    cases = {
        "launch steam": "open steam",
        "boot discord": "open discord",
        "fire up vscode": "open vscode",
        "kill spotify": "close spotify",
        "quit game": "close game",
        "switch to chrome": "focus chrome",
        "bring to front word": "focus word",
        "sleep 5 seconds": "wait 5 seconds",
        "delay 10 seconds": "wait 10 seconds",
        "google something": "search something",
        "unknown intent": "unknown intent"
    }
    
    for input_text, expected in cases.items():
        assert normalizer.normalize(input_text).strip() == expected
