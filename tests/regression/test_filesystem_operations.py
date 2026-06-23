import pytest
from unittest.mock import MagicMock
from src.automation.engine import AutomationEngine

@pytest.fixture
def mock_engine():
    parser = MagicMock()
    resolver = MagicMock()
    task_planner = MagicMock()
    executor = MagicMock()
    history_manager = MagicMock()
    
    return AutomationEngine(
        parser=parser,
        resolver=resolver,
        task_planner=task_planner,
        executor=executor,
        history_manager=history_manager
    )

def test_deterministic_routing_create_folder_variants(mock_engine):
    commands = [
        "create folder reports",
        "create demo folder",
        "make folder reports",
        "new folder reports",
        "make a folder called reports",
        "create a folder called reports"
    ]
    for cmd in commands:
        res = mock_engine._route_semantic_command(cmd)
        assert res is not None, f"Failed on command: {cmd}"
        assert res["action"] == "create_folder"
        assert res["parameters"]["folder_name"] in ["reports", "demo"]

def test_deterministic_routing_create_file_variants(mock_engine):
    commands = [
        "create notes.txt",
        "create file notes.txt",
        "make file notes.txt",
        "new file notes.txt",
        "make a file called notes.txt",
        "create a file called notes.txt"
    ]
    for cmd in commands:
        res = mock_engine._route_semantic_command(cmd)
        assert res is not None, f"Failed on command: {cmd}"
        assert res["action"] == "create_file"
        assert res["parameters"]["file_name"] == "notes.txt"

def test_deterministic_routing_rename_variants(mock_engine):
    commands = [
        "rename notes.txt to report.txt",
        "rename file notes.txt to report.txt",
        "change notes.txt to report.txt"
    ]
    for cmd in commands:
        res = mock_engine._route_semantic_command(cmd)
        assert res is not None, f"Failed on command: {cmd}"
        assert res["action"] == "rename_item"
        assert res["parameters"]["source_name"] == "notes.txt"
        assert res["parameters"]["target_name"] == "report.txt"

def test_deterministic_routing_delete_variants(mock_engine):
    commands = [
        "delete notes.txt",
        "remove notes.txt",
        "remove file notes.txt",
        "remove folder notes"
    ]
    for cmd in commands:
        res = mock_engine._route_semantic_command(cmd)
        assert res is not None, f"Failed on command: {cmd}"
        assert res["action"] == "delete_item"
        assert res["parameters"]["item_name"] in ["notes.txt", "notes"]

def test_deterministic_routing_copy_variants(mock_engine):
    commands = [
        "copy notes.txt to backup.txt",
        "duplicate notes.txt to backup.txt"
    ]
    for cmd in commands:
        res = mock_engine._route_semantic_command(cmd)
        assert res is not None, f"Failed on command: {cmd}"
        assert res["action"] == "copy_file"
        assert res["parameters"]["source_name"] == "notes.txt"
        assert res["parameters"]["target_name"] == "backup.txt"

def test_deterministic_routing_move_variants(mock_engine):
    commands = [
        "move notes.txt to reports",
        "move notes.txt in reports",
        "move notes.txt into reports",
        "move notes.txt inside reports"
    ]
    for cmd in commands:
        res = mock_engine._route_semantic_command(cmd)
        assert res is not None, f"Failed on command: {cmd}"
        assert res["action"] == "move_file"
        assert res["parameters"]["source_name"] == "notes.txt"
        assert res["parameters"]["target_path"] == "reports"

def test_path_intent_protection(mock_engine):
    commands = [
        "create folder reports in desktop",
        "create folder backup in downloads",
        "create folder logs in c drive",
        "move file.txt to c drive",
        "copy notes.txt to desktop"
    ]
    for cmd in commands:
        res = mock_engine._route_semantic_command(cmd)
        assert res is not None, f"Failed to protect path on command: {cmd}"
        assert res["action"] == "reject_custom_path", f"Failed to protect path on command: {cmd}"

