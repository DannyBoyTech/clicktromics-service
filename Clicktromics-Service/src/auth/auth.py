from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from src.documents.profile import AuthProfile, Name
from datetime import datetime
from src.mongo_client import Mongo
from src.logger import Logger
from src.auth.jwt_handler import jwt_handler
from src.auth.user_service import user_service

security = HTTPBearer()
log = Logger.get_logger()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    profiles_collection = Depends(Mongo.get_profiles_collection)
) -> AuthProfile:
    token = credentials.credentials
    
    try:
        # Verify JWT token
        payload = jwt_handler.verify_token(token, "access")
        
        # Check if token is blacklisted
        blacklisted_token = await Mongo.get_refresh_tokens_collection().find_one({
            "token": token,
            "is_blacklisted": True
        })
        if blacklisted_token:
            log.info(f"Access token is blacklisted: {token[:20]}...")
            raise HTTPException(status_code=401, detail="Token has been revoked")
        
        # Check if already cached in MongoDB
        cached_profile = await profiles_collection.find_one({"_id": token})
        if cached_profile:
            log.info(f"Profile found in cache: {cached_profile}")
            return AuthProfile(**cached_profile["profile"])
        
        # Get fresh user data from database
        user = await user_service.get_user_profile(payload["sub"])
        
        # Create AuthProfile object
        profile = AuthProfile(
            email=user["email"],
            name=Name(first=user["first_name"], last=user["last_name"]),
            auth_token=payload["sub"],  # Use user ID as auth token
            created_at=user["created_at"] if isinstance(user["created_at"], datetime) else datetime.fromisoformat(user["created_at"]),
            updated_at=user["updated_at"] if isinstance(user["updated_at"], datetime) else datetime.fromisoformat(user["updated_at"])
        )
        
        # Cache the profile with token as the key
        await profiles_collection.update_one(
            {"_id": token},
            {"$set": {"profile": profile.model_dump(), "created_at": datetime.now()}},
            upsert=True
        )
        
        return profile
        
    except HTTPException:
        # If JWT verification fails, try external auth service as fallback
        log.info("JWT verification failed, trying external auth service")
        try:
            from src.config import AUTH_SERVICE_URL
            import httpx
            
            async with httpx.AsyncClient() as client:
                log.info(f"Sending request to : {AUTH_SERVICE_URL}/auth/profile")
                response = await client.get(
                    f"{AUTH_SERVICE_URL}/auth/profile",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if response.status_code != 200:
                    log.error(f"Auth service error: {response.status_code} {response.content}")
                    raise HTTPException(status_code=response.status_code)
                
                profile_data = response.json().get("profile", {})
                profile = AuthProfile(**profile_data)
                
                # Cache the profile with token as the key
                await profiles_collection.update_one(
                    {"_id": token},
                    {"$set": {"profile": profile.model_dump(), "created_at": datetime.now()}},
                    upsert=True
                )
                return profile
                
        except Exception as e:
            error_message = str(e) if str(e) else "Unknown error occurred"
            log.error(f"Error get_current_user : {error_message}")
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    except Exception as e:
        error_message = str(e) if str(e) else "Unknown error occurred"
        log.error(f"Error get_current_user : {error_message}")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
