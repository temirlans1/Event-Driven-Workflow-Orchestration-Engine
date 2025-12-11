import json
import time
import re
from logging_config import get_logger
from clients.redis_client import redis_client
from orchestrator.executor import execute_workflow
from orchestrator.loader import load_workflow
from orchestrator.models import NodeStatus
from orchestrator.state import get_node_status
from orchestrator.redis_keys import RedisKeyTemplates

logger = get_logger(__name__)

WORKFLOW_KEY_PATTERN = re.compile(
    RedisKeyTemplates.WORKFLOW.format(execution_id=r"([a-f0-9\-]+)")
)


def discover_active_workflow_ids() -> list[str]:
    """Return all execution IDs currently tracked as active in Redis."""
    logger.info("Discovering active workflow ids")
    ids = redis_client.smembers(RedisKeyTemplates.WORKFLOWS_ACTIVE)
    logger.info("Found %d active workflow ids", len(ids))
    return [id.decode() if isinstance(id, bytes) else id for id in ids]


def workflow_is_complete(execution_id: str) -> bool:
    """Determine whether a workflow has reached a terminal state."""
    logger.info("Checking if workflow %s is complete", execution_id)
    workflow = load_workflow(execution_id)

    has_failed_node = False
    all_node_statuses = [get_node_status(execution_id, n.id) for n in workflow.nodes]
    for status in all_node_statuses:
        if status == NodeStatus.FAILED:
            has_failed_node = True

        if status in (NodeStatus.RUNNING, NodeStatus.QUEUED):
            logger.info("Workflow %s still active with status %s", execution_id, status)
            return False  # workflow still active

    # If all nodes are terminal (COMPLETED or FAILED)
    terminal_states = {NodeStatus.COMPLETED, NodeStatus.FAILED}
    if all(status in terminal_states for status in all_node_statuses):
        logger.info("Workflow %s reached terminal state", execution_id)
        return True

    # If any FAILED node exists and all others are not running/queued
    if has_failed_node:
        logger.info("Workflow %s completed with failures", execution_id)
        return True

    logger.info("Workflow %s is not complete yet", execution_id)
    return False


def check_completion(execution_id: str) -> bool:
    """
    If the workflow is complete, remove it from the active set.
    Returns True if completed, False otherwise.
    """
    logger.info("Checking completion for workflow %s", execution_id)
    if workflow_is_complete(execution_id):
        redis_client.set(
            RedisKeyTemplates.WORKFLOW_STATUS.format(execution_id=execution_id),
            NodeStatus.COMPLETED,
        )
        redis_client.srem(RedisKeyTemplates.WORKFLOWS_ACTIVE, execution_id)
        logger.info("Workflow %s marked as complete and removed from active set", execution_id)
        return True
    logger.info("Workflow %s still active", execution_id)
    return False


def main_loop(sleep_seconds: int = 5):
    """Continuously schedule workflows, dispatching eligible tasks in a loop.

    Args:
        sleep_seconds: Delay between scheduler iterations.
    """
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
