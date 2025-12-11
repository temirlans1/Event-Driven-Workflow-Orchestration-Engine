import time
import json
from redis.exceptions import ConnectionError
from logging_config import get_logger
from clients.redis_client import redis_client
from orchestrator.models import NodeStatus
from orchestrator.state import set_node_status, set_node_output, get_node_status
from workers.registry import get_handler

STREAM = "workflow:tasks"
GROUP = "workflow_group"
CONSUMER = "worker-1"

logger = get_logger(__name__)


def ensure_group_exists():
    """Create the Redis consumer group for the worker stream if absent."""
    logger.info("Ensuring consumer group %s exists for stream %s", GROUP, STREAM)
    try:
        redis_client.xgroup_create(STREAM, GROUP, id="0", mkstream=True)
        logger.info("Group '%s' created on stream '%s'", GROUP, STREAM)
    except Exception as e:
        if "BUSYGROUP" in str(e):
            logger.info("Group '%s' already exists", GROUP)
        else:
            raise


def process_message(msg_id, fields):
    """Handle a single stream message and execute its handler."""
    logger.info("Processing message %s with fields %s", msg_id, list(fields.keys()))
    execution_id = fields["execution_id"]
    node_id = fields["node_id"]
    payload = json.loads(fields["payload"])
    handler_name = payload["handler"]
    config = payload.get("config", {})

    logger.info("Received task %s/%s using handler %s", execution_id, node_id, handler_name)

    try:
        status = get_node_status(execution_id, node_id)
        if status != NodeStatus.QUEUED:
            logger.info("Skipping task %s: status is %s, expected QUEUED", node_id, status)
            return

        set_node_status(execution_id, node_id, NodeStatus.RUNNING)

        handler = get_handler(handler_name)
        output = handler(config)
        set_node_output(execution_id, node_id, output)

        logger.info("Task %s/%s completed successfully with output keys %s", execution_id, node_id, list(output.keys()))
        set_node_status(execution_id, node_id, NodeStatus.COMPLETED)

    except Exception as e:
        logger.error("Task %s/%s failed: %s", execution_id, node_id, e)
        set_node_status(execution_id, node_id, NodeStatus.FAILED, error=str(e))


def run_worker():
    """Main worker loop: read tasks, execute handlers, and acknowledge."""
    logger.info("Starting worker consumer loop")
    ensure_group_exists()

    logger.info("Worker is running...")

    while True:
        try:
            messages = redis_client.xreadgroup(
                groupname=GROUP,
                consumername=CONSUMER,
                streams={STREAM: '>'},
                count=1,
                block=5000
            )

            if not messages:
                logger.debug("No messages received, continuing")
                continue

            for stream, entries in messages:
                for msg_id, fields in entries:
                    process_message(msg_id, fields)
                    redis_client._redis.xack(STREAM, GROUP, msg_id)

        except ConnectionError:
            logger.warning("Redis connection lost. Retrying in 5s...")
            time.sleep(5)
        except Exception as e:
            logger.error("Unexpected error in worker loop: %s", e)
            time.sleep(2)


if __name__ == "__main__":
    run_worker()
