# Voice Input Architecture Review

## 1. Goal
To provide a highly accurate, fully offline voice input method for the SystemAutomationAssistant. We prioritize command recognition accuracy over minimal resource usage because executing incorrect real-world commands (e.g., misinterpreting "github") poses a functional risk.

## 2. Library Selection
### Why Vosk Was Replaced
The initial Day 9 implementation used **Vosk**, chosen for its extreme lightweight footprint and fast streaming frame-by-frame processing. However, real-world testing revealed that Vosk hallucinates or fails to reliably recognize specific technical automation keywords (e.g., "github" transcribed as "good well" or "get up"). For a tool executing system commands, this lack of domain accuracy is unacceptable.

### Why Faster-Whisper Was Selected
We selected **Faster-Whisper**:
- **Accuracy**: It leverages OpenAI's Whisper models, which are state-of-the-art for accurate transcription, handling technical jargon flawlessly.
- **Performance**: `faster-whisper` uses CTranslate2, running up to 4x faster than standard Whisper, with lower memory usage.
- **Model Size**: We explicitly selected `medium.en`. While `small.en` is faster, `medium.en` provides the necessary robust accuracy for complex desktop automation routing and easily runs on modern hardware (e.g., RTX 3060 / 16GB RAM).

## 3. Architecture Design
1. **Input Layer (`AutomationEngine`)**:
   - The CLI menu remains. If `[V]` is selected, we invoke the `VoiceListener`.
   - **Confirmation Workflow**: Since Faster-Whisper takes slightly longer to process and is more definitive, we added a `Proceed? [Y/N]` prompt. The user reviews the transcript before actual execution occurs, ensuring absolute safety.
2. **Audio Capture (`VoiceListener`)**:
   - Captures `float32` audio via `sounddevice`.
   - Instead of frame-by-frame streaming, it uses an **RMS Energy-Based Silence Detector**. It buffers speech internally until a 1.5s pause is detected, then passes the full buffer to the engine.
3. **Speech-to-Text (`SpeechToTextWhisper`)**:
   - Automatically attempts to load `medium.en` onto the CUDA GPU (using `float16` compute), gracefully falling back to CPU (`int8`) if necessary.
   - Internal VAD filtering (`vad_filter=True`) strips residual noise.
4. **Legacy Rollback (`SpeechToTextVosk`)**:
   - The original Vosk implementation has been isolated and preserved as `speech_to_text_vosk.py` to allow easy rollbacks in the event of hardware incompatibilities.

## 4. Hardware Expectations
- **GPU**: NVIDIA GPU with minimum 4GB VRAM (e.g., RTX 3060) is highly recommended for sub-second recognition on `medium.en`.
- **CPU Fallback**: Works on CPU, but processing time will increase linearly with speech length.
