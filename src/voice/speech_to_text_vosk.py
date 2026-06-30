import os
import json
import logging
from vosk import Model, KaldiRecognizer, SetLogLevel

logger = logging.getLogger(__name__)

class SpeechToText:
    """
    Offline speech recognition using Vosk.
    """
    def __init__(self, model_path: str = "data/vosk-model-small-en-us-0.15", sample_rate: int = 16000):
        self.model_path = os.path.abspath(model_path)
        self.sample_rate = sample_rate
        self.model = None
        self.recognizer = None
        self._load_model()

    def _load_model(self):
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Vosk model not found at '{self.model_path}'. "
                f"Please download the model and place it in the data directory."
            )
        try:
            # Hide verbose Vosk logs
            SetLogLevel(-1)
            
            self.model = Model(self.model_path)
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
            logger.info("Vosk model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Vosk model: {e}", exc_info=True)
            raise

    def process_frame(self, data: bytes) -> str:
        """
        Process a single audio frame and return the recognized text if complete, 
        otherwise returns an empty string.
        """
        if self.recognizer.AcceptWaveform(data):
            result = json.loads(self.recognizer.Result())
            return result.get("text", "")
        return ""
        
    def get_final_result(self) -> str:
        """
        Returns whatever has been recognized so far at the end of the stream.
        """
        result = json.loads(self.recognizer.FinalResult())
        return result.get("text", "")
