import logging
import contextlib
import os
from typing import Dict, Any
from PySide6.QtCore import QObject, QThread, Signal, Slot

from src.llm.ollama_client import OllamaClient
from src.core.command_parser import CommandParser
from src.core.history_manager import HistoryManager
from src.planner.resolver import CommandResolver
from src.automation.executor import Executor
from src.automation.engine import AutomationEngine
from src.nlp.preprocessor import NLPPreprocessor
from src.tools.registry import ToolRegistry
from src.tools.application_finder import ApplicationFinder
from src.planner.task_planner import TaskPlanner

from src.tools.system_tools import OpenApplicationTool, CloseApplicationTool, TakeScreenshotTool, SearchWebTool, OpenUrlTool
from src.tools.filesystem_tools import (
    CreateFolderTool, CreateFileTool, RenameItemTool, DeleteItemTool,
    CopyFileTool, MoveFileTool, OpenItemTool, FindItemTool,
    ConfirmDeleteTool, CancelDeleteTool
)
from src.tools.wait_tool import WaitTool
from src.tools.desktop_tools import (
    ClickTool, DoubleClickTool, RightClickTool, TypeTextTool,
    HotkeyTool, ScrollTool, MoveMouseTool
)
from src.tools.system_control.window_tools import (
    MinimizeWindowTool, MaximizeWindowTool, RestoreWindowTool,
    GetCurrentWindowTool, ListOpenWindowsTool, IsWindowOpenTool, FocusWindowTool
)
from src.tools.system_control.volume_tools import (
    MuteVolumeTool, UnmuteVolumeTool, IncreaseVolumeTool,
    DecreaseVolumeTool, SetVolumeTool, GetVolumeStatusTool
)
from src.tools.system_control.brightness_tools import (
    IncreaseBrightnessTool, DecreaseBrightnessTool, SetBrightnessTool, GetBrightnessStatusTool
)
from src.tools.system_control.display_tools import GetDisplayStatusTool
from src.tools.system_control.wifi_tools import (
    EnableWifiTool, DisableWifiTool, GetWifiStatusTool, WifiDebugTool
)
from src.tools.system_control.hotspot_tools import GetHotspotStatusTool
from src.tools.system_control.power_tools import (
    GetBatterySaverStatusTool, ListPowerProfilesTool, GetPowerModeStatusTool, SetPowerModeTool
)
from src.tools.system_control.power_actions_tools import (
    ShutdownTool, RestartTool, SleepTool, LockScreenTool,
    ConfirmPowerActionTool, CancelPowerActionTool
)

from src.context.application_state_manager import ApplicationStateManager
from src.context.context_manager import ContextManager
from src.context.reference_resolver import ReferenceResolver
from src.context.persistence_manager import PersistenceManager

logger = logging.getLogger(__name__)

class ExecutionWorker(QObject):
    finished = Signal(dict) # result dict
    
    def __init__(self, engine: AutomationEngine):
        super().__init__()
        self.engine = engine
        self.command = ""
        
    @Slot()
    def run(self):
        try:
            with open(os.devnull, 'w') as fnull:
                with contextlib.redirect_stdout(fnull):
                    self.engine.process_command(self.command, source="keyboard")
            history = self.engine.history_manager.get_recent_commands(limit=1)
            if history:
                self.finished.emit(history[-1])
            else:
                self.finished.emit({"execution_result": {"status": "error", "message": "No history entry found."}})
        except Exception as e:
            logger.error(f"ExecutionWorker error: {e}", exc_info=True)
            self.finished.emit({"execution_result": {"status": "error", "message": str(e)}})

class VoiceWorker(QObject):
    recognized = Signal(str)
    error = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.listener = None
            
    @Slot()
    def listen(self):
        if self.listener is None:
            try:
                from src.voice.voice_listener import VoiceListener
                self.listener = VoiceListener()
            except Exception as e:
                logger.error(f"Failed to initialize VoiceListener: {e}", exc_info=True)
                self.error.emit("Voice recognition is not available or failed to initialize.")
                return
            
        try:
            result = self.listener.listen(manual_stop_only=True)
            if result and result.get("transcript"):
                self.recognized.emit(result["transcript"])
            else:
                self.error.emit("No speech detected.")
        except Exception as e:
            logger.error(f"VoiceWorker error: {e}", exc_info=True)
            self.error.emit(str(e))


