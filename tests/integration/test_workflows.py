from orchestrator.models import NodeStatus
from orchestrator.state import get_node_output, get_node_status
from orchestrator.task_queue import STREAM_NAME
from workers import worker
from clients.redis_client import redis_client


def _register_workflow(client, workflow: dict) -> str:
    response = client.post("/workflow", json=workflow)
    assert response.status_code == 200
    return response.json()["execution_id"]


def _fetch_tasks():
    return redis_client._redis.xrange(STREAM_NAME, min="-", max="+")


def _process_all_tasks():
    tasks = _fetch_tasks()
    for msg_id, fields in tasks:
        worker.process_message(msg_id, fields)
        redis_client._redis.xdel(STREAM_NAME, msg_id)
    return len(tasks)


def test_cycle_detection_via_api(client):
    payload = {
        "name": "cyclic",
        "dag": {
            "nodes": [
                {"id": "A", "handler": "noop", "dependencies": ["B"], "config": {}},
                {"id": "B", "handler": "noop", "dependencies": ["A"], "config": {}},
            ]
        },
    }

    response = client.post("/workflow", json=payload)
    assert response.status_code == 400
    assert "cycle" in response.json()["detail"].lower()


def test_linear_workflow_execution(client):
    workflow = {
        "name": "linear",
        "dag": {
            "nodes": [
                {
                    "id": "A",
                    "handler": "call_external_service",
                    "dependencies": [],
                    "config": {"url": "http://service-a"},
                },
                {
                    "id": "B",
                    "handler": "llm",
                    "dependencies": ["A"],
                    "config": {"prompt": "Summarize {{ A.data }}"},
                },
                {
                    "id": "C",
                    "handler": "call_external_service",
                    "dependencies": ["B"],
                    "config": {"url": "http://consumer/{{ B.answer }}"},
                },
            ]
        },
    }
    execution_id = _register_workflow(client, workflow)

    while True:
        trigger_response = client.post(f"/workflow/trigger/{execution_id}")
        assert trigger_response.status_code == 200
        processed = _process_all_tasks()
        if processed == 0:
            break

    for node_id in ["A", "B", "C"]:
        assert get_node_status(execution_id, node_id) == NodeStatus.COMPLETED

    c_output = get_node_output(execution_id, "C")
    assert "Simulated response for" in c_output["data"]
    assert "Simulated call to http://service-a" in c_output["data"]


def test_fan_out_in_workflow(client):
    workflow = {
        "name": "fanout",
        "dag": {
            "nodes": [
                {
                    "id": "A",
                    "handler": "call_external_service",
                    "dependencies": [],
                    "config": {"url": "http://root"},
                },
                {
                    "id": "B",
                    "handler": "call_external_service",
                    "dependencies": ["A"],
                    "config": {"url": "http://branch-b/{{ A.data }}"},
                },
                {
                    "id": "C",
                    "handler": "call_external_service",
                    "dependencies": ["A"],
                    "config": {"url": "http://branch-c/{{ A.data }}"},
                },
                {
                    "id": "D",
                    "handler": "llm",
                    "dependencies": ["B", "C"],
                    "config": {"prompt": "Aggregate {{ B.data }} and {{ C.data }}"},
                },
            ]
        },
    }
    execution_id = _register_workflow(client, workflow)

    trigger_response = client.post(f"/workflow/trigger/{execution_id}")
    assert trigger_response.status_code == 200
    initial_tasks = _fetch_tasks()
    assert len(initial_tasks) == 1
    _process_all_tasks()

    trigger_response = client.post(f"/workflow/trigger/{execution_id}")
    assert trigger_response.status_code == 200
    branch_tasks = _fetch_tasks()
    assert {fields["node_id"] for _, fields in branch_tasks} == {"B", "C"}
    _process_all_tasks()

    trigger_response = client.post(f"/workflow/trigger/{execution_id}")
    assert trigger_response.status_code == 200
    final_tasks = _fetch_tasks()
    assert len(final_tasks) == 1
    _process_all_tasks()

    for node_id in ["A", "B", "C", "D"]:
        assert get_node_status(execution_id, node_id) == NodeStatus.COMPLETED

    d_output = get_node_output(execution_id, "D")
    assert "branch-b" in d_output["answer"]
    assert "branch-c" in d_output["answer"]


def test_race_condition_only_triggers_once(client):
    workflow = {
        "name": "race",
        "dag": {
            "nodes": [
                {"id": "B", "handler": "noop", "dependencies": [], "config": {}},
                {"id": "C", "handler": "noop", "dependencies": [], "config": {}},
                {
                    "id": "D",
                    "handler": "llm",
                    "dependencies": ["B", "C"],
                    "config": {"prompt": "B={{ B.status }} C={{ C.status }}"},
                },
            ]
        },
    }
    execution_id = _register_workflow(client, workflow)

    trigger_response = client.post(f"/workflow/trigger/{execution_id}")
    assert trigger_response.status_code == 200
    parallel_tasks = _fetch_tasks()
    assert {fields["node_id"] for _, fields in parallel_tasks} == {"B", "C"}

    _process_all_tasks()

    trigger_response = client.post(f"/workflow/trigger/{execution_id}")
    assert trigger_response.status_code == 200
    final_tasks = _fetch_tasks()
    assert len(final_tasks) == 1
    _process_all_tasks()

    assert get_node_status(execution_id, "D") == NodeStatus.COMPLETED
    d_output = get_node_output(execution_id, "D")
    assert "B=ok" in d_output["answer"]
    assert "C=ok" in d_output["answer"]
