from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QWidget, QProgressBar
)
from PySide6.QtCore import Qt
from .theme import PANEL, PANEL_ALT, TEXT_SECONDARY, SUCCESS, ACCENT, BORDER
from .animations import fade_in


class ActionItem(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"QFrame {{ background-color: {PANEL_ALT}; border-radius: 8px; }}")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        check = QLabel("✓")
        check.setStyleSheet(f"color: {SUCCESS}; font-weight: 600;")
        label = QLabel(text)
        label.setStyleSheet("font-size: 12px;")
        label.setWordWrap(True)
        layout.addWidget(check)
        layout.addWidget(label, 1)


class StatusCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header = QLabel("SYSTEM STATUS")
        header.setObjectName("sectionHeader")
        layout.addWidget(header)

        self.labels = {}
        fields = [
            ("Automation Engine", "Online"),
            ("Voice", "Ready"),
            ("Executor", "Idle"),
            ("Ollama", "Ready"),
            ("Current Mode", "Idle"),
            ("Current Task", "None")
        ]

        for label_text, default_val in fields:
            row = QHBoxLayout()
            label = QLabel(label_text)
            label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
            val_label = QLabel(default_val)
            val_label.setStyleSheet(f"color: {ACCENT}; font-weight: 600; font-size: 12px;")
            val_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row.addWidget(label)
            row.addStretch(1)
            row.addWidget(val_label)
            layout.addLayout(row)
            self.labels[label_text] = val_label

    def update_status(self, key: str, value: str):
        if key in self.labels:
            self.labels[key].setText(value)

    def set_mode(self, mode: str):
        self.update_status("Current Mode", mode)


class Sidebar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(260)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)

        self.status_card = StatusCard()
        layout.addWidget(self.status_card)

        actions_panel = QFrame()
        actions_panel.setObjectName("panel")
        actions_layout = QVBoxLayout(actions_panel)
        actions_layout.setContentsMargins(14, 14, 14, 14)
        actions_layout.setSpacing(8)

        header = QLabel("RECENT ACTIONS")
        header.setObjectName("sectionHeader")
        actions_layout.addWidget(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(6)
        self.list_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.list_container)
        actions_layout.addWidget(self.scroll)

        layout.addWidget(actions_panel, 1)

    def add_action(self, text: str):
        item = ActionItem(text)
        self.list_layout.insertWidget(0, item)  # newest on top
        fade_in(item)
