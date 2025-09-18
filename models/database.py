# models/database.py

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from pydantic_core import core_schema

# --- UPDATED PyObjectId CLASS FOR PYDANTIC V2 ---
# This new class structure is the standard way to handle custom types like ObjectId in Pydantic V2.
class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: Any
    ) -> core_schema.CoreSchema:
        def validate_from_str(v: str) -> ObjectId:
            if not ObjectId.is_valid(v):
                raise ValueError("Invalid ObjectId")
            return ObjectId(v)

        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(validate_from_str),
            ]
        )
        return core_schema.json_or_python_schema(
            json_schema=from_str_schema,
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(ObjectId),
                    from_str_schema,
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(lambda x: str(x)),
        )

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    preferred_mode: str = "beginner"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    email: EmailStr
    hashed_password: str
    full_name: str
    preferred_mode: str = "beginner"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

    class Config:
        # --- UPDATED CONFIG KEY ---
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    mode: str = "beginner"
    citations: Optional[List[Dict]] = []
    hindi_translation: Optional[str] = None

class ChatSession(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    title: str = "New Chat"
    messages: List[ChatMessage] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

    class Config:
        # --- UPDATED CONFIG KEY ---
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class QueryRequest(BaseModel):
    query: str
    mode: str = "beginner"
    session_id: Optional[str] = None
    is_voice: bool = False

class QueryResponse(BaseModel):
    answer: str
    hindi_translation: str
    citations: List[Dict]
    recommendations: List[str]
    keywords_explained: Optional[Dict[str, str]] = None
    session_id: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None





