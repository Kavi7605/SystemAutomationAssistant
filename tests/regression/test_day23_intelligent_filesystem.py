import pytest
import os
import shutil
from pathlib import Path
from src.tools.path_resolver import PathResolver
from src.tools.filesystem_tools import (
    resolve_smart_item,
    CreateFolderTool,
    CreateFileTool,
    RenameItemTool,
    MoveFileTool,
    CopyFileTool,
    OpenItemTool,
    FindItemTool,
    ConfirmDeleteTool,
    CancelDeleteTool,
    DeleteItemTool
)
from src.context.context_manager import ContextManager

@pytest.fixture
def test_workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOMATION_WORKSPACE", str(tmp_path / "automation_workspace"))
    return tmp_path / "automation_workspace"

@pytest.fixture
def context():
    return ContextManager()

def test_path_resolver_known_locations():
    res = PathResolver.resolve("c drive")
    assert res["status"] == "success"
    assert res["resolved_path"].path.upper() == "C:\\"

def test_path_resolver_prepositions():
    res = PathResolver.resolve("inside downloads")
    assert res["status"] == "success"
    assert "Downloads" in res["resolved_path"].path

def test_find_item_tool(test_workspace, context):
    test_workspace.mkdir(parents=True, exist_ok=True)
    test_file = test_workspace / "findme.txt"
    test_file.touch()
    
    tool = FindItemTool()
    res = tool.execute("findme.txt", context_manager=context)
    
    assert res["status"] == "success"
    assert "findme.txt" in res["item_name"]
    assert context.get_filesystem_context()["last_found_file"] == res["item_name"]

def test_create_folder_tool(test_workspace, context):
    tool = CreateFolderTool()
    res = tool.execute("reports", context_manager=context)
    assert res["status"] == "success"
    assert "reports" in res["item_name"]

def test_create_file_tool(test_workspace, context):
    tool = CreateFileTool()
    res = tool.execute("test.txt", context_manager=context)
    assert res["status"] == "success"
    assert "test.txt" in res["item_name"]

def test_rename_item_tool(test_workspace, context):
    test_workspace.mkdir(parents=True, exist_ok=True)
    test_file = test_workspace / "old.txt"
    test_file.touch()
    
    tool = RenameItemTool()
    res = tool.execute("old.txt", "new.txt", context_manager=context)
    assert res["status"] == "success"
    assert "new.txt" in res["item_name"]
    assert (test_workspace / "new.txt").exists()

def test_move_item_tool(test_workspace, context):
    test_workspace.mkdir(parents=True, exist_ok=True)
    test_file = test_workspace / "move.txt"
    test_file.touch()
    dest_folder = test_workspace / "dest"
    dest_folder.mkdir()
    
    tool = MoveFileTool()
    res = tool.execute("move.txt", "dest", context_manager=context)
    assert res["status"] == "success"
    assert (dest_folder / "move.txt").exists()

def test_copy_item_tool(test_workspace, context):
    test_workspace.mkdir(parents=True, exist_ok=True)
    test_file = test_workspace / "copy.txt"
    test_file.touch()
    dest_folder = test_workspace / "dest2"
    dest_folder.mkdir()
    
    tool = CopyFileTool()
    res = tool.execute("copy.txt", "dest2/copy.txt", context_manager=context)
    assert res["status"] == "success"
    assert (test_workspace / "copy.txt").exists()
    assert (dest_folder / "copy.txt").exists()

def test_delete_confirmation(test_workspace, context):
    test_workspace.mkdir(parents=True, exist_ok=True)
    test_file = test_workspace / "delete.txt"
    test_file.touch()
    
    tool = DeleteItemTool()
    res = tool.execute("delete.txt", context_manager=context)
    assert res["status"] == "success"
    assert "pending_delete" in context.get_filesystem_context()
    assert context.get_filesystem_context()["pending_delete"] == str(test_file)
    assert test_file.exists()  
    
    confirm_tool = ConfirmDeleteTool()
    res_confirm = confirm_tool.execute(context_manager=context)
    assert res_confirm["status"] == "success"
    assert not test_file.exists()

def test_filesystem_context(test_workspace, context):
    test_workspace.mkdir(parents=True, exist_ok=True)
    target_folder = test_workspace / "context_folder"
    target_folder.mkdir()
    context.update_filesystem_state("last_opened_folder", str(target_folder))
    
    tool = CreateFileTool()
    res = tool.execute("context_file.txt", context_manager=context)
    assert res["status"] == "success"
    assert (target_folder / "context_file.txt").exists()

def test_multiple_search_results(test_workspace, context):
    test_workspace.mkdir(parents=True, exist_ok=True)
    f1 = test_workspace / "dup.txt"
    f1.touch()
    f2_dir = test_workspace / "sub"
    f2_dir.mkdir()
    f2 = f2_dir / "dup.txt"
    f2.touch()
    
    tool = FindItemTool()
    res = tool.execute("dup.txt", context_manager=context)
    assert res["status"] == "ambiguous"
    assert "matches" in res
    assert len(res["matches"]) == 2
