from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials 
from typing import Annotated
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import (
    NotificationRequest,
    StatusUpdateRequest,
    StandardApiResponse,
    NotificationType,
    NotificationLog,
    NotificationStatus
)
import httpx
from .user_service_client import (
    get_and_cache_user_details,
    check_user_preferences
)
from .http_client import set_http_client, get_http_client
from .amqp_client import publisher
from .redis_client import redis_client, get_redis
import redis
from redis.exceptions import RedisError
from .config import settings
import uuid
from .database import engine, Base, get_db
import asyncio

RATE_LIMIT_PER_MINUTE = 20
RATE_LIMIT_WINDOW = 60

http_bearer_scheme = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    """
    print("API Gateway starting...")

    client = httpx.AsyncClient(timeout=10.0)
    
    set_http_client(client)
    print("HTTP client initialized and injected.")

    max_retries = 5
    retry_delay = 3
    for attempt in range(max_retries):
        try:
            print(f"Attempting to connect to RabbitMQ (attempt {attempt + 1}/{max_retries})...")
            publisher.connect()
            print("RabbitMQ connection successful")
            break
        except Exception as e:
            print(f"Failed to connect to RabbitMQ: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                print("WARNING: Starting without RabbitMQ connection. Messages will fail to publish.")

    try:
        if get_redis().ping():
            print("Redis connection successful.")
        else:
            print("Redis connection failed.")
    except Exception as e:
        print(f"Failed to connect to Redis on startup: {e}")

    yield
    
    print("API Gateway shutting down...")
    
    await client.aclose()
    print("HTTP client closed")
    
    publisher.close()
    
    await engine.dispose()

app = FastAPI(lifespan=lifespan)


async def rate_limit_depend(request: Request, redis: redis.Redis = Depends(get_redis)):
    if not request.client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not identify client for rate limiting."
        )
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

async def update_status_in_db(
    request_id: uuid.UUID, 
    new_status: NotificationStatus, 
    db: AsyncSession, 
    error_message: str | None = None
):
    stmt = select(NotificationLog).filter(NotificationLog.request_id == request_id)
    result = await db.execute(stmt)
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification ID not found: {request_id}"
        )
    log.status = new_status
    log.error_message = error_message 
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update status in database: {e}"
        )


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Monitoring"])
async def get_health():
    return {"status": "ok"}


@app.post("/api/v1/notifications/",
          status_code=status.HTTP_202_ACCEPTED,
          response_model=StandardApiResponse,
          tags=["Notifications"],
          dependencies=[Depends(rate_limit_depend)])
async def send_notification(
    request: NotificationRequest,
    creds: Annotated[HTTPAuthorizationCredentials, Depends(http_bearer_scheme)],
    
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    try:
        token = creds.credentials
        
        user_data = await get_and_cache_user_details(
            str(request.user_id), 
            redis_client,
            f"Bearer {token}"
        ) 
        
        if not check_user_preferences(request.notification_type, user_data):
            return StandardApiResponse(
                success=True,
                message="Notification suppressed by user preferences.",
                data={"request_id": str(request.request_id)}
            )
            
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"User validation failed: {e}")
    
    try:
        new_log = NotificationLog(
            request_id=request.request_id,
            user_id=request.user_id,
            notification_type=request.notification_type,
            status=NotificationStatus.pending
        )
        db.add(new_log)
        await db.flush() 

        publisher.publish_message(request)
        
        await db.commit()

        return StandardApiResponse(
            success=True,
            message="Notification request accepted for processing.",
            data={"request_id": str(request.request_id)}
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process notification: {str(e)}"
        )


@app.get("/api/v1/notifications/{request_id}/status/",
         response_model=StandardApiResponse,
         status_code=status.HTTP_200_OK,
         tags=["Notifications"])
async def get_notification_status(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(NotificationLog).filter(NotificationLog.request_id == request_id) # type: ignore
    )
    log_entry = result.scalar_one_or_none()

    if not log_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification status not found for this request_id."
        )

    return StandardApiResponse(
        success=True,
        message="Status retrieved successfully.",
        data={
            "request_id": str(log_entry.request_id),
            "status": log_entry.status.value,
            "last_updated": str(log_entry.updated_at or log_entry.created_at),
            "error": log_entry.error_message
        }
    )


@app.post("/api/v1/email/status/",
          status_code=status.HTTP_200_OK,
          response_model=StandardApiResponse,
          tags=["Status Webhooks"])
async def email_status_update(
    status_request: StatusUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    await update_status_in_db(
        request_id=status_request.notification_id,
        new_status=status_request.status,
        db=db,
        error_message=status_request.error
    )
    return StandardApiResponse(success=True, message="Email status updated.")


@app.post("/api/v1/push/status/",
          status_code=status.HTTP_200_OK,
          response_model=StandardApiResponse,
          tags=["Status Webhooks"])
async def push_status_update(
    status_request: StatusUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    await update_status_in_db(
        request_id=status_request.notification_id,
        new_status=status_request.status,
        db=db,
        error_message=status_request.error
    )
    return StandardApiResponse(success=True, message="Push status updated.")
