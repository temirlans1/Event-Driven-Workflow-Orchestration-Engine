from clients.redis_client import redis_client
import json


def get_ready_nodes(execution_id):
    workflow = json.loads(redis_client.get(f"workflow:{execution_id}"))
    dag = {node["id"]: node["dependencies"] for node in workflow["dag"]["nodes"]}

    ready = []
    for node_id, deps in dag.items():
        node_state = redis_client.get(f"workflow:{execution_id}:node:{node_id}")
        if node_state != "PENDING":
            continue
        if all(redis_client.get(f"workflow:{execution_id}:node:{dep}") == "COMPLETED" for dep in deps):
            ready.append(node_id)
    return ready


def dispatch_task(execution_id, node_id, node_config, handler):
    payload = {
        "execution_id": execution_id,
        "node_id": node_id,
        "handler": handler,
        "config": json.dumps(node_config)
    }
    redis_client.xadd("workflow_tasks", payload)
    redis_client.set(f"workflow:{execution_id}:node:{node_id}", "RUNNING")


def trigger_workflow_execution(execution_id):
    workflow = json.loads(redis_client.get(f"workflow:{execution_id}"))
    for node in workflow["dag"]["nodes"]:
        if not node["dependencies"]:  # Root node
            dispatch_task(execution_id, node["id"], node.get("config", {}), node["handler"])
