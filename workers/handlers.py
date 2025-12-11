import time
import random


def noop_handler(config):
    print("[handler] noop → does nothing")
    return {"status": "ok"}


def call_external_service(config):
    url = config.get("url", "http://example.com")
    print(f"[handler] calling external service: {url}")
    time.sleep(1)  # simulate delay
    return {"status": "ok", "data": f"Simulated call to {url}"}


def llm(config):
    prompt = config.get("prompt", "Hello, world!")
    print(f"[handler] LLM simulating prompt: {prompt}")
    return {"status": "ok", "answer": f"Simulated response for: {prompt}"}


def unreliable_handler(config):
    # Randomly fails
    if random.random() < 0.5:
        raise RuntimeError("Simulated failure")
    return {"status": "ok", "message": "Sometimes it works"}
