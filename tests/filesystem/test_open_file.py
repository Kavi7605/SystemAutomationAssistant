import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.system_tools import OpenFileTool
from src.core.command_parser import CommandParser
from src.automation.engine import AutomationEngine

def test_open_file():
    print("Testing OpenFileTool behavior:")
    from src.tools.system_tools import OpenFileTool
    tool = OpenFileTool()
    
    # Setup test files
    test_dir = os.path.abspath("test_open_file_dir")
    os.makedirs(test_dir, exist_ok=True)
    
    # Mock PathResolver and os.startfile
    from unittest.mock import patch
    with patch('src.tools.path_resolver.PathResolver.resolve') as mock_resolve, \
         patch('os.startfile') as mock_startfile:
        from src.tools.path_resolver import ResolvedPath
        mock_resolve.return_value = {
            "status": "success",
            "resolved_path": ResolvedPath(test_dir)
        }
        
        txt_path = os.path.join(test_dir, "existing.txt")
        with open(txt_path, "w") as f:
            f.write("Hello")
            
        docx_path = os.path.join(test_dir, "existing.docx")
        with open(docx_path, "w") as f:
            f.write("Fake docx content")
            
        # Test 3: Open existing txt file
        print("3. Open existing txt file:")
        res3 = tool.execute(file_name="existing.txt", path=test_dir)
        print("   Result:", res3["status"])
        print("   Message:", res3["message"])
        assert res3["status"] == "success"
        
        # Test 4: Open existing docx
        print("4. Open existing docx file:")
        res4 = tool.execute(file_name="existing.docx", path=test_dir)
        print("   Result:", res4["status"])
        print("   Message:", res4["message"])
        assert res4["status"] == "success"
        
        # Test 5: Open missing file
        print("5. Open missing file:")
        res5 = tool.execute(file_name="missing.pdf", path=test_dir)
        print("   Result:", res5["status"])
        print("   Message:", res5["message"])
        assert res5["status"] == "failed"
        assert "File does not exist" in res5["message"]

    print("\nAll OpenFileTool tests passed!")


