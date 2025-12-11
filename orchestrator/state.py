from logging_config import get_logger
from clients.redis_client import redis_client
from orchestrator.models import NodeStatus


logger = get_logger(__name__)


def set_workflow_status(execution_id: str, status: NodeStatus, error: str = None):
    """Persist the overall workflow status to Redis.

    Args:
        execution_id: Workflow execution identifier.
        status: New status to store for the workflow.
        error: Optional error message when marking a failure.
    """
    logger.info(
        "Setting workflow status for %s to %s%s",
        execution_id,
        status,
        f" with error: {error}" if error else "",
    )
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
    logger.info("Retrieving workflow status for execution_id=%s", execution_id)
    key = f"workflow:{execution_id}:status"
    status = redis_client.get(key)
    if status is None:
        logger.error("Workflow status missing for execution_id=%s", execution_id)
        raise ValueError(f"Workflow not found for execution_id={execution_id}")
    try:
        return NodeStatus(status)
    except (KeyError, ValueError):
        logger.error("Invalid workflow status for execution_id=%s", execution_id)
        raise ValueError(f"Invalid or missing status for workflow {execution_id}")


def set_node_status(execution_id: str, node_id: str, status: NodeStatus, error: str = None):
    """Persist a node's status and optional error message to Redis."""
    logger.info(
        "Setting node status for %s/%s to %s%s",
        execution_id,
        node_id,
        status,
        f" with error: {error}" if error else "",
    )
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
    logger.info("Retrieving node status for %s/%s", execution_id, node_id)
    key = f"workflow:{execution_id}:node:{node_id}"
    data = redis_client.get_json(key)
    if data is None:
        logger.error("Node status missing for %s/%s", execution_id, node_id)
        raise ValueError(f"Node not found for execution_id={execution_id}, node_id={node_id}")
    try:
        return NodeStatus(data["status"])
    except (KeyError, ValueError):
        logger.error("Invalid node status for %s/%s", execution_id, node_id)
        raise ValueError(f"Invalid or missing status for node {node_id} in execution {execution_id}")


def all_dependencies_succeeded(execution_id: str, dependencies: list) -> bool:
    """Return True if all dependency nodes for a workflow are completed."""
    logger.info("Checking dependencies for execution_id=%s: %s", execution_id, dependencies)
    for dep in dependencies:
        status = get_node_status(execution_id, dep)
        if status != NodeStatus.COMPLETED:
            logger.info("Dependency %s has not completed (status=%s)", dep, status)
            return False
    logger.info("All dependencies completed for execution_id=%s", execution_id)
    return True


def set_node_output(execution_id: str, node_id: str, output: dict):
    """Store the output produced by a workflow node."""
    logger.info("Setting output for node %s/%s", execution_id, node_id)
    key = f"workflow:{execution_id}:node:{node_id}:output"
    redis_client.set_json(key, output)


def get_node_output(execution_id: str, node_id: str) -> dict:
    """Retrieve the stored output for a workflow node, or an empty dict."""
    logger.info("Retrieving output for node %s/%s", execution_id, node_id)
    key = f"workflow:{execution_id}:node:{node_id}:output"
    return redis_client.get_json(key) or {}


def get_all_node_outputs(execution_id: str, nodes: list[str]):
    """Collect outputs for a list of nodes keyed by node ID."""
    logger.info("Gathering outputs for workflow %s for nodes: %s", execution_id, nodes)
    return {
        node_id: get_node_output(execution_id, node_id)
        for node_id in nodes
    }
