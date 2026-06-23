import sys
from src.llm.ollama_client import OllamaClient
from src.core.command_parser import CommandParser
from src.core.history_manager import HistoryManager
from src.planner.resolver import CommandResolver
from src.automation.executor import Executor
from src.automation.engine import AutomationEngine
from src.utils.logger import setup_logger
from src.tools.registry import ToolRegistry
from src.tools.application_finder import ApplicationFinder
from src.planner.task_planner import TaskPlanner
from src.tools.system_tools import (
    OpenApplicationTool,
    CloseApplicationTool,
    TakeScreenshotTool,
    SearchWebTool,
    OpenUrlTool,
    OpenFolderTool,
    OpenFileTool
)
from src.tools.filesystem_tools import (
    CreateFolderTool,
    CreateFileTool,
    RenameItemTool,
    DeleteItemTool,
    CopyFileTool,
    MoveFileTool,
    OpenWorkspaceItemTool
)
from src.tools.wait_tool import WaitTool
from src.tools.desktop_tools import (
    ClickTool,
    DoubleClickTool,
    RightClickTool,
    TypeTextTool,
    HotkeyTool,
    ScrollTool,
    MoveMouseTool
)
from src.tools.window_tools import (
    GetActiveWindowTool,
    IsWindowOpenTool,
    FocusWindowTool
)

logger = setup_logger("system_assistant")

def main():
    print("Initializing System Automation Assistant...")
    
    try:
        # 0. Initialize Foundations (Tool Registry & Application Finder)
        registry = ToolRegistry()
        app_finder = ApplicationFinder()
        
        # Register Tools
        registry.register(OpenApplicationTool(app_finder))
        registry.register(CloseApplicationTool())
        registry.register(TakeScreenshotTool())
        registry.register(SearchWebTool())
        registry.register(WaitTool())
        registry.register(OpenUrlTool())
        registry.register(OpenFolderTool())
        registry.register(OpenFileTool())
        
        # Filesystem Tools
        registry.register(CreateFolderTool())
        registry.register(CreateFileTool())
        registry.register(RenameItemTool())
        registry.register(DeleteItemTool())
        registry.register(CopyFileTool())
        registry.register(MoveFileTool())
        registry.register(OpenWorkspaceItemTool())
        
        # Desktop Tools
        registry.register(ClickTool())
        registry.register(DoubleClickTool())
        registry.register(RightClickTool())
        registry.register(TypeTextTool())
        registry.register(HotkeyTool())
        registry.register(ScrollTool())
        registry.register(MoveMouseTool())
        
        # Window Tools
        registry.register(GetActiveWindowTool())
        registry.register(IsWindowOpenTool())
        registry.register(FocusWindowTool())
        
        # 1. Create Ollama client connecting to localhost:11434 with gemma3:4b
        client = OllamaClient(host="http://localhost:11434", model="gemma3:4b")
        
        # 2. Initialize Command Parser with dynamic tool registry
        parser = CommandParser(client=client, registry=registry)
        
        # 3. Initialize Planner Layer (Resolves vague entities)
        resolver = CommandResolver()
        
        # 3.5 Initialize Task Planner (Llama3)
        task_planner = TaskPlanner()
        
        # 4. Initialize Executor Engine (Executes system actions dynamically)
        from src.context.window_manager import WindowManager
        from src.context.application_state_manager import ApplicationStateManager
        from src.context.context_manager import ContextManager
        from src.context.reference_resolver import ReferenceResolver
        
        from src.context.persistence_manager import PersistenceManager
        
        window_manager = WindowManager()
        persistence_manager = PersistenceManager()
        
        state_manager = ApplicationStateManager(window_manager, persistence_manager)
        context_manager = ContextManager(persistence_manager)
        
        # Load persisted data on startup
        state_manager.load()
        context_manager.load()
        
        reference_resolver = ReferenceResolver(context_manager)
        
        executor = Executor(
            registry=registry, 
            state_manager=state_manager, 
            context_manager=context_manager,
            reference_resolver=reference_resolver
        )

        # 5. Initialize Command History Manager
        history_manager = HistoryManager()
        
        # 6. Initialize and start the Automation Engine
        engine = AutomationEngine(
            parser=parser,
            resolver=resolver,
            task_planner=task_planner,
            executor=executor,
            history_manager=history_manager,
            context_manager=context_manager,
            reference_resolver=reference_resolver
        )
        engine.start()
                
    except Exception as e:
        logger.error(f"Critical application error during startup: {e}", exc_info=True)
        print(f"\nFailed to start the Assistant: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
