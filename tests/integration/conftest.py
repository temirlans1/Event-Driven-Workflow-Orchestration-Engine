import pytest
from fastapi.testclient import TestClient

from clients.redis_client import redis_client


@pytest.fixture(scope="session")
def client():
    from main import app

    return TestClient(app)


@pytest.fixture(autouse=True)
def flush_redis():
    redis_client.flush()
