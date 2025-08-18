import bcrypt
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from bson import ObjectId
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

from src.mongo_client import Mongo
from src.auth.models import (
    UserSignupRequest, UserLoginRequest, PasswordResetRequest,
    PasswordResetConfirmRequest, UserProfileUpdateRequest,
    UserDocument, PasswordResetToken, RefreshToken, AuthResponse
)
from src.auth.jwt_handler import jwt_handler
from src.logger import Logger

log = Logger.get_logger()

class UserService:
    def __init__(self):
        self.users_collection = None
        self.password_reset_collection = None
        self.refresh_tokens_collection = None
    
    async def _get_collections(self):
        """Get MongoDB collections"""
        if self.users_collection is None:
            self.users_collection = Mongo.get_users_collection()
        if self.password_reset_collection is None:
            self.password_reset_collection = Mongo.get_password_reset_collection()
        if self.refresh_tokens_collection is None:
            self.refresh_tokens_collection = Mongo.get_refresh_tokens_collection()
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    async def _send_email(self, to_email: str, subject: str, body: str):
        """Send email (placeholder - implement with your email service)"""
        # This is a placeholder. In production, use a proper email service
        # like SendGrid, AWS SES, or configure SMTP
        log.info(f"Email would be sent to {to_email}: {subject}")
        log.info(f"Email body: {body}")
        
        # Example SMTP implementation (uncomment and configure):
        """
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        """
    
    async def signup(self, user_data: UserSignupRequest) -> Dict[str, Any]:
        """Register a new user"""
        await self._get_collections()
        
        # Check if user already exists
        existing_user = await self.users_collection.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create user document
        user_id = str(ObjectId())
        hashed_password = self._hash_password(user_data.password)
        
        user_doc = UserDocument(
            id=user_id,
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            nationality=user_data.nationality,
            is_verified=False,
            is_active=True
        )
        
        # Insert user into database
        await self.users_collection.insert_one({
            "_id": user_id,
            "email": user_data.email,
            "password_hash": hashed_password,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "nationality": user_data.nationality,
            "is_verified": False,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })
        
        # Send verification email
        verification_token = jwt_handler.generate_password_reset_token()
        await self._send_verification_email(user_data.email, verification_token)
        
        log.info(f"User registered successfully: {user_data.email}")
        
        return {
            "message": "User registered successfully. Please check your email for verification.",
            "user_id": user_id
        }
    
    async def login(self, login_data: UserLoginRequest) -> AuthResponse:
        """Authenticate user and return tokens"""
        await self._get_collections()
        
        # Find user by email
        user = await self.users_collection.find_one({"email": login_data.email})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not self._verify_password(login_data.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        # Update last login
        await self.users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.now(timezone.utc)}}
        )
        
        # Generate tokens
        token_data = {
            "sub": user["_id"],
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"]
        }
        
        access_token = jwt_handler.create_access_token(token_data)
        refresh_token = jwt_handler.create_refresh_token(token_data)
        
        # Store refresh token
        await self.refresh_tokens_collection.insert_one({
            "token": refresh_token,
            "user_id": user["_id"],
            "expires_at": jwt_handler.get_token_expiration("refresh"),
            "is_revoked": False,
            "created_at": datetime.now(timezone.utc)
        })
        
        # Prepare user info
        user_info = {
            "id": user["_id"],
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "nationality": user.get("nationality"),
            "profile_description": user.get("profile_description"),
            "is_verified": user.get("is_verified", False)
        }
        
        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=jwt_handler.access_token_expire_minutes * 60,
            user=user_info
        )
    
    async def refresh_token(self, refresh_token: str) -> AuthResponse:
        """Refresh access token using refresh token"""
        await self._get_collections()
        
        # Verify refresh token
        try:
            payload = jwt_handler.verify_token(refresh_token, "refresh")
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Check if refresh token is revoked
        token_doc = await self.refresh_tokens_collection.find_one({
            "token": refresh_token,
            "is_revoked": False
        })
        
        if not token_doc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is revoked"
            )
        
        # Get user
        user = await self.users_collection.find_one({"_id": payload["sub"]})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Generate new tokens
        token_data = {
            "sub": user["_id"],
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"]
        }
        
        new_access_token = jwt_handler.create_access_token(token_data)
        new_refresh_token = jwt_handler.create_refresh_token(token_data)
        
        # Revoke old refresh token
        await self.refresh_tokens_collection.update_one(
            {"token": refresh_token},
            {"$set": {"is_revoked": True}}
        )
        
        # Store new refresh token
        await self.refresh_tokens_collection.insert_one({
            "token": new_refresh_token,
            "user_id": user["_id"],
            "expires_at": jwt_handler.get_token_expiration("refresh"),
            "is_revoked": False,
            "created_at": datetime.now(timezone.utc)
        })
        
        user_info = {
            "id": user["_id"],
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "nationality": user.get("nationality"),
            "profile_description": user.get("profile_description"),
            "is_verified": user.get("is_verified", False)
        }
        
        return AuthResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=jwt_handler.access_token_expire_minutes * 60,
            user=user_info
        )
    
    async def request_password_reset(self, reset_data: PasswordResetRequest) -> Dict[str, str]:
        """Request password reset"""
        await self._get_collections()
        
        # Find user
        user = await self.users_collection.find_one({"email": reset_data.email})
        if not user:
            # Don't reveal if user exists or not
            return {"message": "If the email exists, a password reset link has been sent"}
        
        # Generate reset token
        reset_token = jwt_handler.generate_password_reset_token()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Store reset token
        await self.password_reset_collection.insert_one({
            "token": reset_token,
            "user_id": user["_id"],
            "expires_at": expires_at,
            "used": False,
            "created_at": datetime.now(timezone.utc)
        })
        
        # Send reset email
        reset_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"
        email_body = f"""
        <h2>Password Reset Request</h2>
        <p>You requested a password reset for your account.</p>
        <p>Click the link below to reset your password:</p>
        <a href="{reset_url}">Reset Password</a>
        <p>This link will expire in 1 hour.</p>
        <p>If you didn't request this, please ignore this email.</p>
        """
        
        await self._send_email(reset_data.email, "Password Reset Request", email_body)
        
        return {"message": "If the email exists, a password reset link has been sent"}
    
    async def confirm_password_reset(self, confirm_data: PasswordResetConfirmRequest) -> Dict[str, str]:
        """Confirm password reset with token"""
        await self._get_collections()
        
        # Find reset token
        reset_doc = await self.password_reset_collection.find_one({
            "token": confirm_data.token,
            "used": False,
            "expires_at": {"$gt": datetime.now(timezone.utc)}
        })
        
        if not reset_doc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Update password
        hashed_password = self._hash_password(confirm_data.new_password)
        await self.users_collection.update_one(
            {"_id": reset_doc["user_id"]},
            {"$set": {"password_hash": hashed_password, "updated_at": datetime.now(timezone.utc)}}
        )
        
        # Mark token as used
        await self.password_reset_collection.update_one(
            {"_id": reset_doc["_id"]},
            {"$set": {"used": True}}
        )
        
        # Revoke all refresh tokens for this user
        await self.refresh_tokens_collection.update_many(
            {"user_id": reset_doc["user_id"]},
            {"$set": {"is_revoked": True}}
        )
        
        return {"message": "Password reset successfully"}
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile"""
        await self._get_collections()
        
        user = await self.users_collection.find_one({"_id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Convert datetime objects to ISO format strings for JSON serialization
        def format_datetime(dt):
            if dt is None:
                return None
            if isinstance(dt, datetime):
                return dt.isoformat()
            return dt
        
        return {
            "id": user["_id"],
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "nationality": user.get("nationality"),
            "profile_description": user.get("profile_description"),
            "is_verified": user.get("is_verified", False),
            "created_at": format_datetime(user["created_at"]),
            "updated_at": format_datetime(user["updated_at"]),
            "last_login": format_datetime(user.get("last_login"))
        }
    
    async def update_user_profile(self, user_id: str, profile_data: UserProfileUpdateRequest) -> Dict[str, Any]:
        """Update user profile"""
        await self._get_collections()
        
        update_data = {}
        if profile_data.first_name is not None:
            update_data["first_name"] = profile_data.first_name
        if profile_data.last_name is not None:
            update_data["last_name"] = profile_data.last_name
        if profile_data.nationality is not None:
            update_data["nationality"] = profile_data.nationality
        if profile_data.profile_description is not None:
            update_data["profile_description"] = profile_data.profile_description
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        result = await self.users_collection.update_one(
            {"_id": user_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return await self.get_user_profile(user_id)
    
    async def logout(self, refresh_token: str, access_token: str = None) -> Dict[str, str]:
        """Logout user by revoking refresh token and optionally blacklisting access token"""
        await self._get_collections()
        
        # Verify refresh token exists and is not already revoked
        refresh_token_doc = await self.refresh_tokens_collection.find_one({
            "token": refresh_token,
            "is_revoked": False
        })
        
        if not refresh_token_doc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or already revoked refresh token"
            )
        
        # Verify access token if provided
        if access_token:
            try:
                # Decode the access token to get expiration
                payload = jwt_handler.verify_token(access_token, "access")
                expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
                
                # Check if access token is already blacklisted
                existing_blacklist = await self.refresh_tokens_collection.find_one({
                    "token": access_token,
                    "is_blacklisted": True
                })
                
                if existing_blacklist:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Access token is already blacklisted"
                    )
                
                # Store in blacklist collection
                await self.refresh_tokens_collection.insert_one({
                    "token": access_token,
                    "user_id": payload["sub"],
                    "expires_at": expires_at,
                    "is_revoked": True,
                    "is_blacklisted": True,
                    "created_at": datetime.now(timezone.utc)
                })
                
                log.info(f"Access token blacklisted for user: {payload['sub']}")
                
            except HTTPException:
                raise
            except Exception as e:
                log.error(f"Could not blacklist access token: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid access token"
                )
        
        # Revoke refresh token
        await self.refresh_tokens_collection.update_one(
            {"token": refresh_token},
            {"$set": {"is_revoked": True}}
        )
        
        log.info(f"Refresh token revoked and logout successful for user: {refresh_token_doc['user_id']}")
        return {"message": "Logged out successfully"}
    
    async def _send_verification_email(self, email: str, token: str):
        """Send email verification"""
        verification_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/verify-email?token={token}"
        email_body = f"""
        <h2>Email Verification</h2>
        <p>Please verify your email address by clicking the link below:</p>
        <a href="{verification_url}">Verify Email</a>
        <p>If you didn't create an account, please ignore this email.</p>
        """
        
        await self._send_email(email, "Email Verification", email_body)

# Global instance
user_service = UserService() 