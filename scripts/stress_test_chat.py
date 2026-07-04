import sys
import os
import random
import logging

# Setup basic logging to see geometries
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s')

# Adjust python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PySide6.QtCore import QTimer
from src.gui.chat_widget import ChatWidget

LONG_PARAGRAPH = "This is a very long paragraph intended to test word wrapping. " * 20

MARKDOWN_TEXT = f"""# Heading 1
## Heading 2

{LONG_PARAGRAPH}

Here is a bulleted list:
* Item A
* Item B
* Item C

Here is a numbered list:
1. First
2. Second
3. Third

```python
def test_function():
    print("This is a code block")
    return True
```

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Row 1    | Data A   | Data B   |
| Row 2    | Data C   | Data D   |

And another long paragraph to finish it off.
{LONG_PARAGRAPH}
"""

SHORT_TEXT = "Okay, I will do that."

class StressTester(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChatWidget Stress Tester")
        self.resize(800, 600)
        
        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.layout = QVBoxLayout(self.central)
        
        self.chat_widget = ChatWidget()
        self.layout.addWidget(self.chat_widget)
        
        self.btn = QPushButton("Start Test")
        self.btn.clicked.connect(self.start_test)
        self.layout.addWidget(self.btn)
        
        self.msg_count = 0
        self.max_msgs_per_cycle = 50
        self.cycles = 0
        self.max_cycles = 3
        
        self.inject_timer = QTimer(self)
        self.inject_timer.timeout.connect(self.inject_message)
        
        self.stream_timer = QTimer(self)
        self.stream_timer.timeout.connect(self.stream_next_char)
        self.current_stream_text = ""
        self.stream_index = 0
        
        self.window_state_timer = QTimer(self)
        self.window_state_timer.timeout.connect(self.toggle_window_state)
        self.is_maximized = False
        
        self.scroll_timer = QTimer(self)
        self.scroll_timer.timeout.connect(self.random_scroll)
        
        self.geom_timer = QTimer(self)
        self.geom_timer.timeout.connect(self.log_geometries)
        
    def start_test(self):
        self.btn.setEnabled(False)
        self.msg_count = 0
        self.cycles += 1
        logging.info(f"--- Starting Cycle {self.cycles} ---")
        self.inject_timer.start(500) # Slower injection to allow streaming
        self.window_state_timer.start(2500)
        self.scroll_timer.start(1500)
        self.geom_timer.start(1000)
        
    def inject_message(self):
        if self.stream_timer.isActive():
            return # Wait for stream to finish
            
        if self.msg_count >= self.max_msgs_per_cycle:
            self.inject_timer.stop()
            self.window_state_timer.stop()
            self.scroll_timer.stop()
            logging.info(f"Finished injecting {self.max_msgs_per_cycle} messages for cycle {self.cycles}.")
            
            if self.cycles >= self.max_cycles:
                logging.info("All cycles complete.")
                QTimer.singleShot(2000, QApplication.instance().quit)
            else:
                QTimer.singleShot(2000, self.clear_and_restart)
            return
            
        is_user = random.choice([True, False])
        msg_type = random.choice(["short", "markdown", "stream"])
        
        if is_user:
            text = SHORT_TEXT if msg_type == "short" else f"User asked a complex question: {SHORT_TEXT}"
            self.chat_widget.add_user_message(f"[{self.msg_count}] {text}")
        else:
            if msg_type == "stream":
                self.current_stream_text = MARKDOWN_TEXT if random.choice([True, False]) else SHORT_TEXT
                self.stream_index = 0
                self.chat_widget.stream_assistant_message("") # start empty stream
                self.stream_timer.start(5) # fast char-by-char streaming
            elif msg_type == "markdown":
                self.chat_widget.add_assistant_message(f"[{self.msg_count}] {MARKDOWN_TEXT}")
            else:
                self.chat_widget.add_assistant_message(f"[{self.msg_count}] {SHORT_TEXT}")
            
        self.msg_count += 1
        
    def stream_next_char(self):
        if self.stream_index < len(self.current_stream_text):
            # Stream chunk of chars to be realistic but not infinitely slow
            chunk_size = random.randint(1, 10)
            next_index = min(self.stream_index + chunk_size, len(self.current_stream_text))
            
            chunk = self.current_stream_text[self.stream_index:next_index]
            self.stream_index = next_index
            
            # Use interval_ms=0 because we manage the timer
            self.chat_widget.stream_assistant_message(self.current_stream_text[:self.stream_index], interval_ms=0)
        else:
            self.stream_timer.stop()
        
    def toggle_window_state(self):
        if self.is_maximized:
            self.showNormal()
            self.is_maximized = False
            logging.info("Window Restored")
        else:
            self.showMaximized()
            self.is_maximized = True
            logging.info("Window Maximized")
            
    def random_scroll(self):
        bar = self.chat_widget.scroll.verticalScrollBar()
        if bar.maximum() > 0:
            val = random.choice([0, bar.maximum() // 2, bar.maximum()])
            bar.setValue(val)
            logging.info(f"Random scroll to {val} (max: {bar.maximum()})")
            
    def clear_and_restart(self):
        logging.info("Clearing chat widget...")
        self.chat_widget.clear()
        self.start_test()
        
    def log_geometries(self):
        vbox = self.chat_widget.vbox
        scroll = self.chat_widget.scroll
        container = self.chat_widget.container
        viewport = scroll.viewport()
        
        logging.debug("--- Geometry Snapshot ---")
        logging.debug(f"Viewport: {viewport.geometry()}")
        logging.debug(f"Container: {container.geometry()}")
        logging.debug(f"Container sizeHint: {container.sizeHint()}")
        logging.debug(f"Scrollbar Value: {scroll.verticalScrollBar().value()}, Max: {scroll.verticalScrollBar().maximum()}")
        
        missing_count = 0
        overlap_count = 0
        last_bottom = 0
        
        for i in range(vbox.count()):
            item = vbox.itemAt(i)
            if item and item.widget():
                w = item.widget()
                geom = w.geometry()
                
                if geom.height() == 0 and w.isVisible():
                    missing_count += 1
                
                if geom.top() < last_bottom and i > 1: # Ignore stretch at 0
                    overlap_count += 1
                last_bottom = geom.bottom()
                
        if missing_count > 0:
            logging.warning(f"{missing_count} wrappers have height 0!")
        if overlap_count > 0:
            logging.warning(f"{overlap_count} wrappers are overlapping!")
            
        last_item = vbox.itemAt(vbox.count() - 2)
        if last_item and last_item.widget():
            last_w = last_item.widget()
            if last_w.geometry().bottom() > container.height():
                logging.warning(f"Container height ({container.height()}) is SMALLER than last widget bottom ({last_w.geometry().bottom()})!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StressTester()
    window.show()
    QTimer.singleShot(500, window.start_test)
    sys.exit(app.exec())
