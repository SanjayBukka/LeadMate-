from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from database import get_database
from models.project import ProjectCreate, Project, ProjectInDB, ProjectUpdate
from models.notification import NotificationInDB
from models.user import User
from utils.auth import get_current_user, get_current_manager

router = APIRouter(prefix="/api/projects", tags=["Projects"])

@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_manager)
):
    """Manager creates a new project"""
    db = get_database()
    
    # Validate team lead if provided
    team_lead_name = None
    if project_data.teamLeadId:
        if not ObjectId.is_valid(project_data.teamLeadId):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid team lead ID format"
            )
        
        team_lead = await db.users.find_one({
            "_id": ObjectId(project_data.teamLeadId),
            "startupId": current_user.startupId,
            "role": "teamlead"
        })
        
        if not team_lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team lead not found or not part of your startup"
            )
        
        team_lead_name = team_lead.get("name")
    
    # Create project
    new_project = ProjectInDB(
        title=project_data.title,
        description=project_data.description,
        deadline=project_data.deadline,
        status=project_data.status if project_data.status else "active",
        teamLeadId=project_data.teamLeadId,
        startupId=current_user.startupId,
        managerId=str(current_user.id),
        progress=0,
        createdAt=datetime.utcnow()
    )
    
    result = await db.projects.insert_one(new_project.model_dump(by_alias=True, exclude=['id']))
    
    # Update startup project count
    await db.startups.update_one(
        {"_id": ObjectId(current_user.startupId)},
        {"$inc": {"totalProjects": 1}}
    )
    
    # Fetch and return created project
    created_project = await db.projects.find_one({"_id": result.inserted_id})
    
    # Convert ObjectId to string for Pydantic model
    if "_id" in created_project and isinstance(created_project["_id"], ObjectId):
        created_project["_id"] = str(created_project["_id"])
    
    # Create notification for team lead if assigned
    if project_data.teamLeadId:
        notification = NotificationInDB(
            userId=project_data.teamLeadId,
            startupId=current_user.startupId,
            type="project_assigned",
            title="New Project Assigned",
            message=f"You have been assigned to project: {project_data.title}",
            relatedId=str(result.inserted_id),
            isRead=False
        )
        await db.notifications.insert_one(notification.model_dump(by_alias=True, exclude=['id']))
    
    # Add team lead name to response
    response_data = {
        **created_project,
        "teamLead": team_lead_name or "Unassigned"
    }
    
    return Project(**response_data)


@router.get("", response_model=List[Project])
async def get_projects(current_user: User = Depends(get_current_user)):
    """Get all projects for the current user's startup"""
    db = get_database()
    
    # Managers see all projects, team leads see only their assigned projects
    if current_user.role == "manager":
        query = {"startupId": current_user.startupId}
    else:  # teamlead
        query = {
            "startupId": current_user.startupId,
            "teamLeadId": str(current_user.id)
        }
    
    projects_cursor = db.projects.find(query).sort("createdAt", -1)
    projects = []
    
    async for project_data in projects_cursor:
        # Convert ObjectId to string
        if "_id" in project_data and isinstance(project_data["_id"], ObjectId):
            project_data["_id"] = str(project_data["_id"])
        
        # Fetch team lead name if assigned
        team_lead_name = "Unassigned"
        if project_data.get("teamLeadId"):
            team_lead = await db.users.find_one({"_id": ObjectId(project_data["teamLeadId"])})
            if team_lead:
                team_lead_name = team_lead.get("name", "Unknown")
        
        project_data["teamLead"] = team_lead_name
        projects.append(Project(**project_data))
    
    return projects


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific project by ID"""
    db = get_database()
    
    if not ObjectId.is_valid(project_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project ID format"
        )
    
    project_data = await db.projects.find_one({
        "_id": ObjectId(project_id),
        "startupId": current_user.startupId
    })
    
    if not project_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Convert ObjectId to string
    if "_id" in project_data and isinstance(project_data["_id"], ObjectId):
        project_data["_id"] = str(project_data["_id"])
    
    # Fetch team lead name
    team_lead_name = "Unassigned"
    if project_data.get("teamLeadId"):
        team_lead = await db.users.find_one({"_id": ObjectId(project_data["teamLeadId"])})
        if team_lead:
            team_lead_name = team_lead.get("name", "Unknown")
    
    project_data["teamLead"] = team_lead_name
    
    return Project(**project_data)


@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    update_data: ProjectUpdate,
    current_user: User = Depends(get_current_manager)
):
    """Manager updates a project"""
    db = get_database()
    
    if not ObjectId.is_valid(project_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project ID format"
        )
    
    # Check if project exists and belongs to manager's startup
    existing_project = await db.projects.find_one({
        "_id": ObjectId(project_id),
        "startupId": current_user.startupId
    })
    
    if not existing_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Validate team lead if being updated
    if update_data.teamLeadId and update_data.teamLeadId != existing_project.get("teamLeadId"):
        if not ObjectId.is_valid(update_data.teamLeadId):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid team lead ID format"
            )
        
        team_lead = await db.users.find_one({
            "_id": ObjectId(update_data.teamLeadId),
            "startupId": current_user.startupId,
            "role": "teamlead"
        })
        
        if not team_lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team lead not found"
            )
    
    # Build update dict
    update_dict = {}
    if update_data.title is not None:
        update_dict["title"] = update_data.title
    if update_data.description is not None:
        update_dict["description"] = update_data.description
    if update_data.deadline is not None:
        update_dict["deadline"] = update_data.deadline
    if update_data.status is not None:
        update_dict["status"] = update_data.status
    if update_data.teamLeadId is not None:
        update_dict["teamLeadId"] = update_data.teamLeadId
    if update_data.progress is not None:
        update_dict["progress"] = update_data.progress
    
    update_dict["updatedAt"] = datetime.utcnow()
    
    # Update project
    await db.projects.update_one(
        {"_id": ObjectId(project_id)},
        {"$set": update_dict}
    )
    
    # Fetch and return updated project
    updated_project = await db.projects.find_one({"_id": ObjectId(project_id)})
    
    # Convert ObjectId to string
    if "_id" in updated_project and isinstance(updated_project["_id"], ObjectId):
        updated_project["_id"] = str(updated_project["_id"])
    
    # Fetch team lead name
    team_lead_name = "Unassigned"
    if updated_project.get("teamLeadId"):
        team_lead = await db.users.find_one({"_id": ObjectId(updated_project["teamLeadId"])})
        if team_lead:
            team_lead_name = team_lead.get("name", "Unknown")
    
    updated_project["teamLead"] = team_lead_name
    
    return Project(**updated_project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_manager)
):
    """Manager deletes a project"""
    db = get_database()
    
    if not ObjectId.is_valid(project_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project ID format"
        )
    
    # Check if project exists and belongs to manager's startup
    project = await db.projects.find_one({
        "_id": ObjectId(project_id),
        "startupId": current_user.startupId
    })
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Delete project
    await db.projects.delete_one({"_id": ObjectId(project_id)})
    
    # Update startup project count
    await db.startups.update_one(
        {"_id": ObjectId(current_user.startupId)},
        {"$inc": {"totalProjects": -1}}
    )
    
    return {"message": "Project deleted successfully"}

