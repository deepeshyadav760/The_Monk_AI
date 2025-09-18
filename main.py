# FastAPI application
import os
# Disable problematic environment variables
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Disable torchvision image extension warnings
os.environ['TORCHVISION_USE_IMAGE_EXT'] = '0'

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import tempfile
import os
import logging
from datetime import timedelta
# os.environ['PYTHONIOENCODING'] = 'utf-8'

# Import models and services
from models.database import (
    UserCreate, UserLogin, QueryRequest, QueryResponse,
    Token, ChatSession, User
)
from services.auth import (
    authenticate_user, create_user, create_access_token,
    get_current_active_user
)
from services.rag_pipeline import RAGPipeline
from services.chat_service import ChatService
from database.connection import connect_to_mongo, close_mongo_connection
from config.config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
rag_pipeline = RAGPipeline()
chat_service = ChatService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting The Monk AI application...")
    await connect_to_mongo()
    await rag_pipeline.initialize()
    logger.info("The Monk AI application started successfully!")
    yield
    # Shutdown
    logger.info("Shutting down The Monk AI application...")
    await close_mongo_connection()

# Create FastAPI app
app = FastAPI(
    title="The Monk AI - RAG Chatbot for Hindu Scriptures",
    description="An intelligent chatbot for exploring Hindu philosophy and scriptures",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# --- Authentication endpoints ---
@app.post("/auth/register", response_model=dict)
async def register(user_data: UserCreate):
    """Register a new user"""
    try:
        user = await create_user(user_data)
        return {"message": "User created successfully", "user_id": str(user.id)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/auth/login", response_model=Token)
async def login(login_data: UserLogin):
    """Login user and return access token"""
    user = await authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token_expires = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=dict)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return {
        "user_id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "preferred_mode": current_user.preferred_mode,
    }

# --- Chat endpoints ---
@app.post("/chat/query", response_model=QueryResponse)
async def process_query(query_request: QueryRequest, current_user: User = Depends(get_current_active_user)):
    """Process a text query through the RAG pipeline"""
    try:
        response = await rag_pipeline.process_query(query_request, str(current_user.id))
        return response
    except Exception as e:
        logger.error(f"Query processing error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process query")

@app.post("/chat/voice-query", response_model=QueryResponse)
async def process_voice_query(
    audio_file: UploadFile = File(...),
    mode: str = Form(default="beginner"),
    session_id: str = Form(default=None),
    current_user: User = Depends(get_current_active_user)
):
    """Process a voice query"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.filename)[1]) as tmp_file:
            content = await audio_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        response = await rag_pipeline.process_voice_query(tmp_file_path, mode, str(current_user.id), session_id)
        return response
    except Exception as e:
        logger.error(f"Voice query processing error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process voice query")

@app.get("/chat/sessions", response_model=list)
async def get_user_chat_sessions(current_user: User = Depends(get_current_active_user), limit: int = 50):
    """Get user's chat sessions"""
    sessions = await chat_service.get_user_chat_sessions(str(current_user.id), limit)
    return [
        {"session_id": str(s.id), "title": s.title, "created_at": s.created_at} for s in sessions
    ]

@app.get("/chat/sessions/{session_id}", response_model=ChatSession)
async def get_chat_session(session_id: str, current_user: User = Depends(get_current_active_user)):
    """Get a specific chat session with messages"""
    session = await chat_service.get_chat_session(session_id, str(current_user.id))
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session

@app.delete("/chat/sessions/{session_id}")
async def delete_chat_session(session_id: str, current_user: User = Depends(get_current_active_user)):
    """Delete a chat session"""
    success = await chat_service.delete_chat_session(session_id, str(current_user.id))
    if not success:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return {"message": "Chat session deleted successfully"}

# --- System endpoints ---
@app.get("/system/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)



