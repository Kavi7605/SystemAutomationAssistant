import json
import logging
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.planner.task_planner import TaskPlanner

def test_vs_names():
    planner = TaskPlanner()
    test_inputs = [
        "open visual studio",
        "open visual studio code",
        "open vscode",
        "open vs"
    ]

    for user_input in test_inputs:
        print(f"\n=================================")
        print(f"Testing input: '{user_input}'")
        tasks = planner.plan_tasks(user_input)
        print(f"Generated tasks: {tasks}")

if __name__ == "__main__":
    test_vs_names()
