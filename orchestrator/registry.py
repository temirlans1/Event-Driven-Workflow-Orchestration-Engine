from typing import Callable, Dict

# Registry of handler functions
HANDLER_REGISTRY: Dict[str, Callable] = {}

def register_handler(name: str):
    def wrapper(func: Callable):
        HANDLER_REGISTRY[name] = func
        return func
    return wrapper

def get_handler(name: str):
    if name not in HANDLER_REGISTRY:
        raise ValueError(f"Handler '{name}' is not registered.")
    return HANDLER_REGISTRY[name]
