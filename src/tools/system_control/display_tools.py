import logging
from typing import Dict, Any, List
import win32api
import win32con
import ctypes

from src.tools.base import BaseTool

logger = logging.getLogger(__name__)

class DisplayManager:
    """
    Centralized manager for Windows display controls.
    Exposes structured monitor objects internally.
    """
    @staticmethod
    def _get_orientation_string(orientation: int) -> str:
        if orientation == win32con.DMDO_DEFAULT:
            return "Landscape"
        elif orientation == win32con.DMDO_90:
            return "Portrait"
        elif orientation == win32con.DMDO_180:
            return "Landscape (Flipped)"
        elif orientation == win32con.DMDO_270:
            return "Portrait (Flipped)"
        return "Unknown"

    @staticmethod
    def get_all_monitors_info() -> List[Dict[str, Any]]:
        """
        Retrieves structured information for all connected monitors.
        """
        monitors = win32api.EnumDisplayMonitors()
        info_list = []
        
        # shcore needed for DPI
        shcore = ctypes.windll.shcore
        
        for i, monitor in enumerate(monitors):
            hmonitor = monitor[0].handle
            
            # Use EnumDisplayDevices to get DeviceName
            try:
                device = win32api.EnumDisplayDevices(None, i)
                device_name = device.DeviceName
                is_primary = bool(device.StateFlags & win32con.DISPLAY_DEVICE_PRIMARY_DEVICE)
            except Exception as e:
                logger.error(f"Failed to get device info for monitor {i}: {e}")
                continue
                
            try:
                settings = win32api.EnumDisplaySettings(device_name, win32con.ENUM_CURRENT_SETTINGS)
                width = settings.PelsWidth
                height = settings.PelsHeight
                refresh_rate = settings.DisplayFrequency
                orientation_val = settings.DisplayOrientation
                orientation_str = DisplayManager._get_orientation_string(orientation_val)
            except Exception as e:
                logger.error(f"Failed to get display settings for {device_name}: {e}")
                width, height, refresh_rate, orientation_str = 0, 0, 0, "Unknown"

            # Get scaling (DPI)
            dpiX = ctypes.c_uint()
            dpiY = ctypes.c_uint()
            try:
                # MDT_EFFECTIVE_DPI = 0
                shcore.GetDpiForMonitor(hmonitor, 0, ctypes.byref(dpiX), ctypes.byref(dpiY))
                scaling = round((dpiX.value / 96.0) * 100)
            except Exception as e:
                logger.error(f"Failed to get DPI for {device_name}: {e}")
                scaling = 100

            info = {
                "index": i + 1,
                "device_name": device_name,
                "is_primary": is_primary,
                "resolution": f"{width}x{height}",
                "refresh_rate": refresh_rate,
                "scaling": scaling,
                "orientation": orientation_str
            }
            info_list.append(info)
            
        # Sort so primary is always first
        info_list.sort(key=lambda x: not x["is_primary"])
        
        return info_list

    @staticmethod
    def get_primary_monitor_info() -> Dict[str, Any]:
        """
        Retrieves structured information for the primary monitor.
        """
        monitors = DisplayManager.get_all_monitors_info()
        for m in monitors:
            if m["is_primary"]:
                return m
        # Fallback to the first one if none is marked primary
        return monitors[0] if monitors else {}


class GetDisplayStatusTool(BaseTool):
    name = "display_status"
    description = "Gets the current system display status and monitor configurations."
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            monitors = DisplayManager.get_all_monitors_info()
            if not monitors:
                return {"status": "failed", "message": "No monitors detected."}
                
            primary = DisplayManager.get_primary_monitor_info()
            
            lines = [
                "Display Status",
                "----------------",
                "",
                f"Monitor Count: {len(monitors)}",
                ""
            ]
            
            for monitor in monitors:
                title = "Primary Monitor" if monitor["is_primary"] else f"Monitor {monitor['index']}"
                lines.append(title)
                lines.append(f"Resolution: {monitor['resolution']}")
                lines.append(f"Refresh Rate: {monitor['refresh_rate']} Hz")
                lines.append(f"Scaling: {monitor['scaling']}%")
                lines.append(f"Orientation: {monitor['orientation']}")
                lines.append("")
                
            # Remove trailing newline
            if lines[-1] == "":
                lines.pop()

            message = "\n".join(lines)
            
            return {
                "status": "success", 
                "message": message,
                "display_monitor_count": len(monitors),
                "primary_resolution": primary.get("resolution"),
                "primary_refresh_rate": primary.get("refresh_rate")
            }
        except Exception as e:
            return {"status": "failed", "message": f"Failed to get display status: {e}"}
