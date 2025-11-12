import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI, status
from unittest.mock import AsyncMock, patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.routes.user import user_router


mock_user = {
    "user_id": "abc123",
    "name": "Cipher",
    "email": "cipher@example.com",
    "push_token": "token123",
    "preferences": {"email": True, "push": False},
    "password": "$2b$12$hashhere",
    "created_at": "2025-11-11T12:00:00"
}


@pytest.mark.asyncio
@patch("app.routes.user.get_user", new_callable=AsyncMock)
@patch("app.routes.user.create_user", new_callable=AsyncMock)
async def test_create_user_success(mock_create_user, mock_get_user, async_client):
    mock_get_user.return_value = None
    mock_create_user.return_value = mock_user

    response = await async_client.post("/users/", json={
        "name": "Cipher",
        "email": "cipher@example.com",
        "password": "secret123",
        "push_token": "token123",
        "preferences": {"email": True, "push": False}
    })

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "cipher@example.com"



@pytest.mark.asyncio
@patch("app.routes.user.get_user", new_callable=AsyncMock)
@patch("app.routes.user.generate_token", return_value="fake_jwt_token")
@patch("bcrypt.checkpw", return_value=True)
async def test_login_success(mock_checkpw, mock_token, mock_get_user, async_client):
    mock_get_user.return_value = mock_user

    response = await async_client.post("/users/login", json={
        "email": "cipher@example.com",
        "password": "secret123"
    })

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert data["data"]["access_token"] == "fake_jwt_token"


@pytest.mark.asyncio
@patch("app.routes.user.get_user", new_callable=AsyncMock)
@patch("app.routes.user.get_current_user", return_value={"user_id": "abc123"})
async def test_get_user_success(mock_current_user, mock_get_user, async_client):
    mock_get_user.return_value = mock_user

    response = await async_client.get("/users/abc123")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert data["data"]["user_id"] == "abc123"


@pytest.mark.asyncio
@patch("app.routes.user.update_user", new_callable=AsyncMock)
@patch("app.routes.user.get_current_user", return_value={"user_id": "abc123"})
async def test_update_user_success(mock_current_user, mock_update_user, async_client):
    updated_user = mock_user.copy()
    updated_user["name"] = "Cipher Updated"
    mock_update_user.return_value = updated_user

    response = await async_client.put("/users/abc123", json={
        "name": "Cipher Updated",
        "preferences": {"email": False, "push": True}
    })

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Cipher Updated"
