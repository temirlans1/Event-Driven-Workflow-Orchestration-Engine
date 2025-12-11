from orchestrator.executor import execute_workflow
from clients.redis_client import redis_client


def trigger_workflow_execution(execution_id: str):
    execute_workflow(execution_id)
    redis_client.sadd("workflows:active", execution_id)
