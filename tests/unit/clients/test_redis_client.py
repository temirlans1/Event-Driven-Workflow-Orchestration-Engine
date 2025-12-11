import json

from clients.redis_client import redis_client

def test_set_and_get_string():
    redis_client.set("foo", "bar")
    assert redis_client.get("foo") == "bar"


def test_set_and_get_json():
    payload = {"name": "Alice", "age": 30}
    redis_client.set_json("user:1", payload)
    result = redis_client.get_json("user:1")
    assert result == payload


def test_get_json_none():
    assert redis_client.get_json("missing") is None


def test_get_json_invalid():
    redis_client.set("badjson", "{not valid json")
    assert redis_client.get_json("badjson") is None


def test_exists():
    redis_client.set("test:exists", "yes")
    assert redis_client.exists("test:exists")
    assert not redis_client.exists("nonexistent")


def test_xadd_and_read():
    redis_client.xadd("stream:test", {
        "event": "task_started",
        "node": "A"
    })
    entries = redis_client._redis.xrange("stream:test")
    assert len(entries) == 1
    id, data = entries[0]
    assert data["event"] == "task_started"
    assert data["node"] == "A"


def test_xadd_with_dict_field():
    redis_client.xadd("stream:dict", {"payload": {"a": 1, "b": 2}})
    id, data = redis_client._redis.xrange("stream:dict")[0]
    loaded = json.loads(data["payload"])
    assert loaded["a"] == 1
