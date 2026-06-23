import pytest
import os
import shutil
from pathlib import Path
from src.tools.filesystem_tools import (
    CreateFolderTool,
    CreateFileTool,
    RenameItemTool,
    DeleteItemTool,
    CopyFileTool,
    MoveFileTool,
    WORKSPACE_DIR,
    get_workspace_root
)

@pytest.fixture(autouse=True)
def setup_workspace():
    """Setup and teardown a clean workspace for tests."""
    root = get_workspace_root()
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    yield root
    if root.exists():
        shutil.rmtree(root)

def test_create_folder():
    tool = CreateFolderTool()
    res = tool.execute("reports")
    assert res["status"] == "success"
    assert res["item_name"] == "reports"
    
    # Check directory created
    root = get_workspace_root()
    assert (root / "reports").is_dir()
    
    # Test duplicate
    res2 = tool.execute("reports")
    assert res2["status"] == "success"
    assert "already exists" in res2["message"]
    
def test_create_file():
    tool = CreateFileTool()
    res = tool.execute("notes.txt")
    assert res["status"] == "success"
    assert res["item_name"] == "notes.txt"
    
    # Check file created
    root = get_workspace_root()
    assert (root / "notes.txt").is_file()
    
    # Test duplicate
    res2 = tool.execute("notes.txt")
    assert res2["status"] == "success"
    assert "already exists" in res2["message"]

def test_rename_item():
    CreateFileTool().execute("old.txt")
    tool = RenameItemTool()
    
    # Rename successful
    res = tool.execute("old.txt", "new.txt")
    assert res["status"] == "success"
    assert res["item_name"] == "new.txt"
    
    root = get_workspace_root()
    assert not (root / "old.txt").exists()
    assert (root / "new.txt").exists()
    
    # Missing source
    res2 = tool.execute("missing.txt", "target.txt")
    assert res2["status"] == "failed"
    assert "does not exist" in res2["message"]
    
    # Duplicate target
    CreateFileTool().execute("target.txt")
    res3 = tool.execute("new.txt", "target.txt")
    assert res3["status"] == "failed"
    assert "already exists" in res3["message"]

def test_delete_item():
    CreateFileTool().execute("file.txt")
    CreateFolderTool().execute("folder")
    
    tool = DeleteItemTool()
    
    # File delete
    res = tool.execute("file.txt")
    assert res["status"] == "success"
    assert res["item_name"] == "file.txt"
    assert res["message"] == "File deleted successfully."
    
    # Folder delete
    res2 = tool.execute("folder")
    assert res2["status"] == "success"
    assert res2["message"] == "Folder deleted successfully."
    
    root = get_workspace_root()
    assert not (root / "file.txt").exists()
    assert not (root / "folder").exists()
    
    # Missing item
    res3 = tool.execute("missing.txt")
    assert res3["status"] == "failed"
    assert "does not exist" in res3["message"]

def test_copy_file():
    CreateFileTool().execute("source.txt")
    tool = CopyFileTool()
    
    res = tool.execute("source.txt", "backup.txt")
    assert res["status"] == "success"
    assert res["item_name"] == "backup.txt"
    
    root = get_workspace_root()
    assert (root / "source.txt").exists()
    assert (root / "backup.txt").exists()
    
    # Missing source
    res2 = tool.execute("missing.txt", "backup.txt")
    assert res2["status"] == "failed"
    
    # Duplicate target
    res3 = tool.execute("source.txt", "backup.txt")
    assert res3["status"] == "failed"
    assert "already exists" in res3["message"]
    
def test_move_file():
    CreateFileTool().execute("source.txt")
    CreateFolderTool().execute("reports")
    tool = MoveFileTool()
    
    res = tool.execute("source.txt", "reports")
    assert res["status"] == "success"
    assert res["item_name"] == "source.txt"
    
    root = get_workspace_root()
    assert not (root / "source.txt").exists()
    assert (root / "reports" / "source.txt").exists()
    
    # Missing source
    res2 = tool.execute("missing.txt", "reports")
    assert res2["status"] == "failed"
