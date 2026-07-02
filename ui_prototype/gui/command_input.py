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

        self.mic_btn = QPushButton("🎤")
        self.mic_btn.setObjectName("iconBtn")
        self.mic_btn.setFixedSize(40, 40)
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
            self.mic_btn.setStyleSheet(f"background-color: {ACCENT}33; border-radius: 20px;")
        else:
            self._pulse.stop()
            self.mic_btn.setStyleSheet("")
        self.voice_toggled.emit(self._voice_active)
