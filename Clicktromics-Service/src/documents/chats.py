from pydantic import BaseModel, Field, field_serializer
from typing import List, Optional
from datetime import datetime, timezone
import uuid

class MessageDocument(BaseModel):
    query: str = Field(..., description="The user's query")
    response: Optional[dict] = Field(None, description="The response data (e.g., antigens and message)")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of the message")
    status: str = Field(..., description="Status of the message: success, failed, or error")
    error: Optional[str] = Field(None, description="Error message if status is failed or error")

    class Config:
        arbitrary_types_allowed = True

    @field_serializer("timestamp")
    def serialize_timestamp(self, timestamp: datetime, _info):
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")  # Custom format

class ConversationDocument(BaseModel):
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID for the conversation")
    user_email: str = Field(..., description="Email of the user who owns the conversation")
    messages: List[MessageDocument] = Field(default_factory=list, description="List of messages in the conversation")
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
