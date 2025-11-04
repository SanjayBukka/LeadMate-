"""
Document Upload and Management Router
Handles file uploads, storage, and retrieval
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from typing import List, Optional
import os
import shutil
from pathlib import Path
from datetime import datetime
from bson import ObjectId
import uuid
import logging

from database import get_database
from models.user import User
from utils.auth import get_current_user, get_current_manager
from services.document_extractor import document_extractor
from services.gemini_service import gemini_service
from services.project_data_service import project_data_service
from utils.text_chunker import chunk_text
from utils.validation import (
    validate_file_size, 
    validate_file_extension, 
    sanitize_filename,
    validate_project_id
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["Documents"])

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def get_project_upload_dir(project_id: str) -> Path:
    """Get or create upload directory for a project"""
    project_dir = UPLOAD_DIR / project_id
    project_dir.mkdir(exist_ok=True)
    return project_dir


@router.post("/upload/{project_id}")
async def upload_project_documents(
    project_id: str,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_manager)
):
    """
    Upload one or more documents for a project (Manager only)
    Files are saved to disk and metadata stored in MongoDB
    """
    db = get_database()
    
    # Validate project ID
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
    
    uploaded_documents = []
    project_dir = get_project_upload_dir(project_id)
    
    for file in files:
        try:
            # Validate file
            if not file.filename:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Filename is required"
                )
            
            # Validate file extension
            validate_file_extension(file.filename)
            
            # Sanitize filename
            safe_filename = sanitize_filename(file.filename)
            
            # Generate unique filename
            file_extension = Path(safe_filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = project_dir / unique_filename
            
            # Read file content to get size (before saving)
            content = await file.read()
            await file.seek(0)  # Reset file pointer
            
            # Validate file size
            validate_file_size(len(content))
            
            # Save file to disk
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Extract text content from document
            extracted_text = None
            extracted_content = None
            
            try:
                logger.info(f"Extracting text from {file.filename}...")
                extracted_text = document_extractor.extract_text(
                    str(file_path), 
                    file.content_type or ""
                )
                
                # Check if extraction was successful (not an error message)
                if (extracted_text and 
                    len(extracted_text.strip()) > 10 and 
                    not extracted_text.startswith('[') and 
                    not extracted_text.startswith('[Error')):
                    
                    # Process with LLM to structure the content
                    logger.info(f"Processing content with {gemini_service.llm_type} LLM...")
                    extracted_content = gemini_service.extract_document_content(
                        extracted_text, 
                        file.filename
                    )
                    logger.info(f"Successfully processed {file.filename}")
                else:
                    # Log why we're not processing
                    if extracted_text and extracted_text.startswith('['):
                        logger.warning(f"Extraction failed for {file.filename}: {extracted_text[:100]}")
                        extracted_content = extracted_text  # Store the error message directly
                    else:
                        logger.warning(f"No text extracted from {file.filename}")
                        extracted_content = None
                    
            except Exception as e:
                logger.error(f"Error processing {file.filename}: {e}")
                extracted_content = f"[Error during document processing: {str(e)}]"
            
            # Create document metadata
            doc_id = ObjectId()
            document_data = {
                "_id": doc_id,
                "projectId": project_id,
                "startupId": current_user.startupId,
                "originalFilename": file.filename,
                "storedFilename": unique_filename,
                "filePath": str(file_path),
                "fileSize": file_path.stat().st_size,
                "contentType": file.content_type,
                "uploadedBy": str(current_user.id),
                "uploadedAt": datetime.utcnow(),
                "extractedContent": extracted_content  # Store extracted content
            }
            
            # Store in MongoDB
            result = await db.documents.insert_one(document_data)
            
            # Perform automatic document analysis
            try:
                from services.document_analysis_service import document_analysis_service
                
                # Run analysis in background
                analysis_result = await document_analysis_service.analyze_document(
                    project_id=project_id,
                    company_id=current_user.startupId,
                    lead_id=project_id,  # Using project_id as lead_id for now
                    document_content=extracted_content,
                    filename=file.filename
                )
                
                # Store analysis results
                await document_analysis_service.store_analysis(analysis_result)
                
                logger.info(f"Document analysis completed for {file.filename}")
                
            except Exception as analysis_error:
                logger.error(f"Error in document analysis: {analysis_error}")
                # Don't fail the upload if analysis fails
            
            # Store embeddings in ChromaDB if extraction was successful
            if extracted_content and not extracted_content.startswith('['):
                try:
                    # Get project-specific documents collection
                    docs_collection = project_data_service.get_project_documents_collection(
                        startup_id=current_user.startupId,
                        project_id=project_id
                    )
                    
                    # Chunk the text
                    chunks = chunk_text(extracted_content, chunk_size=1000, overlap=200)
                    
                    # Create IDs and metadata for each chunk
                    chunk_ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
                    chunk_metadatas = [{
                        "document_id": str(doc_id),
                        "filename": file.filename,
                        "chunk_index": i,
                        "project_id": project_id,
                        "startup_id": current_user.startupId,
                        "uploaded_at": datetime.utcnow().isoformat()
                    } for i in range(len(chunks))]
                    
                    # Store in ChromaDB
                    docs_collection.add(
                        documents=chunks,
                        ids=chunk_ids,
                        metadatas=chunk_metadatas
                    )
                    
                    logger.info(f"✅ Stored {len(chunks)} document chunks in ChromaDB for project {project_id}")
                        
                except Exception as embed_error:
                    logger.error(f"Error creating embeddings for {file.filename}: {embed_error}")
                    # Don't fail the upload if embeddings fail
                    pass
            
            # Add to project's documents array
            await db.projects.update_one(
                {"_id": ObjectId(project_id)},
                {
                    "$push": {"documents": str(result.inserted_id)},
                    "$set": {"updatedAt": datetime.utcnow()}
                }
            )
            
            uploaded_documents.append({
                "id": str(result.inserted_id),
                "filename": file.filename,
                "size": document_data["fileSize"],
                "uploadedAt": document_data["uploadedAt"].isoformat()
            })
            
        except Exception as e:
            # Clean up file if database operation fails
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error uploading {file.filename}: {str(e)}"
            )
    
    return {
        "message": f"Successfully uploaded {len(uploaded_documents)} document(s)",
        "documents": uploaded_documents
    }


@router.get("/project/{project_id}")
async def get_project_documents(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all documents for a specific project"""
    db = get_database()
    
    if not ObjectId.is_valid(project_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project ID format"
        )
    
    # Check if project exists and user has access
    project = await db.projects.find_one({
        "_id": ObjectId(project_id),
        "startupId": current_user.startupId
    })
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get all documents for this project
    documents_cursor = db.documents.find({
        "projectId": project_id,
        "startupId": current_user.startupId
    }).sort("uploadedAt", -1)
    
    documents = []
    async for doc in documents_cursor:
        # Get uploader name
        uploader = await db.users.find_one({"_id": ObjectId(doc["uploadedBy"])})
        uploader_name = uploader.get("name", "Unknown") if uploader else "Unknown"
        
        documents.append({
            "id": str(doc["_id"]),
            "filename": doc["originalFilename"],
            "size": doc["fileSize"],
            "contentType": doc["contentType"],
            "uploadedBy": uploader_name,
            "uploadedAt": doc["uploadedAt"].isoformat(),
            "extractedContent": doc.get("extractedContent")  # Include extracted content
        })
    
    return {
        "projectId": project_id,
        "totalDocuments": len(documents),
        "documents": documents
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_manager)
):
    """Delete a document (Manager only)"""
    db = get_database()
    
    if not ObjectId.is_valid(document_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )
    
    # Find document
    document = await db.documents.find_one({
        "_id": ObjectId(document_id),
        "startupId": current_user.startupId
    })
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete file from disk
    file_path = Path(document["filePath"])
    if file_path.exists():
        file_path.unlink()
    
    # Remove from project's documents array
    await db.projects.update_one(
        {"_id": ObjectId(document["projectId"])},
        {
            "$pull": {"documents": document_id},
            "$set": {"updatedAt": datetime.utcnow()}
        }
    )
    
    # Delete from database
    await db.documents.delete_one({"_id": ObjectId(document_id)})
    
    return {"message": "Document deleted successfully"}


