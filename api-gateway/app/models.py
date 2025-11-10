import uuid
import enum
from pydantic import BaseModel, Field, HttpUrl, EmailStr
from typing import Optional, Dict, Any

from sqlalchemy import (
    Integer, Column, String, DateTime, func, Enum as SQLAlchemyEnum, ForeignKey,
    Index
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, Mapped, mapped_column

from app.database import Base



class NotificationType(str, enum.Enum):
    email = "email"
    push = "push"

class NotificationStatus(str, enum.Enum):
    delivered = "delivered"
    pending = "pending"
    failed = "failed"



class NotificationLog(Base):
    __tablename__ = "notification_logs"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    request_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), unique=True, nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    notification_type: Mapped[NotificationType] = mapped_column(
        SQLAlchemyEnum(NotificationType, name="notification_type_enum", create_type=True),
        nullable=False
    )
    status: Mapped[NotificationStatus] = mapped_column(
        SQLAlchemyEnum(NotificationStatus, name="notification_status_enum", create_type=True),
        nullable=False,
        default=NotificationStatus.pending
    )

    error_message: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('ix_notification_logs_request_id', 'request_id', unique=True),
    )



class UserData(BaseModel):
    name: str
    link: HttpUrl
    meta: Optional[Dict[str, Any]] = None

class NotificationRequest(BaseModel):
    notification_type: NotificationType
    user_id: uuid.UUID
    template_code: str
    variables: UserData
    request_id: uuid.UUID
    priority: int
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class StatusUpdateRequest(BaseModel):
    notification_id: uuid.UUID
    status: NotificationStatus
    error: Optional[str] = None

    class Config:
        from_attributes = True



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