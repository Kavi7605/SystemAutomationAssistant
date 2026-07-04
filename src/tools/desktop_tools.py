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
            return {"status": "success", "title": "Mouse Clicked", "message": "The mouse click was executed successfully."}
        except pyautogui.FailSafeException:
            logger.warning("PyAutoGUI fail-safe triggered during click.")
            return {"status": "failed", "title": "Fail-safe Triggered", "message": "PyAutoGUI fail-safe was triggered (mouse moved to a corner)."}
        except Exception as e:
            logger.error(f"Error executing click: {e}", exc_info=True)
            return {"status": "error", "title": "Execution Error", "message": str(e)}

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
            return {"status": "success", "title": "Mouse Double-Clicked", "message": "The mouse double-click was executed successfully."}
        except pyautogui.FailSafeException:
            logger.warning("PyAutoGUI fail-safe triggered during double-click.")
            return {"status": "failed", "title": "Fail-safe Triggered", "message": "PyAutoGUI fail-safe was triggered (mouse moved to a corner)."}
        except Exception as e:
            logger.error(f"Error executing double-click: {e}", exc_info=True)
            return {"status": "error", "title": "Execution Error", "message": str(e)}

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
            return {"status": "success", "title": "Mouse Right-Clicked", "message": "The mouse right-click was executed successfully."}
        except pyautogui.FailSafeException:
            logger.warning("PyAutoGUI fail-safe triggered during right-click.")
            return {"status": "failed", "title": "Fail-safe Triggered", "message": "PyAutoGUI fail-safe was triggered (mouse moved to a corner)."}
        except Exception as e:
            logger.error(f"Error executing right-click: {e}", exc_info=True)
            return {"status": "error", "title": "Execution Error", "message": str(e)}

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
            return {"status": "failed", "title": "Missing Parameters", "message": "Missing text parameter parameter."}
        
        try:
            logger.info(f"Executing type_text action. text='{text}'")
            pyautogui.write(text)
            return {"status": "success", "title": "Text Typed", "message": f"Successfully typed the text: {text}"}
        except pyautogui.FailSafeException:
            logger.warning("PyAutoGUI fail-safe triggered during type_text.")
            return {"status": "failed", "title": "Fail-safe Triggered", "message": "PyAutoGUI fail-safe was triggered (mouse moved to a corner)."}
        except Exception as e:
            logger.error(f"Error executing type_text: {e}", exc_info=True)
            return {"status": "error", "title": "Execution Error", "message": str(e)}

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
            return {"status": "failed", "title": "Missing Parameters", "message": "Missing keys parameter parameter."}
        
        try:
            logger.info(f"Executing hotkey action. keys={keys}")
            pyautogui.hotkey(*keys)
            return {"status": "success", "title": "Hotkey Pressed", "message": f"Successfully pressed the hotkey combination: {' + '.join(keys)}"}
        except pyautogui.FailSafeException:
            logger.warning("PyAutoGUI fail-safe triggered during hotkey.")
            return {"status": "failed", "title": "Fail-safe Triggered", "message": "PyAutoGUI fail-safe was triggered (mouse moved to a corner)."}
        except Exception as e:
            logger.error(f"Error executing hotkey: {e}", exc_info=True)
            return {"status": "error", "title": "Execution Error", "message": str(e)}

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
            return {"status": "failed", "title": "Missing Parameters", "message": "Missing direction parameter parameter."}
            
        amount = 500 if direction.lower() == "up" else -500
            
        try:
            logger.info(f"Executing scroll action. direction={direction}, amount={amount}")
            pyautogui.scroll(amount)
            return {"status": "success", "title": "Scrolled", "message": f"Successfully scrolled the page {direction}."}
        except pyautogui.FailSafeException:
            logger.warning("PyAutoGUI fail-safe triggered during scroll.")
            return {"status": "failed", "title": "Fail-safe Triggered", "message": "PyAutoGUI fail-safe was triggered (mouse moved to a corner)."}
        except Exception as e:
            logger.error(f"Error executing scroll: {e}", exc_info=True)
            return {"status": "error", "title": "Execution Error", "message": str(e)}

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
            return {"status": "failed", "title": "Missing Parameters", "message": "Missing x or y coordinate parameter."}
            
        try:
            logger.info(f"Executing move_mouse action. x={x}, y={y}")
            pyautogui.moveTo(int(x), int(y))
            return {"status": "success", "title": "Mouse Moved", "message": f"Successfully moved the mouse cursor to ({x}, {y})."}
        except pyautogui.FailSafeException:
            logger.warning("PyAutoGUI fail-safe triggered during move_mouse.")
            return {"status": "failed", "title": "Fail-safe Triggered", "message": "PyAutoGUI fail-safe was triggered (mouse moved to a corner)."}
        except Exception as e:
            logger.error(f"Error executing move_mouse: {e}", exc_info=True)
            return {"status": "error", "title": "Execution Error", "message": str(e)}

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
