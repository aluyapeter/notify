from fastapi import FastAPI, Depends, HTTPException, status, Request
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
from .amqp_client import publisher
from .redis_client import redis_client, get_redis
import redis
from redis.exceptions import RedisError
from .config import settings
import uuid
from .database import engine, Base, get_db

RATE_LIMIT_PER_MINUTE = 20
RATE_LIMIT_WINDOW = 60

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    """
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
    await engine.dispose() 

app = FastAPI(lifespan=lifespan)


async def rate_limit_depend(request: Request, redis: redis.Redis = Depends(get_redis)):
    """
    FastAPI Dependency that implements a fixed-window rate limiter.
    """
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
    """
    Helper function to find a log by its *request_id* (UUID) and update it.
    """
    stmt = select(NotificationLog).filter(NotificationLog.request_id == request_id)
    result = await db.execute(stmt)
    log = result.scalar_one_or_none()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification ID not found: {request_id}"
        )


    log.status = new_status
    # ----------------------
    
    log.error_message = error_message  # type: ignore

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update status in database: {e}"
        )

# --- Endpoints ---

@app.get("/health", status_code=status.HTTP_200_OK, tags=["Monitoring"])
async def get_health():
    """Health check endpoint for monitoring."""
    return {"status": "ok"}


@app.post("/api/v1/notifications/",
          status_code=status.HTTP_202_ACCEPTED,
          response_model=StandardApiResponse,
          tags=["Notifications"],
          dependencies=[Depends(rate_limit_depend)])
async def send_notification(
    request: NotificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Main entry point for sending a notification.
    1. Logs the request to the database as "pending".
    2. Publishes the job to RabbitMQ.
    This is an atomic transaction. If publishing fails, the DB log is rolled back.
    """
    
    try:
        new_log = NotificationLog(
            request_id=request.request_id,
            user_id=request.user_id,
            notification_type=request.notification_type,
            status=NotificationStatus.pending
            # ----------------------
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
    """
    Public endpoint to check the status of a notification by its request_id.
    """
    result = await db.execute(
        select(NotificationLog).filter(NotificationLog.request_id == request_id)
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
            "status": log_entry.status.value, # Here we use .value to return the string "pending"
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
    """
    Internal webhook for the Email Service to report status.
    """
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
    """
    Internal webhook for the Push Service to report status.
    """
    await update_status_in_db(
        request_id=status_request.notification_id,
        new_status=status_request.status,
        db=db,
        error_message=status_request.error
    )
    return StandardApiResponse(success=True, message="Push status updated.")