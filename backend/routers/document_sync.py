"""
Document Sync Router
Manual endpoints for document synchronization and debugging
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from models.user import User
from utils.auth import get_current_user
from services.document_sync_service import document_sync_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents/doc", tags=["Document Agent Sync"])


class SyncRequest(BaseModel):
    company_id: Optional[str] = None
    lead_id: Optional[str] = None
    project_id: Optional[str] = None  # NEW: Add project_id support
    force_resync: bool = False


class SyncResponse(BaseModel):
    success: bool
    message: str
    startup_id: Optional[str] = None
    sync_details: Optional[dict] = None


@router.post("/sync", response_model=SyncResponse)
async def sync_documents(
    request: SyncRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Manually sync documents from MongoDB to ChromaDB
    
    Useful for:
    - Testing after uploading new documents
    - Troubleshooting sync issues
    - Force resyncing all documents
    - Syncing documents for a specific project
    """
    try:
        company_id = request.company_id or current_user.startupId
        lead_id = request.lead_id or current_user.id
        project_id = request.project_id  # Use project_id if provided
        
        # If project_id is provided, sync only that project's documents
        if project_id:
            sync_result = await document_sync_service.sync_documents_to_chromadb(
                startup_id=company_id,
                lead_id=lead_id,
                project_id=project_id,
                force_resync=request.force_resync
            )
            return SyncResponse(
                success=sync_result.get('success', False),
                message=sync_result.get('message', 'Sync completed'),
                startup_id=company_id,
                sync_details=sync_result
            )
        else:
            # Sync all documents (legacy behavior)
            result = await document_sync_service.initialize_documents_for_agent(
                company_id=company_id,
                lead_id=lead_id,
                user_startup_id=current_user.startupId
            )
            
            sync_result = result.get('sync', {})
            
            return SyncResponse(
                success=sync_result.get('success', False),
                message=sync_result.get('message', 'Sync completed'),
                startup_id=result.get('startup_id'),
                sync_details=sync_result
            )
        
    except Exception as e:
        logger.error(f"Error in sync endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync/project/{project_id}", response_model=SyncResponse)
async def sync_project_documents(
    project_id: str,
    force_resync: bool = False,
    current_user: User = Depends(get_current_user)
):
    """Convenience GET endpoint to sync a specific project's documents.
    Useful for testing from the browser and avoids 405 when using GET."""
    try:
        company_id = current_user.startupId
        lead_id = current_user.id
        sync_result = await document_sync_service.sync_documents_to_chromadb(
            startup_id=company_id,
            lead_id=project_id,  # use project_id as context id
            project_id=project_id,
            force_resync=force_resync
        )
        return SyncResponse(
            success=sync_result.get('success', False),
            message=sync_result.get('message', 'Sync completed'),
            startup_id=company_id,
            sync_details=sync_result
        )
    except Exception as e:
        logger.error(f"Error in project sync endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sync/status", response_model=dict)
async def get_sync_status(
    current_user: User = Depends(get_current_user)
):
    """Get current document sync status"""
    try:
        status = await document_sync_service.get_sync_status(
            startup_id=current_user.startupId,
            lead_id=current_user.id
        )
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting sync status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

