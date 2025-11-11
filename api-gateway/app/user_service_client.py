import json
import redis
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
    cache_key = f"user_pref:{user_id}"
    try:
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data.decode('utf-8'))
            
    except RedisError as e:
        print(f"Redis cache GET error, proceeding without cache: {e}")

    user_data = await get_user_details_from_service(user_id)
    
    try:
        await redis_client.setex(
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
    if not user_data.get("preferences"):
        # Default to "allow" if preferences aren't set
        return True
        
    prefs = user_data["preferences"]
    
    if notification_type == NotificationType.email:
        return prefs.get("email", True)
    if notification_type == NotificationType.push:
        return prefs.get("push", True)
        
    return False