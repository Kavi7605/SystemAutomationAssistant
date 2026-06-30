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

def normalize_name(name: str) -> str:
    """Removes spaces, underscores, hyphens, periods, and commas, and lowercases the name."""
    import re
    return re.sub(r"[\s_\-\.,]+", "", name).lower()

def resolve_smart_item(item_name: str, preferred_extension: str = None, target_folder: str = None, **kwargs) -> Dict[str, Any]:
    """
    Attempts to resolve an item name smartly via recursive search.
    If preferred_extension is provided, exact extension matches are prioritized.
    If target_folder is provided, limits search to that folder.
    """
    root = get_workspace_root()
    
    if target_folder:
        folder_res = resolve_smart_item(target_folder)
        if folder_res["status"] == "success":
            root = folder_res["path"]
        elif folder_res["status"] == "ambiguous":
            return {"status": "failed", "message": f"Target folder '{target_folder}' is ambiguous."}
        else:
            return {"status": "failed", "message": f"Target folder '{target_folder}' not found."}

    # If no target folder is given, try exact path match first
    if not target_folder:
        exact_path = resolve_safe_path(item_name)
        if exact_path.exists():
            return {"status": "success", "resolved_name": item_name, "path": exact_path}
        
    matches = []
    item_norm = normalize_name(item_name)
    
    for p in root.rglob("*"):
        if p.is_file() or p.is_dir():
            if normalize_name(p.name) == item_norm:
                matches.append(p)
            elif p.is_file() and normalize_name(p.stem) == item_norm:
                matches.append(p)
                
    if preferred_extension:
        pref_matches = [m for m in matches if m.suffix.lower() == preferred_extension.lower()]
        if pref_matches:
            matches = pref_matches
                
    if len(matches) == 1:
        rel_path = str(matches[0].relative_to(get_workspace_root())).replace("\\", "/")
        return {"status": "success", "resolved_name": rel_path, "path": matches[0]}
    elif len(matches) > 1:
        match_list = [str(m.relative_to(get_workspace_root())).replace("\\", "/") for m in matches]
        return {"status": "ambiguous", "matches": match_list}
        
    return {"status": "not_found"}

class CreateFolderTool(BaseTool):
    name = "create_folder"
    description = "Creates a new folder inside the automation workspace."

    def execute(self, folder_name: str, **kwargs) -> Dict[str, Any]:
        if not folder_name:
            return {"status": "failed", "message": "Missing folder_name"}
            
        try:
            target_path = resolve_safe_path(folder_name)
            
            if target_path.exists():
                return {
                    "status": "success", 
                    "message": f"{folder_name} already exists.",
                    "item_name": folder_name
                }
                
            target_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Folder '{folder_name}' created successfully at {target_path}")
            
            return {
                "status": "success", 
                "message": "Folder created successfully.", 
                "item_name": folder_name
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
                }
            },
            "required": ["folder_name"]
        }


class CreateFileTool(BaseTool):
    name = "create_file"
    description = "Creates a new empty file inside the automation workspace."

    def execute(self, file_name: str, target_folder: str = None, **kwargs) -> Dict[str, Any]:
        if not file_name:
            return {"status": "failed", "message": "Missing file_name"}
            
        try:
            if target_folder:
                folder_resolution = resolve_smart_item(target_folder)
                if folder_resolution["status"] == "ambiguous":
                    matches_str = "\n".join(f"{i+1}. {m}" for i, m in enumerate(folder_resolution["matches"]))
                    return {
                        "status": "ambiguous", 
                        "message": f"Multiple matching folders found:\n{matches_str}",
                        "matches": folder_resolution["matches"],
                        "target_key": "target_folder"
                    }
                elif folder_resolution["status"] == "not_found":
                    return {"status": "failed", "message": "Target folder does not exist."}
                
                folder_path = folder_resolution["path"]
                if not folder_path.is_dir():
                    return {"status": "failed", "message": "Target folder does not exist."} # or "Target is not a folder."
                target_path = folder_path / file_name
                # Use relative name for item_name result
                item_name = str(target_path.relative_to(get_workspace_root())).replace("\\", "/")
            else:
                target_path = resolve_safe_path(file_name)
                item_name = file_name
            
            if target_path.exists():
                return {
                    "status": "success", 
                    "message": f"{item_name} already exists.",
                    "item_name": item_name
                }
            
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.touch()
            
            logger.info(f"File '{item_name}' created successfully at {target_path}")
            
            return {
                "status": "success", 
                "message": "File created successfully.", 
                "item_name": item_name
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
                }
            },
            "required": ["file_name"]
        }


