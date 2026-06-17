import json
import logging
import sys
import os

# Add the project root to sys.path so we can import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.planner.task_planner import TaskPlanner
from src.core.command_parser import CommandParser
from src.llm.ollama_client import OllamaClient
from src.tools.registry import ToolRegistry

def test_planner_edge_cases():
    print("Initializing TaskPlanner and CommandParser...")
    planner = TaskPlanner()
    client = OllamaClient(host="http://localhost:11434", model="gemma3:4b")
    registry = ToolRegistry()
    parser = CommandParser(client=client, registry=registry)

    test_inputs = [
        "create folder named testing in c drive",
        "create folder work inside d drive",
        "create folder reports in downloads",
        "create folder internship reports inside C:\\Kavi\\Work\\Degree\\Charusat\\SEM 7",
        "search 4k wallpapers ghost of yotei",
        "search ghost of yotei wallpaper",
        "google latest cyber security news",
        "look up red dead redemption wallpaper",
        "search best python tutorials and create folder python in c drive",
    ]

    for user_input in test_inputs:
        print(f"\n=================================")
        print(f"Testing input: '{user_input}'")
        
        tasks = planner.plan_tasks(user_input)
        print(f"Generated tasks: {tasks}")
        
        for task in tasks:
            print(f"  Parsing task: '{task}'")
            parsed = parser.parse_command(task)
            print(f"  Parsed JSON: {json.dumps(parsed, indent=2)}")

if __name__ == "__main__":
    test_planner_edge_cases()
