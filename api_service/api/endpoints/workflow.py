from fastapi import APIRouter, HTTPException
from api.schemas.workflow import WorkflowRequest
from clients.redis_client import redis_client
from core.validator import validate_workflow
from core.orchestrator import trigger_workflow_execution
import uuid

router = APIRouter()


@router.post("")
def submit_workflow(req: WorkflowRequest):
    try:
        validate_workflow(req.dag.nodes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    execution_id = str(uuid.uuid4())
    redis_client.set(f"workflow:{execution_id}", req.model_dump_json())

    for node in req.dag.nodes:
        redis_client.set(f"workflow:{execution_id}:node:{node.id}", "PENDING")
    redis_client.set(f"workflow:{execution_id}:status", "PENDING")

    return {"execution_id": execution_id, "message": "Workflow accepted"}


@router.post("/trigger/{execution_id}")
def trigger_workflow(execution_id: str):
    if not redis_client.exists(f"workflow:{execution_id}"):
        raise HTTPException(status_code=404, detail="Execution ID not found")

    trigger_workflow_execution(execution_id)
    redis_client.set(f"workflow:{execution_id}:status", "RUNNING")
    return {"message": "Workflow triggered", "execution_id": execution_id}
