from typing import List, Union, Dict

class CommandNode:
    def __init__(self, node_id: str, content: Union[str, Dict[str, str]]):
        self.node_id = node_id
        self.content = content
        self.dependencies: List['CommandNode'] = []

    def add_dependency(self, node: 'CommandNode'):
        self.dependencies.append(node)

class CommandGraph:
    def __init__(self):
        self.nodes: List[CommandNode] = []

    def add_node(self, node: CommandNode):
        self.nodes.append(node)
        
    def get_sequential_tasks(self) -> List[Union[str, Dict[str, str]]]:
        """
        Since Day 19 only needs sequential execution, we just return
        the nodes in their insertion order (which preserves the sequence).
        """
        return [node.content for node in self.nodes]

class DependencyGraphBuilder:
    def __init__(self):
        pass

    def build(self, commands: List[Union[str, Dict[str, str]]]) -> CommandGraph:
        graph = CommandGraph()
        prev_node = None
        
        for i, cmd in enumerate(commands):
            node = CommandNode(f"Node_{i+1}", cmd)
            if prev_node:
                node.add_dependency(prev_node)
            graph.add_node(node)
            prev_node = node
            
        return graph
