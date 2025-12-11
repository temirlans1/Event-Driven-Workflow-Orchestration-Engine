import json
import time
import logging
import re
from clients.redis_client import redis_client
from orchestrator.executor import execute_workflow
from orchestrator.loader import load_workflow
from orchestrator.models import NodeStatus
from orchestrator.state import get_node_status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("starter")

WORKFLOW_KEY_PATTERN = re.compile(r"^workflow:([a-f0-9\-]+)$")


def discover_active_workflow_ids() -> list[str]:
    ids = redis_client.smembers("workflows:active")
    return [id.decode() if isinstance(id, bytes) else id for id in ids]


def workflow_is_complete(execution_id: str) -> bool:
    workflow = load_workflow(execution_id)

    has_failed_node = False
    all_node_statuses = [get_node_status(execution_id, n.id) for n in workflow.nodes]
    for status in all_node_statuses:
        if status == NodeStatus.FAILED:
            has_failed_node = True

        if status in (NodeStatus.RUNNING, NodeStatus.QUEUED):
            return False  # workflow still active

    # If all nodes are terminal (COMPLETED or FAILED)
    terminal_states = {NodeStatus.COMPLETED, NodeStatus.FAILED}
    if all(status in terminal_states for status in all_node_statuses):
        return True

    # If any FAILED node exists and all others are not running/queued
    if has_failed_node:
        return True

    return False


def check_completion(execution_id: str) -> bool:
    """
    If the workflow is complete, remove it from the active set.
    Returns True if completed, False otherwise.
    """
    if workflow_is_complete(execution_id):
        redis_client.set(f"workflow:{execution_id}:status", NodeStatus.COMPLETED)
        redis_client.srem("workflows:active", execution_id)
        return True
    return False


def main_loop(sleep_seconds: int = 5):
    logger.info("[starter] Starting orchestrator scheduler loop...")

    while True:
        try:
            execution_ids = discover_active_workflow_ids()
            logger.info(f"[starter] Discovered {len(execution_ids)} workflows")

            for execution_id in execution_ids:
                if check_completion(execution_id) is True:
                    continue
                try:
                    logger.info(f"[starter] Dispatching workflow: {execution_id}")
                    execute_workflow(execution_id)
                except Exception as e:
                    logger.error(f"[starter] Error executing {execution_id}: {e}")
        except Exception as e:
            logger.critical(f"[starter] Fatal error in main loop: {e}")

        time.sleep(sleep_seconds)


if __name__ == "__main__":
    main_loop()
