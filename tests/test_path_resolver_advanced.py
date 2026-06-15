import sys
import os
import shutil

# Add the project root to sys.path so we can import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.path_resolver import PathResolver
from src.tools.system_tools import CreateFileTool, CreateFolderTool, OpenFolderTool

def test_advanced():
    print("\n--- Advanced PathResolver Tests ---")
    
    test_root = "C:\\PathResolverAdvancedDir"
    if os.path.exists(test_root):
        shutil.rmtree(test_root)
    os.makedirs(test_root)
    
    PathResolver._cache.clear()

    # Create the test file structure
    # C drive Kavi Work Degree Charusat SEM 7 Internship
    # C drive Kavi Work Degree Charusat SEM
    # C drive Kavi Work Degree Charusat SEM 3
    
    base_kavi = os.path.join(test_root, "Kavi", "Work", "Degree", "Charusat")
    os.makedirs(base_kavi)
    
    os.makedirs(os.path.join(base_kavi, "SEM 3"))
    os.makedirs(os.path.join(base_kavi, "SEM 4"))
    os.makedirs(os.path.join(base_kavi, "SEM 5"))
    os.makedirs(os.path.join(base_kavi, "SEM 6"))
    
    sem7 = os.path.join(base_kavi, "SEM 7")
    os.makedirs(sem7)
    os.makedirs(os.path.join(sem7, "Internship"))
    os.makedirs(os.path.join(sem7, "Internship Reports"))
    
    # 1. Test Longest Match vs Ambiguity
    # Query: C:\PathResolverAdvancedDir Kavi Work Degree Charusat SEM 7 Internship Reports
    # Should resolve successfully (longest match wins over Internship).
    query = f"C:\\PathResolverAdvancedDir Kavi Work Degree Charusat SEM 7 Internship Reports"
    res = PathResolver.resolve(query)
    assert res["status"] == "success"
    assert "Internship Reports" in res["resolved_path"].path
    print("[OK] Longest match resolution (Internship Reports vs Internship)")

    # 2. Test Ambiguity Detection
    # Query: C:\PathResolverAdvancedDir Kavi Work Degree Charusat sem
    query_ambiguous = f"C:\\PathResolverAdvancedDir Kavi Work Degree Charusat sem"
    res_ambig = PathResolver.resolve(query_ambiguous)
    assert res_ambig["status"] == "ambiguous"
    assert len(res_ambig["matches"]) >= 5
    print("[OK] Intelligent ambiguity detection (SEM 3, SEM 4, etc.)")
    
    # 3. Desktop path creation and refresh
    cf = CreateFileTool()
    res_desk = cf.execute("demo.txt", "desktop")
    assert res_desk["status"] == "success"
    # Can't programmatically verify desktop refresh visually, but can check file exists
    assert os.path.exists(res_desk["path"])
    print("[OK] Desktop file creation and refresh trigger")
    # Clean up desktop file
    if os.path.exists(res_desk["path"]):
        os.remove(res_desk["path"])
        
    # 4. Downloads folder test
    cf_dl = CreateFileTool()
    res_dl = cf_dl.execute("test.txt", "downloads")
    assert res_dl["status"] == "success"
    assert "Downloads" in res_dl["path"]
    print("[OK] Downloads folder creation")
    if os.path.exists(res_dl["path"]):
        os.remove(res_dl["path"])
        
    # 5. Missing Folder (FakeFolder)
    res_fake = PathResolver.resolve(f"C:\\PathResolverAdvancedDir Kavi Work Degree FakeFolder Internship")
    assert res_fake["status"] == "failed"
    assert "Could not find folder" in res_fake["message"]
    print("[OK] Missing folder safe failure")
    
    # 6. Global search failure (No base specified)
    res_no_base = PathResolver.resolve("Internship")
    assert res_no_base["status"] == "failed"
    assert "No base location specified" in res_no_base["message"]
    print("[OK] Prevent global search (No base specified)")
    
    # Clean up
    shutil.rmtree(test_root)

if __name__ == "__main__":
    test_advanced()
    print("\nAll advanced tests passed successfully.")
