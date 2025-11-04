"""
Team Members API Routes
Endpoints for managing team members and uploading resumes
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Form
from typing import List
from bson import ObjectId
from datetime import datetime
from pathlib import Path
import shutil
import uuid
import logging

from database import get_database
from models.user import User
from models.team_member import TeamMember, TeamMemberCreate, TeamMemberInDB
from utils.auth import get_current_user, get_current_teamlead
from services.resume_processor import resume_processor
from services.project_data_service import project_data_service
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/team-members", tags=["Team Members"])

# Create resumes directory (using project_data_service instead)
# RESUMES_DIR is now handled by project_data_service


@router.post("/upload-resume", status_code=status.HTTP_201_CREATED)
async def upload_resume(
    project_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_teamlead)
):
    """
    Upload resume and extract team member information
    """
    try:
        logger.info(f"Resume upload started by user {current_user.id} for project {project_id}")
        logger.info(f"File: {file.filename}, Type: {file.content_type}, Size: {file.size if hasattr(file, 'size') else 'unknown'}")
        
        # Validate file type
        allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"]
        if file.content_type not in allowed_types:
            logger.warning(f"Invalid file type: {file.content_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF, DOCX, and TXT files are allowed"
            )
        
        db = get_database()
        
        # Verify project exists and user has access
        project = await db.projects.find_one({
            "_id": ObjectId(project_id),
            "startupId": current_user.startupId
        })
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Save resume file using project_data_service
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        resume_dir = project_data_service.get_project_resumes_dir(project_id)
        
        file_path = resume_dir / unique_filename
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Resume saved: {file_path}")
        
        # Extract information from resume
        logger.info(f"Starting AI extraction for {file.filename}...")
        extracted_info = resume_processor.extract_resume_info(
            str(file_path),
            file.content_type,
            file.filename
        )
        logger.info(f"AI extraction completed. Name: {extracted_info.get('name', 'Unknown')}")
        
        if "error" in extracted_info:
            # Still create team member with limited info
            logger.warning(f"Error extracting resume info: {extracted_info['error']}")
        
        # Create team member record
        team_member_data = TeamMemberInDB(
            name=extracted_info.get("name", "Unknown"),
            email=extracted_info.get("email"),
            phone=extracted_info.get("phone"),
            role=extracted_info.get("role", "Unknown"),
            experience=extracted_info.get("experience"),
            education=extracted_info.get("education", []),
            techStack=extracted_info.get("techStack", []),
            recentProjects=extracted_info.get("recentProjects", []),
            skills=extracted_info.get("skills", {}),
            resumeFilePath=str(file_path),
            projectId=project_id,
            startupId=current_user.startupId
        )
        
        # Insert into database
        result = await db.team_members.insert_one(team_member_data.model_dump(by_alias=True, exclude=['id']))
        
        # Get inserted document
        inserted_member = await db.team_members.find_one({"_id": result.inserted_id})
        
        # Store resume in ChromaDB for project-specific team formation
        try:
            resumes_collection = project_data_service.get_project_resumes_collection(
                startup_id=current_user.startupId,
                project_id=project_id
            )
            
            # Store resume data as JSON document
            resume_json = json.dumps({
                "name": extracted_info.get("name", "Unknown"),
                "email": extracted_info.get("email"),
                "phone": extracted_info.get("phone"),
                "role": extracted_info.get("role", "Unknown"),
                "techStack": extracted_info.get("techStack", []),
                "skills": extracted_info.get("skills", {}),
                "experience": extracted_info.get("experience"),
                "education": extracted_info.get("education", []),
                "recentProjects": extracted_info.get("recentProjects", [])
            })
            
            resume_id = f"resume_{str(result.inserted_id)}"
            resumes_collection.add(
                documents=[resume_json],
                ids=[resume_id],
                metadatas=[{
                    "team_member_id": str(result.inserted_id),
                    "project_id": project_id,
                    "startup_id": current_user.startupId,
                    "name": extracted_info.get("name", "Unknown"),
                    "uploaded_at": datetime.utcnow().isoformat()
                }]
            )
            
            logger.info(f"✅ Stored resume embeddings in ChromaDB for project {project_id}")
        except Exception as embed_error:
            logger.error(f"Error storing resume embeddings: {embed_error}")
            # Don't fail if embeddings fail
        
        # Convert to response model
        response_data = {
            **inserted_member,
            "_id": str(inserted_member["_id"])
        }
        
        logger.info(f"Team member created: {extracted_info.get('name')}")
        
        return {
            "message": "Resume uploaded and processed successfully",
            "teamMember": TeamMember(**response_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading resume: {e}")
        # Clean up file if it exists
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing resume: {str(e)}"
        )


@router.get("/project/{project_id}", response_model=List[TeamMember])
async def get_project_team_members(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get all team members for a project
    """
    try:
        db = get_database()
        
        # Verify project access
        project = await db.projects.find_one({
            "_id": ObjectId(project_id),
            "startupId": current_user.startupId
        })
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Get team members
        members_cursor = db.team_members.find({
            "projectId": project_id,
            "startupId": current_user.startupId
        }).sort("createdAt", -1)
        
        members = []
        async for member in members_cursor:
            member["_id"] = str(member["_id"])
            members.append(TeamMember(**member))
        
        return members
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching team members: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching team members: {str(e)}"
        )


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team_member(
    member_id: str,
    current_user: User = Depends(get_current_teamlead)
):
    """
    Delete a team member
    """
    try:
        db = get_database()
        
        if not ObjectId.is_valid(member_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid member ID"
            )
        
        # Find member
        member = await db.team_members.find_one({
            "_id": ObjectId(member_id),
            "startupId": current_user.startupId
        })
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team member not found"
            )
        
        # Delete resume file
        if member.get("resumeFilePath"):
            resume_path = Path(member["resumeFilePath"])
            if resume_path.exists():
                resume_path.unlink()
        
        # Delete from database
        await db.team_members.delete_one({"_id": ObjectId(member_id)})
        
        return {"message": "Team member deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting team member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting team member: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Team Members API is ready"}

