import pytest
from workers.registry import get_handler, HANDLER_REGISTRY

def test_get_handler_returns_callable():
    for handler_name in HANDLER_REGISTRY:
        fn = get_handler(handler_name)
        assert callable(fn)

def test_get_handler_raises_on_unknown():
    with pytest.raises(ValueError) as exc:
        get_handler("nonexistent")
    assert "Unknown handler" in str(exc.value)
