from clients.redis_client import redis_client
from orchestrator.models import NodeStatus


def set_workflow_status(execution_id: str, status: NodeStatus, error: str = None):
    """Persist the overall workflow status to Redis.

    Args:
        execution_id: Workflow execution identifier.
        status: New status to store for the workflow.
        error: Optional error message when marking a failure.
    """
    key = f"workflow:{execution_id}:status"
    value = {"status": status.value}
    if error:
        value["error"] = error
    redis_client.set_json(key, value)


def get_workflow_status(execution_id: str) -> NodeStatus:
    """Retrieve the persisted workflow status from Redis.

    Args:
        execution_id: Workflow execution identifier.

    Returns:
        NodeStatus: Stored status value.

    Raises:
        ValueError: If the workflow is missing or stored status is invalid.
    """
    key = f"workflow:{execution_id}:status"
    status = redis_client.get(key)
    if status is None:
        raise ValueError(f"Workflow not found for execution_id={execution_id}")
    try:
        return NodeStatus(status)
    except (KeyError, ValueError):
        raise ValueError(f"Invalid or missing status for workflow {execution_id}")


def set_node_status(execution_id: str, node_id: str, status: NodeStatus, error: str = None):
    """Persist a node's status and optional error message to Redis."""
    key = f"workflow:{execution_id}:node:{node_id}"
    value = {"status": status.value}
    if error:
        value["error"] = error
    redis_client.set_json(key, value)


def get_node_status(execution_id: str, node_id: str) -> NodeStatus:
    """Fetch the status for a specific node in a workflow.

    Args:
        execution_id: Workflow execution identifier.
        node_id: Identifier for the node within the workflow.

    Returns:
        NodeStatus: Current status of the node.

    Raises:
        ValueError: If the node data is missing or invalid.
    """
    key = f"workflow:{execution_id}:node:{node_id}"
    data = redis_client.get_json(key)
    if data is None:
        raise ValueError(f"Node not found for execution_id={execution_id}, node_id={node_id}")
    try:
        return NodeStatus(data["status"])
    except (KeyError, ValueError):
        raise ValueError(f"Invalid or missing status for node {node_id} in execution {execution_id}")


def all_dependencies_succeeded(execution_id: str, dependencies: list) -> bool:
    """Return True if all dependency nodes for a workflow are completed."""
    for dep in dependencies:
        status = get_node_status(execution_id, dep)
        if status != NodeStatus.COMPLETED:
            return False
    return True


def set_node_output(execution_id: str, node_id: str, output: dict):
    """Store the output produced by a workflow node."""
    key = f"workflow:{execution_id}:node:{node_id}:output"
    redis_client.set_json(key, output)


def get_node_output(execution_id: str, node_id: str) -> dict:
    """Retrieve the stored output for a workflow node, or an empty dict."""
    key = f"workflow:{execution_id}:node:{node_id}:output"
    return redis_client.get_json(key) or {}


def get_all_node_outputs(execution_id: str, nodes: list[str]):
    """Collect outputs for a list of nodes keyed by node ID."""
    return {
        node_id: get_node_output(execution_id, node_id)
        for node_id in nodes
    }
