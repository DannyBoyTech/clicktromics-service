from fastapi import Depends, HTTPException, status
from typing import Optional
from src.auth.auth import get_current_user
from src.documents.profile import AuthProfile

def require_auth() -> AuthProfile:
    """Dependency for endpoints that require authentication"""
    return Depends(get_current_user)

def optional_auth() -> Optional[AuthProfile]:
    """Dependency for endpoints that can work with or without authentication"""
    async def _optional_auth(current_user: Optional[AuthProfile] = Depends(get_current_user)):
        return current_user
    return Depends(_optional_auth)

def require_user_context() -> AuthProfile:
    """Dependency for endpoints that require user context (like job management)"""
    async def _require_user_context(current_user: AuthProfile = Depends(get_current_user)):
        if not current_user or not current_user.auth_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User context required for this operation"
            )
        return current_user
    return Depends(_require_user_context)
