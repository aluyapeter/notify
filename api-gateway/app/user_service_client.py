import json
import redis
from typing import cast, Optional
from fastapi import Depends, HTTPException, status
from .redis_client import get_redis
from .http_client import get_user_details_from_service
from .models import NotificationType
from redis.exceptions import RedisError

USER_PREF_CACHE_TTL = 300 

async def get_and_cache_user_details(
    user_id: str,
    redis_client: redis.Redis = Depends(get_redis)
) -> dict:
    """
    Fetches and caches user details.
    Checks Redis cache first, falls back to user service if not found.
    """
    cache_key = f"user_pref:{user_id}"
    
    try:
        cached_data = cast(Optional[str], redis_client.get(cache_key))
        if cached_data:
            return json.loads(cached_data)
            
    except RedisError as e:
        print(f"Redis cache GET error, proceeding without cache: {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding cached JSON: {e}")

    user_data = await get_user_details_from_service(user_id)
    
    try:
        redis_client.setex(
            cache_key, 
            USER_PREF_CACHE_TTL, 
            json.dumps(user_data)
        )
    except RedisError as e:
        print(f"Redis cache SET error: {e}")

    return user_data

def check_user_preferences(
    notification_type: NotificationType, 
    user_data: dict
) -> bool:
    """
    Check if user has enabled notifications for the given type.
    Returns True if preferences not set (opt-in by default).
    """
    if not user_data.get("preferences"):
        return True
        
    prefs = user_data["preferences"]
    
    if notification_type == NotificationType.email:
        return prefs.get("email", True)
    if notification_type == NotificationType.push:
        return prefs.get("push", True)
        
    return False