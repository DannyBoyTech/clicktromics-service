from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime, timezone
import re

class UserSignupRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")
    first_name: str = Field(..., min_length=1, max_length=50, description="First name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Last name")
    nationality: Optional[str] = Field(None, max_length=100, description="User nationality")
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

class LogoutRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token to revoke")
    access_token: Optional[str] = Field(None, description="Access token to blacklist (optional)")

class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")

class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserProfileUpdateRequest(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    nationality: Optional[str] = Field(None, max_length=100)
    profile_description: Optional[str] = Field(None, max_length=500)

class AuthResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: dict = Field(..., description="User profile information")

class UserDocument(BaseModel):
    id: str = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    nationality: Optional[str] = Field(None, description="Nationality")
    profile_description: Optional[str] = Field(None, description="Profile description")
    is_verified: bool = Field(default=False, description="Email verification status")
    is_active: bool = Field(default=True, description="Account status")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")

class PasswordResetToken(BaseModel):
    token: str = Field(..., description="Reset token")
    user_id: str = Field(..., description="User ID")
    expires_at: datetime = Field(..., description="Token expiration")
    used: bool = Field(default=False, description="Whether token has been used")

class RefreshToken(BaseModel):
    token: str = Field(..., description="Refresh token")
    user_id: str = Field(..., description="User ID")
    expires_at: datetime = Field(..., description="Token expiration")
    is_revoked: bool = Field(default=False, description="Whether token is revoked") 