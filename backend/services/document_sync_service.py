"""
Document Sync Service
Handles synchronization of documents from MongoDB to ChromaDB
System Architecture Layer 2: Dedicated sync service
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import uuid
from bson import ObjectId

from database import get_database
from services.vector_store_service import vector_store_service
from utils.text_chunker import chunk_text

logger = logging.getLogger(__name__)


class DocumentSyncService:
    """
    Service responsible for synchronizing project documents
    from MongoDB to ChromaDB for Document Agent access.
    
    Architecture:
    - MongoDB (documents collection) = Source of Truth
    - ChromaDB (vector store) = Fast search layer
    - This service = Bridge between them
    """
    
    def __init__(self):
        self.sync_cache = {}  # Track synced documents to avoid duplicates
    
    async def resolve_startup_id(self, user_id: str) -> Tuple[str, bool]:
        """
        Resolve user ID to actual startupId
        
        Returns:
            Tuple of (startup_id, is_resolved)
        """
        try:
            db = get_database()
            
            # Check if user_id looks like ObjectId
            if not ObjectId.is_valid(user_id):
                # Not a valid ObjectId, might already be startupId
                return user_id, False
            
            # Look up user to get startupId
            user = await db.users.find_one({"_id": ObjectId(user_id)})
            
            if user and user.get("startupId"):
                logger.info(f"Resolved user_id {user_id} → startupId {user['startupId']}")
                return user["startupId"], True
            
            # Not found or no startupId, return as-is
            logger.warning(f"Could not resolve user_id {user_id} to startupId")
            return user_id, False
            
        except Exception as e:
            logger.error(f"Error resolving startup_id: {e}")
            return user_id, False
    
    async def find_documents(self, startup_id: str, project_id: Optional[str] = None) -> List[Dict]:
        """
        Find all documents for a startup (and optionally a specific project)
        
        Args:
            startup_id: The startup ID
            project_id: Optional project ID filter
            
        Returns:
            List of document dictionaries
        """
        try:
            db = get_database()
            
            # Build query
            query = {"startupId": startup_id}
            if project_id:
                query["projectId"] = project_id
            
            documents = []
            async for doc in db.documents.find(query):
                # Only include documents with valid extracted content
                content = doc.get("extractedContent")
                if content and not content.startswith('[Error') and len(content.strip()) > 10:
                    documents.append({
                        "_id": str(doc["_id"]),
                        "filename": doc.get("originalFilename", "Unknown"),
                        "content": content,
                        "projectId": doc.get("projectId", ""),
                        "uploadedAt": doc.get("uploadedAt"),
                        "contentType": doc.get("contentType", "")
                    })
            
            logger.info(f"Found {len(documents)} valid documents for startup_id {startup_id}" + 
                      (f" and project_id {project_id}" if project_id else ""))
            
            return documents
            
        except Exception as e:
            logger.error(f"Error finding documents: {e}", exc_info=True)
            return []
    
    async def sync_documents_to_chromadb(
        self, 
        startup_id: str, 
        lead_id: str,
        project_id: Optional[str] = None,
        force_resync: bool = False
    ) -> Dict:
        """
        Sync documents from MongoDB to ChromaDB
        
        Args:
            startup_id: The startup ID (resolved)
            lead_id: The lead/user ID (for ChromaDB path)
            project_id: Optional project ID filter
            force_resync: If True, resync even if already synced
            
        Returns:
            Dict with sync results
        """
        try:
            # Get ChromaDB collection for this startup/project
            # Use project_id if provided, otherwise use lead_id (for backward compatibility)
            collection_project_id = project_id if project_id else lead_id
            collection = vector_store_service.get_or_create_collection(
                startup_id=startup_id,
                project_id=collection_project_id,
                collection_type="documents"
            )
            
            # Check if already synced (unless force)
            if not force_resync:
                existing_count = collection.count()
                if existing_count > 0:
                    logger.info(f"Documents already synced for {startup_id}/{lead_id} ({existing_count} chunks)")
                    return {
                        "success": True,
                        "message": "Documents already synced",
                        "synced_count": existing_count,
                        "documents_found": 0,
                        "chunks_synced": 0
                    }
            
            # Find documents in MongoDB
            documents = await self.find_documents(startup_id, project_id)
            
            if not documents:
                logger.warning(f"No documents found for startup_id {startup_id}")
                return {
                    "success": False,
                    "message": "No documents found in MongoDB",
                    "synced_count": 0,
                    "documents_found": 0,
                    "chunks_synced": 0
                }
            
            # Sync each document
            total_chunks = 0
            synced_docs = 0
            
            for doc in documents:
                doc_id = doc["_id"]
                
                # Check if already synced (by checking collection)
                # For duplicate prevention, we'll track by filename and project
                # ChromaDB will handle ID conflicts, so we can safely add
                # If force_resync, we'll add anyway (duplicates will be filtered by ID)
                
                # Chunk the content
                chunks = chunk_text(
                    doc["content"],
                    chunk_size=1000,
                    overlap=200
                )
                
                if not chunks:
                    logger.warning(f"No chunks created for document {doc_id}")
                    continue
                
                # Prepare documents for ChromaDB
                documents_to_add = []
                ids_to_add = []
                metadatas_to_add = []
                
                for i, chunk in enumerate(chunks):
                    chunk_id = f"sync_{doc_id}_chunk_{i}_{uuid.uuid4().hex[:8]}"
                    ids_to_add.append(chunk_id)
                    documents_to_add.append(chunk)
                    
                    # Parse uploadedAt
                    uploaded_at = doc.get("uploadedAt")
                    if isinstance(uploaded_at, datetime):
                        upload_time = uploaded_at.isoformat()
                    elif uploaded_at:
                        upload_time = str(uploaded_at)
                    else:
                        upload_time = datetime.utcnow().isoformat()
                    
                    metadatas_to_add.append({
                        "document_id": doc_id,
                        "filename": doc["filename"],
                        "chunk_index": i,
                        "upload_time": upload_time,
                        "startup_id": startup_id,
                        "lead_id": lead_id,
                        "project_id": doc.get("projectId", ""),
                        "mongodb_doc_id": doc_id,  # Track source
                        "synced_from_mongodb": True,
                        "sync_timestamp": datetime.utcnow().isoformat()
                    })
                
                # Add to ChromaDB
                if documents_to_add:
                    collection.add(
                        documents=documents_to_add,
                        ids=ids_to_add,
                        metadatas=metadatas_to_add
                    )
                    total_chunks += len(documents_to_add)
                    synced_docs += 1
                    logger.info(f"Synced document {doc['filename']}: {len(documents_to_add)} chunks")
            
            result = {
                "success": True,
                "message": f"Synced {synced_docs} documents with {total_chunks} chunks",
                "synced_count": collection.count(),
                "documents_found": len(documents),
                "chunks_synced": total_chunks,
                "documents_synced": synced_docs
            }
            
            logger.info(f"✅ Document sync complete: {result['message']}")
            return result
            
        except Exception as e:
            logger.error(f"Error syncing documents: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error syncing documents: {str(e)}",
                "error": str(e),
                "synced_count": 0,
                "documents_found": 0,
                "chunks_synced": 0
            }
    
    async def initialize_documents_for_agent(
        self,
        company_id: str,
        lead_id: str,
        user_startup_id: Optional[str] = None
    ) -> Dict:
        """
        Initialize documents for Document Agent
        
        This is the main entry point called by the API router.
        It handles:
        1. ID resolution (user.id → startupId)
        2. Document discovery
        3. ChromaDB synchronization
        
        Args:
            company_id: Company/startup ID (might be user.id)
            lead_id: Lead/user ID
            user_startup_id: If provided, use this instead of resolving
            
        Returns:
            Dict with initialization results
        """
        try:
            # Step 1: Resolve startup ID
            if user_startup_id:
                startup_id = user_startup_id
                resolved = True
            else:
                startup_id, resolved = await self.resolve_startup_id(company_id)
            
            logger.info(f"Initializing documents - company_id: {company_id}, "
                      f"startup_id: {startup_id}, resolved: {resolved}, lead_id: {lead_id}")
            
            # Step 2: Sync documents
            sync_result = await self.sync_documents_to_chromadb(
                startup_id=startup_id,
                lead_id=lead_id
            )
            
            return {
                "startup_id": startup_id,
                "company_id_provided": company_id,
                "id_resolved": resolved,
                "sync": sync_result
            }
            
        except Exception as e:
            logger.error(f"Error initializing documents: {e}", exc_info=True)
            return {
                "startup_id": None,
                "company_id_provided": company_id,
                "id_resolved": False,
                "sync": {
                    "success": False,
                    "message": f"Initialization error: {str(e)}",
                    "error": str(e)
                }
            }
    
    async def get_sync_status(
        self,
        startup_id: str,
        lead_id: str
    ) -> Dict:
        """Get current sync status"""
        try:
            collection = vector_store_service.get_or_create_collection(
                startup_id=startup_id,
                project_id=lead_id,
                collection_type="documents"
            )
            
            chromadb_count = collection.count()
            
            documents = await self.find_documents(startup_id)
            mongodb_count = len(documents)
            
            return {
                "startup_id": startup_id,
                "lead_id": lead_id,
                "chromadb_chunks": chromadb_count,
                "mongodb_documents": mongodb_count,
                "is_synced": chromadb_count > 0,
                "sync_needed": mongodb_count > 0 and chromadb_count == 0
            }
            
        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            return {
                "error": str(e)
            }


# Singleton instance
document_sync_service = DocumentSyncService()

