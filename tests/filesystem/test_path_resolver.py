import sys
import os
import shutil

# Add the project root to sys.path so we can import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.path_resolver import PathResolver
from src.tools.system_tools import CreateFileTool, CreateFolderTool

def setup_test_env():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test_env'))
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    os.makedirs(base_dir)
    
    # Create test structures
    # Base: test_env
    # Exact match: "ExactFolder"
    # Case-insensitive: "CASEfolder"
    # Startswith match: "Mach" -> "Machine Learning"
    # Partial match: "Learning" -> "Machine Learning"
    # Fuzzy match: "Internships" (query: "Internship")
    os.makedirs(os.path.join(base_dir, "ExactFolder"))
    os.makedirs(os.path.join(base_dir, "CASEfolder"))
    os.makedirs(os.path.join(base_dir, "Machine Learning"))
    os.makedirs(os.path.join(base_dir, "Internships"))
    
    return base_dir

def test_path_resolver():
    base_dir = setup_test_env()
    
    print("\n--- PathResolver Tests ---")
    
    # Inject our base_dir into PathResolver bases for testing purposes
    # We will use "test drive" -> base_dir
    PathResolver._cache.clear()
    
    # Monkey-patch bases in resolve method by calling it with a known absolute path?
    # Actually, we can just pass the absolute path to PathResolver!
    # Because PathResolver detects os.path.isabs(query).
    # Wait, if we pass absolute path, it just returns it immediately if it exists!
    # "If the query is already an absolute path, we can still progressive match it, or if it already exists, just return it!"
    # Ah! If we want to test progressive matching, we must use a base.
    # Let's temporarily mock the bases in PathResolver.
    original_resolve = PathResolver.resolve
    
    def mocked_resolve(query):
        # simple hack: replace "test drive" with the absolute base_dir
        query_lower = query.lower()
        if query_lower.startswith("test drive"):
            # Replace "test drive" with the base_dir
            new_query = base_dir + query[10:]
            # But the resolver needs to recognize the base_dir as a base.
            pass
            
    # Better approach: We can dynamically add "test drive" to the bases dict inside the function?
    # I can just monkey-patch the module or just rewrite the bases definition for the test?
    # Actually, the base detection in PathResolver checks `if query_lower.startswith(key)`.
    # And we added `"c:\\": "C:\\"`. So if we pass `base_dir + " ExactFolder"`, it might not work unless base_dir is exactly in `bases`.
    # Let's just create a test drive entry in PathResolver bases.
    pass

def test_progressive_matching():
    # Since we can't easily monkeypatch local variables, let's just pass `C:\` and assume it exists.
    # We'll create a test folder in C:\ instead for the real test.
    test_root = "C:\\PathResolverTestDir"
    if os.path.exists(test_root):
        shutil.rmtree(test_root)
    os.makedirs(test_root)
    
    os.makedirs(os.path.join(test_root, "ExactFolder"))
    os.makedirs(os.path.join(test_root, "CASEfolder"))
    os.makedirs(os.path.join(test_root, "Machine Learning"))
    os.makedirs(os.path.join(test_root, "Internships"))
    
    # 1. Exact match
    res = PathResolver.resolve(f"C:\\PathResolverTestDir ExactFolder")
    assert res["status"] == "success", f"Failed exact match: {res}"
    assert os.path.basename(res["resolved_path"].path) == "ExactFolder"
    print("[OK] Exact match")
    
    # 2. Case-insensitive match
    res = PathResolver.resolve(f"C:\\PathResolverTestDir caseFOLDER")
    assert res["status"] == "success"
    assert os.path.basename(res["resolved_path"].path) == "CASEfolder"
    print("[OK] Case-insensitive match")
    
    # 3. Startswith match
    res = PathResolver.resolve(f"C:\\PathResolverTestDir Machine")
    assert res["status"] == "success"
    assert os.path.basename(res["resolved_path"].path) == "Machine Learning"
    print("[OK] Startswith match")
    
    # 4. Partial match
    res = PathResolver.resolve(f"C:\\PathResolverTestDir Learning")
    assert res["status"] == "success"
    assert os.path.basename(res["resolved_path"].path) == "Machine Learning"
    print("[OK] Partial match")
    
    # 5. Fuzzy match (>90%)
    res = PathResolver.resolve(f"C:\\PathResolverTestDir Internship")
    assert res["status"] == "success"
    assert os.path.basename(res["resolved_path"].path) == "Internships"
    print("[OK] Fuzzy match (>90%)")
    
    # 6. Missing folder
    res = PathResolver.resolve(f"C:\\PathResolverTestDir NonExistentFolder")
    assert res["status"] == "failed"
    assert "Could not find folder" in res["message"]
    print("[OK] Missing folder")
    
    # 7. No base specified
    res = PathResolver.resolve(f"PathResolverTestDir")
    assert res["status"] == "failed"
    assert "No base location specified" in res["message"]
    print("[OK] No base specified")
    
    # 8. Cache hit
    assert "c:\\pathresolvertestdir internship" in PathResolver._cache
    print("[OK] Cache hit")
    
    # 9. Downloads / Desktop folder
    res_dl = PathResolver.resolve("downloads")
    assert res_dl["status"] == "success"
    assert "Downloads" in res_dl["resolved_path"].path
    print("[OK] Downloads folder")
    
    res_dk = PathResolver.resolve("desktop")
    assert res_dk["status"] == "success"
    assert "Desktop" in res_dk["resolved_path"].path
    print("[OK] Desktop folder")
    
    # 10. Create file using resolved path
    cf = CreateFileTool()
    res_file = cf.execute("testfile.txt", f"C:\\PathResolverTestDir ExactFolder")
    assert res_file["status"] == "success"
    assert os.path.exists(os.path.join(test_root, "ExactFolder", "testfile.txt"))
    print("[OK] Create file using resolved path")
    
    # 11. Create folder using resolved path
    cfd = CreateFolderTool()
    res_folder = cfd.execute("NewFolder", f"C:\\PathResolverTestDir ExactFolder")
    assert res_folder["status"] == "success"
    assert os.path.exists(os.path.join(test_root, "ExactFolder", "NewFolder"))
    print("[OK] Create folder using resolved path")
    
    # 12. Failure path
    res_fail = cf.execute("testfile.txt", f"C:\\PathResolverTestDir NonExistentFolder")
    assert res_fail["status"] == "failed"
    print("[OK] Failure path")
    
    # Cleanup
    shutil.rmtree(test_root)

if __name__ == "__main__":
    test_progressive_matching()
    print("\nAll tests passed successfully.")
