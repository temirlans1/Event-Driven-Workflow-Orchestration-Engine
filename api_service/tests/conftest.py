import pytest
from fastapi.testclient import TestClient

from clients.redis_client import redis_client


@pytest.fixture
def redis(request):
    def cleanup():
        redis_client.flush()

    request.addfinalizer(cleanup)
    return redis_client


@pytest.fixture(scope="function")
def client():
    from main import app
    return TestClient(app)
