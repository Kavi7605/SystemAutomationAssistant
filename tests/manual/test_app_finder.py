import logging
import json
from src.tools.application_finder import ApplicationFinder
from src.tools.system_tools import OpenApplicationTool
from src.utils.logger import setup_logger

logger = setup_logger("test_app_finder")

def run_tests():
    finder = ApplicationFinder()
    finder.refresh_application_index()
    
    # Dump out UWP apps to verify
    uwp_count = sum(1 for name, app in finder.app_index.items() if "shell:appsfolder" in app['path'].lower())
    print(f"Discovered {uwp_count} UWP apps out of {len(finder.app_index)} total apps.")
    
    test_cases = [
        "calculator",
        "calc",
        "whatsapp",
        "steam",
        "discord",
        "edge",
        "fakeapp123"
    ]
    
    tool = OpenApplicationTool(finder)
    
    for test in test_cases:
        print(f"\n=================================")
        print(f"Testing: open {test}")
        print(f"=================================")
        result = tool.execute(test)
        print(f"Result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    run_tests()
