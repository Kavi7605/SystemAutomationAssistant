import re
from typing import List, Union, Dict
from src.parser.command_splitter import AdvancedCommandSplitter
from src.parser.nested_parser import NestedParser
from src.parser.condition_parser import ConditionParser
from src.parser.dependency_graph import DependencyGraphBuilder, CommandGraph

class SequentialContext:
    def __init__(self):
        self.current_app = None
        self.previous_app = None
        self.referenced_apps = []
        
    def update(self, app_name: str):
        if not app_name:
            return
        if self.current_app and self.current_app.lower() != app_name.lower():
            self.previous_app = self.current_app
        self.current_app = app_name
        if app_name not in self.referenced_apps:
            self.referenced_apps.append(app_name)
            
    def resolve(self, reference: str) -> str:
        ref_lower = reference.lower().strip()
        if ref_lower in ["it", "that", "this", "current app", "active app"]:
            return self.current_app if self.current_app else reference
        if ref_lower in ["previous app", "last app"]:
            return self.previous_app if self.previous_app else reference
        return reference

class ParserPipeline:
    def __init__(self):
        self.splitter = AdvancedCommandSplitter()
        self.nested = NestedParser()
        self.condition = ConditionParser()
        self.graph_builder = DependencyGraphBuilder()

    def _extract_app(self, text: str) -> str:
        match = re.search(r'\b(?:open|close|focus|maximize|minimize|launch|start)\s+([a-zA-Z0-9_\-\s]+?)(?:\s+(?:website|app|application|folder|file))?$', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        match = re.search(r'\b(?:if|when|while)\s+([a-zA-Z0-9_\-\s]+?)\s+(?:is|are)\b', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
            
        match = re.search(r'\bwait\s+(?:until|for)\s+([a-zA-Z0-9_\-\s]+?)\s+(?:to\s+)?(?:open|start|close|load)s?\b', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
            
        return None

    def _resolve_context(self, tasks: List[Union[str, Dict]]) -> List[Union[str, Dict]]:
        ctx = SequentialContext()
        ref_regex = re.compile(r'\b(it|that|this|previous app|last app|current app|active app)\b', re.IGNORECASE)
        
        resolved_tasks = []
        for task in tasks:
            if isinstance(task, str):
                def replacer(match):
                    return ctx.resolve(match.group(1))
                    
                resolved_task = ref_regex.sub(replacer, task)
                
                app = self._extract_app(resolved_task)
                if app:
                    ctx.update(app)
                    
                resolved_tasks.append(resolved_task)
            else:
                resolved_tasks.append(task)
        return resolved_tasks

    def parse(self, user_input: str) -> CommandGraph:
        parts = self.splitter.split(user_input)
        flattened = self.nested.parse(parts)
        resolved = self._resolve_context(flattened)
        conditionals = self.condition.parse(resolved)
        graph = self.graph_builder.build(conditionals)
        return graph
