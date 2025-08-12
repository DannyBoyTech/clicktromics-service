from motor.motor_asyncio import AsyncIOMotorCollection
from src.mongo_client import Mongo
from datetime import datetime, timezone
from src.documents.chats import MessageDocument, ConversationDocument
from typing import List, Optional

class ConversationRepo:
    _collection: AsyncIOMotorCollection = None

    def __init__(self):
        self._collection = Mongo.get_conversations_collection()

    async def save(self,conversation) -> None:
        """Save or update the conversation in MongoDB."""
        existing_conversation = await self._collection.find_one({"conversation_id": conversation.conversation_id})
        if existing_conversation:
            # Update existing conversation
            await self._collection.update_one(
                {"conversation_id": conversation.conversation_id},
                {
                    "$set": {
                        "messages": [msg.model_dump() for msg in conversation.messages],
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
        else:
            # Insert new conversation
            await self._collection.insert_one(conversation.dict())

    async def append_message(self, conversation: ConversationDocument, message: MessageDocument) -> None:
        """Append a new message to the conversation and save it."""
        conversation.messages.append(message)
        await self.save(conversation)

    async def from_conversation_id(self, conversation_id: str, user_email: str) -> Optional['ConversationDocument']:
        """Fetch a conversation from MongoDB by conversation_id and return a ConversationDocument instance."""
        conversation_data = await self._collection.find_one({"conversation_id": conversation_id, "user_email":user_email})
        if conversation_data:
            messages = [MessageDocument(**msg) for msg in conversation_data.get("messages", [])]
            return ConversationDocument(
                conversation_id=conversation_data["conversation_id"],
                user_email=conversation_data["user_email"],
                messages=messages,
                created_at=conversation_data["created_at"],
                updated_at=conversation_data["updated_at"]
            )
        return None

    async def get_conversations_by_email(self, user_email: str) -> List['ConversationDocument']:
        """Retrieve all conversations for a given user_email, sorted by updated_at descending."""
        cursor = self._collection.find({"user_email": user_email}).sort("updated_at", -1)
        conversations = []
        async for conversation_data in cursor:
            messages = [MessageDocument(**msg) for msg in conversation_data.get("messages", [])]
            conversations.append(ConversationDocument(
                conversation_id=conversation_data["conversation_id"],
                user_email=conversation_data["user_email"],
                messages=messages,
                created_at=conversation_data["created_at"],
                updated_at=conversation_data["updated_at"]
            ))
        return conversations

    async def get_newest_conversation_by_email(self, user_email: str) -> Optional['ConversationDocument']:
        """Retrieve the most recent conversation for a given user_email based on updated_at."""
        conversation_data = await self._collection.find_one(
            {"user_email": user_email},
            sort=[("updated_at", -1)]  # -1 for descending order (newest first)
        )
        if conversation_data:
            messages = [MessageDocument(**msg) for msg in conversation_data.get("messages", [])]
            return ConversationDocument(
                conversation_id=conversation_data["conversation_id"],
                user_email=conversation_data["user_email"],
                messages=messages,
                created_at=conversation_data["created_at"],
                updated_at=conversation_data["updated_at"]
            )
        return None