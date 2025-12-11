from collections import defaultdict

from api.schemas.workflow import Node


def validate_workflow(nodes: list[Node]) -> None:
    node_ids = set()
    graph: dict[str, list[str]] = {}

    for node in nodes:
        if node.id in node_ids:
            raise ValueError(f"Duplicate node ID: {node.id}")
        node_ids.add(node.id)
        graph[node.id] = node.dependencies

    for node in nodes:
        for dep in node.dependencies:
            if dep not in graph:
                raise ValueError(f"Invalid dependency: {dep}")

    if has_cycle(graph):
        raise ValueError("Workflow DAG contains a cycle")


def has_cycle(graph: dict[str, list[str]]) -> bool:
    normalized = defaultdict(list, graph)
    visited = set()
    rec_stack = set()

    def visit(node: str) -> bool:
        if node in rec_stack:
            return True
        if node in visited:
            return False

        visited.add(node)
        rec_stack.add(node)
        for neighbor in normalized[node]:
            if visit(neighbor):
                return True
        rec_stack.remove(node)
        return False

    for node in normalized:
        if node not in visited and visit(node):
            return True
    return False