@router.get("/download/{document_id}")
async def download_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Download a document"""
    from fastapi.responses import FileResponse
    
    db = get_database()
    
    if not ObjectId.is_valid(document_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )
    
    # Find document
    document = await db.documents.find_one({
        "_id": ObjectId(document_id),
        "startupId": current_user.startupId
    })
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if file exists
    file_path = Path(document["filePath"])
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )
    
    return FileResponse(
        path=str(file_path),
        filename=document["originalFilename"],
        media_type=document["contentType"]
    )


@router.get("/analysis/{project_id}")
async def get_document_analysis(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get document analysis results for a project"""
    try:
        from services.document_analysis_service import document_analysis_service
        
        # Check if project exists and user has access
        db = get_database()
        project = await db.projects.find_one({
            "_id": ObjectId(project_id),
            "$or": [
                {"startupId": current_user.startupId},  # Manager access
                {"teamLeadId": str(current_user.id)}   # Team lead access
            ]
        })
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied"
            )
        
        # Get analysis results
        analyses = await document_analysis_service.get_document_analysis(project_id)
        
        return {
            "project_id": project_id,
            "analyses": analyses,
            "count": len(analyses)
        }
        
    except Exception as e:
        logger.error(f"Error getting document analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving analysis: {str(e)}"
        )
