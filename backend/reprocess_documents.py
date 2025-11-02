"""
Script to re-process existing documents with improved extraction
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from pathlib import Path
import sys

# Add parent directory to path to import services
sys.path.insert(0, str(Path(__file__).parent))

from services.document_extractor import document_extractor
from services.gemini_service import gemini_service

MONGODB_URL = "mongodb+srv://LeadMate_1:mvbuEfnYmKyCwPEM@cluster0.pslm64p.mongodb.net/"
DATABASE_NAME = "leadmate_db"

async def reprocess_documents():
    """Re-process all documents with the improved extraction"""
    print("=" * 80)
    print("RE-PROCESSING DOCUMENTS WITH IMPROVED EXTRACTION")
    print("=" * 80)
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    try:
        # Get all documents
        documents_cursor = db.documents.find({})
        documents = await documents_cursor.to_list(length=1000)
        
        print(f"\nFound {len(documents)} documents to process\n")
        
        for doc in documents:
            doc_id = doc['_id']
            filename = doc.get('originalFilename', 'Unknown')
            file_path = doc.get('filePath')
            content_type = doc.get('contentType', '')
            
            print(f"\n{'=' * 80}")
            print(f"Processing: {filename}")
            print(f"Document ID: {doc_id}")
            print(f"File Path: {file_path}")
            
            if not file_path or not Path(file_path).exists():
                print(f"  ERROR: File not found at {file_path}")
                continue
            
            try:
                # Extract text
                print(f"  Extracting text...")
                extracted_text = document_extractor.extract_text(file_path, content_type)
                
                if not extracted_text:
                    print(f"  WARNING: No text extracted")
                    await db.documents.update_one(
                        {"_id": doc_id},
                        {"$set": {"extractedContent": None}}
                    )
                    continue
                
                # Check if extraction was successful (not an error message)
                if extracted_text.startswith('['):
                    print(f"  WARNING: Extraction failed: {extracted_text[:100]}")
                    await db.documents.update_one(
                        {"_id": doc_id},
                        {"$set": {"extractedContent": extracted_text}}
                    )
                    continue
                
                print(f"  Extracted {len(extracted_text)} characters")
                
                # Process with LLM
                print(f"  Processing with {gemini_service.llm_type} LLM...")
                extracted_content = gemini_service.extract_document_content(
                    extracted_text, 
                    filename
                )
                
                if extracted_content:
                    print(f"  SUCCESS: Processed {len(extracted_content)} characters")
                    
                    # Update database
                    await db.documents.update_one(
                        {"_id": doc_id},
                        {"$set": {"extractedContent": extracted_content}}
                    )
                    print(f"  Database updated successfully")
                else:
                    print(f"  WARNING: LLM processing returned no content")
                
            except Exception as e:
                print(f"  ERROR: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print("\n" + "=" * 80)
        print("RE-PROCESSING COMPLETE")
        print("=" * 80)
        
    finally:
        client.close()

if __name__ == "__main__":
    print("\nThis script will re-process all documents with the improved extraction.")
    print(f"Using {gemini_service.llm_type} LLM (will fallback to Ollama if Gemini fails)\n")
    
    response = input("Continue? (y/n): ")
    if response.lower() == 'y':
        asyncio.run(reprocess_documents())
    else:
        print("Cancelled.")

