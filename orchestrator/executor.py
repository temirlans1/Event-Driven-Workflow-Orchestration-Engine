from logging_config import get_logger
from orchestrator.loader import load_workflow
from orchestrator.models import NodeStatus
from orchestrator.state import get_node_status, all_dependencies_succeeded, set_node_status
from orchestrator.task_queue import push_task
from orchestrator.template import resolve_templates


logger = get_logger(__name__)


def execute_workflow(execution_id: str):
    """Dispatch tasks for a workflow whose dependencies are satisfied.

    The function loads the workflow DAG for the provided execution ID, checks
    the status of each node, and pushes runnable tasks onto the task queue.
    Nodes are marked as queued once scheduled.

    Args:
        execution_id: Unique identifier for the workflow execution.
    """
    logger.info("Executing workflow %s", execution_id)
    workflow = load_workflow(execution_id)
    for node in workflow.nodes:
        try:
            status = get_node_status(execution_id, node.id)
        except ValueError:
            # First-time run: treat as PENDING
            set_node_status(execution_id, node.id, NodeStatus.PENDING)
            status = NodeStatus.PENDING

        if status == NodeStatus.PENDING and all_dependencies_succeeded(execution_id, node.dependencies):
            logger.info("Scheduling node %s for execution_id=%s", node.id, execution_id)
            inputs = resolve_templates(execution_id, node.config)
            set_node_status(execution_id, node.id, NodeStatus.QUEUED)
            push_task(
                execution_id=execution_id,
                node_id=node.id,
                payload={
                    "handler": node.handler,
                    "config": inputs
                }
            )
        else:
            logger.info(
                "Skipping node %s for execution_id=%s (status=%s or dependencies incomplete)",
                node.id,
                execution_id,
                status,
            )
