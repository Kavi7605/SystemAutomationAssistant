import time
import logging
import numpy as np
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

class SpeechToTextWhisper:
    """
    Offline speech recognition using Faster-Whisper.
    """
    def __init__(self, model_size: str = "medium.en"):
        self.model_size = model_size
        self.model = None
        self.device = "cpu"
        self._load_model()

    def _load_model(self):
        try:
            # Force CPU for reliability during Day 9
            self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            self.device = "CPU"
            logger.info(f"Faster-Whisper running in CPU mode. ({self.model_size}) loaded successfully.")
        except Exception as cpu_err:
            logger.error(f"Failed to load Faster-Whisper on CPU: {cpu_err}", exc_info=True)
            raise

    def process_audio(self, audio_data: np.ndarray) -> dict:
        """
        Process the entire audio buffer and return transcription details.
        Expected audio_data is a numpy array of shape (N,) containing float32 samples at 16000Hz.
        """
        start_time = time.time()
        
        # Transcribe with internal VAD filtering to strip noise and silence
        segments, info = self.model.transcribe(audio_data, beam_size=5, vad_filter=True)
        
        text = " ".join(segment.text.strip() for segment in segments).strip()
        duration = time.time() - start_time
        
        return {
            "transcript": text,
            "duration": round(duration, 2),
            "model": self.model_size,
            "device": self.device
        }
