from fastapi import FastAPI, Depends, HTTPException, status
from contextlib import asynccontextmanager
from .models import (
    NotificationRequest, 
    StatusUpdateRequest, 
    StandardApiResponse,
    NotificationType
)
from .amqp_client import publisher
from .config import settings
import uuid

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("API Gateway starting...")
    try:
        publisher.connect()
    except Exception as e:
        print(f"Failed to connect to RabbitMQ on startup: {e}")
    yield
    print("API Gateway shutting down...")
    publisher.close()

app = FastAPI(lifespan=lifespan)


@app.get("/health", status_code=status.HTTP_200_OK)
async def get_health():
    return {"status": "ok"}

@app.post("/api/v1/notifications/", 
          status_code=status.HTTP_202_ACCEPTED, 
          response_model=StandardApiResponse)
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