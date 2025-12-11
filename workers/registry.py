from workers.handlers import (
    noop_handler,
    call_external_service,
    llm,
    unreliable_handler,
)

HANDLER_REGISTRY = {
    "noop": noop_handler,
    "call_external_service": call_external_service,
    "llm": llm,
    "unreliable": unreliable_handler,
}


def get_handler(name: str):
    if name not in HANDLER_REGISTRY:
        return HANDLER_REGISTRY["noop"]
    return HANDLER_REGISTRY[name]
