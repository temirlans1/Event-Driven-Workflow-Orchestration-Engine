from orchestrator.loader import load_workflow
from orchestrator.models import NodeStatus
from orchestrator.state import get_node_status, all_dependencies_succeeded, set_node_status
from orchestrator.task_queue import push_task
from orchestrator.template import resolve_templates


def execute_workflow(execution_id: str):
    workflow = load_workflow(execution_id)
    for node in workflow.nodes:
        try:
            status = get_node_status(execution_id, node.id)
        except ValueError:
            # First-time run: treat as PENDING
            set_node_status(execution_id, node.id, NodeStatus.PENDING)
            status = NodeStatus.PENDING

        if status == NodeStatus.PENDING and all_dependencies_succeeded(execution_id, node.dependencies):
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
