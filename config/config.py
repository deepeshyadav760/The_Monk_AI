# # config.py

# # Configuration settings
# import os
# from dotenv import load_dotenv

# load_dotenv()

# class Config:
#     # Database
#     MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
#     DATABASE_NAME = os.getenv("DATABASE_NAME", "monk_ai_db")
    
#     # Vector Database
#     CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    
#     # API Keys
#     GROQ_API_KEY = os.getenv("GROQ_API_KEY")
#     HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
    
#     # JWT
#     SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
#     ALGORITHM = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
#     # Embedding Model
#     EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
#     RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
#     # LLM Settings
#     LLM_MODEL = "llama-3.3-70b-versatile"
#     MAX_TOKENS = 2048
#     TEMPERATURE = 0.3
    
#     # Audio Transcription Model
#     WHISPER_MODEL = "whisper-large-v3"
    
#     # RAG Settings
#     CHUNK_SIZE = 700
#     CHUNK_OVERLAP = 140
#     TOP_K_RETRIEVAL = 15
#     TOP_K_RERANK = 5




# config.py

# Configuration settings
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "monk_ai_db")
    
    # Vector Database
    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    
    # API Keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
    
    # JWT
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # Embedding Model
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    # LLM Settings
    LLM_MODEL = "llama-3.3-70b-versatile"
    MAX_TOKENS = 2048
    TEMPERATURE = 0.3
    
    # Audio Transcription Model
    WHISPER_MODEL = "whisper-large-v3"
    
    # RAG Settings
    CHUNK_SIZE = 700
    CHUNK_OVERLAP = 140
    TOP_K_RETRIEVAL = 15
    TOP_K_RERANK = 3