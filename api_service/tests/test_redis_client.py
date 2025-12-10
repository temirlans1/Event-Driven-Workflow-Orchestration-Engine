import pytest
import json


def test_set_and_get_string(redis):
    redis.set("foo", "bar")
    assert redis.get("foo") == "bar"


def test_set_and_get_json(redis):
    payload = {"name": "Alice", "age": 30}
    redis.set_json("user:1", payload)
    result = redis.get_json("user:1")
    assert result == payload


def test_get_json_none(redis):
    assert redis.get_json("missing") is None


def test_get_json_invalid(redis):
    redis.set("badjson", "{not valid json")
    assert redis.get_json("badjson") is None


def test_exists(redis):
    redis.set("test:exists", "yes")
    assert redis.exists("test:exists")
    assert not redis.exists("nonexistent")


def test_xadd_and_read(redis):
    redis.xadd("stream:test", {
        "event": "task_started",
        "node": "A"
    })
    entries = redis._redis.xrange("stream:test")
    assert len(entries) == 1
    id, data = entries[0]
    assert data["event"] == "task_started"
    assert data["node"] == "A"


def test_xadd_with_dict_field(redis):
    redis.xadd("stream:dict", {"payload": {"a": 1, "b": 2}})
    id, data = redis._redis.xrange("stream:dict")[0]
    loaded = json.loads(data["payload"])
    assert loaded["a"] == 1
