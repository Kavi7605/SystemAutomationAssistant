import json
import sys
import os

# Add the project root to sys.path so we can import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.system_tools import CloseApplicationTool
from src.utils.logger import setup_logger

logger = setup_logger("test_close_app")

def test_close_app_edge_cases():
    print("Initializing CloseApplicationTool...")
    tool = CloseApplicationTool()

    test_inputs = [
        "whatsapp",
        "calculator",
        "discord",
        "steam",
        "vscode",
        "github desktop"
    ]

    for app_name in test_inputs:
        print(f"\n=================================")
        print(f"Testing close: '{app_name}'")
        
        # Note: This will actually attempt to close these applications if they are running.
        # This is expected behavior for testing the process matching logic.
        result = tool.execute(application_name=app_name)
        print(f"Result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    test_close_app_edge_cases()
