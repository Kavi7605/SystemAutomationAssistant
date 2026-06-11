import winreg
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def get_default_browser() -> Optional[str]:
    """
    Attempts to detect the user's default browser by querying the Windows Registry.
    Returns the executable name or path, or None if detection fails.
    """
    try:
        # Get the ProgId for http associations
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice") as key:
            prog_id, _ = winreg.QueryValueEx(key, "ProgId")

        # Resolve the ProgId to a command
        command_path = r"{}\shell\open\command".format(prog_id)
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, command_path) as key:
            cmd, _ = winreg.QueryValueEx(key, "")
            
        # The command usually looks like: "C:\Path\To\Browser.exe" -osint -url "%1"
        # We extract just the executable path.
        if cmd.startswith('"'):
            exe_path = cmd.split('"')[1]
        else:
            exe_path = cmd.split(' ')[0]
            
        return exe_path
    except Exception as e:
        logger.warning(f"Failed to detect default browser: {e}")
        return None
