from orchestrator.models import DAGNode
from orchestrator.registry import get_handler

def run_handler(node: DAGNode, execution_id: str):
    handler_fn = get_handler(node.handler)
    handler_fn(node, execution_id)
