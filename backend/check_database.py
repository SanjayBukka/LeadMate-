"""
Quick script to check what's in the database
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

async def check_database():
    """Check database contents"""
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    print("\n" + "="*60)
    print("📊 DATABASE CONTENTS")
    print("="*60)
    
    collections = ["startups", "users", "projects", "documents", "notifications", "team_members"]
    
    for collection_name in collections:
        collection = db[collection_name]
        count = await collection.count_documents({})
        print(f"\n📋 {collection_name}: {count} documents")
        
        if count > 0:
            # Show first few documents
            cursor = collection.find().limit(3)
            async for doc in cursor:
                # Hide sensitive fields
                if 'password' in doc:
                    doc['password'] = '***HIDDEN***'
                if 'hashed_password' in doc:
                    doc['hashed_password'] = '***HIDDEN***'
                print(f"   - {doc}")
    
    print("\n" + "="*60)
    client.close()

if __name__ == "__main__":
    asyncio.run(check_database())
