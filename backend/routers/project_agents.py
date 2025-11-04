"""
Project-Centric Agents API Router
All agents use project-specific data
"""
from fastapi import APIRouter, Depends, HTTPException, status, Form
from typing import Optional
from bson import ObjectId
import logging
import asyncio

from database import get_database
from models.user import User
from utils.auth import get_current_user, get_current_teamlead
from agents.project_document_agent import ProjectDocumentAgent
from agents.project_stack_agent import ProjectStackAgent
from agents.project_team_formation_agent import ProjectTeamFormationAgent
from agents.tasks_designer_agent import TasksDesignerAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/project-agents", tags=["Project Agents"])

# Store agent instances per project
_agent_instances = {}
_agent_instances_lock = {}  # Track lock status to prevent concurrent initialization


def get_project_document_agent(startup_id: str, project_id: str) -> ProjectDocumentAgent:
    """Get or create Document Agent for a project (thread-safe)"""
    key = f"{startup_id}_{project_id}_doc"
    if key not in _agent_instances:
        _agent_instances[key] = ProjectDocumentAgent(startup_id, project_id)
    return _agent_instances[key]


def cleanup_agent_instances(project_id: str):
    """Remove all agent instances for a project"""
    keys_to_remove = [k for k in _agent_instances.keys() if project_id in k]
    for key in keys_to_remove:
        del _agent_instances[key]
    logger.info(f"Cleaned up {len(keys_to_remove)} agent instances for project {project_id}")


def get_project_stack_agent(startup_id: str, project_id: str) -> ProjectStackAgent:
    """Get or create Stack Agent for a project"""
    key = f"{startup_id}_{project_id}_stack"
    if key not in _agent_instances:
        _agent_instances[key] = ProjectStackAgent(startup_id, project_id)
    return _agent_instances[key]


def get_project_team_agent(startup_id: str, project_id: str) -> ProjectTeamFormationAgent:
    """Get or create Team Formation Agent for a project"""
    key = f"{startup_id}_{project_id}_team"
    if key not in _agent_instances:
        _agent_instances[key] = ProjectTeamFormationAgent(startup_id, project_id)
    return _agent_instances[key]


def get_tasks_designer_agent(startup_id: str, project_id: str) -> TasksDesignerAgent:
    """Get or create Tasks Designer Agent for a project"""
    key = f"{startup_id}_{project_id}_tasks"
    if key not in _agent_instances:
        _agent_instances[key] = TasksDesignerAgent(startup_id, project_id)
    return _agent_instances[key]


async def verify_project_access(project_id: str, user: User) -> dict:
    """Verify user has access to project"""
    db = get_database()
    
    if not ObjectId.is_valid(project_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project ID format"
        )
    
    project = await db.projects.find_one({
        "_id": ObjectId(project_id),
        "startupId": user.startupId
    })
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project


# ============= DOCUMENT AGENT ENDPOINTS =============

@router.post("/doc/chat/{project_id}")
async def chat_with_document_agent(
    project_id: str,
    message: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Chat with Document Agent about project's documents"""
    await verify_project_access(project_id, current_user)
    
    try:
        agent = get_project_document_agent(current_user.startupId, project_id)
        
        # Get chat history
        chat_history = await agent.get_chat_history(limit=5)
        
        response = await agent.chat(message, chat_history)
        
        return {
            "project_id": project_id,
            "response": response,
            "message": message
        }
    except Exception as e:
        logger.error(f"Error in document chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/doc/chat-history/{project_id}")
async def get_document_chat_history(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get chat history with Document Agent for a project"""
    await verify_project_access(project_id, current_user)
    
    try:
        agent = get_project_document_agent(current_user.startupId, project_id)
        history = await agent.get_chat_history(limit=20)
        
        return {
            "project_id": project_id,
            "chat_history": history
        }
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/doc/summary/{project_id}")
async def get_project_document_summary(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get summary of project documents"""
    await verify_project_access(project_id, current_user)
    
    try:
        agent = get_project_document_agent(current_user.startupId, project_id)
        summary = await agent.get_document_summary()
        
        return {
            "project_id": project_id,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= STACK AGENT ENDPOINTS =============

@router.post("/stack/recommend/{project_id}")
async def recommend_tech_stack(
    project_id: str,
    feedback: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Get technology stack recommendation for a project"""
    await verify_project_access(project_id, current_user)
    
    try:
        agent = get_project_stack_agent(current_user.startupId, project_id)
        recommendation = await agent.recommend_stack(team_lead_feedback=feedback)
        
        return recommendation
    except Exception as e:
        logger.error(f"Error recommending stack: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stack/iterations/{project_id}")
async def get_stack_iterations(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all stack recommendation iterations for a project"""
    await verify_project_access(project_id, current_user)
    
    try:
        agent = get_project_stack_agent(current_user.startupId, project_id)
        iterations = agent.get_iterations()
        
        return {
            "project_id": project_id,
            "iterations": iterations
        }
    except Exception as e:
        logger.error(f"Error getting iterations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= TEAM FORMATION AGENT ENDPOINTS =============

@router.post("/team/form/{project_id}")
async def form_team(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Form optimal team for a project"""
    await verify_project_access(project_id, current_user)
    
    try:
        agent = get_project_team_agent(current_user.startupId, project_id)
        team_formation = await agent.form_team()
        
        return team_formation
    except Exception as e:
        logger.error(f"Error forming team: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= TASKS DESIGNER AGENT ENDPOINTS =============

@router.post("/tasks/generate/{project_id}")
async def generate_tasks(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Generate tasks for a project"""
    await verify_project_access(project_id, current_user)
    
    try:
        agent = get_tasks_designer_agent(current_user.startupId, project_id)
        result = await agent.generate_tasks()
        
        return result
    except Exception as e:
        logger.error(f"Error generating tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{project_id}")
async def get_project_tasks(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all tasks for a project"""
    await verify_project_access(project_id, current_user)
    
    try:
        agent = get_tasks_designer_agent(current_user.startupId, project_id)
        tasks = await agent.get_project_tasks()
        
        return {
            "project_id": project_id,
            "tasks": tasks,
            "total": len(tasks)
        }
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= PROJECT DATA SUMMARY =============

@router.get("/summary/{project_id}")
async def get_project_data_summary(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get summary of all project data (documents, resumes, tasks)"""
    await verify_project_access(project_id, current_user)
    
    try:
        from services.project_data_service import project_data_service
        summary = await project_data_service.get_project_data_summary(project_id)
        
        return summary
    except Exception as e:
        logger.error(f"Error getting project summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

