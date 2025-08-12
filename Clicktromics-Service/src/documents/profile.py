from pydantic import BaseModel, EmailStr, Field, field_serializer
from datetime import datetime, timezone

class Name(BaseModel):
    first: str = Field(..., example="John")
    last: str = Field(..., example="Doe")

class AuthProfile(BaseModel):
    email: EmailStr = Field(..., description="The user email")
    name: Name = Field(..., description="The user ful name")
    auth_token: str = Field("", description="The user auth_token")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")

    class Config:
        arbitrary_types_allowed = True

    @field_serializer("created_at")
    def serialize_created_at(self, timestamp: datetime, _info):
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")  # Custom format for created_at
    
    @field_serializer("updated_at")
    def serialize_updated_at(self, timestamp: datetime, _info):
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")  # Custom format for updated_at
