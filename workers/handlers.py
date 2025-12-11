import time
import random
from logging_config import get_logger


logger = get_logger(__name__)


def noop_handler(config):
    logger.info("noop_handler invoked with config keys: %s", list(config.keys()))
    return {"status": "ok"}


def call_external_service(config):
    url = config.get("url", "http://example.com")
    logger.info("call_external_service invoked with url=%s", url)
    time.sleep(1)  # simulate delay
    return {"status": "ok", "data": f"Simulated call to {url}"}


def llm(config):
    prompt = config.get("prompt", "Hello, world!")
    logger.info("llm handler invoked with prompt starting: %s", prompt[:30])
    return {"status": "ok", "answer": f"Simulated response for: {prompt}"}


def unreliable_handler(config):
    # Randomly fails
    logger.info("unreliable_handler invoked")
    if random.random() < 0.5:
        logger.error("unreliable_handler encountered simulated failure")
        raise RuntimeError("Simulated failure")
    return {"status": "ok", "message": "Sometimes it works"}
