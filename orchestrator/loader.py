import json
from orchestrator.models import DAGNode, Workflow
from clients.redis_client import redis_client


def load_workflow(execution_id: str) -> Workflow:
    """Load a workflow definition from Redis storage.

    Args:
        execution_id: Identifier for the workflow execution to load.

    Returns:
        Workflow: Parsed workflow object containing DAG nodes.

    Raises:
        ValueError: If the workflow is not present in Redis.
    """
    key = f"workflow:{execution_id}"
    raw = redis_client.get(key)
    if not raw:
        raise ValueError(f"Workflow {execution_id} not found")

    data = json.loads(raw)
    dag_nodes = [DAGNode(**node) for node in data["dag"]["nodes"]]

    return Workflow(
        execution_id=execution_id,
        name=data.get("name", "unnamed"),
        nodes=dag_nodes
    )
