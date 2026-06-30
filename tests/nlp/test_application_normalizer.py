from src.nlp.application_normalizer import ApplicationNormalizer

def test_application_normalizer():
    normalizer = ApplicationNormalizer()
    
    cases = {
        "open vs code": "open vscode",
        "launch visual studio code": "launch vscode",
        "focus google chrome": "focus chrome",
        "close github desktop": "close github",
        "open ms word": "open word",
        "focus microsoft teams": "focus teams",
        "open unknown app": "open unknown app"
    }
    
    for input_text, expected in cases.items():
        assert normalizer.normalize(input_text).strip() == expected
