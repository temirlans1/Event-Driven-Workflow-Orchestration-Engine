import json
from logging_config import get_logger
from orchestrator.models import DAGNode, Workflow
from clients.redis_client import redis_client
from orchestrator.redis_keys import RedisKeyTemplates


logger = get_logger(__name__)


def load_workflow(execution_id: str) -> Workflow:
    """Load a workflow definition from Redis storage.

    Args:
        execution_id: Identifier for the workflow execution to load.

    Returns:
        Workflow: Parsed workflow object containing DAG nodes.

    Raises:
        ValueError: If the workflow is not present in Redis.
    """
    logger.info("Loading workflow with execution_id=%s", execution_id)
    key = RedisKeyTemplates.WORKFLOW.format(execution_id=execution_id)
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
