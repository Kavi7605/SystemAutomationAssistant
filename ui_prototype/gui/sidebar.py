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

        header = QLabel("STATUS")
        header.setObjectName("sectionHeader")
        layout.addWidget(header)

        self.cpu_bar, cpu_row = self._make_bar("CPU")
        self.mem_bar, mem_row = self._make_bar("Memory")
        layout.addLayout(cpu_row)
        layout.addLayout(mem_row)

        mode_row = QHBoxLayout()
        mode_label = QLabel("Mode")
        mode_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        self.mode_value = QLabel("Idle")
        self.mode_value.setStyleSheet(f"color: {ACCENT}; font-weight: 600; font-size: 12px;")
        mode_row.addWidget(mode_label)
        mode_row.addStretch(1)
        mode_row.addWidget(self.mode_value)
        layout.addLayout(mode_row)

    def _make_bar(self, label_text: str):
        row = QVBoxLayout()
        top = QHBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        value = QLabel("0%")
        value.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        top.addWidget(label)
        top.addStretch(1)
        top.addWidget(value)

        bar = QProgressBar()
        bar.setFixedHeight(6)
        bar.setTextVisible(False)
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setStyleSheet(f"""
            QProgressBar {{ background-color: {BORDER}; border-radius: 3px; }}
            QProgressBar::chunk {{ background-color: {ACCENT}; border-radius: 3px; }}
        """)
        bar._value_label = value
        row.addLayout(top)
        row.addWidget(bar)
        return bar, row

    def set_cpu(self, percent: int):
        self.cpu_bar.setValue(percent)
        self.cpu_bar._value_label.setText(f"{percent}%")

    def set_memory(self, percent: int):
        self.mem_bar.setValue(percent)
        self.mem_bar._value_label.setText(f"{percent}%")

    def set_mode(self, mode: str):
        self.mode_value.setText(mode)


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
        self.list_layout.addStretch(1)
        self.scroll.setWidget(self.list_container)
        actions_layout.addWidget(self.scroll)

        layout.addWidget(actions_panel, 1)

    def add_action(self, text: str):
        item = ActionItem(text)
        self.list_layout.insertWidget(0, item)  # newest on top
        fade_in(item)
