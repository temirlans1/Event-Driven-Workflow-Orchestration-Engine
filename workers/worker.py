import time
import json
import redis

from orchestrator.models import NodeStatus
from orchestrator.registry import get_handler
from clients.redis_client import redis_client
from orchestrator.state import set_node_status

STREAM = "workflow:tasks"
GROUP = "workflow_group"
CONSUMER = "worker_1"


def group_setup():
    try:
        redis_client.xgroup_create(STREAM, GROUP, id='0', mkstream=True)
    except redis.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise


def process_task(task_data):
    _, task = task_data
    execution_id = task["execution_id"]
    node_id = task["node_id"]
    payload = json.loads(task["payload"])

    set_node_status(execution_id, node_id, NodeStatus.RUNNING)
    try:
        handler_fn = get_handler(payload["handler"])
        handler_fn(node_id, execution_id, payload["config"])
        set_node_status(execution_id, node_id, NodeStatus.COMPLETED)
    except Exception as e:
        set_node_status(execution_id, node_id, NodeStatus.FAILED, error=str(e))


def run_worker():
    group_setup()

    print(f"[worker] Starting Redis consumer for stream '{STREAM}'...")
    while True:
        try:
            response = redis_client.xreadgroup(
                groupname=GROUP,
                consumername=CONSUMER,
                streams={STREAM: '>'},
            )
            print(response)
            if response:
                for stream_name, messages in response:
                    for msg in messages:
                        process_task(msg)
        except Exception as e:
            print(f"[worker] Error: {e}")
        time.sleep(1)


if __name__ == "__main__":
    run_worker()
