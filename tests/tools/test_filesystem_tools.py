import pytest
import shutil
from src.tools.filesystem_tools import (
    CreateFolderTool,
    CreateFileTool,
    RenameItemTool,
    DeleteItemTool,
    CopyFileTool,
    MoveFileTool,
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
    assert "reports" in res["item_name"]
    
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
    assert "notes.txt" in res["item_name"]
    
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
    assert "new.txt" in res["item_name"]
    
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
    from src.tools.filesystem_tools import ConfirmDeleteTool
    from src.context.context_manager import ContextManager
    context = ContextManager()
    res = tool.execute("file.txt", context_manager=context)
    ConfirmDeleteTool().execute(context_manager=context)
    
    # Folder delete
    res2 = tool.execute("folder", context_manager=context)
    assert res2["status"] == "success"
    ConfirmDeleteTool().execute(context_manager=context)
    
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
