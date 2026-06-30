from unittest.mock import MagicMock
from src.context.context_manager import ContextManager
from src.automation.executor import Executor

def test_power_confirmation_cleared_on_unrelated_command():
    context = ContextManager()
    context.update_system_state("pending_power_action", "shutdown")
    
    # Engine processing an unrelated command should clear the pending state
    parser = MagicMock()
    task_planner = MagicMock()
    executor = MagicMock()
    
    from src.automation.engine import AutomationEngine
    engine = AutomationEngine(
        parser=parser, 
        task_planner=task_planner, 
        executor=executor,
        resolver=MagicMock(),
        history_manager=MagicMock(),
        context_manager=context
    )
    
    # Issue unrelated command
    engine.process_command("open chrome")
    
    assert context.get_context_snapshot()["system_state"].get("pending_power_action") is None

def test_power_confirmation_preserved_on_matching_command():
    context = ContextManager()
    context.update_system_state("pending_power_action", "shutdown")
    
    parser = MagicMock()
    task_planner = MagicMock()
    executor = MagicMock()
    
    from src.automation.engine import AutomationEngine
    engine = AutomationEngine(
        parser=parser, 
        task_planner=task_planner, 
        executor=executor,
        resolver=MagicMock(),
        history_manager=MagicMock(),
        context_manager=context
    )
    
    engine.process_command("confirm shutdown")
    
    # Since executor logic in this test doesn't actually run (mocked), 
    # the pending action should NOT be cleared by the engine itself
    # It would be cleared by executor after execution
    assert context.get_context_snapshot()["system_state"].get("pending_power_action") == "shutdown"

def test_power_confirmation_cleared_by_cancel():
    context = ContextManager()
    context.update_system_state("pending_power_action", "shutdown")
    
    parser = MagicMock()
    task_planner = MagicMock()
    
    # We will use real executor to test the end-to-end context clearing
    from src.tools.registry import ToolRegistry
    from src.tools.system_control.power_actions_tools import CancelPowerActionTool
    registry = ToolRegistry()
    registry.register(CancelPowerActionTool())
    
    executor = Executor(registry=registry, context_manager=context)
    
    from src.automation.engine import AutomationEngine
    engine = AutomationEngine(
        parser=parser, 
        task_planner=task_planner, 
        executor=executor,
        resolver=MagicMock(),
        history_manager=MagicMock(),
        context_manager=context
    )
    
    # Engine routes "cancel" to cancel_power_action
    engine.process_command("cancel")
    
    assert context.get_context_snapshot()["system_state"].get("pending_power_action") is None

def test_power_confirmation_bypassed_by_diagnostic_commands():
    context = ContextManager()
    context.update_system_state("pending_power_action", "shutdown")
    
    parser = MagicMock()
    task_planner = MagicMock()
    executor = MagicMock()
    
    from src.automation.engine import AutomationEngine
    engine = AutomationEngine(
        parser=parser, 
        task_planner=task_planner, 
        executor=executor,
        resolver=MagicMock(),
        history_manager=MagicMock(),
        context_manager=context
    )
    
    engine.process_command("show context")
    assert context.get_context_snapshot()["system_state"].get("pending_power_action") == "shutdown"
    
    engine.process_command("debug context")
    assert context.get_context_snapshot()["system_state"].get("pending_power_action") == "shutdown"

def test_end_to_end_shutdown_confirmation_lifecycle():
    from src.tools.registry import ToolRegistry
    from src.tools.system_control.power_actions_tools import ShutdownTool, ConfirmPowerActionTool, CancelPowerActionTool
    from src.automation.engine import AutomationEngine
    from unittest.mock import patch
    
    context = ContextManager()
    registry = ToolRegistry()
    registry.register(ShutdownTool())
    registry.register(ConfirmPowerActionTool())
    registry.register(CancelPowerActionTool())
    
    executor = Executor(registry=registry, context_manager=context)
    engine = AutomationEngine(
        parser=MagicMock(), 
        task_planner=MagicMock(), 
        executor=executor,
        resolver=MagicMock(),
        history_manager=MagicMock(),
        context_manager=context
    )
    
    # 1. Initiate Shutdown
    engine.process_command("shutdown pc")
    assert context.get_context_snapshot()["system_state"].get("pending_power_action") == "shutdown"
    
    # 2. Check Context (Should not clear)
    engine.process_command("show context")
    assert context.get_context_snapshot()["system_state"].get("pending_power_action") == "shutdown"
    
    # 3. Confirm Shutdown (Mock the actual destructive subprocess)
    with patch('src.tools.system_control.power_actions_tools.subprocess.run') as mock_run:
        engine.process_command("confirm shutdown")
        mock_run.assert_called_once_with(["shutdown", "/s", "/t", "0"], check=True)
        
    assert context.get_context_snapshot()["system_state"].get("pending_power_action") is None
    assert context.get_context_snapshot()["system_state"].get("last_power_action") == "shutdown"

def test_end_to_end_restart_cancellation_lifecycle():
    from src.tools.registry import ToolRegistry
    from src.tools.system_control.power_actions_tools import RestartTool, CancelPowerActionTool
    from src.automation.engine import AutomationEngine
    
    context = ContextManager()
    registry = ToolRegistry()
    registry.register(RestartTool())
    registry.register(CancelPowerActionTool())
    
    executor = Executor(registry=registry, context_manager=context)
    engine = AutomationEngine(
        parser=MagicMock(), 
        task_planner=MagicMock(), 
        executor=executor,
        resolver=MagicMock(),
        history_manager=MagicMock(),
        context_manager=context
    )
    
    # 1. Initiate Restart
    engine.process_command("restart pc")
    assert context.get_context_snapshot()["system_state"].get("pending_power_action") == "restart"
    
    # 2. Check Context (Should not clear)
    engine.process_command("show context")
    assert context.get_context_snapshot()["system_state"].get("pending_power_action") == "restart"
    
    # 3. Cancel
    engine.process_command("cancel")
    assert context.get_context_snapshot()["system_state"].get("pending_power_action") is None
