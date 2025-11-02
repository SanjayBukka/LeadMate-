"""
Script to delete all test data from MongoDB and ChromaDB
"""
import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
import shutil
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def delete_all_test_data():
    """Delete all test data from MongoDB"""
    try:
        # Connect to MongoDB
        logger.info("Connecting to MongoDB...")
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        db = client[settings.DATABASE_NAME]
        
        # Test connection
        await client.admin.command('ping')
        logger.info(f"✅ Connected to MongoDB database: {settings.DATABASE_NAME}")
        
        # Collections to clean
        collections = [
            "startups",
            "users",
            "projects",
            "documents",
            "notifications",
            "team_members",
            "tasks",
            "agent_chat_history",
            "team_iterations"
        ]
        
        # Delete data from each collection
        logger.info("\n🗑️  Starting data deletion...")
        for collection_name in collections:
            try:
                collection = db[collection_name]
                count = await collection.count_documents({})
                
                if count > 0:
                    result = await collection.delete_many({})
                    logger.info(f"✅ Deleted {result.deleted_count} documents from '{collection_name}' collection")
                else:
                    logger.info(f"ℹ️  Collection '{collection_name}' is already empty")
            except Exception as e:
                logger.warning(f"⚠️  Error deleting from '{collection_name}': {e}")
        
        logger.info("\n✅ All MongoDB test data deleted successfully!")
        
        # Close connection
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Error deleting test data: {e}")
        raise


def delete_chromadb_data():
    """Delete all ChromaDB test data"""
    try:
        chroma_db_path = Path("./chroma_db")
        
        if chroma_db_path.exists():
            logger.info("\n🗑️  Deleting ChromaDB data...")
            
            # Get size before deletion
            total_size = sum(f.stat().st_size for f in chroma_db_path.rglob('*') if f.is_file())
            size_mb = total_size / (1024 * 1024)
            
            # Delete all files and directories
            for item in chroma_db_path.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                    logger.info(f"✅ Deleted ChromaDB directory: {item.name}")
                elif item.is_file():
                    item.unlink()
                    logger.info(f"✅ Deleted ChromaDB file: {item.name}")
            
            logger.info(f"✅ ChromaDB data deleted successfully! (Freed {size_mb:.2f} MB)")
        else:
            logger.info("ℹ️  ChromaDB directory doesn't exist")
            
    except Exception as e:
        logger.warning(f"⚠️  Error deleting ChromaDB data: {e}")


async def main():
    """Main function"""
    logger.info("=" * 60)
    logger.info("🧹 TEST DATA DELETION SCRIPT")
    logger.info("=" * 60)
    
    # Delete MongoDB data
    await delete_all_test_data()
    
    # Delete ChromaDB data
    delete_chromadb_data()
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ ALL TEST DATA DELETED SUCCESSFULLY!")
    logger.info("=" * 60)
    logger.info("\n📋 Summary:")
    logger.info("  - All MongoDB collections cleared")
    logger.info("  - All ChromaDB data removed")
    logger.info("\n💡 You can now start fresh with your testing!")


if __name__ == "__main__":
    asyncio.run(main())

