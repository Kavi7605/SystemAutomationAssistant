import pytest
import os
from pathlib import Path
from unittest.mock import MagicMock
from src.automation.engine import AutomationEngine
from src.context.context_manager import ContextManager
from src.tools.filesystem_tools import get_workspace_root

@pytest.fixture
def test_workspace(tmp_path, monkeypatch):
    # Set workspace root to a temporary directory for testing
    monkeypatch.setattr("src.tools.filesystem_tools.get_workspace_root", lambda: tmp_path)
    root = tmp_path
    
    # Create files for testing
    (root / "notes.txt").touch()
    (root / "notes.pdf").touch()
    (root / "report.docx").touch()
    (root / "report.pdf").touch()
    
    # Voice normalization files
    (root / "Hello Automation.docx").touch()
    
    # Folder scoped files
    semester_8 = root / "semester 8"
    semester_8.mkdir()
    (semester_8 / "report.docx").touch()
    
    return root

@pytest.fixture
def engine(test_workspace):
    from src.automation.executor import Executor
    from src.tools.registry import ToolRegistry
    from src.core.history_manager import HistoryManager
    from src.tools.filesystem_tools import (
        CreateFileTool, CreateFolderTool, DeleteItemTool, 
        RenameItemTool, CopyFileTool, MoveFileTool, OpenWorkspaceItemTool
    )
    from src.tools.registry import ToolRegistry as RealToolRegistry
    
    parser = MagicMock()
    resolver = MagicMock()
    task_planner = MagicMock()
    history_manager = HistoryManager()
    
    registry = RealToolRegistry()
    registry.register(CreateFileTool())
    registry.register(CreateFolderTool())
    registry.register(DeleteItemTool())
    registry.register(RenameItemTool())
    registry.register(CopyFileTool())
    registry.register(MoveFileTool())
    registry.register(OpenWorkspaceItemTool())
    
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

def test_type_hint_expansion(engine, test_workspace):
    root = test_workspace
    # delete pdf notes
    engine.process_command("delete pdf notes")
    assert engine.task_planner.plan_tasks.call_count == 0
    assert not (root / "notes.pdf").exists()
    assert (root / "notes.txt").exists()

    # delete text notes
    engine.process_command("delete text notes")
    assert engine.task_planner.plan_tasks.call_count == 0
    assert not (root / "notes.txt").exists()

    # open pdf report
    engine.process_command("open pdf report")
    assert engine.task_planner.plan_tasks.call_count == 0
    
def test_create_command_coverage(engine, test_workspace):
    root = test_workspace
    # create text notes
    engine.process_command("create text notes")
    assert engine.task_planner.plan_tasks.call_count == 0
    assert (root / "notes.txt").exists()

    # create pdf report
    engine.process_command("create pdf report")
    assert engine.task_planner.plan_tasks.call_count == 0
    assert (root / "report.pdf").exists()
    
def test_folder_scoped_operations(engine, test_workspace):
    root = test_workspace
    # delete report in semester 8
    engine.process_command("delete report in semester 8")
    assert engine.task_planner.plan_tasks.call_count == 0
    assert not (root / "semester 8" / "report.docx").exists()
    # Should not have touched root report
    assert (root / "report.docx").exists()

def test_voice_normalization(engine, test_workspace):
    root = test_workspace
    
    # All these should be able to open Hello Automation.docx
    engine.process_command("open HelloAutomation")
    assert engine.task_planner.plan_tasks.call_count == 0
    
    engine.process_command("open hello automation")
    assert engine.task_planner.plan_tasks.call_count == 0
    
    engine.process_command("open hello-automation")
    assert engine.task_planner.plan_tasks.call_count == 0
    
    engine.process_command("open hello_automation")
    assert engine.task_planner.plan_tasks.call_count == 0

def test_filesystem_open_intent(engine):
    # Ensure explicit filesystem grammar prevents web search fallthrough
    
    cmd1 = engine._route_semantic_command("open missing report in semester 8")
    assert cmd1 and cmd1.get("action") == "open_workspace_item"
    
    cmd2 = engine._route_semantic_command("open document missing_report")
    assert cmd2 and cmd2.get("action") == "open_workspace_item"
    
    cmd3 = engine._route_semantic_command("open pdf missing_report")
    assert cmd3 and cmd3.get("action") == "open_workspace_item"
    
    cmd4 = engine._route_semantic_command("open file missing_file_name")
    assert cmd4 and cmd4.get("action") == "open_workspace_item"
    
    # Run one full execution just to verify it terminates inside filesystem logic
    engine.process_command("open missing report in semester 8")
    assert engine.task_planner.plan_tasks.call_count == 0
