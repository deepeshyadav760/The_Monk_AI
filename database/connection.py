# MongoDB connection
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config.config import Config
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None

mongodb = MongoDB()

async def connect_to_mongo():
    """Create database connection"""
    try:
        mongodb.client = AsyncIOMotorClient(Config.MONGODB_URL)
        mongodb.database = mongodb.client[Config.DATABASE_NAME]
        
        # Test connection
        await mongodb.database.command("ping")
        logger.info("Successfully connected to MongoDB")
        
        # Create indexes
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if mongodb.client:
        mongodb.client.close()
        logger.info("MongoDB connection closed")

async def create_indexes():
    """Create necessary database indexes"""
    try:
        # User collection indexes
        await mongodb.database.users.create_index("email", unique=True)
        
        # Chat sessions indexes
        await mongodb.database.chat_sessions.create_index("user_id")
        await mongodb.database.chat_sessions.create_index("created_at")
        await mongodb.database.chat_sessions.create_index([("user_id", 1), ("created_at", -1)])
        
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")

def get_database():
    return mongodb.database