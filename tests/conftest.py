import pytest
from fastapi.testclient import TestClient

from clients.redis_client import redis_client


@pytest.fixture(autouse=True)
def flush_redis():
    redis_client.flush()


@pytest.fixture(scope="function")
def client():
    from main import app
    return TestClient(app)
