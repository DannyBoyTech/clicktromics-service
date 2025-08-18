from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Any

from src.auth.models import (
    UserSignupRequest, UserLoginRequest, LogoutRequest, PasswordResetRequest,
    PasswordResetConfirmRequest, UserProfileUpdateRequest, AuthResponse
)
from src.auth.user_service import user_service
from src.auth.jwt_handler import jwt_handler
from src.auth.auth import get_current_user
from src.documents.profile import AuthProfile
from src.logger import Logger

log = Logger.get_logger()

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/signup", response_model=Dict[str, Any])
async def signup(user_data: UserSignupRequest):
    """Register a new user account"""
    try:
        result = await user_service.signup(user_data)
        return JSONResponse(
            content={"status": "success", "data": result},
            status_code=status.HTTP_201_CREATED
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during signup"
        )

@router.post("/login", response_model=AuthResponse)
async def login(login_data: UserLoginRequest):
    """Authenticate user and return access tokens"""
    try:
        result = await user_service.login(login_data)
        return JSONResponse(
            content={"status": "success", "data": result.model_dump()},
            status_code=status.HTTP_200_OK
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token"""
    try:
        result = await user_service.refresh_token(refresh_token)
        return JSONResponse(
            content={"status": "success", "data": result.model_dump()},
            status_code=status.HTTP_200_OK
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token refresh"
        )

@router.post("/logout")
async def logout(logout_data: LogoutRequest):
    """Logout user by revoking refresh token and optionally blacklisting access token"""
    try:
        result = await user_service.logout(logout_data.refresh_token, logout_data.access_token)
        return JSONResponse(
            content={"status": "success", "data": result},
            status_code=status.HTTP_200_OK
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout"
        )

@router.post("/password-reset")
async def request_password_reset(reset_data: PasswordResetRequest):
    """Request password reset email"""
    try:
        result = await user_service.request_password_reset(reset_data)
        return JSONResponse(
            content={"status": "success", "data": result},
            status_code=status.HTTP_200_OK
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Password reset request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during password reset request"
        )

@router.post("/password-reset/confirm")
async def confirm_password_reset(confirm_data: PasswordResetConfirmRequest):
    """Confirm password reset with token"""
    try:
        result = await user_service.confirm_password_reset(confirm_data)
        return JSONResponse(
            content={"status": "success", "data": result},
            status_code=status.HTTP_200_OK
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Password reset confirmation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during password reset confirmation"
        )

@router.get("/profile")
async def get_profile(current_user: AuthProfile = Depends(get_current_user)):
    """Get current user profile"""
    try:
        result = await user_service.get_user_profile(current_user.auth_token)
        return JSONResponse(
            content={"status": "success", "data": result},
            status_code=status.HTTP_200_OK
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Get profile error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching profile"
        )

@router.put("/profile")
async def update_profile(
    profile_data: UserProfileUpdateRequest,
    current_user: AuthProfile = Depends(get_current_user)
):
    """Update current user profile"""
    try:
        result = await user_service.update_user_profile(current_user.auth_token, profile_data)
        return JSONResponse(
            content={"status": "success", "data": result},
            status_code=status.HTTP_200_OK
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Update profile error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while updating profile"
        )

@router.get("/verify")
async def verify_token(current_user: AuthProfile = Depends(get_current_user)):
    """Verify if the current token is valid"""
    return JSONResponse(
        content={
            "status": "success", 
            "data": {
                "valid": True,
                "user": {
                    "email": current_user.email,
                    "name": current_user.name.model_dump(),
                    "auth_token": current_user.auth_token
                }
            }
        },
        status_code=status.HTTP_200_OK
    ) 