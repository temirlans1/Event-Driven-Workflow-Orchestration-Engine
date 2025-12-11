from collections import defaultdict
from logging_config import get_logger

from api.schemas.workflow import Node


logger = get_logger(__name__)


def validate_workflow(nodes: list[Node]) -> None:
    """Validate workflow nodes for duplicate IDs, missing deps, and cycles."""
    logger.info("Validating workflow with %d nodes", len(nodes))
    node_ids = set()
    graph: dict[str, list[str]] = {}

    for node in nodes:
        if node.id in node_ids:
            logger.error("Duplicate node id detected: %s", node.id)
            raise ValueError(f"Duplicate node ID: {node.id}")
        node_ids.add(node.id)
        graph[node.id] = node.dependencies

    for node in nodes:
        for dep in node.dependencies:
            if dep not in graph:
                logger.error("Invalid dependency %s referenced by node %s", dep, node.id)
                raise ValueError(f"Invalid dependency: {dep}")

    if has_cycle(graph):
        logger.error("Workflow DAG contains a cycle")
        raise ValueError("Workflow DAG contains a cycle")

    logger.info("Workflow validation succeeded")


def has_cycle(graph: dict[str, list[str]]) -> bool:
    """Return True if the directed graph contains a cycle."""
    logger.info("Checking workflow DAG for cycles")
    normalized = defaultdict(list, graph)
    visited = set()
    rec_stack = set()

    def visit(node: str) -> bool:
        """Depth-first traversal helper used for cycle detection."""
        logger.info("Visiting node %s for cycle detection", node)
        if node in rec_stack:
            logger.info("Cycle detected via node %s", node)
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
    logger.info("No cycles detected in workflow DAG")
    return False
