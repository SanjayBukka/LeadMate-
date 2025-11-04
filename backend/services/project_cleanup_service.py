"""
Project Cleanup Service
Handles complete cleanup when projects are deleted
Ensures no orphaned data remains
"""
import logging
from pathlib import Path
from typing import List, Dict
from bson import ObjectId
import shutil

from database import get_database
from services.project_data_service import project_data_service

logger = logging.getLogger(__name__)


class ProjectCleanupService:
    """Service to clean up all project-related data"""
    
    async def cleanup_project(self, project_id: str, startup_id: str) -> Dict:
        """
        Complete cleanup of a project:
        1. Delete all documents (MongoDB + files + ChromaDB)
        2. Delete all resumes (MongoDB + files + ChromaDB)
        3. Delete all tasks
        4. Delete tech stack
        5. Delete team formations
        6. Delete agent chat history (ChromaDB)
        7. Delete stack iterations (ChromaDB)
        8. Delete team formations (ChromaDB)
        9. Delete file uploads directory
        10. Clean up agent instances from cache
        
        Returns:
            Dict with cleanup results
        """
        results = {
            "project_id": project_id,
            "startup_id": startup_id,
            "documents_deleted": 0,
            "resumes_deleted": 0,
            "tasks_deleted": 0,
            "tech_stacks_deleted": 0,
            "team_formations_deleted": 0,
            "files_deleted": 0,
            "chromadb_cleaned": False,
            "errors": []
        }
        
        db = get_database()
        
        try:
            # 1. Delete all documents for this project
            documents = await db.documents.find({"projectId": project_id}).to_list(None)
            for doc in documents:
                try:
                    # Delete file
                    file_path = Path(doc.get("filePath", ""))
                    if file_path.exists():
                        file_path.unlink()
                        results["files_deleted"] += 1
                    
                    # Delete from MongoDB
                    await db.documents.delete_one({"_id": doc["_id"]})
                    results["documents_deleted"] += 1
                except Exception as e:
                    logger.error(f"Error deleting document {doc.get('_id')}: {e}")
                    results["errors"].append(f"Document {doc.get('_id')}: {str(e)}")
            
            # 2. Delete all resumes/team members for this project
            team_members = await db.team_members.find({"projectId": project_id}).to_list(None)
            for member in team_members:
                try:
                    # Delete resume file
                    resume_path = Path(member.get("resumeFilePath", ""))
                    if resume_path.exists():
                        resume_path.unlink()
                        results["files_deleted"] += 1
                    
                    # Delete from MongoDB
                    await db.team_members.delete_one({"_id": member["_id"]})
                    results["resumes_deleted"] += 1
                except Exception as e:
                    logger.error(f"Error deleting team member {member.get('_id')}: {e}")
                    results["errors"].append(f"Team member {member.get('_id')}: {str(e)}")
            
            # 3. Delete all tasks for this project
            result = await db.tasks.delete_many({"projectId": project_id})
            results["tasks_deleted"] = result.deleted_count
            
            # 4. Delete tech stack
            result = await db.tech_stacks.delete_many({"projectId": project_id})
            results["tech_stacks_deleted"] = result.deleted_count
            
            # 5. Delete team formations
            result = await db.team_formations.delete_many({"projectId": project_id})
            results["team_formations_deleted"] = result.deleted_count
            
            # 6. Clean up ChromaDB collections
            try:
                # Delete document embeddings
                docs_collection = project_data_service.get_project_documents_collection(startup_id, project_id)
                docs_collection.delete()  # Delete entire collection
                
                # Delete resume embeddings
                resumes_collection = project_data_service.get_project_resumes_collection(startup_id, project_id)
                resumes_collection.delete()
                
                # Delete doc chat history
                chat_collection = project_data_service.get_project_doc_chat_collection(startup_id, project_id)
                chat_collection.delete()
                
                # Delete stack iterations
                stack_collection = project_data_service.get_project_stack_iterations_collection(startup_id, project_id)
                stack_collection.delete()
                
                # Delete team formation
                team_collection = project_data_service.get_project_team_formation_collection(startup_id, project_id)
                team_collection.delete()
                
                results["chromadb_cleaned"] = True
            except Exception as e:
                logger.error(f"Error cleaning ChromaDB: {e}")
                results["errors"].append(f"ChromaDB cleanup: {str(e)}")
            
            # 7. Delete upload directory for this project
            upload_dir = Path("uploads") / project_id
            if upload_dir.exists():
                try:
                    shutil.rmtree(upload_dir)
                    logger.info(f"✅ Deleted upload directory: {upload_dir}")
                except Exception as e:
                    logger.error(f"Error deleting upload directory: {e}")
                    results["errors"].append(f"Upload directory: {str(e)}")
            
            # 8. Clean up agent instances (from project_agents router cache)
            try:
                from routers.project_agents import cleanup_agent_instances
                cleanup_agent_instances(project_id)
            except Exception as e:
                logger.warning(f"Could not cleanup agent instances: {e}")
            
            logger.info(f"✅ Project cleanup completed for {project_id}")
            
        except Exception as e:
            logger.error(f"Critical error during project cleanup: {e}")
            results["errors"].append(f"Critical: {str(e)}")
        
        return results


# Global instance
project_cleanup_service = ProjectCleanupService()

