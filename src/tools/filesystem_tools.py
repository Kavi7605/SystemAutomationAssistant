import os
import shutil
from pathlib import Path
from typing import Dict, Any
import logging

from src.tools.base import BaseTool

logger = logging.getLogger(__name__)

# Define the safe workspace root
WORKSPACE_DIR = "automation_workspace"

def get_workspace_root() -> Path:
    """Returns the absolute Path to the safe automation workspace, creating it if necessary."""
    env_root = os.environ.get("AUTOMATION_WORKSPACE")
    if env_root:
        root = Path(env_root)
    else:
        root = Path(os.getcwd()) / WORKSPACE_DIR
    root.mkdir(parents=True, exist_ok=True)
    return root

def resolve_safe_path(target_path: str) -> Path:
    """
    Resolves a target path relative to the workspace root.
    Ensures the path does not escape the workspace root.
    """
    root = get_workspace_root()
    
    # If the user provides something like "backup/file.txt", we join it with root.
    # We use resolve() to get the absolute path and then check if it's relative to root.
    safe_target = (root / target_path).resolve()
    
    try:
        safe_target.relative_to(root)
    except ValueError:
        # If it's not relative to root, it means they tried to escape using ../..
        # We enforce it to be inside root by just using the name if it escaped,
        # but to be truly safe, let's just append the original string as a clean path
        safe_target = root / Path(target_path).name
        
    return safe_target

def _resolve_target_parent(target_folder: str, context_manager=None) -> Path:
    if not target_folder:
        if context_manager:
            fs_state = context_manager.get_filesystem_context()
            last_opened = fs_state.get("last_opened_folder")
            if last_opened and os.path.exists(last_opened):
                return Path(last_opened)
        return get_workspace_root()
        
    from src.tools.path_resolver import PathResolver
    # 1. Windows Known Folder / PathResolver
    res = PathResolver.resolve(target_folder)
    if res["status"] == "success":
        return Path(res["resolved_path"].path)
        
    # 2. Absolute/custom path
    if os.path.isabs(target_folder):
        return Path(target_folder)
        
    # 3. Nested path
    smart_res = resolve_smart_item(target_folder, context_manager=context_manager)
    if smart_res["status"] == "success":
        p = smart_res["path"]
        if p.is_dir():
            return p
        else:
            return p.parent
            
    # 4. Workspace fallback
    return get_workspace_root() / target_folder


def normalize_name(name: str) -> str:
    """Removes spaces, underscores, hyphens, periods, and commas, and lowercases the name."""
    import re
    return re.sub(r"[\s_\-\.,]+", "", name).lower()

