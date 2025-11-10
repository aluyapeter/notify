import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI, status
from unittest.mock import MagicMock, AsyncMock
from typing import AsyncGenerator, Any

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app as fast_app
from app.database import get_db
from app.redis_client import get_redis
from app.amqp_client import publisher as global_publisher


@pytest_asyncio.fixture
async def db_session_mock():
    """Mock async database session"""
    db_mock = AsyncMock()
    db_mock.add = MagicMock()
    db_mock.commit = AsyncMock()
    db_mock.rollback = AsyncMock()
    db_mock.refresh = AsyncMock()
    db_mock.execute = AsyncMock()
    db_mock.get = AsyncMock()
    return db_mock


@pytest.fixture
def redis_client_mock():
    """Fake Redis client"""
    redis_mock = MagicMock()
    pipeline_mock = MagicMock()
    pipeline_mock.incr.return_value = pipeline_mock
    pipeline_mock.expire.return_value = pipeline_mock
    pipeline_mock.execute.return_value = [1]
    redis_mock.pipeline.return_value = pipeline_mock
    return redis_mock


@pytest.fixture
def mock_publisher(monkeypatch):
    """
    This fixture automatically mocks the global publisher
    for every test.
    """
    publisher_mock = MagicMock()
    publisher_mock.publish_message = MagicMock()
    
    monkeypatch.setattr("app.main.publisher", publisher_mock)
    return publisher_mock


@pytest_asyncio.fixture
async def async_client(db_session_mock, redis_client_mock) -> AsyncGenerator[AsyncClient, None]:
    """Create an AsyncClient for testing with dependency overrides."""
    fast_app.dependency_overrides[get_db] = lambda: db_session_mock
    fast_app.dependency_overrides[get_redis] = lambda: redis_client_mock
    
    async with AsyncClient(
        transport=ASGITransport(app=fast_app), 
        base_url="http://test"
    ) as client:
        yield client
  
    fast_app.dependency_overrides = {}


# -tests

@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    """Tests the /health endpoint."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_send_notification_happy_path(
    async_client: AsyncClient, 
    db_session_mock: AsyncMock,
    mock_publisher: MagicMock
):
    """
    Tests the POST /api/v1/notifications/ endpoint for a successful request.
    """
    payload = {
        "notification_type": "email",
        "user_id": "c4b4b4b4-b4b4-4b4b-b4b4-c4b4b4b4b4b4",
        "template_code": "welcome_email",
        "variables": {
            "name": "Peter",
            "link": "http://example.com/verify"
        },
        "request_id": "a1b1b1b1-b1b1-1b1b-b1b1-a1b1b1b1b1b1",
        "priority": 1
    }
    
    response = await async_client.post("/api/v1/notifications/", json=payload)
    
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json()["success"] == True
    assert response.json()["data"]["request_id"] == "a1b1b1b1-b1b1-1b1b-b1b1-a1b1b1b1b1b1"
    
    db_session_mock.add.assert_called_once()
    db_session_mock.commit.assert_called_once()
    
    mock_publisher.publish_message.assert_called_once()


@pytest.mark.asyncio
async def test_send_notification_validation_error(async_client: AsyncClient):
    """
    Tests that a request with an invalid payload fails validation (422).
    """
    payload = {
        "notification_type": "sms",
        "user_id": "c4b4b4b4-b4b4-4b4b-b4b4-c4b4b4b4b4b4",
        "template_code": "welcome_email",
        "variables": {
            "name": "Peter", 
            "link": "http://example.com/verify"
        },
        "request_id": "a1b1b1b1-b1b1-1b1b-b1b1-a1b1b1b1b1b1",
        "priority": 1
    }

    response = await async_client.post("/api/v1/notifications/", json=payload)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_send_notification_rate_limited(
    db_session_mock: AsyncMock,
    mock_publisher: MagicMock
):
    """
    Tests that the rate limiter returns a 429.
    We do this by re-configuring the redis_client_mock.
    """
    #redis mock that simulates rate limiting
    redis_mock = MagicMock()
    pipeline_mock = MagicMock()
    pipeline_mock.incr.return_value = pipeline_mock
    pipeline_mock.expire.return_value = pipeline_mock
    pipeline_mock.execute.return_value = [99]  # Over the limit
    redis_mock.pipeline.return_value = pipeline_mock
    
    fast_app.dependency_overrides[get_db] = lambda: db_session_mock
    fast_app.dependency_overrides[get_redis] = lambda: redis_mock

    payload = {
        "notification_type": "email",
        "user_id": "c4b4b4b4-b4b4-4b4b-b4b4-c4b4b4b4b4b4",
        "template_code": "welcome_email",
        "variables": {
            "name": "Peter", 
            "link": "http://example.com/verify"
        },
        "request_id": "a1b1b1b1-b1b1-1b1b-b1b1-a1b1b1b1b1b1",
        "priority": 1
    }

    async with AsyncClient(
        transport=ASGITransport(app=fast_app), 
        base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/notifications/", json=payload)

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "Too many requests" in response.json()["detail"]
    
    fast_app.dependency_overrides = {}