from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserPreference(BaseModel):
    email: bool
    push: bool


class UserRequest(BaseModel):
    name: str
    email: str
    push_token: Optional[str] = ""
    preferences: UserPreference
    password: str

class UserResponse(BaseModel):
    user_id: str
    name: str
    email: EmailStr
    push_token: str
    preferences: UserPreference
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = None
    push_token: Optional[str] = None
    preferences: Optional[UserPreference] = None
    password: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str
