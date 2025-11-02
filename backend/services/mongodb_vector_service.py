"""
MongoDB Atlas Vector Search Service
Replaces ChromaDB with MongoDB Atlas Vector Search for better integration
"""
import os
import logging
from typing import List, Dict, Optional, Any
from pymongo import MongoClient
from bson import ObjectId
import numpy as np
from sentence_transformers import SentenceTransformer
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class MongoDBVectorService:
    """Service for managing document embeddings with MongoDB Atlas Vector Search"""
    
    def __init__(self):
        """Initialize MongoDB Vector Service"""
        self.mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client.leadmate_db
        
        # Initialize sentence transformer for embeddings
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Collections
        self.documents_collection = self.db.documents
        self.embeddings_collection = self.db.document_embeddings
        
        logger.info("MongoDB Vector Service initialized")
    
    def create_embeddings(self, text: str) -> List[float]:
        """Create embeddings for text using sentence transformers"""
        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error creating embeddings: {e}")
            return []
    
    def add_document(self, 
                    startup_id: str, 
                    project_id: str, 
                    filename: str, 
                    content: str, 
                    file_type: str = "pdf") -> Dict[str, Any]:
        """
        Add a document with embeddings to MongoDB
        
        Args:
            startup_id: Startup identifier
            project_id: Project identifier  
            filename: Original filename
            content: Document text content
            file_type: Type of file (pdf, docx, txt)
            
        Returns:
            Dict with document_id and status
        """
        try:
            # Split content into chunks
            chunks = self._split_text(content)
            
            document_id = str(uuid.uuid4())
            chunk_documents = []
            embedding_documents = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document_id}_chunk_{i}"
                
                # Create embedding for chunk
                embedding = self.create_embeddings(chunk)
                if not embedding:
                    continue
                
                # Document metadata
                doc_metadata = {
                    "_id": chunk_id,
                    "document_id": document_id,
                    "startup_id": startup_id,
                    "project_id": project_id,
                    "filename": filename,
                    "chunk_index": i,
                    "content": chunk,
                    "file_type": file_type,
                    "uploaded_at": datetime.utcnow(),
                    "created_at": datetime.utcnow()
                }
                
                # Embedding document for vector search
                embedding_doc = {
                    "_id": chunk_id,
                    "document_id": document_id,
                    "startup_id": startup_id,
                    "project_id": project_id,
                    "filename": filename,
                    "chunk_index": i,
                    "content": chunk,
                    "embedding": embedding,
                    "file_type": file_type,
                    "uploaded_at": datetime.utcnow()
                }
                
                chunk_documents.append(doc_metadata)
                embedding_documents.append(embedding_doc)
            
            # Insert documents
            if chunk_documents:
                self.documents_collection.insert_many(chunk_documents)
            
            if embedding_documents:
                self.embeddings_collection.insert_many(embedding_documents)
            
            # Create indexes for better performance
            self._create_indexes()
            
            logger.info(f"Added document {filename} with {len(chunks)} chunks")
            
            return {
                "success": True,
                "document_id": document_id,
                "chunks_count": len(chunks),
                "filename": filename
            }
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def search_documents(self, 
                        startup_id: str, 
                        project_id: str, 
                        query: str, 
                        limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search documents using vector similarity
        
        Args:
            startup_id: Startup identifier
            project_id: Project identifier
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching document chunks
        """
        try:
            # Create embedding for query
            query_embedding = self.create_embeddings(query)
            if not query_embedding:
                return []
            
            # Use MongoDB aggregation pipeline for vector search
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "vector_index",  # This needs to be created in Atlas
                        "path": "embedding",
                        "queryVector": query_embedding,
                        "numCandidates": limit * 10,
                        "limit": limit,
                        "filter": {
                            "startup_id": startup_id,
                            "project_id": project_id
                        }
                    }
                },
                {
                    "$project": {
                        "content": 1,
                        "filename": 1,
                        "chunk_index": 1,
                        "document_id": 1,
                        "score": {"$meta": "vectorSearchScore"}
                    }
                }
            ]
            
            # For now, use simple text search until vector index is set up
            results = self.embeddings_collection.find({
                "startup_id": startup_id,
                "project_id": project_id,
                "$text": {"$search": query}
            }).limit(limit)
            
            return list(results)
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def get_documents(self, startup_id: str, project_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a project"""
        try:
            documents = self.documents_collection.find({
                "startup_id": startup_id,
                "project_id": project_id
            }).sort("uploaded_at", -1)
            
            return list(documents)
            
        except Exception as e:
            logger.error(f"Error getting documents: {e}")
            return []
    
    def has_documents(self, startup_id: str, project_id: str) -> bool:
        """Check if project has any documents"""
        try:
            count = self.documents_collection.count_documents({
                "startup_id": startup_id,
                "project_id": project_id
            })
            return count > 0
            
        except Exception as e:
            logger.error(f"Error checking documents: {e}")
            return False
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document and its embeddings"""
        try:
            # Delete from both collections
            self.documents_collection.delete_many({"document_id": document_id})
            self.embeddings_collection.delete_many({"document_id": document_id})
            
            logger.info(f"Deleted document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    def _split_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                for i in range(end, max(start + chunk_size // 2, end - 100), -1):
                    if text[i] in '.!?':
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Text search index
            self.embeddings_collection.create_index([
                ("startup_id", 1),
                ("project_id", 1),
                ("content", "text")
            ])
            
            # Compound index for filtering
            self.embeddings_collection.create_index([
                ("startup_id", 1),
                ("project_id", 1),
                ("uploaded_at", -1)
            ])
            
            logger.info("Database indexes created")
            
        except Exception as e:
            logger.warning(f"Could not create indexes: {e}")
    
    def get_stats(self, startup_id: str, project_id: str) -> Dict[str, Any]:
        """Get document statistics for a project"""
        try:
            total_docs = self.documents_collection.count_documents({
                "startup_id": startup_id,
                "project_id": project_id
            })
            
            total_chunks = self.embeddings_collection.count_documents({
                "startup_id": startup_id,
                "project_id": project_id
            })
            
            # Get unique filenames
            filenames = self.documents_collection.distinct("filename", {
                "startup_id": startup_id,
                "project_id": project_id
            })
            
            return {
                "total_documents": total_docs,
                "total_chunks": total_chunks,
                "unique_files": len(filenames),
                "filenames": filenames
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}