def resolve_smart_item(item_name: str, preferred_extension: str = None, target_folder: str = None, context_manager=None, **kwargs) -> Dict[str, Any]:
    """
    Attempts to resolve an item name smartly via recursive search.
    If preferred_extension is provided, exact extension matches are prioritized.
    If target_folder is provided, limits search to that folder.
    """
    from src.tools.path_resolver import PathResolver, get_real_desktop_path
    
    # Strip trailing type words
    item_lower = item_name.lower().strip()
    for word in [" file", " folder", " directory", " document"]:
        if item_lower.endswith(word):
            item_name = item_name[:-len(word)].strip()
            item_lower = item_name.lower()
            
    if os.path.isabs(item_name):
        path_obj = Path(item_name)
        if path_obj.exists():
            return {"status": "success", "resolved_name": path_obj.name, "path": path_obj}

            
    # Phase 1: Known Windows Folder Priority (Bypass fuzzy search)
    if not target_folder:
        pr_res = PathResolver.resolve(item_name)
        if pr_res["status"] == "success" and pr_res["resolved_path"].exists:
            p = Path(pr_res["resolved_path"].path)
            return {"status": "success", "resolved_name": p.name, "path": p}
            
    # Phase 2: Context Memory Priority
    if context_manager and not target_folder and not kwargs.get("literal_name"):
        item_norm = normalize_name(item_name)
        # If it's a pronoun or we just want to check memory first
        fs_state = context_manager.get_filesystem_context()
        priority_keys = [
            "last_created_file",
            "last_renamed_file",
            "last_found_file",
            "last_opened_file",
            "last_created_folder",
            "last_found_folder"
        ]
        
        # If it's literally a pronoun, resolve to the most recent relevant
        if item_norm in ["it", "that", "this"]:
            for key in priority_keys:
                if fs_state.get(key) and os.path.exists(fs_state[key]):
                    p = Path(fs_state[key])
                    return {"status": "success", "resolved_name": p.name, "path": p}
        else:
            # Otherwise, check if what they typed exactly matches something in memory
            for key in priority_keys:
                if fs_state.get(key) and os.path.exists(fs_state[key]):
                    p = Path(fs_state[key])
                    if item_norm == normalize_name(p.name) or item_norm == normalize_name(p.stem):
                        return {"status": "success", "resolved_name": p.name, "path": p}
            
    search_roots = []
    global_roots = []
    
    if target_folder:
        res = PathResolver.resolve(target_folder)
        if res["status"] == "success":
            search_roots.append(res["resolved_path"].path)
        else:
            folder_res = resolve_smart_item(target_folder, context_manager=context_manager)
            if folder_res["status"] == "success":
                search_roots.append(str(folder_res["path"]))
            else:
                return {"status": "failed", "message": f"Could not resolve target folder: {target_folder}"}
                
    # Build global fallback order
    if context_manager:
        fs_state = context_manager.get_filesystem_context()
        last_opened = fs_state.get("last_opened_folder")
        if last_opened and os.path.exists(last_opened):
            global_roots.append(last_opened)
            
    # Known locations
    home = os.path.expanduser("~")
    global_roots.extend([
        os.path.join(home, "Downloads"),
        os.path.join(home, "Documents"),
        get_real_desktop_path(),
        str(get_workspace_root())
    ])

    # Deduplicate while preserving order
    seen = set()
    search_roots = [r for r in search_roots if not (r in seen or seen.add(r))]
    
    seen_global = set(search_roots)
    global_roots = [r for r in global_roots if not (r in seen_global or seen_global.add(r))]
    
    item_norm = normalize_name(item_name)
    
    def search_in_roots(roots):
        exact_files, exact_folders = [], []
        partial_files, partial_folders = [], []
        fuzzy_files, fuzzy_folders = [], []
        for root_str in roots:
            root_path = Path(root_str)
            if not root_path.exists() or not root_path.is_dir():
                continue
            try:
                for p in root_path.rglob("*"):
                    if p.is_file() or p.is_dir():
                        p_name_norm = normalize_name(p.name)
                        is_exact = (p_name_norm == item_norm) or (p.is_file() and normalize_name(p.stem) == item_norm)
                        if is_exact:
                            if p.is_file(): exact_files.append(p)
                            else: exact_folders.append(p)
                        elif item_norm in p_name_norm:
                            if p.is_file(): partial_files.append(p)
                            else: partial_folders.append(p)
                        else:
                            import difflib
                            if difflib.get_close_matches(item_norm, [p_name_norm], n=1, cutoff=0.8):
                                if p.is_file(): fuzzy_files.append(p)
                                else: fuzzy_folders.append(p)
            except Exception:
                pass
        return {
            "exact": exact_files + exact_folders,
            "partial": partial_files + partial_folders,
            "fuzzy": fuzzy_files + fuzzy_folders
        }

    if not search_roots:
        search_roots = global_roots
        global_roots = []
        
    matches = []
    
    scoped_results = search_in_roots(search_roots)
    if scoped_results["exact"]: matches = scoped_results["exact"]
    elif scoped_results["partial"]: matches = scoped_results["partial"]
    elif scoped_results["fuzzy"]: matches = scoped_results["fuzzy"]
    
    if not matches and global_roots:
        global_results = search_in_roots(global_roots)
        if global_results["exact"]: matches = global_results["exact"]
        elif global_results["partial"]: matches = global_results["partial"]
        elif global_results["fuzzy"]: matches = global_results["fuzzy"]
                
    if preferred_extension:
        pref_matches = [m for m in matches if m.suffix.lower() == preferred_extension.lower()]
        if pref_matches:
            matches = pref_matches
                
    if len(matches) == 1:
        return {"status": "success", "resolved_name": matches[0].name, "path": matches[0]}
    elif len(matches) > 1:
        match_list = [str(m) for m in matches]
        return {"status": "ambiguous", "matches": match_list}
        
    return {"status": "not_found"}

