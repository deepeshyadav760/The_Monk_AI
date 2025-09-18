# services/chat_service.py

from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from models.database import ChatSession, ChatMessage
from database.connection import get_database
import logging

logger = logging.getLogger(__name__)

class ChatService:
    """Service for handling chat session business logic."""

    async def create_chat_session(self, user_id: str, title: str = "New Chat") -> ChatSession:
        """
        Creates a new chat session for a user.
        The title is generated from the first user message.
        """
        db = get_database()
        try:
            session_data = {
                "user_id": ObjectId(user_id),
                "title": title,
                "messages": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True
            }
            result = await db.chat_sessions.insert_one(session_data)
            created_session = await db.chat_sessions.find_one({"_id": result.inserted_id})
            return ChatSession(**created_session)
        except Exception as e:
            logger.error(f"Error creating chat session for user {user_id}: {e}")
            raise

    async def get_chat_session(self, session_id: str, user_id: str) -> Optional[ChatSession]:
        """Retrieves a specific chat session by its ID, ensuring it belongs to the user."""
        db = get_database()
        try:
            session_data = await db.chat_sessions.find_one({
                "_id": ObjectId(session_id), 
                "user_id": ObjectId(user_id),
                "is_active": True
            })
            return ChatSession(**session_data) if session_data else None
        except Exception as e:
            logger.error(f"Error retrieving chat session {session_id} for user {user_id}: {e}")
            return None

    async def get_user_chat_sessions(self, user_id: str, limit: int = 50) -> List[ChatSession]:
        """Retrieves all active chat sessions for a specific user, sorted by most recent."""
        db = get_database()
        try:
            cursor = db.chat_sessions.find({
                "user_id": ObjectId(user_id), 
                "is_active": True
            }).sort("updated_at", -1).limit(limit)
            sessions = [ChatSession(**session_data) async for session_data in cursor]
            return sessions
        except Exception as e:
            logger.error(f"Error retrieving chat sessions for user {user_id}: {e}")
            return []

    async def add_message_to_session(self, session_id: str, user_id: str, message: ChatMessage) -> bool:
        """Adds a new message to an existing chat session and updates the timestamp."""
        db = get_database()
        try:
            result = await db.chat_sessions.update_one(
                {"_id": ObjectId(session_id), "user_id": ObjectId(user_id)},
                {
                    "$push": {"messages": message.model_dump()},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error adding message to session {session_id}: {e}")
            return False

    async def update_session_title(self, session_id: str, user_id: str, title: str) -> bool:
        """Updates the title of a specific chat session."""
        db = get_database()
        try:
            result = await db.chat_sessions.update_one(
                {"_id": ObjectId(session_id), "user_id": ObjectId(user_id)},
                {"$set": {"title": title, "updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating title for session {session_id}: {e}")
            return False

    async def delete_chat_session(self, session_id: str, user_id: str) -> bool:
        """
        Performs a soft delete on a chat session by setting its 'is_active' flag to False.
        This preserves the chat history while hiding it from the user's active view.
        """
        db = get_database()
        try:
            result = await db.chat_sessions.update_one(
                {"_id": ObjectId(session_id), "user_id": ObjectId(user_id)},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False

    def generate_session_title(self, first_message: str) -> str:
        """Generates a concise title for a new chat session from the user's first message."""
        title = first_message.strip()
        if len(title) > 50:
            title = title[:50].rsplit(' ', 1)[0] + "..."
        
        # Clean up newlines and extra spaces
        title = ' '.join(title.replace('\n', ' ').split())
        
        return title if title else "New Chat"

    async def search_chat_history(self, user_id: str, search_term: str, limit: int = 10) -> List[dict]:
        """
        Searches through a user's entire chat history for a specific term.
        Uses a MongoDB aggregation pipeline for efficient searching within message arrays.
        """
        db = get_database()
        try:
            pipeline = [
                {"$match": {"user_id": ObjectId(user_id), "is_active": True}},
                {"$unwind": "$messages"},
                {"$match": {"messages.content": {"$regex": search_term, "$options": "i"}}},
                {"$sort": {"messages.timestamp": -1}},
                {"$limit": limit},
                {"$project": {
                    "session_id": "$_id",
                    "session_title": "$title",
                    "message_content": "$messages.content",
                    "message_role": "$messages.role",
                    "timestamp": "$messages.timestamp"
                }}
            ]
            
            results = []
            async for result in db.chat_sessions.aggregate(pipeline):
                # Convert ObjectId to string for JSON serialization
                result["session_id"] = str(result["session_id"])
                results.append(result)
            return results
        except Exception as e:
            logger.error(f"Error searching chat history for user {user_id}: {e}")
            return []