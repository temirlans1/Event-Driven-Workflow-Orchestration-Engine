import pytest
from workers.handlers import (
    noop_handler,
    call_external_service,
    llm,
    unreliable_handler,
)


def test_noop_handler_returns_ok():
    result = noop_handler({})
    assert result["status"] == "ok"


def test_call_external_service_simulates_call():
    config = {"url": "http://fake.api"}
    result = call_external_service(config)
    assert result["status"] == "ok"
    assert "Simulated call" in result["data"]


def test_llm_handler_simulates_prompt():
    config = {"prompt": "Write me a poem"}
    result = llm(config)
    assert result["status"] == "ok"
    assert "Simulated response" in result["answer"]


def test_unreliable_handler_eventually_works():
    # Run multiple times to simulate retryability
    success = False
    for _ in range(100):
        try:
            result = unreliable_handler({})
            assert result["status"] == "ok"
            success = True
            break
        except RuntimeError:
            continue
    assert success, "unreliable_handler failed too many times"
