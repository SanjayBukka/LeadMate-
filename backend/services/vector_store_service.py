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
        Generate isolated collection name
        
        Args:
            startup_id: Startup identifier
            project_id: Project identifier
            collection_type: Type of collection (documents, chat_history, etc.)
        
        Returns:
            Collection name string
        """
        return f"startup_{startup_id}_project_{project_id}_{collection_type}"
    
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

