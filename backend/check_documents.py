"""
Quick script to check documents in the database
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()

async def check_documents():
    # Connect to MongoDB
    mongo_uri = "mongodb+srv://LeadMate_1:mvbuEfnYmKyCwPEM@cluster0.pslm64p.mongodb.net/"
    client = AsyncIOMotorClient(mongo_uri)
    db = client.leadmate_db
    
    print("=" * 80)
    print("CHECKING DOCUMENTS IN DATABASE")
    print("=" * 80)
    
    # Get all projects
    projects_cursor = db.projects.find({})
    projects = await projects_cursor.to_list(length=100)
    
    print(f"\nFound {len(projects)} projects\n")
    
    for project in projects:
        print(f"\n{'=' * 80}")
        print(f"Project: {project.get('title')}")
        print(f"Project ID: {project.get('_id')}")
        print(f"Team Lead ID: {project.get('teamLeadId', 'N/A')}")
        
        # Get documents for this project
        docs_cursor = db.documents.find({"projectId": str(project['_id'])})
        docs = await docs_cursor.to_list(length=100)
        
        print(f"\nDocuments: {len(docs)} found")
        
        if docs:
            for i, doc in enumerate(docs, 1):
                print(f"\n  Document #{i}:")
                print(f"    - ID: {doc.get('_id')}")
                print(f"    - Filename: {doc.get('originalFilename')}")
                print(f"    - Size: {doc.get('fileSize')} bytes")
                print(f"    - Uploaded At: {doc.get('uploadedAt')}")
                print(f"    - Uploaded By: {doc.get('uploadedBy')}")
                print(f"    - Has Extracted Content: {'YES' if doc.get('extractedContent') else 'NO'}")
                if doc.get('extractedContent'):
                    preview = doc.get('extractedContent')[:200]
                    print(f"    - Content Preview: {preview}...")
        else:
            print("    No documents found for this project")
    
    print("\n" + "=" * 80)
    
    # Check for orphaned documents (not linked to any project)
    all_docs = await db.documents.find({}).to_list(length=100)
    print(f"\nTotal documents in database: {len(all_docs)}")
    
    project_ids = [str(p['_id']) for p in projects]
    orphaned = [doc for doc in all_docs if doc.get('projectId') not in project_ids]
    
    if orphaned:
        print(f"\nWARNING: Found {len(orphaned)} orphaned documents (not linked to any project):")
        for doc in orphaned:
            print(f"  - {doc.get('originalFilename')} (Project ID: {doc.get('projectId')})")
    else:
        print("\nNo orphaned documents found")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_documents())

