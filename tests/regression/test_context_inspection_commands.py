import pytest
from unittest.mock import MagicMock
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.automation.engine import AutomationEngine
from src.core.command_parser import CommandParser
from src.core.history_manager import HistoryManager
from src.planner.resolver import CommandResolver
from src.planner.task_planner import TaskPlanner
from src.automation.executor import Executor

class TestContextInspectionRouting:
    def setup_method(self):
        self.parser_mock = MagicMock(spec=CommandParser)
        self.resolver_mock = MagicMock(spec=CommandResolver)
        self.task_planner_mock = MagicMock(spec=TaskPlanner)
        self.executor_mock = MagicMock(spec=Executor)
        self.history_manager_mock = MagicMock(spec=HistoryManager)
        
        self.engine = AutomationEngine(
            parser=self.parser_mock,
            resolver=self.resolver_mock,
            task_planner=self.task_planner_mock,
            executor=self.executor_mock,
            history_manager=self.history_manager_mock
        )

    @pytest.mark.parametrize("command, expected_action", [
        ("show context", "debug_context"),
        ("debug context", "debug_context"),
        ("show state", "debug_state"),
        ("debug state", "debug_state"),
        ("what is my current app", "get_current_app"),
        ("current app", "get_current_app"),
        ("active app", "get_current_app"),
        ("what was my previous app", "get_previous_app"),
        ("previous app", "get_previous_app"),
        ("last app", "get_previous_app"),
        ("what apps have i opened", "get_opened_history"),
        ("what apps i have opened", "get_opened_history"),
        ("which apps have i opened", "get_opened_history"),
        ("show opened apps", "get_opened_history"),
        ("show opened apps history", "get_opened_history"),
        ("opened apps", "get_opened_history"),
        ("opened history", "get_opened_history"),
        ("show apps that i opened", "get_opened_history"),
        ("show apps i opened", "get_opened_history"),
        ("what apps i opened", "get_opened_history"),
        ("  WHAT   APPS   I HAVE   OPENED  ", "get_opened_history"),
        
        ("what apps have i focused", "get_focused_history"),
        ("what apps i have focused", "get_focused_history"),
        ("what app i have focused", "get_focused_history"),
        ("which apps have i focused", "get_focused_history"),
        ("show focused apps", "get_focused_history"),
        ("show focused apps history", "get_focused_history"),
        ("focused apps", "get_focused_history"),
        ("focused history", "get_focused_history"),
        ("show apps that i focused", "get_focused_history"),
        ("show apps i focused", "get_focused_history"),
        ("what apps i focused", "get_focused_history"),
        ("  WHAT   APPS   I HAVE   FOCUSED  ", "get_focused_history"),
        
        ("what apps have i closed", "get_closed_history"),
        ("what apps i have closed", "get_closed_history"),
        ("which apps have i closed", "get_closed_history"),
        ("show closed apps", "get_closed_history"),
        ("show closed apps history", "get_closed_history"),
        ("closed apps", "get_closed_history"),
        ("closed history", "get_closed_history"),
        ("show apps that i closed", "get_closed_history"),
        ("show apps i closed", "get_closed_history"),
        ("what apps i closed", "get_closed_history"),
        ("what apps i closed?", "get_closed_history"),
        ("what apps i closed.!", "get_closed_history"),
        ("  WHAT   APPS   I HAVE   CLOSED  ", "get_closed_history")
    ])
    def test_inspection_commands_bypass_planner(self, command, expected_action):
        self.engine.process_command(command)
        
        # Verify planner was bypassed
        self.task_planner_mock.plan_tasks.assert_not_called()
        self.parser_mock.parse_command.assert_not_called()
        
        # Verify executor received the deterministic route
        self.executor_mock.execute.assert_called_once()
        args, _ = self.executor_mock.execute.call_args
        
        # Since the engine puts single commands directly or wraps in list based on logic:
        # In engine.py line 512, if it's not a list, it's wrapped in a list for parsed_commands,
        # but in line 614 it extracts [0] if length is 1.
        passed_command = args[0]
        assert passed_command["action"] == expected_action
