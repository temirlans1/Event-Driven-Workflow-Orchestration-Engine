import json
import pytest

from orchestrator.models import NodeStatus
from orchestrator.trigger import trigger_workflow_execution
from orchestrator.task_queue import STREAM_NAME
from clients.redis_client import redis_client
from orchestrator.redis_keys import RedisKeyTemplates


def test_trigger_positive():
    execution_id = "t1"
    redis_client.set(RedisKeyTemplates.WORKFLOW.format(execution_id=execution_id), json.dumps({
        "name": "WF",
        "dag": {"nodes": [{"id": "a", "handler": "noop", "dependencies": []}]}
    }))
    redis_client.set_json(
        RedisKeyTemplates.WORKFLOW_NODE.format(
            execution_id=execution_id, node_id="a"
        ),
        {"status": NodeStatus.PENDING.value},
    )

    trigger_workflow_execution(execution_id)

    msgs = redis_client._redis.xrevrange(STREAM_NAME, count=1)
    assert msgs
    assert msgs[0][1]["node_id"] == "a"


def test_trigger_missing_workflow():
    with pytest.raises(ValueError):
        trigger_workflow_execution("missing-id")
