import json
from clients.redis_client import redis_client

STREAM_NAME = "workflow:tasks"


def push_task(execution_id: str, node_id: str, payload: dict):
    redis_client.xadd(STREAM_NAME, {
        "execution_id": execution_id,
        "node_id": node_id,
        "payload": json.dumps(payload)
    })