class RenameItemTool(BaseTool):
    name = "rename_item"
    description = "Renames a file or folder inside the automation workspace."

    def execute(self, source_name: str, target_name: str, **kwargs) -> Dict[str, Any]:
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
                
            source_path = resolution["path"]
            actual_source_name = resolution["resolved_name"]
            
            target_path = resolve_safe_path(target_name)
                
            if target_path.exists():
                return {
                    "status": "failed",
                    "message": f"Cannot rename. {target_name} already exists."
                }
                
            source_path.rename(target_path)
            logger.info(f"Renamed '{actual_source_name}' to '{target_name}'")
            
            return {
                "status": "success", 
                "message": f"Renamed {actual_source_name} to {target_name} successfully.", 
                "item_name": target_name
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
    description = "Deletes a file or folder from the automation workspace."

    def execute(self, item_name: str, **kwargs) -> Dict[str, Any]:
        if not item_name:
            return {"status": "failed", "message": "Missing item_name"}
            
        try:
            preferred_extension = kwargs.get("preferred_extension")
            target_folder = kwargs.get("target_folder")
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
                return {"status": "failed", "message": f"{item_name} does not exist."}
                
            target_path = resolution["path"]
            actual_name = resolution["resolved_name"]
            
            if target_path.is_dir():
                shutil.rmtree(target_path)
                item_type = "Folder"
            else:
                target_path.unlink()
                item_type = "File"
                
            logger.info(f"Deleted '{actual_name}'")
            
            return {
                "status": "success", 
                "message": f"{item_type} deleted successfully.", 
                "item_name": actual_name
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

    def execute(self, source_name: str, target_name: str, **kwargs) -> Dict[str, Any]:
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
                
            source_path = resolution["path"]
            actual_source_name = resolution["resolved_name"]
            
            target_path = resolve_safe_path(target_name)
                
            if not source_path.is_file():
                return {
                    "status": "failed",
                    "message": f"{actual_source_name} is not a file."
                }
                
            if target_path.exists():
                return {
                    "status": "failed",
                    "message": f"Cannot copy. {target_name} already exists."
                }
                
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
            
            logger.info(f"Copied '{actual_source_name}' to '{target_name}'")
            
            return {
                "status": "success", 
                "message": "File copied successfully.", 
                "item_name": target_name
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

    def execute(self, source_name: str, target_path: str, preferred_extension: str = None, target_folder: str = None, **kwargs) -> Dict[str, Any]:
        if not source_name or not target_path:
            return {"status": "failed", "message": "Missing source_name or target_path"}
            
        try:
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
                
            source_path_obj = resolution["path"]
            actual_source_name = resolution["resolved_name"]
            
            # target_path might be a directory or a new file name.
            target_res = resolve_smart_item(target_path)
            
            # If target exists and is ambiguous, we can't move into it reliably
            if target_res["status"] == "ambiguous":
                matches_str = "\n".join(f"{i+1}. {m}" for i, m in enumerate(target_res["matches"]))
                return {"status": "failed", "message": f"Multiple matching target folders found:\n{matches_str}"}
                
            if target_res["status"] == "success":
                target_path_obj = target_res["path"]
            else:
                target_path_obj = resolve_safe_path(target_path)
            
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
            
            return {
                "status": "success", 
                "message": "File moved successfully.", 
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

class OpenWorkspaceItemTool(BaseTool):
    name = "open_workspace_item"
    description = "Opens a file or folder inside the automation workspace."

    def execute(self, item_name: str, preferred_extension: str = None, target_folder: str = None, **kwargs) -> Dict[str, Any]:
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
                
            target_path = resolution["path"]
            actual_name = resolution["resolved_name"]
            
            # Start the file or folder using Windows default handler
            os.startfile(str(target_path))
            logger.info(f"Opened workspace item '{actual_name}'")
            
            return {
                "status": "success", 
                "message": f"Opened {actual_name} successfully.", 
                "item_name": actual_name
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
