"""
MongoDB database connection and utilities
"""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from config import settings
import logging

logger = logging.getLogger(__name__)

# Global database client
mongodb_client: AsyncIOMotorClient = None
database = None


async def connect_to_mongodb():
    """Connect to MongoDB database"""
    global mongodb_client, database
    
    try:
        logger.info("Connecting to MongoDB...")
        mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
        
        # Test connection
        await mongodb_client.admin.command('ping')
        
        database = mongodb_client[settings.DATABASE_NAME]
        logger.info(f"✅ Successfully connected to MongoDB database: {settings.DATABASE_NAME}")
        
        # Create indexes
        await create_indexes()
        
        return database
        
    except ConnectionFailure as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error connecting to MongoDB: {e}")
        raise


async def close_mongodb_connection():
    """Close MongoDB connection"""
    global mongodb_client
    
    if mongodb_client:
        logger.info("Closing MongoDB connection...")
        mongodb_client.close()
        logger.info("✅ MongoDB connection closed")


async def create_indexes():
    """Create database indexes for better performance"""
    try:
        # Startups collection indexes
        await database.startups.create_index("companyEmail", unique=True)
        await database.startups.create_index("companyName")
        
        # Users collection indexes
        await database.users.create_index("email", unique=True)
        await database.users.create_index("startupId")
        await database.users.create_index([("startupId", 1), ("role", 1)])
        
        # Projects collection indexes
        await database.projects.create_index("startupId")
        await database.projects.create_index("teamLeadId")
        await database.projects.create_index([("startupId", 1), ("status", 1)])
        
        # Notifications collection indexes
        await database.notifications.create_index("userId")
        await database.notifications.create_index("startupId")
        await database.notifications.create_index([("userId", 1), ("isRead", 1)])
        await database.notifications.create_index([("userId", 1), ("createdAt", -1)])
        
        logger.info("✅ Database indexes created successfully")
        
    except Exception as e:
        logger.warning(f"⚠️  Error creating indexes: {e}")


def get_database():
    """Get database instance"""
    return database

