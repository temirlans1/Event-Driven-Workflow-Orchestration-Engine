from orchestrator.task_queue import push_task, STREAM_NAME
from clients.redis_client import redis_client


def test_push_task_positive():
    execution_id = "stream1"
    push_task(execution_id, "n1", {"handler": "noop", "config": {}})

    msgs = redis_client._redis.xrevrange(STREAM_NAME, count=1)
    assert msgs
    data = msgs[0][1]
    assert data["execution_id"] == execution_id
    assert data["node_id"] == "n1"


def test_push_task_empty_payload():
    execution_id = "stream2"
    push_task(execution_id, "n2", {})

    msgs = redis_client._redis.xrevrange(STREAM_NAME, count=1)
    assert msgs
    assert msgs[0][1]["node_id"] == "n2"
