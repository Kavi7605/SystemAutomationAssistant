import os
import difflib
from typing import Dict, Any

DEBUG_PATH_RESOLUTION = False

class ResolvedPath:
    def __init__(self, path: str):
        self.path = os.path.abspath(path)
        self.exists = os.path.exists(self.path)
        self.is_file = os.path.isfile(self.path) if self.exists else False
        self.is_directory = os.path.isdir(self.path) if self.exists else False

def get_real_desktop_path() -> str:
    # 1. OneDrive Desktop
    onedrive = os.environ.get('OneDrive')
    if onedrive:
        od_desktop = os.path.join(onedrive, "Desktop")
        if os.path.exists(od_desktop):
            return od_desktop
            
    # 2. USERPROFILE Desktop
    userprofile = os.environ.get('USERPROFILE')
    if userprofile:
        up_desktop = os.path.join(userprofile, "Desktop")
        if os.path.exists(up_desktop):
            return up_desktop
            
    # 3. Fallback
    return os.path.join(os.path.expanduser("~"), "Desktop")

class PathResolver:
    _cache = {}

    @classmethod
    def resolve(cls, query: str) -> Dict[str, Any]:
        import logging
        logger = logging.getLogger("system_assistant")
        logger.info(f"PathResolver Input:\n{query}")
        
        result = cls._resolve_internal(query)
        
        logger.info(f"PathResolver Output:\n{result}")
        return result

    @classmethod
    def _resolve_internal(cls, query: str) -> Dict[str, Any]:
        if not query or query == ".":
            return {"status": "failed", "message": "No base location specified"}

        query_lower = query.lower().strip()

        # Cache check
        if query_lower in cls._cache:
            return {"status": "success", "resolved_path": cls._cache[query_lower]}

        bases = {
            "c drive": "C:\\",
            "d drive": "D:\\",
            "e drive": "E:\\",
            "c:\\": "C:\\",
            "d:\\": "D:\\",
            "e:\\": "E:\\",
            "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
            "desktop": get_real_desktop_path(),
            "documents": os.path.join(os.path.expanduser("~"), "Documents"),
            "pictures": os.path.join(os.path.expanduser("~"), "Pictures"),
            "videos": os.path.join(os.path.expanduser("~"), "Videos"),
            "music": os.path.join(os.path.expanduser("~"), "Music")
        }

        base_path = None
        consumed_len = 0

        # Sort bases by length descending to match longest first
        for key in sorted(bases.keys(), key=len, reverse=True):
            if query_lower.startswith(key):
                base_path = bases[key]
                consumed_len = len(key)
                break

        if not base_path:
            if os.path.isabs(query) and os.path.exists(query):
                res = ResolvedPath(query)
                cls._cache[query_lower] = res
                return {"status": "success", "resolved_path": res}
            return {"status": "failed", "message": "No base location specified"}

        remaining = query[consumed_len:].strip()
        current_path = base_path
        
        if DEBUG_PATH_RESOLUTION:
            print(f"Base detected: {current_path}")
            if remaining:
                print("Matched:")

        while remaining:
            try:
                if not os.path.isdir(current_path):
                    return {
                        "status": "failed",
                        "failed_token": remaining,
                        "current_path": current_path,
                        "message": f"Cannot traverse through non-directory: '{current_path}'"
                    }
                entries = os.listdir(current_path)
            except Exception:
                return {
                    "status": "failed",
                    "failed_token": remaining,
                    "current_path": current_path,
                    "message": f"Could not find folder '{remaining.split()[0]}'"
                }

            rem_words = remaining.split()
            best_priority = 99
            best_consumed_words = 0
            best_matches = []

            for entry in entries:
                entry_lower = entry.lower()

                for i in range(1, len(rem_words) + 1):
                    test_str = " ".join(rem_words[:i])
                    test_lower = test_str.lower()
                    
                    priority = 99
                    
                    if test_str == entry:
                        priority = 1
                    elif test_lower == entry_lower:
                        priority = 2
                    elif entry_lower.startswith(test_lower):
                        priority = 3
                    elif test_lower in entry_lower:
                        priority = 4
                    else:
                        matches = difflib.get_close_matches(test_lower, [entry_lower], n=1, cutoff=0.9)
                        if matches:
                            priority = 5

                    if priority < 99:
                        # Prioritize higher priority first, then consuming MORE words
                        if priority < best_priority or (priority == best_priority and i > best_consumed_words):
                            best_priority = priority
                            best_consumed_words = i
                            best_matches = [entry]
                        elif priority == best_priority and i == best_consumed_words:
                            if entry not in best_matches:
                                best_matches.append(entry)

            if not best_matches:
                return {
                    "status": "failed",
                    "failed_token": rem_words[0],
                    "current_path": current_path,
                    "message": f"Could not find folder '{rem_words[0]}'"
                }
                
            # Check ambiguity ONLY if priority > 2 (Exact and Case-insensitive are safe)
            if len(best_matches) > 1 and best_priority > 2:
                # Return ambiguity error
                return {
                    "status": "ambiguous",
                    "token": " ".join(rem_words[:best_consumed_words]),
                    "matches": best_matches
                }

            best_match = best_matches[0]
            current_path = os.path.join(current_path, best_match)
            
            if DEBUG_PATH_RESOLUTION:
                print(f"\u2192 {best_match}")
                
            remaining = " ".join(rem_words[best_consumed_words:]).strip()

        if DEBUG_PATH_RESOLUTION:
            print(f"\nResolved:\n{current_path}")

        res = ResolvedPath(current_path)
        cls._cache[query_lower] = res
        return {"status": "success", "resolved_path": res}
