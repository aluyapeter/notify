from pydantic import BaseModel, HttpUrl, UUID4
from typing import Optional, Dict, Any
from enum import Enum


class NotificationType(str, Enum):
    email = "email"
    push = "push"

class NotificationStatus(str, Enum):
    delivered = "delivered"
    pending = "pending"
    failed = "failed"


class UserData(BaseModel):
    name: str
    link: HttpUrl
    meta: Optional[Dict[str, Any]] = None

class NotificationRequest(BaseModel):
    notification_type: NotificationType
    user_id: UUID4
    template_code: str
    variables: UserData
    request_id: UUID4 
    priority: int
    metadata: Optional[Dict[str, Any]] = None

class StatusUpdateRequest(BaseModel):
    notification_id: str
    status: NotificationStatus
    timestamp: Optional[str] = None
    error: Optional[str] = None


class PaginationMeta(BaseModel):
    total: int
    limit: int
    page: int
    total_pages: int
    has_next: bool
    has_previous: bool

class StandardApiResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Dict[str, Any] | list] = None
    error: Optional[str] = None
    meta: Optional[PaginationMeta] = None