import os
import sys
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.system_tools import CreateFileTool

def test_create_file():
    print("Testing CreateFileTool behavior:")
    tool = CreateFileTool()
    
    # Setup test files
    test_dir = os.path.abspath("test_create_file_dir")
    os.makedirs(test_dir, exist_ok=True)
    
    # Mock PathResolver to return the absolute test_dir
    from unittest.mock import patch
    with patch('src.tools.path_resolver.PathResolver.resolve') as mock_resolve:
        from src.tools.path_resolver import ResolvedPath
        mock_resolve.return_value = {
            "status": "success",
            "resolved_path": ResolvedPath(test_dir)
        }
        
        # Test 1: Create new file -> verify created message
        print("\n1. Create new file:")
        new_file = "new_file.txt"
        new_file_path = os.path.join(test_dir, new_file)
        if os.path.exists(new_file_path):
            os.remove(new_file_path)
            
        res1 = tool.execute(file_name=new_file, path=test_dir)
        print("   Result:", res1["status"])
        print("   Message:", res1["message"])
        assert res1["status"] == "success"
        assert f"File '{new_file}' created successfully" in res1["message"]
        assert os.path.exists(new_file_path)
        
        # Setup existing file with content
        existing_file = "existing_file.txt"
        existing_file_path = os.path.join(test_dir, existing_file)
        with open(existing_file_path, "w") as f:
            f.write("Important content")
            
        # Get initial stats
        initial_size = os.path.getsize(existing_file_path)
        initial_mtime = os.path.getmtime(existing_file_path)
        
        # Wait slightly to ensure timestamp would change if modified
        time.sleep(0.1)
        
        # Test 2: Create existing file -> verify already exists message
        print("\n2. Create existing file:")
        res2 = tool.execute(file_name=existing_file, path=test_dir)
        print("   Result:", res2["status"])
        print("   Message:", res2["message"])
        assert res2["status"] == "success"
        assert f"File '{existing_file}' already exists. No changes made." in res2["message"]
        
        # Test 3: Verify existing file contents remain unchanged
        print("\n3. Verify existing file contents remain unchanged:")
        with open(existing_file_path, "r") as f:
            content = f.read()
        print(f"   Content: '{content}'")
        assert content == "Important content"
        
        # Test 4: Verify file size & timestamp remains unchanged
        print("\n4. Verify file size and timestamp remains unchanged:")
        final_size = os.path.getsize(existing_file_path)
        final_mtime = os.path.getmtime(existing_file_path)
        print(f"   Initial Size: {initial_size}, Final Size: {final_size}")
        print(f"   Initial Mtime: {initial_mtime}, Final Mtime: {final_mtime}")
        assert final_size == initial_size
        assert final_mtime == initial_mtime
        
    print("\nAll CreateFileTool tests passed!")


