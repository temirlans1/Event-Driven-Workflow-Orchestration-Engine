from fastapi import APIRouter, HTTPException
from orchestrator.loader import load_workflow
from orchestrator.state import get_all_node_outputs, get_workflow_status
from logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/{execution_id}")
def get_workflow_status_endpoint(execution_id: str):
    logger.info("Fetching status for workflow %s", execution_id)
    try:
        status = get_workflow_status(execution_id)
    except ValueError as e:
        logger.error("Error fetching status for %s: %s", execution_id, e)
        raise HTTPException(status_code=404, detail=str(e))

    logger.info("Returning status for workflow %s: %s", execution_id, status)
    return {
        "execution_id": execution_id,
        "status": status,
    }


@router.get("/{execution_id}/results")
def get_results(execution_id: str):
    logger.info("Fetching results for workflow %s", execution_id)
    workflow = load_workflow(execution_id)
    node_ids = [node.id for node in workflow.nodes]
    all_outputs = get_all_node_outputs(execution_id, node_ids)
    logger.info("Returning results for workflow %s", execution_id)
    return {
        "execution_id": execution_id,
        "results": all_outputs
    }
