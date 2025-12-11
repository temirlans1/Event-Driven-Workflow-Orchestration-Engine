import json
import pytest

from orchestrator.models import NodeStatus
from clients.redis_client import redis_client

VALID_WORKFLOW = {
    "name": "Test DAG",
    "dag": {
        "nodes": [
            {"id": "input", "handler": "input", "dependencies": []},
            {"id": "task1", "handler": "call_external_service", "dependencies": ["input"], "config": {"url": "http://mock"}},
            {"id": "output", "handler": "output", "dependencies": ["task1"]}
        ]
    }
}

INVALID_WORKFLOW_CYCLE = {
    "name": "Cycle DAG",
    "dag": {
        "nodes": [
            {"id": "A", "handler": "input", "dependencies": ["C"]},
            {"id": "B", "handler": "call_external_service", "dependencies": ["A"]},
            {"id": "C", "handler": "output", "dependencies": ["B"]}
        ]
    }
}


def test_submit_valid_workflow(client):
    response = client.post("/workflow", json=VALID_WORKFLOW)
    assert response.status_code == 200
    assert "execution_id" in response.json()


def test_submit_invalid_workflow_cycle(client):
    response = client.post("/workflow", json=INVALID_WORKFLOW_CYCLE)
    assert response.status_code == 400
    assert "detail" in response.json()


def test_trigger_valid_workflow(client):
    post_resp = client.post("/workflow", json=VALID_WORKFLOW)
    execution_id = post_resp.json()["execution_id"]

    response = client.post(f"/workflow/trigger/{execution_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Workflow triggered"


def test_trigger_invalid_execution_id(client):
    response = client.post("/workflow/trigger/invalid-id")
    assert response.status_code == 404


def test_get_status(client):
    post_resp = client.post("/workflow", json=VALID_WORKFLOW)
    execution_id = post_resp.json()["execution_id"]
    client.post(f"/workflow/trigger/{execution_id}")
    status_resp = client.get(f"/workflows/{execution_id}")
    assert status_resp.status_code == 200
    assert "status" in status_resp.json()


def test_get_status_invalid_id(client):
    response = client.get("/workflows/invalid-id")
    assert response.status_code == 404


def test_get_results_before_execution(client):
    post_resp = client.post("/workflow", json=VALID_WORKFLOW)
    execution_id = post_resp.json()["execution_id"]

    results = client.get(f"/workflows/{execution_id}/results")
    assert results.status_code == 200
    assert results.json()["results"]["task1"] == {}


def test_get_results_after_mock_output(client):
    post_resp = client.post("/workflow", json=VALID_WORKFLOW)
    execution_id = post_resp.json()["execution_id"]

    # Manually inject mock output for testing
    redis_client.set(f"workflow:{execution_id}:node:task1:output", json.dumps({"value": 123}))
    redis_client.set(f"workflow:{execution_id}:node:task1", NodeStatus.COMPLETED.value)

    results = client.get(f"/workflows/{execution_id}/results")
    assert results.status_code == 200
    assert results.json()["results"]["task1"] == {"value": 123}