class CreateFolderTool(BaseTool):
    name = "create_folder"
    description = "Creates a new folder."

    def execute(self, folder_name: str, target_folder: str = None, context_manager=None, **kwargs) -> Dict[str, Any]:
        if not folder_name:
            return {"status": "failed", "message": "Missing folder_name"}
            
        try:
            target_parent = _resolve_target_parent(target_folder, context_manager)

                
            target_path = target_parent / folder_name
            
            if target_path.exists():
                return {
                    "status": "success", 
                    "message": f"{folder_name} already exists.",
                    "item_name": str(target_path)
                }
                
            target_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Folder '{folder_name}' created successfully at {target_path}")
            
            if context_manager:
                context_manager.update_filesystem_state("last_found_folder", str(target_path))
                context_manager.update_filesystem_state("last_found_item", str(target_path))
                context_manager.update_filesystem_state("last_resolved_absolute_path", str(target_path))
            
            return {
                "status": "success", 
                "message": f"Folder created successfully at {target_path}", 
                "item_name": str(target_path)
            }
        except Exception as e:
            logger.error(f"Failed to create folder: {e}", exc_info=True)
            return {"status": "failed", "message": f"Failed to create folder: {str(e)}"}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "folder_name": {
                    "type": "string",
                    "description": "The name of the new folder."
                },
                "target_folder": {
                    "type": "string",
                    "description": "Optional parent path for the folder."
                }
            },
            "required": ["folder_name"]
        }


class CreateFileTool(BaseTool):
    name = "create_file"
    description = "Creates a new empty file."

    def execute(self, file_name: str, target_folder: str = None, context_manager=None, **kwargs) -> Dict[str, Any]:
        if not file_name:
            return {"status": "failed", "message": "Missing file_name"}
            
        try:
            target_parent = _resolve_target_parent(target_folder, context_manager)

                
            target_path = target_parent / file_name
            
            if target_path.exists():
                return {
                    "status": "success", 
                    "message": f"{file_name} already exists.",
                    "item_name": str(target_path)
                }
            
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.touch()
            
            logger.info(f"File '{file_name}' created successfully at {target_path}")
            
            if context_manager:
                context_manager.update_filesystem_state("last_found_file", str(target_path))
                context_manager.update_filesystem_state("last_found_item", str(target_path))
                context_manager.update_filesystem_state("last_resolved_absolute_path", str(target_path))
            
            return {
                "status": "success", 
                "message": f"File created successfully at {target_path}", 
                "item_name": str(target_path)
            }
        except Exception as e:
            logger.error(f"Failed to create file: {e}", exc_info=True)
            return {"status": "failed", "message": f"Failed to create file: {str(e)}"}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "file_name": {
                    "type": "string",
                    "description": "The name of the new file, including extension."
                },
                "target_folder": {
                    "type": "string",
                    "description": "Optional parent path for the file."
                }
            },
            "required": ["file_name"]
        }


