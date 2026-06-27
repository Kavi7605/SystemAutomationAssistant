import pytest
from src.parser.dependency_graph import DependencyGraphBuilder

def test_dependency_graph():
    builder = DependencyGraphBuilder()
    graph = builder.build(["open steam", "wait until steam opens", "focus steam", "maximize steam"])
    tasks = graph.get_sequential_tasks()
    assert tasks == ["open steam", "wait until steam opens", "focus steam", "maximize steam"]
    
    assert len(graph.nodes) == 4
    assert graph.nodes[0].node_id == "Node_1"
    assert len(graph.nodes[0].dependencies) == 0
    
    assert graph.nodes[1].node_id == "Node_2"
    assert len(graph.nodes[1].dependencies) == 1
    assert graph.nodes[1].dependencies[0] == graph.nodes[0]
