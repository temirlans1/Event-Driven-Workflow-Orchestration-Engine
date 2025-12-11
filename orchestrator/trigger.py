from logging_config import get_logger
from orchestrator.executor import execute_workflow
from clients.redis_client import redis_client
from orchestrator.redis_keys import RedisKeyTemplates


logger = get_logger(__name__)


def trigger_workflow_execution(execution_id: str):
    """Kick off a workflow and track it as active in Redis."""
    logger.info("Triggering workflow execution for %s", execution_id)
    execute_workflow(execution_id)
    redis_client.sadd(RedisKeyTemplates.WORKFLOWS_ACTIVE, execution_id)
    logger.info("Workflow %s added to active set", execution_id)
