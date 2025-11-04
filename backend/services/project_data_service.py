"""
Project Data Service
Centralized service for managing project-specific data storage and retrieval
Ensures all data (documents, resumes, embeddings, agent data) is scoped to projects
"""
import chromadb
from pathlib import Path
from typing import List, Dict, Optional
import logging
from database import get_database
from bson import ObjectId

logger = logging.getLogger(__name__)


class ProjectDataService:
    """Centralized service for project-scoped data management"""
    
    def __init__(self):
        self.base_path = Path("chroma_db")
        self.base_path.mkdir(exist_ok=True)
        self.uploads_base = Path("uploads")
        self.uploads_base.mkdir(exist_ok=True)
        
    def get_project_collection_name(self, startup_id: str, project_id: str, collection_type: str) -> str:
        """
        Generate project-scoped collection name
        
        Args:
            startup_id: Startup identifier
            project_id: Project identifier
            collection_type: Type (documents, resumes, doc_chat, stack_iterations, team_formation)
        
        Returns:
            Collection name string (sanitized for ChromaDB)
        """
        import re
        # Sanitize IDs to ensure valid collection name
        safe_startup = re.sub(r'[^a-zA-Z0-9_-]', '_', str(startup_id))[:50]
        safe_project = re.sub(r'[^a-zA-Z0-9_-]', '_', str(project_id))[:50]
        safe_type = re.sub(r'[^a-zA-Z0-9_-]', '_', collection_type)[:30]
        
        collection_name = f"startup_{safe_startup}_project_{safe_project}_{safe_type}"
        
        # Ensure length is within ChromaDB limits (63 chars)
        max_length = 63
        if len(collection_name) > max_length:
            # Use hash for long names
            import hashlib
            hash_full = hashlib.md5(f"{startup_id}_{project_id}_{collection_type}".encode()).hexdigest()
            # Shortened format: "s_{hash1}_p_{hash2}_{type}"
            hash1 = hash_full[:8]
            hash2 = hash_full[8:16]
            type_part = safe_type[:15]
            collection_name = f"s_{hash1}_p_{hash2}_{type_part}"
            # Ensure it's still within limits
            if len(collection_name) > max_length:
                hash_simple = hash_full[:12]
                type_short = safe_type[:10]
                collection_name = f"s_{hash_simple}_{type_short}"
                collection_name = collection_name[:max_length]
        
        # Ensure starts and ends with alphanumeric
        import re
        collection_name = re.sub(r'^[^a-zA-Z0-9]+', '', collection_name)
        collection_name = re.sub(r'[^a-zA-Z0-9]+$', '', collection_name)
        
        # Final fallback if still invalid
        if len(collection_name) < 3 or len(collection_name) > max_length:
            import hashlib
            hash_fallback = hashlib.md5(f"{startup_id}_{project_id}_{collection_type}".encode()).hexdigest()[:16]
            collection_name = f"col_{hash_fallback}_{safe_type[:8]}"
            collection_name = collection_name[:max_length]
        
        return collection_name
    
    def get_chromadb_client(self, startup_id: str) -> chromadb.PersistentClient:
        """Get ChromaDB client for startup"""
        startup_path = self.base_path / f"startup_{startup_id}"
        startup_path.mkdir(exist_ok=True)
        return chromadb.PersistentClient(path=str(startup_path))
    
    def get_project_collection(self, startup_id: str, project_id: str, collection_type: str):
        """Get or create ChromaDB collection for a project"""
        client = self.get_chromadb_client(startup_id)
        collection_name = self.get_project_collection_name(startup_id, project_id, collection_type)
        
        return client.get_or_create_collection(
            name=collection_name,
            metadata={
                "startup_id": startup_id,
                "project_id": project_id,
                "type": collection_type
            }
        )
    
    def get_project_documents_collection(self, startup_id: str, project_id: str):
        """Get documents collection for a project"""
        return self.get_project_collection(startup_id, project_id, "documents")
    
    def get_project_resumes_collection(self, startup_id: str, project_id: str):
        """Get resumes collection for a project"""
        return self.get_project_collection(startup_id, project_id, "resumes")
    
    def get_project_doc_chat_collection(self, startup_id: str, project_id: str):
        """Get document chat history collection for a project"""
        return self.get_project_collection(startup_id, project_id, "doc_chat")
    
    def get_project_stack_iterations_collection(self, startup_id: str, project_id: str):
        """Get stack iterations collection for a project"""
        return self.get_project_collection(startup_id, project_id, "stack_iterations")
    
    def get_project_team_formation_collection(self, startup_id: str, project_id: str):
        """Get team formation collection for a project"""
        return self.get_project_collection(startup_id, project_id, "team_formation")
    
    def get_project_uploads_dir(self, project_id: str) -> Path:
        """Get uploads directory for a project"""
        project_dir = self.uploads_base / project_id
        project_dir.mkdir(exist_ok=True)
        return project_dir
    
    def get_project_resumes_dir(self, project_id: str) -> Path:
        """Get resumes directory for a project"""
        resumes_dir = self.get_project_uploads_dir(project_id) / "resumes"
        resumes_dir.mkdir(exist_ok=True)
        return resumes_dir
    
    async def get_project_documents_from_db(self, project_id: str) -> List[Dict]:
        """Get all documents for a project from MongoDB"""
        db = get_database()
        cursor = db.documents.find({"projectId": project_id})
        documents = []
        async for doc in cursor:
            documents.append({
                "_id": str(doc["_id"]),
                "originalFilename": doc.get("originalFilename", ""),
                "extractedContent": doc.get("extractedContent", ""),
                "uploadedAt": doc.get("uploadedAt"),
                "filePath": doc.get("filePath", "")
            })
        return documents
    
    async def get_project_resumes_from_db(self, project_id: str) -> List[Dict]:
        """Get all resumes for a project from MongoDB"""
        db = get_database()
        cursor = db.team_members.find({"projectId": project_id})
        resumes = []
        async for member in cursor:
            if member.get("resumeFilePath"):
                resumes.append({
                    "_id": str(member["_id"]),
                    "name": member.get("name", ""),
                    "email": member.get("email", ""),
                    "techStack": member.get("techStack", []),
                    "resumeFilePath": member.get("resumeFilePath", ""),
                    "skills": member.get("skills", {})
                })
        return resumes
    
    async def get_project_data_summary(self, project_id: str) -> Dict:
        """Get summary of all data for a project"""
        db = get_database()
        project = await db.projects.find_one({"_id": ObjectId(project_id)})
        
        if not project:
            return {}
        
        startup_id = project.get("startupId", "")
        
        # Get document count
        doc_count = await db.documents.count_documents({"projectId": project_id})
        
        # Get resume/team member count
        resume_count = await db.team_members.count_documents({"projectId": project_id})
        
        # Get task count
        task_count = await db.tasks.count_documents({"projectId": project_id})
        
        # Get ChromaDB collection counts
        try:
            docs_collection = self.get_project_documents_collection(startup_id, project_id)
            docs_embedded = docs_collection.count()
        except:
            docs_embedded = 0
        
        try:
            resumes_collection = self.get_project_resumes_collection(startup_id, project_id)
            resumes_embedded = resumes_collection.count()
        except:
            resumes_embedded = 0
        
        return {
            "projectId": project_id,
            "startupId": startup_id,
            "documents": {
                "count": doc_count,
                "embedded": docs_embedded
            },
            "resumes": {
                "count": resume_count,
                "embedded": resumes_embedded
            },
            "tasks": {
                "count": task_count
            },
            "techStackId": project.get("techStackId"),
            "teamFormationId": project.get("teamFormationId")
        }


# Global instance
project_data_service = ProjectDataService()

