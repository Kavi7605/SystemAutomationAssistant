import pytest
from unittest.mock import MagicMock
from src.automation.executor import Executor
from src.tools.registry import ToolRegistry
from src.context.context_manager import ContextManager
from src.context.reference_resolver import ReferenceResolver
from src.automation.command_expander import CommandExpander

class TestSequentialReferenceResolution:
    def setup_method(self):
        self.registry = MagicMock(spec=ToolRegistry)
        self.registry.execute_tool.return_value = {"status": "success", "message": "ok"}
        
        self.context_manager = ContextManager()
        self.reference_resolver = ReferenceResolver(self.context_manager)
        
        self.executor = Executor(
            registry=self.registry,
            context_manager=self.context_manager,
            reference_resolver=self.reference_resolver
        )
        self.command_expander = CommandExpander(self.reference_resolver)

    def test_open_discord_and_close_it(self):
        commands = [
            {"action": "open_application", "parameters": {"application_name": "discord"}},
            {"action": "close_application", "parameters": {"application_name": "it"}}
        ]
        
        commands = self.command_expander.expand(commands)
        self.executor.execute(commands)
        
        # Verify first call
        first_call = self.registry.execute_tool.call_args_list[0]
        assert first_call[0][0] == "open_application"
        assert first_call[1]["application_name"] == "discord"
        
        # Verify second call resolved "it" to "discord" sequentially
        second_call = self.registry.execute_tool.call_args_list[1]
        assert second_call[0][0] == "close_application"
        assert second_call[1]["application_name"] == "discord"

    def test_open_discord_and_open_whatsapp_and_close_it(self):
        commands = [
            {"action": "open_application", "parameters": {"application_name": "discord"}},
            {"action": "open_application", "parameters": {"application_name": "whatsapp"}},
            {"action": "close_application", "parameters": {"application_name": "it"}}
        ]
        
        commands = self.command_expander.expand(commands)
        self.executor.execute(commands)
        
        third_call = self.registry.execute_tool.call_args_list[2]
        assert third_call[0][0] == "close_application"
        assert third_call[1]["application_name"] == "whatsapp"

    def test_open_steam_and_focus_it_and_close_it(self):
        commands = [
            {"action": "open_application", "parameters": {"application_name": "steam"}},
            {"action": "focus_window", "parameters": {"window_name": "it"}},
            {"action": "close_application", "parameters": {"application_name": "it"}}
        ]
        
        commands = self.command_expander.expand(commands)
        self.executor.execute(commands)
        
        second_call = self.registry.execute_tool.call_args_list[1]
        assert second_call[0][0] == "focus_window"
        assert second_call[1]["window_name"] == "steam"
        
        third_call = self.registry.execute_tool.call_args_list[2]
        assert third_call[0][0] == "close_application"
        assert third_call[1]["application_name"] == "steam"

    def test_open_vscode_wait_until_it_opens_focus_it(self):
        commands = [
            {"action": "open_application", "parameters": {"application_name": "vscode"}},
            {"action": "wait", "parameters": {"wait_type": "window", "window_name": "it"}},
            {"action": "focus_window", "parameters": {"window_name": "it"}}
        ]
        
        commands = self.command_expander.expand(commands)
        self.executor.execute(commands)
        
        second_call = self.registry.execute_tool.call_args_list[1]
        assert second_call[0][0] == "wait"
        assert second_call[1]["window_name"] == "vscode"
        
        third_call = self.registry.execute_tool.call_args_list[2]
        assert third_call[0][0] == "focus_window"
        assert third_call[1]["window_name"] == "vscode"

    def test_focus_steam_focus_discord_focus_previous_app(self):
        commands = [
            {"action": "focus_window", "parameters": {"window_name": "steam"}},
            {"action": "focus_window", "parameters": {"window_name": "discord"}},
            {"action": "focus_window", "parameters": {"window_name": "previous app"}}
        ]
        
        commands = self.command_expander.expand(commands)
        self.executor.execute(commands)
        
        third_call = self.registry.execute_tool.call_args_list[2]
        assert third_call[0][0] == "focus_window"
        assert third_call[1]["window_name"] == "steam"

    def test_close_it_with_no_context(self):
        commands = [
            {"action": "close_application", "parameters": {"application_name": "it"}}
        ]
        
        commands = self.command_expander.expand(commands)
        result = self.executor.execute(commands)
        
        # Verify it safely fails and aborts
        assert result["status"] == "failed"
        assert "No application reference available" in result["results"][0]["result"]["message"]
        self.registry.execute_tool.assert_not_called()

    def test_open_github_focus_it_close_it_with_partial_success(self):
        commands = [
            {"action": "open_application", "parameters": {"application_name": "github"}},
            {"action": "focus_window", "parameters": {"window_name": "it"}},
            {"action": "close_application", "parameters": {"application_name": "it"}}
        ]
        
        # Make the focus call return partial_success
        self.registry.execute_tool.side_effect = [
            {"status": "success", "message": "Opened github"},
            {"status": "partial_success", "message": "GitHub Desktop found but Windows prevented foreground activation."},
            {"status": "success", "message": "Closed github"}
        ]
        
        commands = self.command_expander.expand(commands)
        self.executor.execute(commands)
        
        third_call = self.registry.execute_tool.call_args_list[2]
        assert third_call[0][0] == "close_application"
        assert third_call[1]["application_name"] == "github"

    def test_priority_open_whatsapp_focus_discord_close_it(self):
        commands = [
            {"action": "open_application", "parameters": {"application_name": "whatsapp"}},
            {"action": "focus_window", "parameters": {"window_name": "discord"}},
            {"action": "close_application", "parameters": {"application_name": "it"}}
        ]
        
        commands = self.command_expander.expand(commands)
        self.executor.execute(commands)
        
        third_call = self.registry.execute_tool.call_args_list[2]
        assert third_call[0][0] == "close_application"
        assert third_call[1]["application_name"] == "discord"
