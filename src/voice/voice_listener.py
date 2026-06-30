import queue
import logging
import time
import numpy as np
import sounddevice as sd
from src.voice.speech_to_text_whisper import SpeechToTextWhisper

logger = logging.getLogger(__name__)

class VoiceListener:
    def __init__(self):
        self.sample_rate = 16000
        # Default to Whisper now
        self.stt = SpeechToTextWhisper(model_size="medium.en")
        
    def listen(self, silence_threshold: float = 0.01, silence_duration: float = 1.5) -> dict:
        """
        Listens to the microphone using an energy-based silence detector.
        Returns a dict containing transcript and metadata: {transcript, duration, model, device}
        """
        q = queue.Queue()

        def callback(indata, _frames, _time_info, status):
            if status:
                logger.warning(f"Audio status: {status}")
            # Put float32 frames into queue
            q.put(indata.copy())

        print("Listening...")
        
        audio_buffer = []
        is_recording = False
        silence_start_time = None
        
        try:
            with sd.InputStream(samplerate=self.sample_rate, blocksize=8000, dtype='float32',
                                   channels=1, callback=callback):
                while True:
                    data = q.get()
                    audio_buffer.append(data)
                    
                    rms = np.sqrt(np.mean(data**2))
                    
                    if rms > silence_threshold:
                        is_recording = True
                        silence_start_time = None
                    elif is_recording:
                        if silence_start_time is None:
                            silence_start_time = time.time()
                        elif time.time() - silence_start_time > silence_duration:
                            break
                            
        except Exception as e:
            logger.error(f"Voice listener error: {e}", exc_info=True)
            print("\nError accessing microphone. Make sure you have a microphone connected.")
            return {}

        if not audio_buffer:
            return {}
            
        full_audio = np.concatenate(audio_buffer).flatten()
        result = self.stt.process_audio(full_audio)
        return result
