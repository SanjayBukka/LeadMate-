from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
import logging
from pathlib import Path
try:
    # Load environment variables from backend/.env if present
    from dotenv import load_dotenv  # type: ignore
    # Try local .env in the backend directory
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=str(env_path))
    else:
        # Fallback to default search (current working directory)
        load_dotenv()
except Exception:
    # dotenv is optional; proceed if not installed
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the backend models to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend models'))

# Import database
from database import connect_to_mongodb, close_mongodb_connection

# Import routers
from routers import documents, team, stack, assistant
from routers.auth import router as auth_router
from routers.projects import router as projects_router
from routers.notifications import router as notifications_router
from routers.doc_agent import router as doc_agent_router
from routers.team_members import router as team_members_router
from routers.agents import router as agents_router
from routers.workflow import router as workflow_router
from routers.reports import router as reports_router
from routers.notifications_ws import router as notifications_ws_router
from routers.team_formation import router as team_formation_router
from routers.mongodb_agents import router as mongodb_agents_router # NEW MongoDB Agents
from routers.document_sync import router as document_sync_router  # Document sync endpoints
from routers.project_agents import router as project_agents_router  # Project-centric agents
from routers.management import router as management_router  # Team Lead Management endpoints
from routes.management_routes import router as management_legacy_router  # Legacy workflow-style endpoints

app = FastAPI(title="LeadMate API", version="1.0.0")

# Startup event - Connect to MongoDB
@app.on_event("startup")
async def startup_db_client():
    """Connect to MongoDB on startup"""
    try:
        await connect_to_mongodb()
        logger.info("✅ LeadMate API Started Successfully")
    except Exception as e:
        logger.error(f"❌ Failed to start API: {e}")
        raise

# Shutdown event - Close MongoDB connection
@app.on_event("shutdown")
async def shutdown_db_client():
    """Close MongoDB connection on shutdown"""
    await close_mongodb_connection()
    logger.info("✅ LeadMate API Shutdown Complete")

# Add error handler middleware (must be first)
from middleware.error_handler import error_handler_middleware
app.middleware("http")(error_handler_middleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:5174",
        "http://localhost:5175"  # In case Vite uses another port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)  # Authentication and user management
app.include_router(projects_router)  # Project management
app.include_router(notifications_router)  # Notifications
app.include_router(doc_agent_router)  # DocAgent - Document Analysis & Q&A
app.include_router(team_members_router)  # Team Members Management
app.include_router(agents_router)  # NEW: Multi-Agent System (Document + Stack Agents)
app.include_router(workflow_router)  # Workflow - Git Repository Analysis
app.include_router(reports_router)  # Reports - Progress Reports & Analytics
app.include_router(notifications_ws_router)  # WebSocket - Real-time Notifications
app.include_router(team_formation_router)  # Team Formation - CrewAI Orchestration
app.include_router(mongodb_agents_router)  # MongoDB Agents - New Vector Search System # NEW
app.include_router(document_sync_router)  # Document sync endpoints
app.include_router(project_agents_router)  # Project-centric agents (NEW)
app.include_router(management_router)  # Management dashboard analysis
app.include_router(management_legacy_router)  # Legacy workflow routes (/api/workflow/*)
app.include_router(documents.router)
app.include_router(team.router)
app.include_router(stack.router)
app.include_router(assistant.router)

@app.get("/")
async def root():
    return {
        "message": "LeadMate API is running!",
        "version": "1.0.0",
        "status": "healthy",
        "database": "connected"
    }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)