class RenameItemTool(BaseTool):
    name = "rename_item"
    description = "Renames a file or folder."

    def execute(self, source_name: str, target_name: str, context_manager=None, **kwargs) -> Dict[str, Any]:
        if not source_name or not target_name:
            return {"status": "failed", "message": "Missing source_name or target_name"}
            
        try:
            preferred_extension = kwargs.get("preferred_extension")
            target_folder = kwargs.get("target_folder")
            resolution = resolve_smart_item(source_name, preferred_extension, target_folder, context_manager=context_manager)
            if resolution["status"] == "ambiguous":
                matches_str = "\n".join(f"{i+1}. {m}" for i, m in enumerate(resolution["matches"]))
                return {
                    "status": "ambiguous", 
                    "message": f"Multiple matching files found:\n{matches_str}",
                    "matches": resolution["matches"],
                    "target_key": "source_name"
                }
            elif resolution["status"] == "not_found":
                return {"status": "failed", "message": f"{source_name} does not exist."}
            elif resolution["status"] == "failed":
                return resolution
                
            source_path = resolution["path"]
            actual_source_name = resolution["resolved_name"]
            
            target_path = source_path.parent / target_name
                
            if target_path.exists():
                return {
                    "status": "failed",
                    "message": f"Cannot rename. {target_name} already exists."
                }
                
            source_path.rename(target_path)
            logger.info(f"Renamed '{actual_source_name}' to '{target_name}'")
            
            if context_manager:
                item_type = "last_found_folder" if target_path.is_dir() else "last_found_file"
                context_manager.update_filesystem_state(item_type, str(target_path))
                context_manager.update_filesystem_state("last_found_item", str(target_path))
                context_manager.update_filesystem_state("last_resolved_absolute_path", str(target_path))
            
            return {
                "status": "success", 
                "message": f"Renamed {actual_source_name} to {target_name} successfully.", 
                "item_name": str(target_path)
            }
        except Exception as e:
            logger.error(f"Failed to rename item: {e}", exc_info=True)
            return {"status": "failed", "message": f"Failed to rename item: {str(e)}"}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "source_name": {
                    "type": "string",
                    "description": "The current name of the file or folder."
                },
                "target_name": {
                    "type": "string",
                    "description": "The new name of the file or folder."
                }
            },
            "required": ["source_name", "target_name"]
        }


class DeleteItemTool(BaseTool):
    name = "delete_item"
    description = "Deletes a file or folder (requires confirmation)."

    def execute(self, item_name: str, context_manager=None, **kwargs) -> Dict[str, Any]:
        if not item_name:
            return {"status": "failed", "message": "Missing item_name"}
            
        try:
            preferred_extension = kwargs.get("preferred_extension")
            target_folder = kwargs.get("target_folder")
            resolution = resolve_smart_item(item_name, preferred_extension, target_folder, context_manager=context_manager)
            if resolution["status"] == "ambiguous":
                matches_str = "\n".join(f"{i+1}. {m}" for i, m in enumerate(resolution["matches"]))
                return {
                    "status": "ambiguous", 
                    "message": f"Multiple matching files found:\n{matches_str}",
                    "matches": resolution["matches"],
                    "target_key": "item_name"
                }
            elif resolution["status"] == "not_found":
                return {"status": "failed", "message": f"{item_name} does not exist."}
            elif resolution["status"] == "failed":
                return resolution
                
            target_path = resolution["path"]
            actual_name = resolution["resolved_name"]
            if context_manager:
                context_manager.update_filesystem_state("pending_delete", str(target_path))
            
            return {
                "status": "success", 
                "message": f"Found:\n{actual_name}\n\nAre you sure you want to delete it?\nType yes or no.", 
            }
        except Exception as e:
            logger.error(f"Failed to delete item: {e}", exc_info=True)
            return {"status": "failed", "message": f"Failed to delete item: {str(e)}"}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "item_name": {
                    "type": "string",
                    "description": "The name of the file or folder to delete."
                }
            },
            "required": ["item_name"]
        }


