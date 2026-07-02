from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
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
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setTextFormat(Qt.MarkdownText)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        self.label.setStyleSheet(f"color: {text_color}; font-size: 13px; background: transparent;")
        layout.addWidget(self.label)
        
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.setMaximumWidth(800) # Fallback, updated dynamically


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
        self.vbox.setSpacing(6)
        self.vbox.addStretch(1)

        self.scroll.setWidget(self.container)
        outer.addWidget(self.scroll)

        self._thinking_row = None
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Update max width of all bubbles to 70% of chat width
        max_w = int(self.width() * 0.7)
        for i in range(self.vbox.count() - 1): # Exclude stretch
            item = self.vbox.itemAt(i)
            if item and item.widget():
                row_widget = item.widget()
                # Find the ChatBubble in the row
                for child in row_widget.children():
                    if isinstance(child, ChatBubble):
                        child.setMaximumWidth(max_w)

    def clear(self):
        # Remove all items except the stretch at the end
        while self.vbox.count() > 1:
            item = self.vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
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
        # Apply current max width
        widget.setMaximumWidth(int(self.width() * 0.7) if self.width() > 0 else 600)
        self._scroll_to_bottom()
        return wrapper

    def add_user_message(self, text: str):
        self._add_row(ChatBubble(text, is_user=True), is_user=True)

    def add_assistant_message(self, text: str):
        self._add_row(ChatBubble(text, is_user=False), is_user=False)
        
    def stream_assistant_message(self, text: str, interval_ms: int = 25):
        bar = self.scroll.verticalScrollBar()
        self._should_auto_scroll = (bar.value() >= bar.maximum() - 20)
        
        self._stream_text = text
        self._stream_index = 0
        
        self._stream_bubble = ChatBubble("", is_user=False)
        self._add_row(self._stream_bubble, is_user=False)
        
        self._stream_timer = QTimer(self)
        self._stream_timer.timeout.connect(self._on_stream_tick)
        self._stream_timer.start(interval_ms)
        
    def _on_stream_tick(self):
        # Find next logical chunk boundary (space or newline) after min 20 chars
        min_chunk = 30
        end_idx = min(self._stream_index + min_chunk, len(self._stream_text))
        
        # Extend to next space or newline if we are in middle of word
        while end_idx < len(self._stream_text) and self._stream_text[end_idx] not in (' ', '\n'):
            end_idx += 1
            
        current_text = self._stream_text[:end_idx]
        
        label = self._stream_bubble.findChild(QLabel)
        if label:
            label.setText(current_text)
            
        self._stream_index = end_idx
        
        if self._should_auto_scroll:
            QTimer.singleShot(0, self._scroll_to_bottom)
            
        if self._stream_index >= len(self._stream_text):
            self._stream_timer.stop()

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
