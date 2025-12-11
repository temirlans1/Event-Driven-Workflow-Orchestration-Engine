import json
import pytest
from orchestrator.loader import load_workflow
from clients.redis_client import redis_client
from orchestrator.redis_keys import RedisKeyTemplates


def test_load_workflow_positive():
    execution_id = "load-01"
    data = {
        "name": "TestLoad",
        "dag": {"nodes": [{"id": "a", "handler": "noop", "dependencies": []}]}
    }

    redis_client.set(
        RedisKeyTemplates.WORKFLOW.format(execution_id=execution_id),
        json.dumps(data),
    )
    wf = load_workflow(execution_id)

    assert wf.name == "TestLoad"
    assert wf.nodes[0].id == "a"


def test_load_workflow_missing():
    with pytest.raises(ValueError):
        load_workflow("does-not-exist")


def test_load_workflow_invalid_json():
    execution_id = "load-invalid"
    redis_client.set(
        RedisKeyTemplates.WORKFLOW.format(execution_id=execution_id), "not-json"
    )
    with pytest.raises(Exception):
        load_workflow(execution_id)


def test_load_workflow_missing_node_fields():
    execution_id = "load-bad-nodes"
    redis_client.set(
        RedisKeyTemplates.WORKFLOW.format(execution_id=execution_id),
        json.dumps({
            "name": "Bad",
            "dag": {"nodes": [{"handler": "noop"}]}
        }),
    )
    with pytest.raises(TypeError):
        load_workflow(execution_id)
