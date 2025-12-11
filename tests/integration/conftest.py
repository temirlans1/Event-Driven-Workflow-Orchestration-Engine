import pytest
from redis.exceptions import ConnectionError

from clients.redis_client import redis_client


@pytest.fixture(autouse=True)
def flush_redis():
    try:
        redis_client.flush()
    except ConnectionError as exc:
        pytest.skip(f"Redis is not available: {exc}")
