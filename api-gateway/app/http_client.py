import httpx
from fastapi import HTTPException, status
from .config import settings
from typing import Optional

http_client: Optional[httpx.AsyncClient] = None

def set_http_client(client: httpx.AsyncClient):
    """
    Called by main.py's lifespan startup to set the global client.
    This breaks the circular import.
    """
    global http_client
    http_client = client

def get_http_client() -> httpx.AsyncClient:
    """
    A dependency function to get the client.
    """
    if http_client is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, 
            "HTTP client not initialized"
        )
    return http_client
# ---------

async def get_user_details_from_service(user_id: str, token: str) -> dict:
    """
    Fetches user details from the User Service.
    """
    client = get_http_client()
    
    url = f"{settings.USER_SERVICE_URL}/api/v1/users/{user_id}"
    headers = {"Authorization": token}
    
    try:
        response = await client.get(url, timeout=5.0, headers=headers)
        response.raise_for_status() 
        
        data = response.json()
        
        if not data.get("success") or not data.get("data"):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found or invalid response from user-service")
            
        return data["data"]
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401 or e.response.status_code == 403:
             raise HTTPException(status_code=e.response.status_code, detail="Authentication failed: Invalid token.")
        if e.response.status_code == 404:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        else:
            print(f"User service returned an error: {e.response.status_code}")
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "User service is down or faulty")
    except httpx.RequestError as e:
        print(f"Cannot connect to User Service: {e}")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "User service is unreachable")