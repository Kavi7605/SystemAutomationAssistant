from unittest.mock import MagicMock
from unittest.mock import patch
import pytest
import numpy as np
from src.voice.speech_to_text_whisper import SpeechToTextWhisper

@patch("src.voice.speech_to_text_whisper.WhisperModel")
def test_whisper_cpu_initialization(mock_whisper_model):
    # Ensure it only attempts CPU initialization
    mock_whisper_model.return_value = MagicMock()
    
    stt = SpeechToTextWhisper(model_size="medium.en")
    assert stt.device == "CPU"
    assert mock_whisper_model.call_count == 1
    mock_whisper_model.assert_any_call("medium.en", device="cpu", compute_type="int8")

@patch("src.voice.speech_to_text_whisper.WhisperModel")
def test_whisper_process_audio(mock_whisper_model):
    mock_model_instance = MagicMock()
    mock_whisper_model.return_value = mock_model_instance
    
    # Mock transcribe result
    mock_segment1 = MagicMock()
    mock_segment1.text = "open "
    mock_segment2 = MagicMock()
    mock_segment2.text = "github"
    mock_model_instance.transcribe.return_value = ([mock_segment1, mock_segment2], None)
    
    stt = SpeechToTextWhisper(model_size="medium.en")
    
    audio = np.zeros(16000, dtype=np.float32)
    result = stt.process_audio(audio)
    
    assert result["transcript"] == "open github"
    assert result["model"] == "medium.en"
    assert result["device"] in ["CUDA", "CPU"]
    assert "duration" in result
