from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy
from PySide6.QtCore import Qt
from .theme import SUCCESS, TEXT_SECONDARY


class StatusPill(QFrame):
    """Small rounded pill showing a connection/status dot + label."""

    def __init__(self, text: str, ok: bool = True, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background-color: #1B212B; border-radius: 10px; }}"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(6)

        dot_color = SUCCESS if ok else "#F85149"
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {dot_color}; font-size: 10px;")
        label = QLabel(text)
        label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")

        layout.addWidget(dot)
        layout.addWidget(label)


class TopBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("topBar")
        self.setFixedHeight(56)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 8, 18, 8)
        layout.setSpacing(14)

        title = QLabel("System Automation Assistant")
        title.setObjectName("title")

        layout.addWidget(title)

        spacer = QLabel()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(spacer)

        layout.addWidget(StatusPill("Ollama Connected", ok=True))
        layout.addWidget(StatusPill("Microphone Ready", ok=True))
        layout.addWidget(StatusPill("Executor Ready", ok=True))

        settings_btn = QPushButton("⚙")
        settings_btn.setObjectName("iconBtn")
        settings_btn.setFixedSize(34, 34)
        settings_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(settings_btn)