class AutomationBackend(QObject):
    command_finished = Signal(dict)
    voice_recognized = Signal(str)
    voice_error = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.engine = self._initialize_engine()
        
        # Execution Thread
        self.exec_thread = QThread()
        self.exec_worker = ExecutionWorker(self.engine)
        self.exec_worker.moveToThread(self.exec_thread)
        self.exec_worker.finished.connect(self._on_execution_finished)
        self.exec_thread.start()
        
        # Voice Thread
        self.voice_thread = QThread()
        self.voice_worker = VoiceWorker()
        self.voice_worker.moveToThread(self.voice_thread)
        self.voice_worker.recognized.connect(self.voice_recognized)
        self.voice_worker.error.connect(self.voice_error)
        self.voice_thread.start()
        
    def _initialize_engine(self) -> AutomationEngine:
        registry = ToolRegistry()
        app_finder = ApplicationFinder()
        
        registry.register(OpenApplicationTool(app_finder))
        registry.register(CloseApplicationTool())
        registry.register(TakeScreenshotTool())
        registry.register(SearchWebTool())
        registry.register(WaitTool())
        registry.register(OpenUrlTool())
        
        registry.register(CreateFolderTool())
        registry.register(CreateFileTool())
        registry.register(RenameItemTool())
        registry.register(DeleteItemTool())
        registry.register(CopyFileTool())
        registry.register(MoveFileTool())
        registry.register(OpenItemTool())
        registry.register(FindItemTool())
        registry.register(ConfirmDeleteTool())
        registry.register(CancelDeleteTool())
        
        registry.register(ClickTool())
        registry.register(DoubleClickTool())
        registry.register(RightClickTool())
        registry.register(TypeTextTool())
        registry.register(HotkeyTool())
        registry.register(ScrollTool())
        registry.register(MoveMouseTool())
        
        registry.register(IsWindowOpenTool())
        registry.register(FocusWindowTool())
        registry.register(MinimizeWindowTool())
        registry.register(MaximizeWindowTool())
        registry.register(RestoreWindowTool())
        registry.register(GetCurrentWindowTool())
        registry.register(ListOpenWindowsTool())
        
        registry.register(MuteVolumeTool())
        registry.register(UnmuteVolumeTool())
        registry.register(IncreaseVolumeTool())
        registry.register(DecreaseVolumeTool())
        registry.register(SetVolumeTool())
        registry.register(GetVolumeStatusTool())
        
        registry.register(IncreaseBrightnessTool())
        registry.register(DecreaseBrightnessTool())
        registry.register(SetBrightnessTool())
        registry.register(GetBrightnessStatusTool())
        
        registry.register(GetDisplayStatusTool())
        
        registry.register(EnableWifiTool())
        registry.register(DisableWifiTool())
        registry.register(GetWifiStatusTool())
        registry.register(WifiDebugTool())
        registry.register(GetHotspotStatusTool())
        registry.register(GetBatterySaverStatusTool())
        registry.register(ListPowerProfilesTool())
        registry.register(GetPowerModeStatusTool())
        registry.register(SetPowerModeTool())
        registry.register(ShutdownTool())
        registry.register(RestartTool())
        registry.register(SleepTool())
        registry.register(LockScreenTool())
        registry.register(ConfirmPowerActionTool())
        registry.register(CancelPowerActionTool())
        
        client = OllamaClient(host="http://localhost:11434", model="gemma3:4b")
        parser = CommandParser(client=client, registry=registry)
        resolver = CommandResolver()
        task_planner = TaskPlanner()
        
        persistence_manager = PersistenceManager()
        state_manager = ApplicationStateManager(persistence_manager)
        context_manager = ContextManager(persistence_manager)
        
        state_manager.load()
        context_manager.load()
        
        reference_resolver = ReferenceResolver(context_manager)
        
        executor = Executor(
            registry=registry, 
            state_manager=state_manager, 
            context_manager=context_manager,
            reference_resolver=reference_resolver
        )

        history_manager = HistoryManager()
        nlp_preprocessor = NLPPreprocessor()
        
        engine = AutomationEngine(
            parser=parser,
            resolver=resolver,
            task_planner=task_planner,
            executor=executor,
            history_manager=history_manager,
            context_manager=context_manager,
            reference_resolver=reference_resolver,
            nlp_preprocessor=nlp_preprocessor
        )
        return engine

    def execute(self, text: str):
        self.exec_worker.command = text
        # trigger run on worker thread
        from PySide6.QtCore import QMetaObject, Qt
        QMetaObject.invokeMethod(self.exec_worker, "run", Qt.QueuedConnection)

    def start_voice(self):
        from PySide6.QtCore import QMetaObject, Qt
        QMetaObject.invokeMethod(self.voice_worker, "listen", Qt.QueuedConnection)

    @Slot(dict)
    def _on_execution_finished(self, result: dict):
        self.command_finished.emit(result)
        
    def get_recent_actions(self):
        return self.engine.history_manager.get_recent_commands(limit=20)
        
    def get_status(self) -> Dict[str, Any]:
        if not self.engine.context_manager:
            return {}
        return self.engine.context_manager.get_context_snapshot()

    def shutdown(self):
        self.exec_thread.quit()
        self.exec_thread.wait()
        self.voice_thread.quit()
        self.voice_thread.wait()
        
    def stop_voice(self):
        if self.voice_worker.listener:
            self.voice_worker.listener.stop()
