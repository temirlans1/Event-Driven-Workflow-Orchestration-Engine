from clients.redis_client import redis_client
from orchestrator.models import NodeStatus


def set_node_status(execution_id: str, node_id: str, status: NodeStatus, error: str = None):
    key = f"workflow:{execution_id}:node:{node_id}"
    value = {"status": status.value}
    if error:
        value["error"] = error
    redis_client.set_json(key, value)


def get_node_status(execution_id: str, node_id: str) -> NodeStatus:
    key = f"workflow:{execution_id}:node:{node_id}"
    data = redis_client.get_json(key)
    if data is None:
        raise ValueError(f"Node not found for execution_id={execution_id}, node_id={node_id}")
    try:
        return NodeStatus(data["status"])
    except (KeyError, ValueError):
        raise ValueError(f"Invalid or missing status for node {node_id} in execution {execution_id}")


def all_dependencies_succeeded(execution_id: str, dependencies: list) -> bool:
    for dep in dependencies:
        status = get_node_status(execution_id, dep)
        if status != NodeStatus.COMPLETED:
            return False
    return True


def set_node_output(execution_id: str, node_id: str, output: dict):
    key = f"workflow:{execution_id}:node:{node_id}:output"
    redis_client.set_json(key, output)


def get_node_output(execution_id: str, node_id: str) -> dict:
    key = f"workflow:{execution_id}:node:{node_id}:output"
    return redis_client.get_json(key) or {}


def get_all_node_outputs(execution_id: str, nodes: list[str]):
    return {
        node_id: get_node_output(execution_id, node_id)
        for node_id in nodes
    }
