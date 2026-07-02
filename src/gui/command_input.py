from PySide6.QtWidgets import QFrame, QHBoxLayout, QLineEdit, QPushButton
from PySide6.QtCore import Qt, Signal
from .animations import PulseGlow
from .theme import ACCENT, DANGER


class CommandInput(QFrame):
    execute_requested = Signal(str)
    clear_requested = Signal()
    voice_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._voice_active = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(10)

        self.input = QLineEdit()
        self.input.setObjectName("commandInput")
        self.input.setPlaceholderText("Type or speak a command...")
        self.input.returnPressed.connect(self._on_execute)

        self.mic_btn = QPushButton("🎤 Ready")
        self.mic_btn.setObjectName("secondary")
        self.mic_btn.setCursor(Qt.PointingHandCursor)
        self.mic_btn.clicked.connect(self._toggle_voice)
        self._pulse = PulseGlow(self.mic_btn)

        self.execute_btn = QPushButton("▶ Execute")
        self.execute_btn.setObjectName("primary")
        self.execute_btn.setCursor(Qt.PointingHandCursor)
        self.execute_btn.clicked.connect(self._on_execute)

        self.clear_btn = QPushButton("🧹 Clear")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.clicked.connect(self._on_clear)

        layout.addWidget(self.mic_btn)
        layout.addWidget(self.input, 1)
        layout.addWidget(self.execute_btn)
        layout.addWidget(self.clear_btn)

    def _on_execute(self):
        text = self.input.text().strip()
        if text:
            self.execute_requested.emit(text)
            self.input.clear()

    def _on_clear(self):
        self.input.clear()
        self.clear_requested.emit()

    def _toggle_voice(self):
        self._voice_active = not self._voice_active
        if self._voice_active:
            self._pulse.start()
            self.mic_btn.setText("🔴 Listening...")
            self.mic_btn.setStyleSheet(f"background-color: {ACCENT}33; border-radius: 8px; color: white;")
            self.input.setEnabled(False)
            self.execute_btn.setEnabled(False)
        else:
            self._pulse.stop()
            self.mic_btn.setText("🎤 Ready")
            self.mic_btn.setStyleSheet("")
            self.input.setEnabled(True)
            self.execute_btn.setEnabled(True)
        self.voice_toggled.emit(self._voice_active)

    def set_enabled(self, enabled: bool):
        self.input.setEnabled(enabled)
        self.execute_btn.setEnabled(enabled)

    def clear(self):
        self.input.clear()

    def get_text(self) -> str:
        return self.input.text()

    def set_text(self, text: str):
        self.input.setText(text)

    def focus(self):
        self.input.setFocus()
