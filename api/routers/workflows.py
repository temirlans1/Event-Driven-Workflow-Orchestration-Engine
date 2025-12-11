from fastapi import APIRouter, HTTPException
from clients.redis_client import redis_client
from orchestrator.loader import load_workflow
from orchestrator.state import get_all_node_outputs

router = APIRouter()


@router.get("/{execution_id}")
def get_workflow_status(execution_id: str):
    if not redis_client.exists(f"workflow:{execution_id}"):
        raise HTTPException(status_code=404, detail="Workflow not found")

    status = redis_client.get(f"workflow:{execution_id}:status")

    return {
        "execution_id": execution_id,
        "status": status,
    }


@router.get("/{execution_id}/results")
def get_results(execution_id: str):
    workflow = load_workflow(execution_id)
    node_ids = [node.id for node in workflow.nodes]
    all_outputs = get_all_node_outputs(execution_id, node_ids)
    return {
        "execution_id": execution_id,
        "results": all_outputs
    }
