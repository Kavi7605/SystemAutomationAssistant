import pytest
from unittest.mock import patch, MagicMock
from src.voice.voice_listener import VoiceListener

@patch("src.voice.voice_listener.SpeechToTextWhisper")
@patch("sounddevice.InputStream")
def test_voice_listener_audio_error(mock_sd, mock_stt_class):
    mock_stt_class.return_value = MagicMock()
    
    # Simulate sounddevice throwing an error on context manager enter
    mock_sd.return_value.__enter__.side_effect = Exception("Microphone in use")
    
    listener = VoiceListener()
    result = listener.listen()
    
    # Should gracefully handle error and return empty dict
    assert result == {}
