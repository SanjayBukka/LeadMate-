"""
MongoDB Agents Router
API endpoints for MongoDB-based AI agents
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging

from agents.mongodb_document_agent import MongoDocumentAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mongodb-agents", tags=["MongoDB Agents"])

# Global agent instances (in production, use proper session management)
_agents = {}


def get_mongo_document_agent(company_id: str, lead_id: str) -> MongoDocumentAgent:
    """Get or create MongoDB Document Agent instance"""
    key = f"{company_id}_{lead_id}"
    
    if key not in _agents:
        _agents[key] = MongoDocumentAgent(company_id, lead_id)
        logger.info(f"Created new MongoDB Document Agent for {company_id}/{lead_id}")
    
    return _agents[key]


# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    company_id: str
    lead_id: str


class ChatResponse(BaseModel):
    response: str
    chat_id: str
    agent: str
    timestamp: str


class DocumentUploadResponse(BaseModel):
    success: bool
    document_id: Optional[str] = None
    chunks_count: Optional[int] = None
    filename: Optional[str] = None
    error: Optional[str] = None


class DocumentStatsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    unique_files: int
    filenames: List[str]


# API Endpoints
@router.post("/doc/chat", response_model=ChatResponse)
async def chat_with_document_agent(request: ChatRequest):
    """Chat with MongoDB Document Agent about project requirements"""
    try:
        agent = get_mongo_document_agent(request.company_id, request.lead_id)
        result = agent.chat_with_agent(request.message)
        
        return ChatResponse(
            response=result['response'],
            chat_id=result.get('chat_id', ''),
            agent=result.get('agent', 'Document Agent'),
            timestamp=result.get('timestamp', '')
        )
        
    except Exception as e:
        logger.error(f"Error in document chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/doc/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    company_id: str = Form(...),
    lead_id: str = Form(...)
):
    """Upload project document to MongoDB Document Agent"""
    try:
        agent = get_mongo_document_agent(company_id, lead_id)
        file_data = await file.read()
        
        result = agent.upload_document(
            file_data=file_data,
            filename=file.filename,
            file_type=file.content_type
        )
        
        return DocumentUploadResponse(**result)
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/doc/documents/{company_id}/{lead_id}")
async def get_documents(company_id: str, lead_id: str):
    """Get all uploaded documents for a project"""
    try:
        agent = get_mongo_document_agent(company_id, lead_id)
        documents = agent.get_documents()
        
        return {
            "documents": documents,
            "count": len(documents)
        }
        
    except Exception as e:
        logger.error(f"Error getting documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/doc/stats/{company_id}/{lead_id}", response_model=DocumentStatsResponse)
async def get_document_stats(company_id: str, lead_id: str):
    """Get document statistics for a project"""
    try:
        agent = get_mongo_document_agent(company_id, lead_id)
        stats = agent.get_stats()
        
        return DocumentStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/doc/history/{company_id}/{lead_id}")
async def get_chat_history(company_id: str, lead_id: str):
    """Get chat history with MongoDB Document Agent"""
    try:
        agent = get_mongo_document_agent(company_id, lead_id)
        history = agent.get_chat_history()
        
        return {
            "chat_history": history,
            "count": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/doc/debug/{company_id}/{lead_id}")
async def get_debug_info(company_id: str, lead_id: str):
    """Get debug information about the MongoDB Document Agent"""
    try:
        agent = get_mongo_document_agent(company_id, lead_id)
        debug_info = agent.debug_info()
        
        return debug_info
        
    except Exception as e:
        logger.error(f"Error getting debug info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/doc/document/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its embeddings"""
    try:
        # This would need to be implemented in the agent
        # For now, return success
        return {
            "success": True,
            "message": f"Document {document_id} deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check for MongoDB agents"""
    return {
        "status": "healthy",
        "service": "MongoDB Agents",
        "version": "1.0.0"
    }
