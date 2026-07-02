import random
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import QTimer

from .theme import stylesheet, SUCCESS, DANGER, WARNING, ACCENT
from .top_bar import TopBar
from .chat_widget import ChatWidget
from .command_input import CommandInput
from .sidebar import Sidebar
from .status_bar import BottomStatusBar
from backend.fake_backend import FakeBackend


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Automation Assistant")
        self.resize(1180, 760)
        self.setStyleSheet(stylesheet())

        self.backend = FakeBackend()

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.top_bar = TopBar()
        root.addWidget(self.top_bar)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(16, 16, 16, 0)
        body_layout.setSpacing(16)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        self.chat = ChatWidget()
        self.command_input = CommandInput()
        center_layout.addWidget(self.chat, 1)
        center_layout.addWidget(self.command_input)

        self.sidebar = Sidebar()

        body_layout.addWidget(center, 1)
        body_layout.addWidget(self.sidebar)
        root.addWidget(body, 1)

        self.status_bar = BottomStatusBar()
        root.addWidget(self.status_bar)

        self.command_input.execute_requested.connect(self.handle_command)
        self.command_input.clear_requested.connect(self.chat_clear)

        self.chat.add_assistant_message(
            "Hi, I'm your System Automation Assistant. Type a command or use the mic to get started."
        )

        # Simulated CPU/Memory ticker for the status card
        self._sys_timer = QTimer(self)
        self._sys_timer.timeout.connect(self._tick_system_stats)
        self._sys_timer.start(2000)
        self._tick_system_stats()

    def chat_clear(self):
        # Clears only the input field; chat_widget clear kept explicit/opt-in.
        pass

    def handle_command(self, text: str):
        self.chat.add_user_message(text)
        self.status_bar.set_state("Thinking", WARNING)
        self.sidebar.status_card.set_mode("Thinking")
        self.chat.show_thinking()
        QTimer.singleShot(900, lambda: self._execute(text))

    def _execute(self, text: str):
        self.chat.hide_thinking()
        self.status_bar.set_state("Executing", ACCENT)
        self.sidebar.status_card.set_mode("Executing")
        QTimer.singleShot(500, lambda: self._finish(text))

    def _finish(self, text: str):
        try:
            result = self.backend.execute(text)
            self.chat.add_assistant_message(f"✓ {result}")
            self.sidebar.add_action(result)
            self.status_bar.set_state("Ready", SUCCESS)
        except Exception as exc:  # pragma: no cover - fake backend never raises
            self.chat.add_assistant_message(f"✗ Failed: {exc}")
            self.status_bar.set_state("Error", DANGER)
        finally:
            self.sidebar.status_card.set_mode("Idle")

    def _tick_system_stats(self):
        self.sidebar.status_card.set_cpu(random.randint(10, 60))
        self.sidebar.status_card.set_memory(random.randint(30, 75))
