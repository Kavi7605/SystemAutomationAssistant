import pytest
from src.voice.speech_to_text_vosk import SpeechToText

def test_speech_to_text_missing_model():
    with pytest.raises(FileNotFoundError, match="Vosk model not found"):
        SpeechToText(model_path="invalid_path_that_does_not_exist")
