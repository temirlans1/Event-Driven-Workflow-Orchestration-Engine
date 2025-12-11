from orchestrator.registry import register_handler

@register_handler("noop")
def noop_handler(node_id: str, execution_id: str, config: dict):
    print(f"[{execution_id}] Node '{node_id}' running noop.")


@register_handler("call_external_service")
def call_external(node_id: str, execution_id: str, config: dict):
    import requests
    url = config.get("url")
    if not url:
        raise ValueError("Missing 'url' in config.")

    print(f"[{execution_id}] Calling external URL: {url}")
    response = requests.get(url)
    print(f"[{execution_id}] Got response: {response.status_code}")
