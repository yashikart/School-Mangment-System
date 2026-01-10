from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models import UserRole


# Auth Schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int
    role: UserRole
    school_id: Optional[int] = None


# User Schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: UserRole
    school_id: Optional[int] = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    
    class Config:
        from_attributes = True


# Super Admin Setup Response
class SuperAdminSetupResponse(BaseModel):
    success: bool
    message: str
    already_exists: bool = False
