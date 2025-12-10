from fastapi import APIRouter, HTTPException
from api.schemas.workflow import WorkflowRequest
from clients.redis_client import redis_client
from core.validator import validate_workflow
from core.orchestrator import trigger_workflow_execution
import uuid

router = APIRouter()


@router.get("/{execution_id}")
def get_workflow_status(execution_id: str):
    if not redis_client.exists(f"workflow:{execution_id}"):
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow = redis_client.get_json(f"workflow:{execution_id}")
    status = redis_client.get(f"workflow:{execution_id}:status")
    states = {
        node["id"]: redis_client.get(f"workflow:{execution_id}:node:{node['id']}")
        for node in workflow["dag"]["nodes"]
    }

    return {
        "execution_id": execution_id,
        "status": status,
        "nodes": states
    }


@router.get("/{execution_id}/results")
def get_results(execution_id: str):
    if not redis_client.exists(f"workflow:{execution_id}"):
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow = redis_client.get_json(f"workflow:{execution_id}")
    results = {}
    for node in workflow["dag"]["nodes"]:
        key = f"workflow:{execution_id}:node:{node['id']}:output"
        output = redis_client.get_json(key) or {}
        results[node["id"]] = output

    return {
        "execution_id": execution_id,
        "results": results
    }
