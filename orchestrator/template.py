import re
from logging_config import get_logger

from orchestrator.state import get_node_output

TEMPLATE_PATTERN = re.compile(r"\{\{\s*([\w_]+)\.([\w_]+)\s*\}\}")


logger = get_logger(__name__)


def resolve_templates(execution_id: str, config: dict) -> dict:
    logger.info("Resolving templates for execution_id=%s", execution_id)
    resolved = {}

    for key, value in config.items():
        if isinstance(value, str):
            matches = TEMPLATE_PATTERN.findall(value)
            for node_id, output_key in matches:
                output = get_node_output(execution_id, node_id)
                replacement = output.get(output_key, f"<missing:{node_id}.{output_key}>")
                logger.info(
                    "Resolved template for key=%s using %s.%s -> %s",
                    key,
                    node_id,
                    output_key,
                    replacement,
                )
                value = value.replace(f"{{{{ {node_id}.{output_key} }}}}", str(replacement))
        resolved[key] = value

    logger.info("Template resolution complete for execution_id=%s", execution_id)
    return resolved
