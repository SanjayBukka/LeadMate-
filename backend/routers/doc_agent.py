"""
DocAgent API Routes
Endpoints for document analysis, Q&A, and summarization
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging

from models.user import User
from utils.auth import get_current_user, get_current_teamlead
from services.doc_agent_service import doc_agent_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents/doc-agent", tags=["DocAgent"])


class ChatRequest(BaseModel):
    """Request model for chat"""
    project_id: str
    question: str


class ChatResponse(BaseModel):
    """Response model for chat"""
    answer: str
    success: bool
    message: Optional[str] = None


class SummaryRequest(BaseModel):
    """Request model for summary generation"""
    project_id: str


class SummaryResponse(BaseModel):
    """Response model for summary"""
    summary: str
    success: bool
    message: Optional[str] = None


class ChatHistoryResponse(BaseModel):
    """Response model for chat history"""
    history: List[Dict]
    success: bool


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest,
    current_user: User = Depends(get_current_teamlead)
):
    """
    Chat with DocAgent about project documents
    """
    try:
        logger.info(f"DocAgent chat request from user {current_user.id} for project {request.project_id}")
        
        # Get chat history for context
        chat_history = doc_agent_service.get_chat_history(
            startup_id=current_user.startupId,
            project_id=request.project_id,
            limit=5
        )
        
        # Get answer from DocAgent
        answer = doc_agent_service.answer_question(
            startup_id=current_user.startupId,
            project_id=request.project_id,
            question=request.question,
            chat_history=chat_history
        )
        
        return ChatResponse(
            answer=answer,
            success=True,
            message="Answer generated successfully"
        )
    
    except Exception as e:
        logger.error(f"Error in DocAgent chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing your question: {str(e)}"
        )


@router.post("/summary", response_model=SummaryResponse)
async def generate_summary(
    request: SummaryRequest,
    current_user: User = Depends(get_current_teamlead)
):
    """
    Generate a comprehensive project summary
    """
    try:
        logger.info(f"Summary request from user {current_user.id} for project {request.project_id}")
        
        # Generate summary
        summary = doc_agent_service.generate_project_summary(
            startup_id=current_user.startupId,
            project_id=request.project_id
        )
        
        return SummaryResponse(
            summary=summary,
            success=True,
            message="Summary generated successfully"
        )
    
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating summary: {str(e)}"
        )


@router.get("/history/{project_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    project_id: str,
    limit: int = 10,
    current_user: User = Depends(get_current_teamlead)
):
    """
    Get chat history for a project
    """
    try:
        history = doc_agent_service.get_chat_history(
            startup_id=current_user.startupId,
            project_id=project_id,
            limit=limit
        )
        
        return ChatHistoryResponse(
            history=history,
            success=True
        )
    
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving chat history: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for DocAgent"""
    try:
        # Check if services are initialized
        if doc_agent_service.agent is None:
            return {
                "status": "unhealthy",
                "message": "DocAgent not properly initialized"
            }
        
        return {
            "status": "healthy",
            "message": "DocAgent is ready"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": str(e)
        }

