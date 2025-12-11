import json
from logging_config import get_logger
from clients.redis_client import redis_client

STREAM_NAME = "workflow:tasks"


logger = get_logger(__name__)


def push_task(execution_id: str, node_id: str, payload: dict):
    """Push a serialized task message onto the workflow stream."""
    logger.info(
        "Queueing task for execution_id=%s node_id=%s with payload keys=%s",
        execution_id,
        node_id,
        list(payload.keys()),
    )
    redis_client.xadd(STREAM_NAME, {
        "execution_id": execution_id,
        "node_id": node_id,
        "payload": json.dumps(payload)
    })
    logger.info("Task queued on stream %s for %s/%s", STREAM_NAME, execution_id, node_id)
