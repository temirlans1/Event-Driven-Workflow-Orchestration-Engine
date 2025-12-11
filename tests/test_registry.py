import pytest
from orchestrator.registry import register_handler, get_handler


def test_register_and_get_handler():
    @register_handler("custom_test")
    def handler(node, eid):
        return True

    assert get_handler("custom_test") is handler


def test_get_unregistered_handler_fails():
    with pytest.raises(ValueError):
        get_handler("missing_handler")
