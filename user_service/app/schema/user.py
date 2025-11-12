from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class UserPreference(BaseModel):
    email: bool
    push: bool


class UserRequest(BaseModel):
    name: str
    email: EmailStr
    push_token: Optional[str] = ""
    preferences: UserPreference
    password: str

class UserResponse(BaseModel):
    user_id: str
    name: str
    email: str
    push_token: str
    preferences: UserPreference
    access_token: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(
        json_schema_extra={"exclude_none": True}
    )


class GenericResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None
    meta: Optional[dict] = None

    model_config = ConfigDict(
        json_schema_extra={"exclude_none": True}
    )


class UserUpdate(BaseModel):
    name: Optional[str] = None
    push_token: Optional[str] = None
    preferences: Optional[UserPreference] = None
    password: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str