class CopyFileTool(BaseTool):
    name = "copy_file"
    description = "Copies a file inside the automation workspace."

    def execute(self, source_name: str, target_name: str, context_manager=None, **kwargs) -> Dict[str, Any]:
        if not source_name or not target_name:
            return {"status": "failed", "message": "Missing source_name or target_name"}
            
        try:
            preferred_extension = kwargs.get("preferred_extension")
            target_folder = kwargs.get("target_folder")
            resolution = resolve_smart_item(source_name, preferred_extension, target_folder)
            if resolution["status"] == "ambiguous":
                matches_str = "\n".join(f"{i+1}. {m}" for i, m in enumerate(resolution["matches"]))
                return {
                    "status": "ambiguous", 
                    "message": f"Multiple matching files found:\n{matches_str}",
                    "matches": resolution["matches"],
                    "target_key": "source_name"
                }
            elif resolution["status"] == "not_found":
                return {"status": "failed", "message": f"{source_name} does not exist."}
            elif resolution["status"] == "failed":
                return resolution
                
            source_path = resolution["path"]
            actual_source_name = resolution["resolved_name"]
            
            from src.tools.path_resolver import PathResolver
            res = PathResolver.resolve(target_name)
            if res["status"] == "success":
                target_path = Path(res["resolved_path"].path)
                if target_path.is_dir():
                    target_path = target_path / source_path.name
            else:
                if os.path.isabs(target_name):
                    target_path = Path(target_name)
                else:
                    target_path = get_workspace_root() / target_name
                
            if target_path.exists():
                return {
                    "status": "failed",
                    "message": f"Cannot copy. {target_name} already exists."
                }
                
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if source_path.is_dir():
                shutil.copytree(source_path, target_path)
            else:
                shutil.copy2(source_path, target_path)
            
            logger.info(f"Copied '{actual_source_name}' to '{target_name}'")
            
            if context_manager:
                item_type = "last_found_folder" if target_path.is_dir() else "last_found_file"
                context_manager.update_filesystem_state(item_type, str(target_path))
                context_manager.update_filesystem_state("last_found_item", str(target_path))
                context_manager.update_filesystem_state("last_resolved_absolute_path", str(target_path))
            
            msg_type = "Folder" if source_path.is_dir() else "File"
            return {
                "status": "success", 
                "message": f"{msg_type} copied successfully.", 
                "item_name": target_path.name
            }
        except Exception as e:
            logger.error(f"Failed to copy file: {e}", exc_info=True)
            return {"status": "failed", "message": f"Failed to copy file: {str(e)}"}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "source_name": {
                    "type": "string",
                    "description": "The name of the file to copy."
                },
                "target_name": {
                    "type": "string",
                    "description": "The destination name or path for the copied file."
                }
            },
            "required": ["source_name", "target_name"]
        }


