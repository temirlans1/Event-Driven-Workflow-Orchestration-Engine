import redis
import json

r = redis.Redis(host="localhost", port=6379, decode_responses=True)


def get_ready_nodes(execution_id):
    workflow = json.loads(r.get(f"workflow:{execution_id}"))
    dag = {node["id"]: node["dependencies"] for node in workflow["dag"]["nodes"]}

    ready = []
    for node_id, deps in dag.items():
        node_state = r.get(f"workflow:{execution_id}:node:{node_id}")
        if node_state != "PENDING":
            continue
        if all(r.get(f"workflow:{execution_id}:node:{dep}") == "COMPLETED" for dep in deps):
            ready.append(node_id)
    return ready


def dispatch_task(execution_id, node_id, node_config, handler):
    payload = {
        "execution_id": execution_id,
        "node_id": node_id,
        "handler": handler,
        "config": json.dumps(node_config)
    }
    r.xadd("workflow_tasks", payload)
    r.set(f"workflow:{execution_id}:node:{node_id}", "RUNNING")


def trigger_workflow_execution(execution_id):
    workflow = json.loads(r.get(f"workflow:{execution_id}"))
    for node in workflow["dag"]["nodes"]:
        if not node["dependencies"]:  # Root node
            dispatch_task(execution_id, node["id"], node.get("config", {}), node["handler"])
