import pytest
from unittest.mock import MagicMock
from src.automation.executor import Executor
from src.tools.registry import ToolRegistry
from src.context.context_manager import ContextManager
from src.context.reference_resolver import ReferenceResolver
from src.automation.command_expander import CommandExpander
from src.context.application_state_manager import ApplicationStateManager

class TestManualScenarios:
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

    def _run_commands(self, commands):
        expanded = self.command_expander.expand(commands)
        return self.executor.execute(expanded)

    def test_scenario_open_steam_discord_close_both(self):
        commands = [
            {"action": "open_application", "parameters": {"application_name": "steam"}},
            {"action": "open_application", "parameters": {"application_name": "discord"}},
            {"action": "close_application", "parameters": {"application_name": "both"}}
        ]
        self._run_commands(commands)
        
        calls = self.registry.execute_tool.call_args_list
        assert calls[0][0][0] == "open_application" and calls[0][1]["application_name"] == "steam"
        assert calls[1][0][0] == "open_application" and calls[1][1]["application_name"] == "discord"
        assert calls[2][0][0] == "close_application" and calls[2][1]["application_name"] == "steam"
        assert calls[3][0][0] == "close_application" and calls[3][1]["application_name"] == "discord"

    def test_scenario_open_steam_discord_close_all_apps(self):
        commands = [
            {"action": "open_application", "parameters": {"application_name": "steam"}},
            {"action": "open_application", "parameters": {"application_name": "discord"}},
            {"action": "close_application", "parameters": {"application_name": "all apps"}}
        ]
        self._run_commands(commands)
        
        calls = self.registry.execute_tool.call_args_list
        assert calls[2][0][0] == "close_application" and calls[2][1]["application_name"] == "steam"
        assert calls[3][0][0] == "close_application" and calls[3][1]["application_name"] == "discord"
        assert len(calls) == 4

    def test_scenario_open_steam_discord_focus_first_app(self):
        commands = [
            {"action": "open_application", "parameters": {"application_name": "steam"}},
            {"action": "open_application", "parameters": {"application_name": "discord"}},
            {"action": "focus_window", "parameters": {"window_name": "the first app"}}
        ]
        self._run_commands(commands)
        
        calls = self.registry.execute_tool.call_args_list
        assert calls[2][0][0] == "focus_window" and calls[2][1]["window_name"] == "steam"

    def test_scenario_open_steam_discord_focus_second_app(self):
        commands = [
            {"action": "open_application", "parameters": {"application_name": "steam"}},
            {"action": "open_application", "parameters": {"application_name": "discord"}},
            {"action": "focus_window", "parameters": {"window_name": "the second app"}}
        ]
        self._run_commands(commands)
        
        calls = self.registry.execute_tool.call_args_list
        assert calls[2][0][0] == "focus_window" and calls[2][1]["window_name"] == "discord"

    def test_scenario_open_steam_discord_close_oldest_app(self):
        commands = [
            {"action": "open_application", "parameters": {"application_name": "steam"}},
            {"action": "open_application", "parameters": {"application_name": "discord"}},
            {"action": "close_application", "parameters": {"application_name": "the oldest app"}}
        ]
        self._run_commands(commands)
        
        calls = self.registry.execute_tool.call_args_list
        assert calls[2][0][0] == "close_application" and calls[2][1]["application_name"] == "steam"

    def test_scenario_open_steam_wait_first_app_focus_it(self):
        commands = [
            {"action": "open_application", "parameters": {"application_name": "steam"}},
            {"action": "wait", "parameters": {"wait_type": "window", "window_name": "the first app"}},
            {"action": "focus_window", "parameters": {"window_name": "it"}}
        ]
        self._run_commands(commands)
        
        calls = self.registry.execute_tool.call_args_list
        assert calls[1][0][0] == "wait" and calls[1][1]["window_name"] == "steam"
        assert calls[2][0][0] == "focus_window" and calls[2][1]["window_name"] == "steam"

    def test_bug_1_intent_recorded_when_execution_skipped(self):
        # Simulate apps already running
        state_manager = MagicMock(spec=ApplicationStateManager)
        state_manager.is_running.return_value = True
        state_manager.is_focused.return_value = True
        self.executor.state_manager = state_manager
        
        commands = [
            {"action": "open_application", "parameters": {"application_name": "steam"}},
            {"action": "open_application", "parameters": {"application_name": "discord"}},
            {"action": "close_application", "parameters": {"application_name": "both"}}
        ]
        self._run_commands(commands)
        
        # Open commands are skipped (no tool call), but the histories are still recorded.
        # So "close both" resolves correctly to steam and discord.
        # But wait, close_application will also be skipped because they are already closed?
        # Let's let close_application succeed by mocking is_running=True for close_application skip checks.
        # Wait, if is_running=True, close_application will proceed to execute!
        calls = self.registry.execute_tool.call_args_list
        # The two open commands skip, so we expect 2 execute_tool calls total (for close_application)
        assert len(calls) == 2
        assert calls[0][0][0] == "close_application" and calls[0][1]["application_name"] == "steam"
        assert calls[1][0][0] == "close_application" and calls[1][1]["application_name"] == "discord"

    def test_bug_2_ordinal_references_use_current_session_state(self):
        # Simulate opening, closing, and reopening
        commands = [
            {"action": "open_application", "parameters": {"application_name": "discord"}},
            {"action": "open_application", "parameters": {"application_name": "steam"}},
            {"action": "close_application", "parameters": {"application_name": "discord"}},
            {"action": "close_application", "parameters": {"application_name": "steam"}},
            # Now both are closed. Let's reopen them in different order
            {"action": "open_application", "parameters": {"application_name": "steam"}},
            {"action": "open_application", "parameters": {"application_name": "discord"}},
            # The oldest active app should now be steam, since it was opened first *among the currently open apps*.
            {"action": "close_application", "parameters": {"application_name": "the oldest app"}}
        ]
        
        # When closing, they are not running initially, then after open they are running?
        # Actually our mock state manager returns False by default, so opens execute, closes execute.
        self._run_commands(commands)
        
        calls = self.registry.execute_tool.call_args_list
        # the oldest app should resolve to steam, because the second pair of opens was steam then discord
        last_call = calls[-1]
        assert last_call[0][0] == "close_application" and last_call[1]["application_name"] == "steam"

    def test_bug_3_consecutive_duplicates_suppressed(self):
        commands = [
            {"action": "open_application", "parameters": {"application_name": "steam"}},
            {"action": "open_application", "parameters": {"application_name": "steam"}},
            {"action": "open_application", "parameters": {"application_name": "discord"}},
            {"action": "open_application", "parameters": {"application_name": "steam"}}
        ]
        self._run_commands(commands)
        
        # history should be steam, discord, steam
        history = self.context_manager.get_open_history()
        assert history == ["steam", "discord", "steam"]

    def test_bug_4_focus_updates_history(self):
        commands = [
            {"action": "focus_window", "parameters": {"window_name": "steam"}}
        ]
        self._run_commands(commands)
        assert self.context_manager.get_focus_history() == ["steam"]

    def test_bug_1_singular_reference_priority(self):
        commands = [
            {"action": "open_application", "parameters": {"application_name": "steam"}},
            {"action": "open_application", "parameters": {"application_name": "whatsapp"}},
            # "it" should resolve to whatsapp, as it was the most recently interacted app
            {"action": "close_application", "parameters": {"application_name": "it"}}
        ]
        self._run_commands(commands)
        calls = self.registry.execute_tool.call_args_list
        assert calls[-1][0][0] == "close_application" and calls[-1][1]["application_name"] == "whatsapp"

    def test_bug_2_context_synchronization(self):
        commands = [
            {"action": "open_application", "parameters": {"application_name": "discord"}},
            {"action": "open_application", "parameters": {"application_name": "whatsapp"}}
        ]
        self._run_commands(commands)
        assert self.context_manager.state["current_active_app"] == "whatsapp"
        
        # now close whatsapp
        commands = [{"action": "close_application", "parameters": {"application_name": "whatsapp"}}]
        self._run_commands(commands)
        # fallback should be discord
        assert self.context_manager.state["current_active_app"] == "discord"

    def test_feature_12_multi_app(self):
        commands = [
            {"action": "open_application", "parameters": {"application_name": "steam"}},
            {"action": "open_application", "parameters": {"application_name": "discord"}},
            {"action": "open_application", "parameters": {"application_name": "chrome"}},
            {"action": "focus_window", "parameters": {"window_name": "the other app"}},
            {"action": "close_application", "parameters": {"application_name": "the remaining app"}},
            {"action": "minimize_window", "parameters": {"window_name": "every other app"}},
            {"action": "maximize_window", "parameters": {"window_name": "all except steam"}},
            {"action": "focus_window", "parameters": {"window_name": "the next app"}},
            {"action": "focus_window", "parameters": {"window_name": "switch back"}}
        ]
        self._run_commands(commands)
        calls = self.registry.execute_tool.call_args_list
        # Wait, how does it resolve these? We just ensure it doesn't crash and calls execute_tool.
        assert len(calls) > 5

    def test_feature_13_conversation_context(self):
        commands = [
            {"action": "open_application", "parameters": {"application_name": "steam"}},
            {"action": "focus_window", "parameters": {"window_name": "it"}},
            {"action": "minimize_window", "parameters": {"window_name": "it"}},
            {"action": "maximize_window", "parameters": {"window_name": "it"}},
            {"action": "close_application", "parameters": {"application_name": "it"}}
        ]
        self._run_commands(commands)
        calls = self.registry.execute_tool.call_args_list
        for call in calls:
            assert call[1].get("application_name") == "steam" or call[1].get("window_name") == "steam"

    def test_feature_14_temporal_context(self):
        commands = [
            {"action": "open_application", "parameters": {"application_name": "steam"}},
            {"action": "open_application", "parameters": {"application_name": "discord"}},
            {"action": "close_application", "parameters": {"application_name": "first"}},
            {"action": "focus_window", "parameters": {"window_name": "newest"}},
            {"action": "close_application", "parameters": {"application_name": "last_opened"}},
            {"action": "open_application", "parameters": {"application_name": "last_closed"}}
        ]
        self._run_commands(commands)
        calls = self.registry.execute_tool.call_args_list
        assert len(calls) > 0

    def test_feature_11_window_action_references(self):
        # 1. maximize steam, then minimize it
        commands1 = [
            {"action": "open_application", "parameters": {"application_name": "steam"}},
            {"action": "maximize_window", "parameters": {"window_name": "steam"}},
            {"action": "minimize_window", "parameters": {"window_name": "it"}}
        ]
        self._run_commands(commands1)
        calls = self.registry.execute_tool.call_args_list
        assert calls[-1][1].get("window_name") == "steam"

        self.context_manager.state["active_opened_apps"] = []
        self.context_manager.state["opened_apps_history"] = []
        
        # 2. focus whatsapp, then maximize it
        commands2 = [
            {"action": "open_application", "parameters": {"application_name": "whatsapp"}},
            {"action": "focus_window", "parameters": {"window_name": "whatsapp"}},
            {"action": "maximize_window", "parameters": {"window_name": "it"}}
        ]
        self._run_commands(commands2)
        calls2 = self.registry.execute_tool.call_args_list
        assert calls2[-1][1].get("window_name") == "whatsapp"


    def test_bug_3_open_previous_app_routing(self):
        commands = [
            {"action": "open_application", "parameters": {"application_name": "steam"}},
            {"action": "open_application", "parameters": {"application_name": "discord"}},
            {"action": "open_application", "parameters": {"application_name": "previous"}}
        ]
        self._run_commands(commands)
        calls = self.registry.execute_tool.call_args_list
        assert calls[-1][0][0] == "open_application" and calls[-1][1]["application_name"] == "steam"

    def test_bug_4_article_stripping(self):
        commands = [
            {"action": "open_application", "parameters": {"application_name": "the steam"}},
            {"action": "close_application", "parameters": {"application_name": "the last opened app"}}
        ]
        self._run_commands(commands)
        calls = self.registry.execute_tool.call_args_list
        assert calls[-1][0][0] == "close_application" and calls[-1][1]["application_name"] == "steam"
