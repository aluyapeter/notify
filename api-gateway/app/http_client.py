import httpx
from fastapi import HTTPException, status
from .config import settings

async def get_user_details_from_service(user_id: str) -> dict:
    """
    Fetches user details from the User Service using the global http_client.
    
    TODO: Remove mock data when user-service is ready.
    """
    # TEMPORARY MOCK DATA FOR TESTING
    # Remove this when user-service is deployed and ready
    return {
        "id": user_id,
        "email": "test@example.com",
        "preferences": {
            "email": True,
            "push": True
        }
    }
    
    # Uncomment below when user-service is ready
    """
    from .main import http_client
    
    if http_client is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, 
            "HTTP client not initialized"
        )
    
    url = f"{settings.USER_SERVICE_URL}/api/v1/users/{user_id}/"
    
    try:
        response = await http_client.get(url, timeout=5.0)
        response.raise_for_status() 
        
        data = response.json()
        
        if not data.get("success") or not data.get("data"):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found or invalid response")
            
        return data["data"]
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        else:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "User service is down")
    except httpx.RequestError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "User service is unreachable")
    """