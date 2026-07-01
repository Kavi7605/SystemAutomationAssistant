import pytest
import os
from unittest.mock import MagicMock
from src.automation.engine import AutomationEngine
from src.context.context_manager import ContextManager
from src.tools.filesystem_tools import get_workspace_root

@pytest.fixture
def test_workspace(tmp_path, monkeypatch):
    # Set workspace root to a temporary directory for testing
    os.environ["AUTOMATION_WORKSPACE"] = str(tmp_path)
    root = get_workspace_root()
    
    # Patch expanduser and get_real_desktop_path
    monkeypatch.setattr(os.path, "expanduser", lambda x: str(tmp_path) if x == "~" else str(tmp_path))
    monkeypatch.setattr("src.tools.path_resolver.get_real_desktop_path", lambda: str(tmp_path / "Desktop"))
    
    # Create ambiguous files
    (root / "REPORT.docx").touch()
    (root / "REPORT.pdf").touch()
    (root / "report.txt").touch()
    
    # Create single file for normal resolution
    (root / "unique_file.txt").touch()
    
    return root

@pytest.fixture
def engine(test_workspace):
    from src.automation.executor import Executor
    from src.tools.registry import ToolRegistry
    from src.core.history_manager import HistoryManager
    from src.tools.filesystem_tools import (
        CreateFileTool, CreateFolderTool, DeleteItemTool, 
        RenameItemTool, CopyFileTool, MoveFileTool, OpenItemTool, ConfirmDeleteTool
    )
    
    parser = MagicMock()
    resolver = MagicMock()
    resolver.resolve.side_effect = lambda x: x
    task_planner = MagicMock()
    history_manager = MagicMock()
    
    registry = ToolRegistry()
    registry.register(CreateFileTool())
    registry.register(CreateFolderTool())
    registry.register(DeleteItemTool())
    registry.register(RenameItemTool())
    registry.register(CopyFileTool())
    registry.register(MoveFileTool())
    registry.register(OpenItemTool())
    registry.register(ConfirmDeleteTool())
    
    executor = Executor(registry=registry)
    
    eng = AutomationEngine(
        parser=parser,
        resolver=resolver,
        task_planner=task_planner,
        executor=executor,
        history_manager=history_manager
    )
    eng.context_manager = ContextManager()
    executor.context_manager = eng.context_manager
    
    # Mock Planner to count calls
    eng.task_planner.plan_tasks.return_value = ["mock_task"]
    
    return eng

def test_document_type_resolution(engine):
    # "delete document report" should prioritize .docx
    engine.process_command("delete doc file report")
    engine.process_command("yes")

    assert engine.task_planner.plan_tasks.call_count == 0
    assert engine.context_manager.state["pending_disambiguation"] is None

    # REPORT.docx should be deleted
    root = get_workspace_root()
    assert not (root / "REPORT.docx").exists()
    assert (root / "REPORT.pdf").exists()

def test_pdf_type_resolution(engine):
    # "delete pdf file report" should prioritize .pdf
    engine.process_command("delete pdf file report")
    engine.process_command("yes")

    assert engine.task_planner.plan_tasks.call_count == 0
    assert engine.context_manager.state["pending_disambiguation"] is None

    # REPORT.pdf should be deleted
    root = get_workspace_root()
    assert not (root / "REPORT.pdf").exists()
    assert (root / "REPORT.docx").exists()

def test_interactive_disambiguation_flow(engine):
    # Trigger ambiguous response
    engine.process_command("delete report")
    
    # State should be active
    assert engine.context_manager.state["pending_disambiguation"] is not None
    assert engine.context_manager.state["pending_disambiguation"]["prompt"] == "delete report"
    assert engine.context_manager.state["pending_disambiguation"]["action"] == "delete_item"
    assert len(engine.context_manager.state["pending_disambiguation"]["matches"]) == 3
    assert engine.task_planner.plan_tasks.call_count == 0
    
    # Invalid selection should keep state active
    engine.process_command("9")
    assert engine.context_manager.state["pending_disambiguation"] is not None
    assert engine.task_planner.plan_tasks.call_count == 0
    
    # Non-digit input that isn't cancel implicitly cancels state and proceeds as new command
    engine.process_command("what is this")
    assert engine.context_manager.state.get("pending_disambiguation") is None
    
    # We must trigger ambiguous response again since we cancelled it
    engine.process_command("delete report")
    assert engine.context_manager.state.get("pending_disambiguation") is not None
    
    # Valid selection should execute and clear state
    # Delete the first match
    matches = engine.context_manager.state["pending_disambiguation"]["matches"]
    engine.process_command("1")
    engine.process_command("yes")
    
    assert engine.context_manager.state["pending_disambiguation"] is None
    assert engine.task_planner.plan_tasks.call_count == 1
    
    from pathlib import Path
    assert not Path(matches[0]).exists()

def test_interactive_disambiguation_cancel(engine):
    engine.process_command("delete report")
    
    assert engine.context_manager.state["pending_disambiguation"] is not None
    
    # Cancel selection
    engine.process_command("cancel")
    
    assert engine.context_manager.state["pending_disambiguation"] is None
    assert engine.task_planner.plan_tasks.call_count == 0
    
    # Files should still exist
    root = get_workspace_root()
    assert (root / "REPORT.docx").exists()
    assert (root / "REPORT.pdf").exists()
    assert (root / "report.txt").exists()
