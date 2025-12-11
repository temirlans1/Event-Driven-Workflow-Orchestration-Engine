from fastapi import APIRouter, HTTPException
from orchestrator.loader import load_workflow
from orchestrator.state import get_all_node_outputs, get_workflow_status

router = APIRouter()


@router.get("/{execution_id}")
def get_workflow_status_endpoint(execution_id: str):
    try:
        status = get_workflow_status(execution_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

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
