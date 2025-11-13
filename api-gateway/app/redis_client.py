import redis
from typing import Optional
from redis.exceptions import ConnectionError
from .config import settings

try:
    redis_pool = redis.ConnectionPool(
        host=settings.REDIS_HOST, 
        port=6379, 
        db=0, 
        decode_responses=True
    )
    
    redis_client: Optional[redis.Redis] = redis.Redis(connection_pool=redis_pool)
    
    redis_client.ping()
    print("Redis client connected successfully.")

except ConnectionError as e:
    print(f"Failed to connect to Redis: {e}")
    redis_client = None

def get_redis() -> redis.Redis:
    """
    A dependency function that provides a Redis client
    from the connection pool.
    """
    if not redis_client:
        raise Exception("Redis connection not established")
    return redis_client