class MoveFileTool(BaseTool):
    name = "move_file"
    description = "Moves a file inside the automation workspace."

    def execute(self, source_name: str, target_path: str, preferred_extension: str = None, target_folder: str = None, context_manager=None, **kwargs) -> Dict[str, Any]:
        if not source_name or not target_path:
            return {"status": "failed", "message": "Missing source_name or target_path"}
            
        try:
            if " to " in target_path and not target_folder:
                parts = target_path.split(" to ", 1)
                target_folder = parts[0].strip()
                target_path = parts[1].strip()
                
            resolution = resolve_smart_item(source_name, preferred_extension, target_folder, context_manager=context_manager)
            if resolution["status"] == "ambiguous":
                matches_str = "\n".join(f"{i+1}. {m}" for i, m in enumerate(resolution["matches"]))
                return {
                    "status": "ambiguous", 
                    "message": f"Multiple matching files found:\n{matches_str}",
                    "matches": resolution["matches"],
                    "target_key": "source_name"
                }
            elif resolution["status"] == "not_found":
                return {"status": "failed", "message": f"{source_name} does not exist."}
            elif resolution["status"] == "failed":
                return resolution
                
            source_path_obj = resolution["path"]
            actual_source_name = resolution["resolved_name"]
            
            target_res = resolve_smart_item(target_path, context_manager=context_manager)
            
            if target_res["status"] == "ambiguous":
                matches_str = "\n".join(f"{i+1}. {m}" for i, m in enumerate(target_res["matches"]))
                return {"status": "failed", "message": f"Multiple matching target folders found:\n{matches_str}"}
                
            if target_res["status"] == "success":
                target_path_obj = target_res["path"]
            else:
                from src.tools.path_resolver import PathResolver
                res = PathResolver.resolve(target_path)
                if res["status"] == "success":
                    target_path_obj = Path(res["resolved_path"].path)
                else:
                    if os.path.isabs(target_path):
                        target_path_obj = Path(target_path)
                    else:
                        target_path_obj = get_workspace_root() / target_path
            
            if target_path_obj.is_dir():
                target_path_obj = target_path_obj / source_path_obj.name
                
            if target_path_obj.exists():
                return {
                    "status": "failed",
                    "message": f"Cannot move. {target_path_obj.name} already exists at destination."
                }
                
            target_path_obj.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_path_obj), str(target_path_obj))
            
            logger.info(f"Moved '{actual_source_name}' to '{target_path}'")
            
            if context_manager:
                item_type = "last_found_folder" if target_path_obj.is_dir() else "last_found_file"
                context_manager.update_filesystem_state(item_type, str(target_path_obj))
                context_manager.update_filesystem_state("last_found_item", str(target_path_obj))
                context_manager.update_filesystem_state("last_resolved_absolute_path", str(target_path_obj))
            
            msg_type = "Folder" if source_path_obj.is_dir() else "File"
            return {
                "status": "success", 
                "message": f"{msg_type} moved successfully.", 
                # According to metadata specs, returning the new item_name relative to workspace
                "item_name": target_path_obj.name
            }
        except Exception as e:
            logger.error(f"Failed to move file: {e}", exc_info=True)
            return {"status": "failed", "message": f"Failed to move file: {str(e)}"}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "source_name": {
                    "type": "string",
                    "description": "The name of the file to move."
                },
                "target_path": {
                    "type": "string",
                    "description": "The destination folder or file name."
                }
            },
            "required": ["source_name", "target_path"]
        }

class OpenItemTool(BaseTool):
    name = "open_item"
    description = "Opens a file or folder."

    def execute(self, item_name: str, preferred_extension: str = None, target_folder: str = None, context_manager=None, **kwargs) -> Dict[str, Any]:
        if not item_name:
            return {"status": "failed", "message": "Missing item_name"}
            
        try:
            resolution = resolve_smart_item(item_name, preferred_extension, target_folder)
            if resolution["status"] == "ambiguous":
                matches_str = "\n".join(f"{i+1}. {m}" for i, m in enumerate(resolution["matches"]))
                return {
                    "status": "ambiguous", 
                    "message": f"Multiple matching files found:\n{matches_str}",
                    "matches": resolution["matches"],
                    "target_key": "item_name"
                }
            elif resolution["status"] == "not_found":
                return {"status": "failed", "message": "Folder not found."} # Fallback text
            elif resolution["status"] == "failed":
                return resolution
                
            target_path = resolution["path"]
            actual_name = resolution["resolved_name"]
            
            # Start the file or folder using Windows default handler
            os.startfile(str(target_path))
            logger.info(f"Opened workspace item '{actual_name}'")
            
            if context_manager:
                item_type = "last_found_folder" if target_path.is_dir() else "last_found_file"
                context_manager.update_filesystem_state(item_type, str(target_path))
                context_manager.update_filesystem_state("last_found_item", str(target_path))
                context_manager.update_filesystem_state("last_resolved_absolute_path", str(target_path))
            
            return {
                "status": "success", 
                "message": f"Opened {actual_name} successfully.", 
                "item_name": str(target_path)
            }
        except Exception as e:
            logger.error(f"Failed to open workspace item: {e}", exc_info=True)
            return {"status": "failed", "message": f"Failed to open item: {str(e)}"}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "item_name": {
                    "type": "string",
                    "description": "The name of the file or folder to open."
                }
            },
            "required": ["item_name"]
        }


