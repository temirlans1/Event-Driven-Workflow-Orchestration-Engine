import json
from logging_config import get_logger
from orchestrator.models import DAGNode, Workflow
from clients.redis_client import redis_client


logger = get_logger(__name__)


def load_workflow(execution_id: str) -> Workflow:
    logger.info("Loading workflow with execution_id=%s", execution_id)
    key = f"workflow:{execution_id}"
    raw = redis_client.get(key)
    if not raw:
        logger.error("Workflow %s not found in Redis", execution_id)
        raise ValueError(f"Workflow {execution_id} not found")

    data = json.loads(raw)
    logger.debug("Parsed workflow data for execution_id=%s", execution_id)
    dag_nodes = [DAGNode(**node) for node in data["dag"]["nodes"]]

    workflow = Workflow(
        execution_id=execution_id,
        name=data.get("name", "unnamed"),
        nodes=dag_nodes
    )
    logger.info("Loaded workflow '%s' with %d nodes", workflow.name, len(workflow.nodes))
    return workflow
