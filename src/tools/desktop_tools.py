import logging
import pyautogui
from typing import Dict, Any, List

from src.tools.base import BaseTool

logger = logging.getLogger(__name__)

class ClickTool(BaseTool):
    name = "click"
    description = "Clicks the mouse at the current position or specified coordinates."

    def execute(self, x: int = None, y: int = None, **kwargs) -> Dict[str, Any]:
        try:
            logger.info(f"Executing click action. x={x}, y={y}")
            if x is not None and y is not None:
                pyautogui.click(x=int(x), y=int(y))
            else:
                pyautogui.click()
            return {"status": "success", "message": "Click executed successfully"}
        except pyautogui.FailSafeException:
            logger.warning("PyAutoGUI fail-safe triggered during click.")
            return {"status": "failed", "message": "Fail-safe triggered (mouse moved to a corner)."}
        except Exception as e:
            logger.error(f"Error executing click: {e}", exc_info=True)
            return {"status": "failed", "message": str(e)}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "x": {"type": "integer", "description": "Optional X coordinate"},
                "y": {"type": "integer", "description": "Optional Y coordinate"}
            }
        }


class DoubleClickTool(BaseTool):
    name = "double_click"
    description = "Double-clicks the mouse at the current position or specified coordinates."

    def execute(self, x: int = None, y: int = None, **kwargs) -> Dict[str, Any]:
        try:
            logger.info(f"Executing double-click action. x={x}, y={y}")
            if x is not None and y is not None:
                pyautogui.doubleClick(x=int(x), y=int(y))
            else:
                pyautogui.doubleClick()
            return {"status": "success", "message": "Double-click executed successfully"}
        except pyautogui.FailSafeException:
            logger.warning("PyAutoGUI fail-safe triggered during double-click.")
            return {"status": "failed", "message": "Fail-safe triggered (mouse moved to a corner)."}
        except Exception as e:
            logger.error(f"Error executing double-click: {e}", exc_info=True)
            return {"status": "failed", "message": str(e)}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "x": {"type": "integer", "description": "Optional X coordinate"},
                "y": {"type": "integer", "description": "Optional Y coordinate"}
            }
        }


class RightClickTool(BaseTool):
    name = "right_click"
    description = "Right-clicks the mouse at the current position or specified coordinates."

    def execute(self, x: int = None, y: int = None, **kwargs) -> Dict[str, Any]:
        try:
            logger.info(f"Executing right-click action. x={x}, y={y}")
            if x is not None and y is not None:
                pyautogui.rightClick(x=int(x), y=int(y))
            else:
                pyautogui.rightClick()
            return {"status": "success", "message": "Right-click executed successfully"}
        except pyautogui.FailSafeException:
            logger.warning("PyAutoGUI fail-safe triggered during right-click.")
            return {"status": "failed", "message": "Fail-safe triggered (mouse moved to a corner)."}
        except Exception as e:
            logger.error(f"Error executing right-click: {e}", exc_info=True)
            return {"status": "failed", "message": str(e)}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "x": {"type": "integer", "description": "Optional X coordinate"},
                "y": {"type": "integer", "description": "Optional Y coordinate"}
            }
        }


class TypeTextTool(BaseTool):
    name = "type_text"
    description = "Types the specified text using the keyboard."

    def execute(self, text: str, **kwargs) -> Dict[str, Any]:
        if not text:
            return {"status": "failed", "message": "Missing text parameter"}
        
        try:
            logger.info(f"Executing type_text action. text='{text}'")
            pyautogui.write(text)
            return {"status": "success", "message": f"Typed text: {text}"}
        except pyautogui.FailSafeException:
            logger.warning("PyAutoGUI fail-safe triggered during type_text.")
            return {"status": "failed", "message": "Fail-safe triggered (mouse moved to a corner)."}
        except Exception as e:
            logger.error(f"Error executing type_text: {e}", exc_info=True)
            return {"status": "failed", "message": str(e)}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "text": {"type": "string", "description": "The text to type"}
            },
            "required": ["text"]
        }


class HotkeyTool(BaseTool):
    name = "hotkey"
    description = "Presses a combination of keys."

    def execute(self, keys: List[str], **kwargs) -> Dict[str, Any]:
        if not keys:
            return {"status": "failed", "message": "Missing keys parameter"}
        
        try:
            logger.info(f"Executing hotkey action. keys={keys}")
            pyautogui.hotkey(*keys)
            return {"status": "success", "message": f"Pressed hotkey: {' + '.join(keys)}"}
        except pyautogui.FailSafeException:
            logger.warning("PyAutoGUI fail-safe triggered during hotkey.")
            return {"status": "failed", "message": "Fail-safe triggered (mouse moved to a corner)."}
        except Exception as e:
            logger.error(f"Error executing hotkey: {e}", exc_info=True)
            return {"status": "failed", "message": str(e)}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "An array of keys to press together"
                }
            },
            "required": ["keys"]
        }


class ScrollTool(BaseTool):
    name = "scroll"
    description = "Scrolls the mouse wheel up or down."

    def execute(self, direction: str, **kwargs) -> Dict[str, Any]:
        if not direction:
            return {"status": "failed", "message": "Missing direction parameter"}
            
        amount = 500 if direction.lower() == "up" else -500
            
        try:
            logger.info(f"Executing scroll action. direction={direction}, amount={amount}")
            pyautogui.scroll(amount)
            return {"status": "success", "message": f"Scrolled {direction}"}
        except pyautogui.FailSafeException:
            logger.warning("PyAutoGUI fail-safe triggered during scroll.")
            return {"status": "failed", "message": "Fail-safe triggered (mouse moved to a corner)."}
        except Exception as e:
            logger.error(f"Error executing scroll: {e}", exc_info=True)
            return {"status": "failed", "message": str(e)}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "direction": {
                    "type": "string",
                    "enum": ["up", "down"],
                    "description": "The direction to scroll"
                }
            },
            "required": ["direction"]
        }


class MoveMouseTool(BaseTool):
    name = "move_mouse"
    description = "Moves the mouse cursor to the specified coordinates."

    def execute(self, x: int, y: int, **kwargs) -> Dict[str, Any]:
        if x is None or y is None:
            return {"status": "failed", "message": "Missing x or y coordinate"}
            
        try:
            logger.info(f"Executing move_mouse action. x={x}, y={y}")
            pyautogui.moveTo(int(x), int(y))
            return {"status": "success", "message": f"Moved mouse to ({x}, {y})"}
        except pyautogui.FailSafeException:
            logger.warning("PyAutoGUI fail-safe triggered during move_mouse.")
            return {"status": "failed", "message": "Fail-safe triggered (mouse moved to a corner)."}
        except Exception as e:
            logger.error(f"Error executing move_mouse: {e}", exc_info=True)
            return {"status": "failed", "message": str(e)}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "x": {"type": "integer", "description": "The X coordinate"},
                "y": {"type": "integer", "description": "The Y coordinate"}
            },
            "required": ["x", "y"]
        }
