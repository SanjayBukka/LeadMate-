"""
API Router for Document Agent, Stack Agent, and Task Agent
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import sys
import os
import logging

from models.user import User
from utils.auth import get_current_user

logger = logging.getLogger(__name__)

# Add agents to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agents.document_agent import DocumentAgent
from agents.stack_agent import StackAgent
from agents.task_agent import TaskAgent
from agents.team_agent import TeamAgent

router = APIRouter(prefix="/api/agents", tags=["agents"])

# In-memory storage for agent instances (In production, use Redis or similar)
agent_instances = {}


def get_document_agent(company_id: str, lead_id: str) -> DocumentAgent:
    """Get or create Document Agent instance"""
    key = f"{company_id}_{lead_id}_doc"
    if key not in agent_instances:
        agent_instances[key] = DocumentAgent(company_id, lead_id)
    return agent_instances[key]


def get_stack_agent(company_id: str, lead_id: str) -> StackAgent:
    """Get or create Stack Agent instance"""
    key = f"{company_id}_{lead_id}_stack"
    if key not in agent_instances:
        agent_instances[key] = StackAgent(company_id, lead_id)
    return agent_instances[key]


def get_task_agent(company_id: str, lead_id: str) -> TaskAgent:
    """Get or create Task Agent instance"""
    key = f"{company_id}_{lead_id}_task"
    if key not in agent_instances:
        agent_instances[key] = TaskAgent(company_id, lead_id)
    return agent_instances[key]


def get_team_agent(company_id: str, lead_id: str) -> TeamAgent:
    """Get or create Team Agent instance"""
    key = f"{company_id}_{lead_id}_team"
    if key not in agent_instances:
        agent_instances[key] = TeamAgent(company_id, lead_id)
    return agent_instances[key]


# ============= DOCUMENT AGENT ENDPOINTS =============

class DocumentUploadResponse(BaseModel):
    success: bool
    document_id: Optional[str] = None
    filename: Optional[str] = None
    chunks: Optional[int] = None
    error: Optional[str] = None


@router.post("/doc/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    company_id: str = Form(...),
    lead_id: str = Form(...)
):
    """Upload project document to Document Agent"""
    try:
        agent = get_document_agent(company_id, lead_id)
        file_data = await file.read()
        
        result = agent.upload_document(
            file_data=file_data,
            filename=file.filename,
            file_type=file.content_type
        )
        
        return DocumentUploadResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ChatRequest(BaseModel):
    message: str
    company_id: str
    lead_id: str
    project_id: Optional[str] = None  # NEW: Optional project_id


class ChatResponse(BaseModel):
    response: str
    chat_id: str
    agent: str
    timestamp: str


class ChatHistoryResponse(BaseModel):
    chat_history: List[dict]


@router.get("/doc/history/{company_id}/{lead_id}", response_model=ChatHistoryResponse)
async def get_chat_history(company_id: str, lead_id: str):
    """Get chat history with Document Agent"""
    try:
        agent = get_document_agent(company_id, lead_id)
        history = agent.get_chat_history()
        
        return ChatHistoryResponse(chat_history=history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class DocumentsSummaryResponse(BaseModel):
    summary: dict


@router.get("/doc/summary/{company_id}/{lead_id}", response_model=DocumentsSummaryResponse)
async def get_documents_summary(company_id: str, lead_id: str):
    """Get summary of all uploaded documents"""
    try:
        agent = get_document_agent(company_id, lead_id)
        summary = agent.get_all_documents_summary()
        
        return DocumentsSummaryResponse(summary=summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ContextExportResponse(BaseModel):
    context: dict


@router.get("/doc/export-context/{company_id}/{lead_id}", response_model=ContextExportResponse)
async def export_context_for_stack(company_id: str, lead_id: str):
    """Export Document Agent context for Stack Agent"""
    try:
        agent = get_document_agent(company_id, lead_id)
        context = agent.export_context_for_stack_agent()
        
        return ContextExportResponse(context=context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= STACK AGENT ENDPOINTS =============

class ResumeUploadResponse(BaseModel):
    success: bool
    resume_id: Optional[str] = None
    candidate_name: Optional[str] = None
    skills_extracted: Optional[dict] = None
    error: Optional[str] = None


@router.post("/stack/upload-resume", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    candidate_name: str = Form(...),
    company_id: str = Form(...),
    lead_id: str = Form(...)
):
    """Upload team member resume to Stack Agent"""
    try:
        agent = get_stack_agent(company_id, lead_id)
        file_data = await file.read()
        
        result = agent.upload_resume(
            file_data=file_data,
            filename=file.filename,
            candidate_name=candidate_name
        )
        
        return ResumeUploadResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ResumesListResponse(BaseModel):
    resumes: List[dict]


@router.get("/stack/resumes/{company_id}/{lead_id}", response_model=ResumesListResponse)
async def get_all_resumes(company_id: str, lead_id: str):
    """Get all uploaded resumes"""
    try:
        agent = get_stack_agent(company_id, lead_id)
        resumes = agent.get_all_resumes()
        
        # Remove full text from response for brevity
        for resume in resumes:
            resume['resume_preview'] = resume['resume_text'][:200] + "..."
            del resume['resume_text']
        
        return ResumesListResponse(resumes=resumes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class TeamGenerationRequest(BaseModel):
    company_id: str
    lead_id: str


class TeamGenerationResponse(BaseModel):
    success: bool
    iteration_id: Optional[str] = None
    team_recommendation: Optional[str] = None
    iteration_number: Optional[int] = None
    error: Optional[str] = None


@router.post("/stack/generate-initial-team", response_model=TeamGenerationResponse)
async def generate_initial_team(request: TeamGenerationRequest):
    """Generate initial team recommendation"""
    try:
        agent = get_stack_agent(request.company_id, request.lead_id)
        result = agent.generate_initial_team()
        
        return TeamGenerationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class IterationRequest(BaseModel):
    lead_feedback: str
    company_id: str
    lead_id: str


@router.post("/stack/iterate-team", response_model=TeamGenerationResponse)
async def iterate_team(request: IterationRequest):
    """Iterate on team based on lead feedback"""
    try:
        agent = get_stack_agent(request.company_id, request.lead_id)
        result = agent.iterate_team(request.lead_feedback)
        
        return TeamGenerationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class FinalizeRequest(BaseModel):
    company_id: str
    lead_id: str


class FinalizeResponse(BaseModel):
    success: bool
    report_id: Optional[str] = None
    report_path: Optional[str] = None
    report_content: Optional[str] = None
    metadata: Optional[dict] = None
    error: Optional[str] = None


@router.post("/stack/finalize-team", response_model=FinalizeResponse)
async def finalize_team(request: FinalizeRequest):
    """Finalize team and generate comprehensive report"""
    try:
        agent = get_stack_agent(request.company_id, request.lead_id)
        result = agent.finalize_team()
        
        return FinalizeResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class IterationHistoryResponse(BaseModel):
    iterations: List[dict]


@router.get("/stack/iterations/{company_id}/{lead_id}", response_model=IterationHistoryResponse)
async def get_iteration_history(company_id: str, lead_id: str):
    """Get all team formation iterations"""
    try:
        agent = get_stack_agent(company_id, lead_id)
        iterations = agent._get_iteration_history()
        
        return IterationHistoryResponse(iterations=iterations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= TASK AGENT ENDPOINTS =============

class TaskGenerationRequest(BaseModel):
    company_id: str
    lead_id: str
    project_name: Optional[str] = "Project"


class TaskGenerationResponse(BaseModel):
    success: bool
    tasks_generated: Optional[int] = None
    tasks: Optional[List[dict]] = None
    error: Optional[str] = None


@router.post("/tasks/generate", response_model=TaskGenerationResponse)
async def generate_tasks(request: TaskGenerationRequest):
    """
    Generate comprehensive task breakdown based on:
    - Project documents (from Document Agent)
    - Requirements clarifications (from Document Agent chat)
    - Team composition (from Stack Agent)
    """
    try:
        agent = get_task_agent(request.company_id, request.lead_id)
        result = agent.generate_tasks(request.project_name)
        
        return TaskGenerationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class TasksListResponse(BaseModel):
    tasks: List[dict]


@router.get("/tasks/{company_id}/{lead_id}", response_model=TasksListResponse)
async def get_all_tasks(company_id: str, lead_id: str, project_name: Optional[str] = None):
    """Get all tasks for this lead, optionally filtered by project"""
    try:
        agent = get_task_agent(company_id, lead_id)
        tasks = agent.get_all_tasks(project_name)
        
        return TasksListResponse(tasks=tasks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class TaskStatusUpdateRequest(BaseModel):
    task_id: str
    new_status: str  # "todo" | "inprogress" | "completed"
    company_id: str
    lead_id: str


class TaskStatusUpdateResponse(BaseModel):
    success: bool
    task: Optional[dict] = None
    error: Optional[str] = None


@router.put("/tasks/status", response_model=TaskStatusUpdateResponse)
async def update_task_status(request: TaskStatusUpdateRequest):
    """Update task status (for drag & drop in frontend Task Board)"""
    try:
        agent = get_task_agent(request.company_id, request.lead_id)
        result = agent.update_task_status(request.task_id, request.new_status)
        
        return TaskStatusUpdateResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class TaskDeleteRequest(BaseModel):
    task_id: str
    company_id: str
    lead_id: str


class TaskDeleteResponse(BaseModel):
    success: bool
    error: Optional[str] = None


@router.delete("/tasks/delete", response_model=TaskDeleteResponse)
async def delete_task(request: TaskDeleteRequest):
    """Delete a task"""
    try:
        agent = get_task_agent(request.company_id, request.lead_id)
        result = agent.delete_task(request.task_id)
        
        return TaskDeleteResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class TaskRegenerateRequest(BaseModel):
    company_id: str
    lead_id: str
    project_name: Optional[str] = "Project"


@router.post("/tasks/regenerate", response_model=TaskGenerationResponse)
async def regenerate_tasks(request: TaskRegenerateRequest):
    """Clear all tasks and regenerate fresh ones"""
    try:
        agent = get_task_agent(request.company_id, request.lead_id)
        result = agent.regenerate_tasks(request.project_name)
        
        return TaskGenerationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class TaskStatisticsResponse(BaseModel):
    statistics: dict


@router.get("/tasks/stats/{company_id}/{lead_id}", response_model=TaskStatisticsResponse)
async def get_task_statistics(company_id: str, lead_id: str):
    """Get task statistics for dashboard"""
    try:
        agent = get_task_agent(company_id, lead_id)
        stats = agent.get_task_statistics()
        
        return TaskStatisticsResponse(statistics=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= CHAT ENDPOINTS =============

class ChatRequest(BaseModel):
    message: str
    company_id: str
    lead_id: str
    project_id: Optional[str] = None  # NEW: Optional project_id


class ChatResponse(BaseModel):
    response: str
    agent: str
    timestamp: str


@router.post("/doc/chat", response_model=ChatResponse)
async def chat_with_document_agent(request: ChatRequest):
    """Chat with Document Agent"""
    try:
        from services.document_sync_service import document_sync_service
        
        # Try to get authenticated user (optional - for better ID resolution)
        startup_id = None
        try:
            from fastapi import Request
            from utils.auth import get_current_user
            # This won't work without proper request injection, so we'll resolve IDs manually
            startup_id = None  # Will be resolved in sync service
        except:
            pass
        
        logger.info(f"Doc Agent chat request - company_id: {request.company_id}, "
                   f"lead_id: {request.lead_id}, message length: {len(request.message)}")
        
        # If project_id is provided, sync that project's documents
        if request.project_id:
            logger.info(f"Syncing documents for project: {request.project_id}")
            sync_result = await document_sync_service.sync_documents_to_chromadb(
                startup_id=request.company_id,
                lead_id=request.project_id,  # Use project_id as context identifier
                project_id=request.project_id,
                force_resync=False
            )
            logger.info(f"Project sync result: {sync_result.get('message', 'Unknown')}")
            actual_startup_id = request.company_id
            context_id = request.project_id  # Use project_id as context
        else:
            # Initialize documents using the sync service (all documents)
            # The service will handle ID resolution internally
            init_result = await document_sync_service.initialize_documents_for_agent(
                company_id=request.company_id,
                lead_id=request.lead_id,
                user_startup_id=startup_id
            )
            
            logger.info(f"Document initialization: {init_result['sync']['message']}")
            logger.info(f"ID Resolution - provided: {request.company_id}, "
                       f"resolved: {init_result.get('startup_id')}, "
                       f"was_resolved: {init_result.get('id_resolved')}")
            
            # Use resolved startup_id for agent
            actual_startup_id = init_result.get('startup_id') or request.company_id
            context_id = request.lead_id  # Use lead_id as context
        
        # Get or create agent with proper IDs
        # Use project_id as context if available, otherwise use lead_id
        agent = get_document_agent(actual_startup_id, context_id)
        
        # Document agent's chat_with_agent is async, so we need await
        # Pass project_id if available
        result = await agent.chat_with_agent(request.message, project_id=request.project_id)
        
        logger.info(f"Agent response generated successfully")
        
        return ChatResponse(
            response=result.get('response', 'I received your message but couldn\'t generate a response.'),
            agent=result.get('agent', 'Document Agent'),
            timestamp=result.get('timestamp', '')
        )
    except Exception as e:
        logger.error(f"Error in chat_with_document_agent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")


@router.get("/stack/history/{company_id}/{lead_id}", response_model=ChatHistoryResponse)
async def get_stack_chat_history(company_id: str, lead_id: str):
    """Get chat history with Stack Agent"""
    try:
        agent = get_stack_agent(company_id, lead_id)
        history = agent.get_chat_history()
        
        return ChatHistoryResponse(chat_history=history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stack/chat", response_model=ChatResponse)
async def chat_with_stack_agent(request: ChatRequest):
    """Chat with Stack Agent"""
    try:
        logger.info(f"Stack Agent chat request - company_id: {request.company_id}, lead_id: {request.lead_id}, project_id: {request.project_id}")
        context_id = request.project_id or request.lead_id
        agent = get_stack_agent(request.company_id, context_id)
        result = agent.chat_with_agent(request.message)
        
        logger.info(f"Stack Agent response generated successfully")
        
        return ChatResponse(
            response=result.get('response', 'I received your message but couldn\'t generate a response.'),
            agent="Stack Agent",
            timestamp=result.get('timestamp', '')
        )
    except Exception as e:
        logger.error(f"Error in chat_with_stack_agent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")


@router.get("/tasks/history/{company_id}/{lead_id}", response_model=ChatHistoryResponse)
async def get_task_chat_history(company_id: str, lead_id: str):
    """Get chat history with Task Agent"""
    try:
        agent = get_task_agent(company_id, lead_id)
        history = agent.get_chat_history()
        
        return ChatHistoryResponse(chat_history=history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/chat", response_model=ChatResponse)
async def chat_with_task_agent(request: ChatRequest):
    """Chat with Task Agent"""
    try:
        logger.info(f"Task Agent chat request - company_id: {request.company_id}, lead_id: {request.lead_id}, project_id: {request.project_id}")
        context_id = request.project_id or request.lead_id
        agent = get_task_agent(request.company_id, context_id)
        result = agent.chat_with_agent(request.message)
        
        logger.info(f"Task Agent response generated successfully")
        
        return ChatResponse(
            response=result.get('response', 'I received your message but couldn\'t generate a response.'),
            agent="Task Agent",
            timestamp=result.get('timestamp', '')
        )
    except Exception as e:
        logger.error(f"Error in chat_with_task_agent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")


@router.post("/team/chat", response_model=ChatResponse)
async def chat_with_team_agent(request: ChatRequest):
    """Chat with Team Agent"""
    try:
        logger.info(f"Team Agent chat request - company_id: {request.company_id}, lead_id: {request.lead_id}, project_id: {request.project_id}")
        context_id = request.project_id or request.lead_id
        agent = get_team_agent(request.company_id, context_id)
        result = await agent.chat_with_agent(request.message)
        
        logger.info(f"Team Agent response generated successfully")
        
        return ChatResponse(
            response=result.get('response', 'I received your message but couldn\'t generate a response.'),
            agent="Team Agent",
            timestamp=result.get('timestamp', '')
        )
    except Exception as e:
        logger.error(f"Error in chat_with_team_agent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")


# ============= UTILITY ENDPOINTS =============

@router.get("/test")
async def test_agents():
    """Test agents system"""
    try:
        agent = get_document_agent("demo_company", "demo_lead")
        result = agent.chat_with_agent("Hello")
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}

@router.get("/health")
async def agents_health_check():
    """Health check for agents system"""
    return {
        "status": "healthy",
        "active_agents": len(agent_instances),
        "document_agents": sum(1 for k in agent_instances.keys() if k.endswith('_doc')),
        "stack_agents": sum(1 for k in agent_instances.keys() if k.endswith('_stack')),
        "task_agents": sum(1 for k in agent_instances.keys() if k.endswith('_task'))
    }

