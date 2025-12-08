import redis
import json
from core.orchestrator_trigger import get_ready_nodes, trigger_workflow_execution

r = redis.Redis(host="localhost", port=6379, decode_responses=True)


def setup_workflow(execution_id):
    nodes = [
        {"id": "A", "handler": "input", "dependencies": []},
        {"id": "B", "handler": "service", "dependencies": ["A"]},
        {"id": "C", "handler": "output", "dependencies": ["B"]}
    ]
    dag = {"name": "Test", "dag": {"nodes": nodes}}
    r.set(f"workflow:{execution_id}", json.dumps(dag))
    for node in nodes:
        r.set(f"workflow:{execution_id}:node:{node['id']}", "PENDING")


def test_trigger_executes_roots():
    execution_id = "test123"
    r.flushall()
    setup_workflow(execution_id)

    trigger_workflow_execution(execution_id)

    # Root node A should now be RUNNING
    assert r.get(f"workflow:{execution_id}:node:A") == "RUNNING"


def test_get_ready_nodes():
    execution_id = "test123"
    r.flushall()
    setup_workflow(execution_id)

    # Mark A as completed
    r.set(f"workflow:{execution_id}:node:A", "COMPLETED")

    # B should now be ready
    ready = get_ready_nodes(execution_id)
    assert "B" in ready
    assert "C" not in ready
