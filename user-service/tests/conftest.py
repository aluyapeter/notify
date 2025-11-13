import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, str(Path(__file__).parent.parent))

pytest_plugins = ('pytest_asyncio',)

from app.routes.user import user_router
from app.database.connection import get_db
from app.services.auth import get_current_user


@pytest.fixture
def mock_db():
    """Fixture for mocking database connection"""
    return AsyncMock()


@pytest.fixture
def mock_current_user():
    """Fixture for mocking current authenticated user"""
    return {"user_id": "abc123", "email": "cipher@example.com"}


@pytest.fixture
def app(mock_db, mock_current_user):
    """Create a FastAPI test app with mocked database"""
    app = FastAPI()
    app.include_router(user_router)
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    return app


@pytest.fixture
async def async_client(app):
    """Async HTTP client for testing"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac
