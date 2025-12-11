from fastapi import APIRouter, HTTPException
from api.schemas.workflow import WorkflowRequest
from clients.redis_client import redis_client
from api.validator import validate_workflow
from orchestrator.models import NodeStatus
from orchestrator.trigger import trigger_workflow_execution
from orchestrator.redis_keys import RedisKeyTemplates
import uuid
from logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("")
def submit_workflow(req: WorkflowRequest):
    logger.info("Received workflow submission request for name=%s", req.name)
    try:
        validate_workflow(req.dag.nodes)
    except ValueError as e:
        logger.error("Workflow validation failed: %s", e)
        raise HTTPException(status_code=400, detail=str(e))

    execution_id = str(uuid.uuid4())
    logger.info("Storing workflow %s with execution_id=%s", req.name, execution_id)
    redis_client.set(
        RedisKeyTemplates.WORKFLOW.format(execution_id=execution_id),
        req.model_dump_json(),
    )

    for node in req.dag.nodes:
        redis_client.set(
            RedisKeyTemplates.WORKFLOW_NODE.format(
                execution_id=execution_id, node_id=node.id
            ),
            NodeStatus.PENDING.value,
        )
    redis_client.set(
        RedisKeyTemplates.WORKFLOW_STATUS.format(execution_id=execution_id),
        NodeStatus.PENDING.value,
    )

    logger.info("Workflow %s queued successfully", execution_id)
    return {"execution_id": execution_id, "message": "Workflow accepted"}


@router.post("/trigger/{execution_id}")
def trigger_workflow(execution_id: str):
    logger.info("Trigger request received for execution_id=%s", execution_id)
    if not redis_client.exists(
        RedisKeyTemplates.WORKFLOW.format(execution_id=execution_id)
    ):
        logger.error("Execution ID %s not found", execution_id)
        raise HTTPException(status_code=404, detail="Execution ID not found")
    trigger_workflow_execution(execution_id)
    redis_client.set(
        RedisKeyTemplates.WORKFLOW_STATUS.format(execution_id=execution_id),
        NodeStatus.RUNNING.value,
    )
    logger.info("Workflow %s triggered", execution_id)
    return {"message": "Workflow triggered", "execution_id": execution_id}
