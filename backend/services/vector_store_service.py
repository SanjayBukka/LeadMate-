"""
ChromaDB Vector Store Service
Manages embeddings storage with per-startup/project isolation
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path
from typing import List, Dict, Optional
import logging
import uuid

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for managing ChromaDB vector stores with isolation"""
    
    def __init__(self):
        self.base_path = Path("chroma_db")
        self.base_path.mkdir(exist_ok=True)
        logger.info(f"VectorStore initialized at: {self.base_path}")
    
    def get_collection_name(self, startup_id: str, project_id: str, collection_type: str = "documents") -> str:
        """
        Generate isolated collection name that complies with ChromaDB naming rules:
        - 3-63 characters
        - Starts and ends with alphanumeric
        - Only alphanumeric, underscores, or hyphens
        - No consecutive periods
        
        Args:
            startup_id: Startup identifier
            project_id: Project identifier
            collection_type: Type of collection (documents, chat_history, etc.)
        
        Returns:
            Collection name string (sanitized and length-limited)
        """
        import re
        import hashlib
        
        # Sanitize IDs to ensure valid characters only
        safe_startup = re.sub(r'[^a-zA-Z0-9_-]', '_', str(startup_id))
        safe_project = re.sub(r'[^a-zA-Z0-9_-]', '_', str(project_id))
        safe_type = re.sub(r'[^a-zA-Z0-9_-]', '_', str(collection_type))
        
        # Ensure starts and ends with alphanumeric (remove leading/trailing non-alphanumeric)
        safe_startup = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', safe_startup)
        safe_project = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', safe_project)
        safe_type = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', safe_type)
        
        # Base template: "startup_{id}_project_{id}_{type}"
        # This is about 29 chars (startup_ + _project_ + _documents)
        base_length = len("startup_") + len("_project_") + len(f"_{safe_type}")
        
        # ChromaDB limit is 63 characters
        max_length = 63
        available_chars = max_length - base_length  # ~34 chars for IDs
        
        # If IDs are too long, use hash-based approach
        if len(safe_startup) + len(safe_project) > available_chars:
            # Generate hash from both IDs for uniqueness
            hash_input = f"{startup_id}_{project_id}_{collection_type}"
            hash_full = hashlib.md5(hash_input.encode()).hexdigest()
            
            # Use shortened prefix with hash
            # Format: "s_{hash1}_p_{hash2}_{type}" to stay under 63 chars
            hash1 = hash_full[:8]
            hash2 = hash_full[8:16]
            type_part = safe_type[:15]
            collection_name = f"s_{hash1}_p_{hash2}_{type_part}"
            
            # Final length check and truncation
            if len(collection_name) > max_length:
                # More aggressive truncation
                hash_simple = hash_full[:12]
                type_short = safe_type[:10]
                collection_name = f"s_{hash_simple}_{type_short}"
                collection_name = collection_name[:max_length]
        else:
            # IDs fit, use normal format
            collection_name = f"startup_{safe_startup}_project_{safe_project}_{safe_type}"
            
            # Final truncation if still too long
            if len(collection_name) > max_length:
                # Truncate IDs proportionally
                excess = len(collection_name) - max_length
                startup_share = len(safe_startup) / (len(safe_startup) + len(safe_project))
                startup_reduce = int(excess * startup_share)
                project_reduce = excess - startup_reduce
                
                safe_startup = safe_startup[:max(1, len(safe_startup) - startup_reduce)]
                safe_project = safe_project[:max(1, len(safe_project) - project_reduce)]
                collection_name = f"startup_{safe_startup}_project_{safe_project}_{safe_type}"
                collection_name = collection_name[:max_length]
        
        # Ensure starts and ends with alphanumeric (final check)
        collection_name = re.sub(r'^[^a-zA-Z0-9]+', '', collection_name)
        collection_name = re.sub(r'[^a-zA-Z0-9]+$', '', collection_name)
        
        # Fallback: if somehow still invalid, use hash-only approach
        if len(collection_name) < 3 or len(collection_name) > max_length:
            hash_fallback = hashlib.md5(f"{startup_id}_{project_id}_{collection_type}".encode()).hexdigest()[:16]
            collection_name = f"col_{hash_fallback}_{safe_type[:8]}"
            collection_name = collection_name[:max_length]
        
        # Final validation: ensure 3-63 chars and alphanumeric start/end
        if not (3 <= len(collection_name) <= max_length and 
                collection_name[0].isalnum() and collection_name[-1].isalnum()):
            # Last resort: simple hash-based name
            hash_simple = hashlib.md5(f"{startup_id}_{project_id}_{collection_type}".encode()).hexdigest()[:12]
            collection_name = f"c{hash_simple}"
        
        return collection_name
    
    def get_client(self, startup_id: str) -> chromadb.PersistentClient:
        """
        Get or create ChromaDB client for a startup
        
        Args:
            startup_id: Startup identifier
        
        Returns:
            ChromaDB client instance
        """
        startup_path = self.base_path / f"startup_{startup_id}"
        startup_path.mkdir(exist_ok=True)
        
        try:
            client = chromadb.PersistentClient(path=str(startup_path))
            logger.info(f"ChromaDB client created for startup: {startup_id}")
            return client
        except Exception as e:
            logger.error(f"Error creating ChromaDB client: {e}")
            raise
    
    def get_or_create_collection(self, startup_id: str, project_id: str, collection_type: str = "documents"):
        """
        Get or create a collection for a specific project
        
        Args:
            startup_id: Startup identifier
            project_id: Project identifier
            collection_type: Type of collection
        
        Returns:
            ChromaDB collection instance
        """
        try:
            client = self.get_client(startup_id)
            collection_name = self.get_collection_name(startup_id, project_id, collection_type)
            
            collection = client.get_or_create_collection(
                name=collection_name,
                metadata={
                    "startup_id": startup_id,
                    "project_id": project_id,
                    "type": collection_type
                }
            )
            
            logger.info(f"Collection ready: {collection_name}")
            return collection
        except Exception as e:
            logger.error(f"Error getting/creating collection: {e}")
            raise
    
    def add_documents(
        self, 
        startup_id: str, 
        project_id: str, 
        documents: List[str], 
        metadatas: List[Dict],
        ids: Optional[List[str]] = None
    ) -> bool:
        """
        Add documents to a project's collection
        
        Args:
            startup_id: Startup identifier
            project_id: Project identifier
            documents: List of document texts
            metadatas: List of metadata dicts
            ids: Optional list of document IDs
        
        Returns:
            Success boolean
        """
        try:
            collection = self.get_or_create_collection(startup_id, project_id, "documents")
            
            # Generate IDs if not provided
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in documents]
            
            # Add documents to collection
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} documents to collection")
            return True
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False
    
    def search_documents(
        self, 
        startup_id: str, 
        project_id: str, 
        query: str, 
        n_results: int = 5
    ) -> List[str]:
        """
        Search documents in a project's collection
        
        Args:
            startup_id: Startup identifier
            project_id: Project identifier
            query: Search query
            n_results: Number of results to return
        
        Returns:
            List of document texts
        """
        try:
            collection = self.get_or_create_collection(startup_id, project_id, "documents")
            
            # Check if collection has documents
            count = collection.count()
            if count == 0:
                logger.warning(f"Collection is empty for project {project_id}")
                return []
            
            # Query the collection
            results = collection.query(
                query_texts=[query],
                n_results=min(n_results, count)
            )
            
            # Extract documents from results
            if results and 'documents' in results and len(results['documents']) > 0:
                documents = results['documents'][0]
                logger.info(f"Found {len(documents)} relevant documents")
                return documents
            
            return []
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def delete_project_collections(self, startup_id: str, project_id: str) -> bool:
        """
        Delete all collections for a project
        
        Args:
            startup_id: Startup identifier
            project_id: Project identifier
        
        Returns:
            Success boolean
        """
        try:
            client = self.get_client(startup_id)
            
            # Collection types to delete
            collection_types = ["documents", "chat_history", "stack_discussions"]
            
            for coll_type in collection_types:
                try:
                    collection_name = self.get_collection_name(startup_id, project_id, coll_type)
                    client.delete_collection(name=collection_name)
                    logger.info(f"Deleted collection: {collection_name}")
                except Exception as e:
                    logger.warning(f"Collection {coll_type} not found or error deleting: {e}")
            
            return True
        except Exception as e:
            logger.error(f"Error deleting project collections: {e}")
            return False
    
    def store_chat_message(
        self,
        startup_id: str,
        project_id: str,
        user_message: str,
        agent_response: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Store a chat conversation in ChromaDB
        
        Args:
            startup_id: Startup identifier
            project_id: Project identifier
            user_message: User's message
            agent_response: Agent's response
            metadata: Optional additional metadata
        
        Returns:
            Success boolean
        """
        try:
            collection = self.get_or_create_collection(startup_id, project_id, "chat_history")
            
            conversation = f"User: {user_message}\nDocAgent: {agent_response}"
            chat_id = str(uuid.uuid4())
            
            chat_metadata = {
                "user_message": user_message,
                "agent_response": agent_response,
                "type": "chat"
            }
            
            if metadata:
                chat_metadata.update(metadata)
            
            collection.add(
                documents=[conversation],
                metadatas=[chat_metadata],
                ids=[chat_id]
            )
            
            logger.info(f"Stored chat message in collection")
            return True
        except Exception as e:
            logger.error(f"Error storing chat message: {e}")
            return False
    
    def get_chat_history(
        self,
        startup_id: str,
        project_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Retrieve chat history for a project
        
        Args:
            startup_id: Startup identifier
            project_id: Project identifier
            limit: Maximum number of messages to retrieve
        
        Returns:
            List of chat message dictionaries
        """
        try:
            collection = self.get_or_create_collection(startup_id, project_id, "chat_history")
            
            # Get all documents (chat history)
            results = collection.get()
            
            chat_history = []
            if results and 'metadatas' in results:
                for metadata in results['metadatas']:
                    if metadata.get('type') == 'chat':
                        chat_history.append({
                            "user_message": metadata.get('user_message', ''),
                            "agent_response": metadata.get('agent_response', '')
                        })
            
            # Return last 'limit' messages
            return chat_history[-limit:] if len(chat_history) > limit else chat_history
        except Exception as e:
            logger.error(f"Error retrieving chat history: {e}")
            return []


# Global instance
vector_store_service = VectorStoreService()

