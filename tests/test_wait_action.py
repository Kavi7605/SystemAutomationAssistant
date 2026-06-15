import sys
import os
import time

# Add the project root to sys.path so we can import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.system_tools import WaitTool
from src.utils.logger import setup_logger

logger = setup_logger("test_wait_action")

def test_wait_tool():
    print("Initializing WaitTool...")
    tool = WaitTool()

    print("\nTesting wait for 2 seconds...")
    start_time = time.time()
    result = tool.execute(seconds=2)
    end_time = time.time()
    
    elapsed = end_time - start_time
    print(f"Result: {result}")
    print(f"Elapsed time: {elapsed:.2f} seconds")
    
    if 1.9 <= elapsed <= 2.5:
        print("Wait time is within expected range.")
    else:
        print("Wait time was outside expected bounds.")

    print("\nTesting wait with invalid parameter (string instead of int)...")
    result = tool.execute(seconds="invalid")
    print(f"Result: {result}")

if __name__ == "__main__":
    test_wait_tool()
