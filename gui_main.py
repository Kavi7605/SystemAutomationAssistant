import sys
from PySide6.QtWidgets import QApplication
from src.gui.main_window import MainWindow
from src.utils.logger import setup_logger

from src.gui.backend.automation_backend import AutomationBackend

logger = setup_logger("gui_main")

def main():
    print("Launching System Automation Assistant GUI...")
    app = QApplication(sys.argv)
    
    window = MainWindow()
    backend = AutomationBackend()
    window.set_backend(backend)
    
    window.showMaximized()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
