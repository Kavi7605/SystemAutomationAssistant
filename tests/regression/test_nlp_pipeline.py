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
        "maximize chrome and vscode": "maximize chrome and vscode",
        "close both of them": "close both",
        "close all of them": "close all",
        "close both apps": "close both",
        "close both applications": "close both",
        "close these apps": "close all",
        "close those apps": "close all",
        "close them": "close all",
        "focus the other app": "focus other",
        "close the remaining app": "close other",
        "minimize every other app": "minimize other_all",
        "maximize all except steam": "maximize all except steam",
        "switch to the next app": "focus next",
        "switch back": "focus previous",
        "reopen the last closed app": "open the last closed app",
        "focus whichever app is still open": "focus other",
        "focus it": "focus it",
        "minimize it": "minimize it",
        "maximize it": "maximize it",
        "close it": "close it",
        "focus the previous one": "focus previous",
        "focus the other one": "focus other",
        "focus the same app": "focus it",
        "focus the one i opened earlier": "focus previous",
        "close the app i opened first": "close first",
        "close the app i opened last": "close newest",
        "focus the app i closed most recently": "focus last_closed",
        "focus the oldest app": "focus the oldest app",
        "focus the newest app": "focus the newest app",
        "focus recently opened": "focus newest",
        "focus recently focused": "focus last_focused",
        "maximize all app": "maximize all",
        "minimize every app": "minimize all",
        "close every application": "close all",
        "close every one": "close all"
    }
    
    for input_text, expected in cases.items():
        assert preprocessor.process(input_text) == expected
