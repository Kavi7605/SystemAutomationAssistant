import sys
import os

# Add the project root to sys.path so we can import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.system_tools import OpenUrlTool
from src.utils.logger import setup_logger

logger = setup_logger("test_open_url")

def test_open_url_tool():
    print("Initializing OpenUrlTool...")
    tool = OpenUrlTool()

    print("\nTesting open valid URL (https://youtube.com)...")
    result = tool.execute(url="https://youtube.com")
    print(f"Result: {result}")

    print("\nTesting open URL without scheme (github.com)...")
    result = tool.execute(url="github.com")
    print(f"Result: {result}")

    print("\nTesting open URL with missing parameter...")
    try:
        result = tool.execute(url="")
        print(f"Result: {result}")
    except TypeError as e:
        print(f"Caught expected TypeError: {e}")

if __name__ == "__main__":
    test_open_url_tool()
