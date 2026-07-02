from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt
from .theme import ACCENT, PANEL_ALT, TEXT, TEXT_SECONDARY
from .animations import fade_in, ThinkingDots


class ChatBubble(QFrame):
    def __init__(self, text: str, is_user: bool, parent=None):
        super().__init__(parent)
        color = ACCENT if is_user else PANEL_ALT
        text_color = "white" if is_user else TEXT
        self.setStyleSheet(
            f"QFrame {{ background-color: {color}; border-radius: 14px; }}"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(f"color: {text_color}; font-size: 13px; background: transparent;")
        layout.addWidget(label)
        self.setMaximumWidth(420)


class ChatWidget(QWidget):
    """Scrollable chat conversation, ChatGPT-style: user bubbles right, assistant left."""

    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.container = QWidget()
        self.vbox = QVBoxLayout(self.container)
        self.vbox.setContentsMargins(20, 20, 20, 20)
        self.vbox.setSpacing(12)
        self.vbox.addStretch(1)

        self.scroll.setWidget(self.container)
        outer.addWidget(self.scroll)

        self._thinking_row = None

    def _add_row(self, widget: QFrame, is_user: bool):
        row = QHBoxLayout()
        if is_user:
            row.addStretch(1)
            row.addWidget(widget)
        else:
            row.addWidget(widget)
            row.addStretch(1)
        wrapper = QWidget()
        wrapper.setLayout(row)
        self.vbox.insertWidget(self.vbox.count() - 1, wrapper)
        fade_in(widget)
        self._scroll_to_bottom()
        return wrapper

    def add_user_message(self, text: str):
        self._add_row(ChatBubble(text, is_user=True), is_user=True)

    def add_assistant_message(self, text: str):
        self._add_row(ChatBubble(text, is_user=False), is_user=False)

    def show_thinking(self):
        bubble = QFrame()
        bubble.setStyleSheet(f"QFrame {{ background-color: {PANEL_ALT}; border-radius: 14px; }}")
        layout = QHBoxLayout(bubble)
        layout.setContentsMargins(14, 10, 14, 10)
        dots = ThinkingDots()
        dots.start()
        layout.addWidget(dots)
        self._thinking_row = self._add_row(bubble, is_user=False)
        self._thinking_dots = dots

    def hide_thinking(self):
        if self._thinking_row is not None:
            self._thinking_dots.stop()
            self._thinking_row.setParent(None)
            self._thinking_row = None

    def _scroll_to_bottom(self):
        bar = self.scroll.verticalScrollBar()
        bar.setValue(bar.maximum())
