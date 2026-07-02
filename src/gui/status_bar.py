from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PySide6.QtCore import QTimer, QDateTime
from .theme import TEXT_SECONDARY, SUCCESS


class BottomStatusBar(QFrame):
    def __init__(self, model_name: str = "llama3.1", parent=None):
        super().__init__(parent)
        self.setObjectName("statusBar")
        self.setFixedHeight(30)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 4, 16, 4)

        self.time_label = QLabel()
        self.time_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")

        self.model_label = QLabel(f"Model: {model_name}")
        self.model_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")

        self.ready_label = QLabel("● Ready")
        self.ready_label.setStyleSheet(f"color: {SUCCESS}; font-size: 11px;")

        layout.addWidget(self.time_label)
        layout.addStretch(1)
        layout.addWidget(self.model_label)
        layout.addSpacing(16)
        layout.addWidget(self.ready_label)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_time)
        self._timer.start(1000)
        self._update_time()

    def set_state(self, text: str, color: str):
        self.ready_label.setText(f"● {text}")
        self.ready_label.setStyleSheet(f"color: {color}; font-size: 11px;")

    def _update_time(self):
        self.time_label.setText(QDateTime.currentDateTime().toString("hh:mm:ss  |  dd MMM yyyy"))
