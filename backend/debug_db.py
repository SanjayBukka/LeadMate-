"""
Debug script to check database contents
"""
import asyncio
from database import get_database
from bson import ObjectId

async def debug_database():
    """Debug database contents"""
    from database import connect_to_mongodb
    await connect_to_mongodb()
    db = get_database()
    
    print("=== DEBUGGING DATABASE ===")
    
    # Check projects
    print("\n--- PROJECTS ---")
    projects = []
    async for project in db.projects.find().limit(5):
        projects.append(project)
    
    for project in projects:
        print(f"Project ID: {project['_id']}")
        print(f"Startup ID: {project.get('startupId', 'N/A')}")
        print(f"Title: {project.get('title', 'N/A')}")
        print(f"Documents in project: {len(project.get('documents', []))}")
        print("---")
    
    # Check documents collection
    print("\n--- DOCUMENTS COLLECTION ---")
    documents = []
    async for doc in db.documents.find().limit(5):
        documents.append(doc)
    
    for doc in documents:
        print(f"Document ID: {doc['_id']}")
        print(f"Startup ID: {doc.get('startupId', 'N/A')}")
        print(f"Project ID: {doc.get('projectId', 'N/A')}")
        print(f"Filename: {doc.get('originalFilename', 'N/A')}")
        print(f"Has content: {bool(doc.get('extractedContent'))}")
        print("---")
    
    # Check users
    print("\n--- USERS ---")
    users = []
    async for user in db.users.find().limit(3):
        users.append(user)
    
    for user in users:
        print(f"User ID: {user['_id']}")
        print(f"Email: {user.get('email', 'N/A')}")
        print(f"Startup ID: {user.get('startupId', 'N/A')}")
        print("---")

if __name__ == "__main__":
    asyncio.run(debug_database())
