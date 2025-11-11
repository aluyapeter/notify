import httpx
from contextlib import asynccontextmanager
from fastapi import HTTPException, status
from .config import settings
import redis
import json

# We'll use this client to talk to other services
http_client = httpx.AsyncClient()

@asynccontextmanager
async def lifespan_http_client():
    """Manages the lifespan of the HTTP client."""
    global http_client
    http_client = httpx.AsyncClient()
    yield
    await http_client.aclose()

async def get_user_details_from_service(user_id: str) -> dict:
    """
    Fetches user details from the User Service.
    This is the "uncached" function.
    """
    url = f"{settings.USER_SERVICE_URL}/api/v1/users/{user_id}/"
    try:
        response = await http_client.get(url, timeout=5.0)
        
        # Raise an error if the User Service is down
        response.raise_for_status() 
        
        # The User Service *must* return our standard format
        data = response.json()
        if not data.get("success") or not data.get("data"):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found or invalid response")
            
        return data["data"] # Return the actual user data
        
    except httpx.HTTPStatusError as e:
        # The User Service returned 4xx or 5xx
        if e.response.status_code == 404:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        else:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "User service is down")
    except httpx.RequestError:
        # Network error, timeout, or connection refused
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "User service is unreachable")