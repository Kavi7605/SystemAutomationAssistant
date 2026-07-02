"""Reusable animation helpers: fade-in, slide-in, pulse, and a typing-dots widget."""
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Qt, QTimer, Signal
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget, QHBoxLayout, QLabel
from PySide6.QtGui import QColor


def fade_in(widget: QWidget, duration: int = 220):
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.OutCubic)
    anim.start(QPropertyAnimation.DeleteWhenStopped)
    widget._fade_anim = anim  # keep reference alive
    return anim


def slide_in(widget: QWidget, start_x_offset: int = 24, duration: int = 220):
    start_pos = widget.pos()
    widget.move(start_pos.x() + start_x_offset, start_pos.y())
    anim = QPropertyAnimation(widget, b"pos", widget)
    anim.setDuration(duration)
    anim.setStartValue(widget.pos())
    anim.setEndValue(start_pos)
    anim.setEasingCurve(QEasingCurve.OutCubic)
    anim.start(QPropertyAnimation.DeleteWhenStopped)
    widget._slide_anim = anim
    return anim


class PulseGlow:
    """Attach a pulsing opacity animation to a widget (e.g. active mic button)."""

    def __init__(self, widget: QWidget):
        self.widget = widget
        self.effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(self.effect)
        self.anim = QPropertyAnimation(self.effect, b"opacity", widget)
        self.anim.setDuration(900)
        self.anim.setStartValue(0.45)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.InOutSine)
        self.anim.setLoopCount(-1)

    def start(self):
        self.anim.start()

    def stop(self):
        self.anim.stop()
        self.effect.setOpacity(1.0)


class ThinkingDots(QWidget):
    """Animated '● ● ●' loading indicator."""

    def __init__(self, color: str = "#9DA5B4", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self._labels = []
        for _ in range(3):
            lbl = QLabel("●")
            lbl.setStyleSheet(f"color: {color}; font-size: 14px;")
            layout.addWidget(lbl)
            self._labels.append(lbl)
        self._index = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def start(self):
        self._timer.start(280)

    def stop(self):
        self._timer.stop()
        for lbl in self._labels:
            lbl.setStyleSheet(lbl.styleSheet().replace("opacity: 0.3;", ""))

    def _tick(self):
        for i, lbl in enumerate(self._labels):
            active = (i == self._index)
            opacity = "1.0" if active else "0.35"
            lbl.setStyleSheet(f"color: {lbl.property('base_color') or '#9DA5B4'}; ")
            lbl.setWindowOpacity(1.0)  # no-op, per-label opacity via stylesheet below
            lbl.setStyleSheet(f"color: rgba(157,165,180,{opacity});font-size:14px;")
        self._index = (self._index + 1) % 3
