from workers.handlers import (
    noop_handler,
    call_external_service,
    llm,
    unreliable_handler,
)
from logging_config import get_logger

HANDLER_REGISTRY = {
    "noop": noop_handler,
    "call_external_service": call_external_service,
    "llm": llm,
    "unreliable": unreliable_handler,
}

logger = get_logger(__name__)


def get_handler(name: str):
    logger.info("Fetching handler for name=%s", name)
    if name not in HANDLER_REGISTRY:
        logger.warning("Handler %s not found. Using noop handler.", name)
        return HANDLER_REGISTRY["noop"]
    logger.info("Handler %s found", name)
    return HANDLER_REGISTRY[name]
