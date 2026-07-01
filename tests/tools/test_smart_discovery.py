import pytest
from src.tools.filesystem_tools import resolve_smart_item, get_workspace_root

@pytest.fixture
def workspace():
    root = get_workspace_root()
    # Create test structure
    (root / "Semester 8").mkdir(parents=True, exist_ok=True)
    (root / "Semester 8" / "report.docx").touch()
    (root / "ambiguous_file.txt").touch()
    (root / "ambiguous_file.pdf").touch()
    
    yield root
    
    # Cleanup
    import shutil
    for item in root.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)

def test_resolve_exact_match(workspace):
    res = resolve_smart_item("Semester 8")
    assert res["status"] == "success"
    assert res["resolved_name"] == "Semester 8"
    
def test_resolve_recursive_base_name(workspace):
    res = resolve_smart_item("report")
    assert res["status"] == "success"
    # It should return relative path or correct nested path
    assert "Semester 8" in str(res["path"])

def test_resolve_ambiguous(workspace):
    res = resolve_smart_item("ambiguous_file")
    assert res["status"] == "ambiguous"
    assert len(res["matches"]) == 2

def test_resolve_not_found(workspace):
    res = resolve_smart_item("doesnotexist")
    assert res["status"] == "not_found"
