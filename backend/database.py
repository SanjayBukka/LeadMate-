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
        
        # Documents collection indexes (project-centric)
        await database.documents.create_index("projectId")
        await database.documents.create_index("startupId")
        await database.documents.create_index([("projectId", 1), ("uploadedAt", -1)])
        await database.documents.create_index([("startupId", 1), ("projectId", 1)])
        
        # Team members collection indexes (project-centric)
        await database.team_members.create_index("projectId")
        await database.team_members.create_index("startupId")
        await database.team_members.create_index([("projectId", 1), ("createdAt", -1)])
        
        # Tasks collection indexes (project-centric)
        await database.tasks.create_index("projectId")
        await database.tasks.create_index("startupId")
        await database.tasks.create_index([("projectId", 1), ("status", 1)])
        await database.tasks.create_index([("projectId", 1), ("priority", 1), ("createdAt", -1)])
        
        # Tech stacks collection indexes (project-centric)
        await database.tech_stacks.create_index("projectId", unique=True)  # One stack per project
        await database.tech_stacks.create_index("startupId")
        await database.tech_stacks.create_index([("projectId", 1), ("createdAt", -1)])
        
        # Team formations collection indexes (project-centric)
        await database.team_formations.create_index("projectId")
        await database.team_formations.create_index("startupId")
        await database.team_formations.create_index([("projectId", 1), ("createdAt", -1)])
        
        logger.info("✅ Database indexes created successfully")
        
    except Exception as e:
        logger.warning(f"⚠️  Error creating indexes: {e}")


def get_database():
    """Get database instance"""
    return database