class FindItemTool(BaseTool):
    name = "find_item"
    description = "Searches for a file or folder."

    def execute(self, item_name: str, target_folder: str = None, preferred_extension: str = None, context_manager=None, **kwargs) -> Dict[str, Any]:
        if not item_name:
            return {"status": "failed", "message": "Missing item_name"}
            
        try:
            resolution = resolve_smart_item(item_name, target_folder=target_folder, context_manager=context_manager)
            if resolution["status"] == "ambiguous":
                matches_str = "\n".join(f"{i+1}. {m}" for i, m in enumerate(resolution["matches"]))
                return {
                    "status": "ambiguous", 
                    "message": f"Multiple matching items found:\n{matches_str}",
                    "matches": resolution["matches"],
                    "target_key": "item_name"
                }
            elif resolution["status"] == "not_found":
                return {"status": "failed", "message": f"Item '{item_name}' not found."}
            elif resolution["status"] == "failed":
                return resolution
                
            target_path = resolution["path"]
            actual_name = resolution["resolved_name"]
            
            logger.info(f"Found item '{actual_name}' at '{target_path}'")
            
            if context_manager:
                item_type = "last_found_folder" if target_path.is_dir() else "last_found_file"
                context_manager.update_filesystem_state(item_type, str(target_path))
                context_manager.update_filesystem_state("last_found_item", str(target_path))
                context_manager.update_filesystem_state("last_resolved_absolute_path", str(target_path))
            
            return {
                "status": "success", 
                "message": f"Found: {actual_name}\nPath: {target_path}", 
                "item_name": str(target_path)
            }
        except Exception as e:
            logger.error(f"Failed to find item: {e}", exc_info=True)
            return {"status": "failed", "message": f"Failed to find item: {str(e)}"}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "item_name": {
                    "type": "string",
                    "description": "The name of the file or folder to find."
                }
            },
            "required": ["item_name"]
        }


class ConfirmDeleteTool(BaseTool):
    name = "confirm_delete"
    description = "Confirms deletion of an item."

    def execute(self, context_manager=None, **kwargs) -> Dict[str, Any]:
        if not context_manager:
            return {"status": "failed", "message": "ContextManager not available."}
            
        fs_state = context_manager.get_filesystem_context()
        pending = fs_state.get("pending_delete")
        if not pending:
            return {"status": "failed", "message": "No pending deletion."}
            
        try:
            target_path = Path(pending)
            if target_path.exists():
                if target_path.is_dir():
                    shutil.rmtree(target_path)
                    item_type = "Folder"
                else:
                    target_path.unlink()
                    item_type = "File"
                    
                logger.info(f"Confirmed delete of '{target_path}'")
                context_manager.update_filesystem_state("pending_delete", None)
                
                return {
                    "status": "success", 
                    "message": f"{item_type} deleted successfully.", 
                    "item_name": str(target_path)
                }
            else:
                context_manager.update_filesystem_state("pending_delete", None)
                return {"status": "failed", "message": "Item to delete no longer exists."}
        except Exception as e:
            logger.error(f"Failed to confirm delete: {e}", exc_info=True)
            return {"status": "failed", "message": f"Failed to confirm delete: {str(e)}"}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {},
            "required": []
        }

class CancelDeleteTool(BaseTool):
    name = "cancel_delete"
    description = "Cancels a pending deletion."

    def execute(self, context_manager=None, **kwargs) -> Dict[str, Any]:
        if context_manager:
            context_manager.update_filesystem_state("pending_delete", None)
        return {
            "status": "success",
            "message": "Deletion cancelled."
        }

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {},
            "required": []
        }
