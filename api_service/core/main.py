from fastapi import FastAPI, HTTPException
import uuid
import redis
import json

from core.validator import validate_workflow
from core.orchestrator_trigger import trigger_workflow_execution
from core.models import WorkflowRequest

app = FastAPI()
r = redis.Redis(host='localhost', port=6379, decode_responses=True)


@app.post("/workflow")
def submit_workflow(req: WorkflowRequest):
    try:
        validate_workflow(req.dag.nodes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    execution_id = str(uuid.uuid4())

    # Save workflow to Redis
    r.set(f"workflow:{execution_id}", req.model_dump_json())

    # Initialize node states
    for node in req.dag.nodes:
        r.set(f"workflow:{execution_id}:node:{node.id}", "PENDING")

    r.set(f"workflow:{execution_id}:status", "PENDING")

    return {"execution_id": execution_id, "message": "Workflow accepted"}


@app.post("/workflow/trigger/{execution_id}")
def trigger(execution_id: str):
    if not r.exists(f"workflow:{execution_id}"):
        raise HTTPException(status_code=404, detail="Execution ID not found")

    trigger_workflow_execution(execution_id)
    r.set(f"workflow:{execution_id}:status", "RUNNING")

    return {"message": "Workflow triggered", "execution_id": execution_id}


@app.get("/workflows/{execution_id}")
def get_status(execution_id: str):
    if not r.exists(f"workflow:{execution_id}"):
        raise HTTPException(status_code=404, detail="Execution ID not found")

    nodes_data = json.loads(r.get(f"workflow:{execution_id}"))
    status = r.get(f"workflow:{execution_id}:status")

    node_states = {}
    for node in nodes_data['dag']['nodes']:
        state = r.get(f"workflow:{execution_id}:node:{node['id']}")
        node_states[node['id']] = state

    return {
        "execution_id": execution_id,
        "status": status,
        "nodes": node_states
    }


@app.get("/workflows/{execution_id}/results")
def get_results(execution_id: str):
    if not r.exists(f"workflow:{execution_id}"):
        raise HTTPException(status_code=404, detail="Execution ID not found")

    nodes_data = json.loads(r.get(f"workflow:{execution_id}"))
    results = {}

    for node in nodes_data['dag']['nodes']:
        key = f"workflow:{execution_id}:node:{node['id']}:output"
        output = r.get(key)
        results[node['id']] = json.loads(output) if output else {}

    return {
        "execution_id": execution_id,
        "results": results
    }
