from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import httpx
from src.config import AUTH_SERVICE_URL
from src.documents.profile import AuthProfile
import datetime
from src.mongo_client import Mongo
from src.logger import Logger

security = HTTPBearer()
log = Logger.get_logger()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    profiles_collection = Depends(Mongo.get_profiles_collection)
) -> AuthProfile:
    token = credentials.credentials
    
    # Check if already cached in MongoDB
    cached_profile = await profiles_collection.find_one({"_id": token})
    if cached_profile:
        log.info(f"Profile found: {cached_profile}")
        return AuthProfile(**cached_profile["profile"])
    
    # Fetch fresh data from Auth service for new token
    try:
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
            
    except httpx.RequestError:
        log.error(f"Auth service unavailable: {response.status_code} {response.content}")
        raise HTTPException(status_code=503, detail="Auth service unavailable")
    except Exception as e:
        error_message = str(e) if str(e) else "Unknown error occurred"
        log.error(f"Error get_current_user : {error_message}")
        raise HTTPException(status_code=503, detail="Error get_current_user")
