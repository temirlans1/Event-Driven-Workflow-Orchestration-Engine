import time
import json
from redis.exceptions import ConnectionError
from clients.redis_client import redis_client
from orchestrator.models import NodeStatus
from orchestrator.state import set_node_status, set_node_output, get_node_status
from workers.registry import get_handler

STREAM = "workflow:tasks"
GROUP = "workflow_group"
CONSUMER = "worker-1"


def ensure_group_exists():
    try:
        redis_client.xgroup_create(STREAM, GROUP, id="0", mkstream=True)
        print(f"[worker] Group '{GROUP}' created on stream '{STREAM}'")
    except Exception as e:
        if "BUSYGROUP" in str(e):
            print(f"[worker] Group '{GROUP}' already exists")
        else:
            raise


def process_message(msg_id, fields):
    execution_id = fields["execution_id"]
    node_id = fields["node_id"]
    payload = json.loads(fields["payload"])
    handler_name = payload["handler"]
    config = payload.get("config", {})

    print(f"[worker] Received task: {execution_id}/{node_id} (handler: {handler_name})")

    try:
        status = get_node_status(execution_id, node_id)
        if status != NodeStatus.QUEUED:
            print(f"[worker] Skipping task {node_id}: status is {status}, expected QUEUED")
            return

        set_node_status(execution_id, node_id, NodeStatus.RUNNING)

        handler = get_handler(handler_name)
        output = handler(config)
        set_node_output(execution_id, node_id, output)

        print(f"[worker] Success: {output}")
        set_node_status(execution_id, node_id, NodeStatus.COMPLETED)

    except Exception as e:
        print(f"[worker] ERROR: {e}")
        set_node_status(execution_id, node_id, NodeStatus.FAILED, error=str(e))


def run_worker():
    ensure_group_exists()

    print("[worker] Worker is running...")

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
                continue

            for stream, entries in messages:
                for msg_id, fields in entries:
                    process_message(msg_id, fields)
                    redis_client._redis.xack(STREAM, GROUP, msg_id)

        except ConnectionError:
            print("[worker] Redis connection lost. Retrying in 5s...")
            time.sleep(5)
        except Exception as e:
            print(f"[worker] Unexpected error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run_worker()
