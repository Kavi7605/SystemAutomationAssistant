import pytest
from src.nlp.preprocessor import NLPPreprocessor

def test_nlp_pipeline_e2e():
    preprocessor = NLPPreprocessor()
    
    cases = {
        "Could you please launch steam": "open steam",
        "Fire up Discord": "open discord",
        "Switch to VS Code": "focus vscode",
        "Pause for five seconds": "wait for 5 seconds", # "Pause" -> "wait", "five" -> "5" -> wait for 5 seconds
        "Please close GitHub Desktop": "close github",
        "Could you boot Chrome": "open chrome",
        "Run Visual Studio Code": "open vscode",
        "I need you to launch WhatsApp": "open whatsapp",
        "Hold for half minute": "wait for 30 seconds", # "Hold" -> "wait", "half minute" -> "30 seconds" -> wait for 30 seconds
        "Wait one minute": "wait 60 seconds",
        "Could you please open steam for me": "open steam",
        "Can you switch to Discord": "focus discord",
        "Could you close Steam please": "close steam",
        "wait for five minutes": "wait for 300 seconds",
        "wait for 2 hours": "wait for 7200 seconds",
        "show running apps": "focus running apps",
        "list running apps": "list running apps",
        "running applications": "running applications",
        "what apps are running": "what apps are running",
        "what applications are running": "what applications are running",
        "what apps are open": "what apps are open",
        "what applications are open": "what applications are open",
        "list open applications": "list open applications",
        "list open apps": "list open apps",
        "minimize discord and whatsapp": "minimize discord and whatsapp",
        "maximize chrome and vscode": "maximize chrome and vscode"
    }
    
    for input_text, expected in cases.items():
        assert preprocessor.process(input_text) == expected
