from fastapi import FastAPI, Depends, HTTPException, status, Request
from contextlib import asynccontextmanager
from .models import (
    NotificationRequest, 
    StatusUpdateRequest, 
    StandardApiResponse,
    NotificationType
)
from .amqp_client import publisher
from .redis_client import redis_client, get_redis
import redis
from redis.exceptions import RedisError
from .config import settings
import uuid

RATE_LIMIT_PER_MINUTE = 20
RATE_LIMIT_WINDOW = 60

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("API Gateway starting...")
    try:
        publisher.connect()
    except Exception as e:
        print(f"Failed to connect to RabbitMQ on startup: {e}")
    try:
        if get_redis().ping():
            print("Redis connection successful.")
        else:
            print("Redis connection failed.")
    except Exception as e:
        print(f"Failed to connect to Redis on startup: {e}")
    yield
    print("API Gateway shutting down...")
    publisher.close()

app = FastAPI(lifespan=lifespan)

##redis
async def rate_limit_depend(request: Request, redis: redis.Redis = Depends(get_redis)):
    """
    FastAPI Dependency that implements a fixed-window rate limiter.
    """
    if not request.client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not identify client for rate limiting."
        )
    
    # Use the client's IP address as the key
    ip = request.client.host
    key = f"rate_limit:{ip}"

    try:
        pipeline = redis.pipeline()
        pipeline.incr(key)
        pipeline.expire(key, RATE_LIMIT_WINDOW)
        
        requests_in_window = pipeline.execute()[0] 

        if requests_in_window > RATE_LIMIT_PER_MINUTE:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Limit is {RATE_LIMIT_PER_MINUTE} per minute."
            )
    except RedisError as e:
        print(f"Redis error, failing closed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error connecting to rate limiter."
        )
    
    return True

@app.get("/health", status_code=status.HTTP_200_OK)
async def get_health():
    return {"status": "ok"}

@app.post("/api/v1/notifications/", 
          status_code=status.HTTP_202_ACCEPTED, 
          response_model=StandardApiResponse,
          dependencies=[Depends(rate_limit_depend)])
async def send_notification(request: NotificationRequest):
    try:
        publisher.publish_message(request)
        
        return StandardApiResponse(
            success=True,
            message="Notification request accepted for processing.",
            data={"request_id": str(request.request_id)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish notification: {str(e)}"
        )

@app.post("/api/v1/email/status/", 
          status_code=status.HTTP_200_OK,
          response_model=StandardApiResponse)
async def email_status_update(status: StatusUpdateRequest):
    print(f"STATUS_UPDATE (Email): {status.model_dump_json()}")
    return StandardApiResponse(success=True, message="Email status received.")


@app.post("/api/v1/push/status/", 
          status_code=status.HTTP_200_OK,
          response_model=StandardApiResponse)
async def push_status_update(status: StatusUpdateRequest):
    print(f"STATUS_UPDATE (Push): {status.model_dump_json()}")
    return StandardApiResponse(success=True, message="Push status received.")