def test_multi_action_expansion(mock_engine):
    cmd = "create folder reports and create file notes.txt"
    normalized = mock_engine._normalize_app_chains(cmd)
    tasks = mock_engine._expand_multi_actions(normalized)
    
    assert len(tasks) == 2
    assert tasks[0] == "create folder reports"
    assert tasks[1] == "create file notes.txt"
    
    res1 = mock_engine._route_semantic_command(tasks[0])
    res2 = mock_engine._route_semantic_command(tasks[1])
    
    assert res1["action"] == "create_folder"
    assert res2["action"] == "create_file"

def test_deterministic_routing_create_folder_spaces(mock_engine):
    commands = [
        "create new folder HelloAutomation",
        "create new folder Semester 8",
        "create a folder named Internship Reports"
    ]
    expected = ["HelloAutomation", "Semester 8", "Internship Reports"]
    for cmd, exp in zip(commands, expected):
        res = mock_engine._route_semantic_command(cmd)
        assert res is not None, f"Failed on command: {cmd}"
        assert res["action"] == "create_folder"
        assert res["parameters"]["folder_name"] == exp

def test_deterministic_routing_create_documents(mock_engine):
    commands = [
        "create document Internship Report",
        "create word document Final Report",
        "create resume pdf file",
        "create notes text file"
    ]
    expected_files = [
        "Internship Report.docx",
        "Final Report.docx",
        "resume.pdf",
        "notes.txt"
    ]
    for cmd, exp in zip(commands, expected_files):
        res = mock_engine._route_semantic_command(cmd)
        assert res is not None, f"Failed on command: {cmd}"
        assert res["action"] == "create_file"
        assert res["parameters"]["file_name"] == exp

def test_deterministic_routing_folder_aware(mock_engine):
    commands = [
        "create document Internship Report in Semester 8",
        "create file notes.txt inside Reports"
    ]
    expected_files = ["Internship Report.docx", "notes.txt"]
    expected_folders = ["Semester 8", "Reports"]
    
    for cmd, f_name, f_folder in zip(commands, expected_files, expected_folders):
        res = mock_engine._route_semantic_command(cmd)
        assert res is not None, f"Failed on command: {cmd}"
        assert res["action"] == "create_file"
        assert res["parameters"]["file_name"] == f_name
        assert res["parameters"]["target_folder"] == f_folder

@pytest.fixture
def mock_open_priority_engine(mock_engine, monkeypatch):
    # Mock resolve_smart_item to test open command priority
    def mock_resolve(target, preferred_extension=None, **kwargs):
        if target == "Semester 8":
            return {"status": "success", "resolved_name": "Semester 8", "path": "mock"}
        if target == "Internship Report":
            return {"status": "success", "resolved_name": "Internship Report.docx", "path": "mock"}
        if target == "ambiguous":
            return {"status": "ambiguous", "matches": []}
        return {"status": "not_found"}
        
    monkeypatch.setattr("src.tools.filesystem_tools.resolve_smart_item", mock_resolve)
    
    # Mock _classify_target
    def mock_classify(target):
        if target.lower() in ["spotify", "steam"]:
            return {"action": "open_application", "parameters": {"application_name": target}}
        return {"action": "search_web", "parameters": {"query": target}}
        
    mock_engine._classify_target = mock_classify
    return mock_engine

def test_open_command_priority(mock_open_priority_engine):
    # Workspace items
    res1 = mock_open_priority_engine._route_semantic_command("open Semester 8")
    assert res1["action"] == "open_workspace_item"
    assert res1["parameters"]["item_name"] == "Semester 8"
    
    res2 = mock_open_priority_engine._route_semantic_command("open Internship Report")
    assert res2["action"] == "open_workspace_item"
    assert res2["parameters"]["item_name"] == "Internship Report"
    
    # Apps
    res3 = mock_open_priority_engine._route_semantic_command("open spotify")
    assert res3["action"] == "open_application"
    assert res3["parameters"]["application_name"] == "spotify"
    
    # Unknown
    res4 = mock_open_priority_engine._route_semantic_command("open unknownthing")
    assert res4["action"] == "search_web"
    assert res4["parameters"]["query"] == "unknownthing"
