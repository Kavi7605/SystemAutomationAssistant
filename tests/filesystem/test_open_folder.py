import sys
import os

# Add the project root to sys.path so we can import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.system_tools import OpenFolderTool
from src.utils.logger import setup_logger

logger = setup_logger("test_open_folder")

def test_open_folder_tool():
    print("Initializing OpenFolderTool...")
    tool = OpenFolderTool()

    print("\nTesting opening Downloads folder...")
    result = tool.execute(folder_name="downloads")
    print(f"Result: {result}")

    print("\nTesting opening Documents folder...")
    result = tool.execute(folder_name="documents")
    print(f"Result: {result}")

    print("\nTesting opening an unsupported folder...")
    result = tool.execute(folder_name="system32")
    print(f"Result: {result}")

    print("\nTesting opening with missing parameter...")
    result = tool.execute(folder_name="")
    print(f"Result: {result}")

if __name__ == "__main__":
    test_open_folder_tool()
