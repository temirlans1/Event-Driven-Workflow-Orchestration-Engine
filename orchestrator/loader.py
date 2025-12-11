import json
from orchestrator.models import DAGNode, Workflow
from clients.redis_client import redis_client


def load_workflow(execution_id: str) -> Workflow:
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
