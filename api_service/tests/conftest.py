import pytest
from fastapi.testclient import TestClient
from core.main import app
import redis


@pytest.fixture(scope="function")
def client():
    return TestClient(app)


@pytest.fixture(scope="function")
def redis_client():
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    r.flushall()  # Clear Redis between test runs
    return r
