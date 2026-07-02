import random
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QMessageBox
from PySide6.QtCore import QTimer

from .theme import stylesheet, SUCCESS, DANGER, WARNING, ACCENT
from .top_bar import TopBar
from .chat_widget import ChatWidget
from .command_input import CommandInput
from .sidebar import Sidebar
from .status_bar import BottomStatusBar


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Automation Assistant")
        self.resize(1180, 760)
        self.setStyleSheet(stylesheet())

        self.backend = None  # Will be set by gui_main.py

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
        self.command_input.voice_toggled.connect(self._handle_voice_toggle)

        self.chat.add_assistant_message(
            "Hi, I'm your System Automation Assistant. Type a command or use the mic to get started."
        )


    def set_backend(self, backend):
        self.backend = backend
        self.backend.command_finished.connect(self._on_command_finished)
        self.backend.voice_recognized.connect(self._on_voice_recognized)
        self.backend.voice_error.connect(self._on_voice_error)
        
        # Initial population of sidebar
        history = self.backend.get_recent_actions()
        for entry in history[-20:]: # max 20
            res = entry.get("execution_result", {})
            msg = res.get("message", "")
            if msg:
                self.sidebar.add_action(msg)
                
    def _handle_voice_toggle(self, active: bool):
        if self.backend:
            if active:
                self.command_input.set_text("")
                self.command_input.input.setPlaceholderText("Listening...")
                self.command_input.input.setEnabled(False)
                self.command_input.execute_btn.setEnabled(False)
                self.sidebar.status_card.update_status("Voice", "Listening")
                self.backend.start_voice()
            else:
                self.command_input.input.setPlaceholderText("Processing speech...")
                self.command_input.mic_btn.setEnabled(False)
                self.backend.stop_voice()
            
    def _on_voice_recognized(self, text: str):
        self._reset_voice_ui()
        self.sidebar.status_card.update_status("Voice", "Ready")
        self.handle_command(text)
        
    def _on_voice_error(self, error_msg: str):
        self._reset_voice_ui()
        self.sidebar.status_card.update_status("Voice", "Ready")
        self.chat.add_assistant_message(f"🎤 Voice Error: {error_msg}")
        
    def _reset_voice_ui(self):
        self.command_input._voice_active = False
        self.command_input._pulse.stop()
        self.command_input.mic_btn.setStyleSheet("")
        self.command_input.input.setPlaceholderText("Type or speak a command...")
        self.command_input.input.setEnabled(True)

    def chat_clear(self):
        reply = QMessageBox.question(self, 'Clear Chat', 'Clear current conversation?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.chat.clear()
            self.chat.add_assistant_message("Hi, I'm your System Automation Assistant.\n\nType a command or press the microphone to begin.")

    def handle_command(self, text: str):
        if not text.strip(): return
        self.chat.add_user_message(text)
        self.status_bar.set_state("Thinking", WARNING)
        
        self.sidebar.status_card.update_status("Automation Engine", "Processing")
        self.sidebar.status_card.update_status("Executor", "Active")
        self.sidebar.status_card.set_mode("Executing")
        self.sidebar.status_card.update_status("Current Task", text[:20] + "..." if len(text) > 20 else text)
        
        self.chat.show_thinking()
        
        # Disable input while processing
        self.command_input.set_enabled(False)
        
        if self.backend:
            self.backend.execute(text)

    def _on_command_finished(self, result: dict):
        self.chat.hide_thinking()
        
        # Re-enable inputs
        self.command_input.set_enabled(True)
        self.command_input.focus()
        
        parsed = result.get("parsed_command", {})
        if isinstance(parsed, list):
            action = "execute_queue"
        else:
            action = parsed.get("action", "unknown")
            
        exec_result = result.get("execution_result", {})
        
        from src.gui.response_formatter import ResponseFormatter
        rich_text, summary = ResponseFormatter.format_result(action, exec_result)
        
        self.chat.stream_assistant_message(rich_text)
        self.sidebar.add_action(summary)
        
        status = exec_result.get("status", "unknown")
        if status in ["success", "completed", "partial_success"]:
            self.status_bar.set_state("Ready", SUCCESS)
        else:
            self.status_bar.set_state("Error", DANGER)
            
        self.sidebar.status_card.update_status("Automation Engine", "Online")
        self.sidebar.status_card.update_status("Executor", "Idle")
        self.sidebar.status_card.set_mode("Idle")
        self.sidebar.status_card.update_status("Current Task", "None")

    def closeEvent(self, event):
        if self.backend:
            self.backend.shutdown()
        event.accept()
