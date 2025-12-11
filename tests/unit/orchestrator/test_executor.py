import json
import json

from orchestrator.executor import execute_workflow
from orchestrator.models import NodeStatus
from orchestrator.task_queue import STREAM_NAME
from clients.redis_client import redis_client
from orchestrator.redis_keys import RedisKeyTemplates


def test_executor_schedules_ready_node():
    execution_id = "exec1"
    redis_client.set(RedisKeyTemplates.WORKFLOW.format(execution_id=execution_id), json.dumps({
        "name": "DAG",
        "dag": {
            "nodes": [
                {"id": "start", "handler": "noop", "dependencies": []},
                {"id": "end", "handler": "noop", "dependencies": ["start"]}
            ]
        }
    }))
    redis_client.set_json(
        RedisKeyTemplates.WORKFLOW_NODE.format(
            execution_id=execution_id, node_id="start"
        ),
        {"status": NodeStatus.PENDING.value},
    )
    redis_client.set_json(
        RedisKeyTemplates.WORKFLOW_NODE.format(
            execution_id=execution_id, node_id="end"
        ),
        {"status": NodeStatus.PENDING.value},
    )

    execute_workflow(execution_id)

    msgs = redis_client._redis.xrevrange(STREAM_NAME, count=10)
    ids = [m[1]["node_id"] for m in msgs]
    assert "start" in ids


def test_executor_schedules_ready_nodes_fan_out():
    execution_id = "exec1"
    redis_client.set(RedisKeyTemplates.WORKFLOW.format(execution_id=execution_id), json.dumps({
        "name": "DAG",
        "dag": {
            "nodes": [
                {"id": "start", "handler": "noop", "dependencies": []},
                {"id": "middle1", "handler": "noop", "dependencies": ['start']},
                {"id": "middle2", "handler": "noop", "dependencies": ['start']},
            ]
        }
    }))
    redis_client.set_json(
        RedisKeyTemplates.WORKFLOW_NODE.format(
            execution_id=execution_id, node_id="start"
        ),
        {"status": NodeStatus.COMPLETED.value},
    )
    redis_client.set_json(
        RedisKeyTemplates.WORKFLOW_NODE.format(
            execution_id=execution_id, node_id="middle1"
        ),
        {"status": NodeStatus.PENDING.value},
    )
    redis_client.set_json(
        RedisKeyTemplates.WORKFLOW_NODE.format(
            execution_id=execution_id, node_id="middle2"
        ),
        {"status": NodeStatus.PENDING.value},
    )

    execute_workflow(execution_id)

    msgs = redis_client._redis.xrevrange(STREAM_NAME, count=10)
    ids = [m[1]["node_id"] for m in msgs]
    assert "middle1" in ids
    assert "middle2" in ids


def test_executor_does_not_schedule_if_dependencies_not_ready():
    execution_id = "exec2"
    redis_client.set(RedisKeyTemplates.WORKFLOW.format(execution_id=execution_id), json.dumps({
        "name": "DAG",
        "dag": {
            "nodes": [
                {"id": "a", "handler": "noop", "dependencies": []},
                {"id": "b", "handler": "noop", "dependencies": ["a"]}
            ]
        }
    }))
    redis_client.set_json(
        RedisKeyTemplates.WORKFLOW_NODE.format(
            execution_id=execution_id, node_id="a"
        ),
        {"status": NodeStatus.QUEUED.value},
    )
    redis_client.set_json(
        RedisKeyTemplates.WORKFLOW_NODE.format(
            execution_id=execution_id, node_id="b"
        ),
        {"status": NodeStatus.PENDING.value},
    )

    execute_workflow(execution_id)

    msgs = redis_client._redis.xrevrange(STREAM_NAME, count=1)
    assert len(msgs) == 0


def test_executor_does_not_schedule_if_already_running():
    execution_id = "exec3"
    redis_client.set(RedisKeyTemplates.WORKFLOW.format(execution_id=execution_id), json.dumps({
        "name": "DAG",
        "dag": {"nodes": [{"id": "x", "handler": "noop", "dependencies": []}]}
    }))
    redis_client.set_json(
        RedisKeyTemplates.WORKFLOW_NODE.format(
            execution_id=execution_id, node_id="x"
        ),
        {"status": NodeStatus.RUNNING.value},
    )
    execute_workflow(execution_id)

    msgs = redis_client._redis.xrevrange(STREAM_NAME, count=1)
    assert msgs == []
