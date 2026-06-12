import json
from src.planner.task_planner import TaskPlanner

def test_planner():
    planner = TaskPlanner()
    tasks = planner.plan_tasks("open notepad and calc")
    print(f"Generated tasks: {tasks}")
    
    tasks = planner.plan_tasks("search chatgpt")
    print(f"Generated tasks: {tasks}")

if __name__ == "__main__":
    test_planner()
