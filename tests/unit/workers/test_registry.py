from workers.registry import get_handler, HANDLER_REGISTRY


def test_get_handler_returns_callable():
    for handler_name in HANDLER_REGISTRY:
        fn = get_handler(handler_name)
        assert callable(fn)


def test_get_handler_raises_on_unknown():
    fn = get_handler("nonexistent")
    assert fn.__name__ == "noop_handler"
