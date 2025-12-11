import re
from orchestrator.state import get_node_output

TEMPLATE_PATTERN = re.compile(r"\{\{\s*([\w_]+)\.([\w_]+)\s*\}\}")


def resolve_templates(execution_id: str, config: dict) -> dict:
    resolved = {}

    for key, value in config.items():
        if isinstance(value, str):
            matches = TEMPLATE_PATTERN.findall(value)
            for node_id, output_key in matches:
                output = get_node_output(execution_id, node_id)
                replacement = output.get(output_key, f"<missing:{node_id}.{output_key}>")
                value = value.replace(f"{{{{ {node_id}.{output_key} }}}}", str(replacement))
        resolved[key] = value

    return resolved
