"""
Team Formation Agent Router
Handles team formation analysis and recommendations
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from agents.team_formation_agent import TeamFormationAgent
from routers.auth import get_current_user

router = APIRouter(prefix="/api/team-formation", tags=["Team Formation"])

# Pydantic models
class TeamFormationRequest(BaseModel):
    company_id: str
    lead_id: str
    project_requirements: str
    available_team_members: List[Dict[str, Any]]

class TeamFormationResponse(BaseModel):
    success: bool
    analysis_id: Optional[str] = None
    recommendations: Optional[str] = None
    error: Optional[str] = None
    timestamp: str

class ChatRequest(BaseModel):
    company_id: str
    lead_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    agent: str
    timestamp: str
    chat_id: Optional[str] = None

class TeamAnalysisRequest(BaseModel):
    company_id: str
    lead_id: str

class TeamAnalysisResponse(BaseModel):
    success: bool
    analyses: List[Dict[str, Any]] = []
    error: Optional[str] = None

# Helper function to get team formation agent
def get_team_formation_agent(company_id: str, lead_id: str) -> TeamFormationAgent:
    """Get or create team formation agent instance"""
    return TeamFormationAgent(company_id, lead_id)

@router.post("/analyze", response_model=TeamFormationResponse)
async def analyze_team_formation(request: TeamFormationRequest):
    """Analyze team formation based on project requirements and available members"""
    try:
        agent = get_team_formation_agent(request.company_id, request.lead_id)
        result = agent.analyze_team_formation(
            request.project_requirements,
            request.available_team_members
        )
        
        return TeamFormationResponse(
            success=result["success"],
            analysis_id=result.get("analysis_id"),
            recommendations=result.get("recommendations"),
            error=result.get("error"),
            timestamp=result["timestamp"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", response_model=ChatResponse)
async def chat_with_team_formation_agent(request: ChatRequest):
    """Chat with Team Formation Agent about team building"""
    try:
        agent = get_team_formation_agent(request.company_id, request.lead_id)
        result = agent.chat_with_agent(request.message)
        
        return ChatResponse(
            response=result["response"],
            agent=result["agent"],
            timestamp=result["timestamp"],
            chat_id=result.get("chat_id")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analyses/{company_id}/{lead_id}", response_model=TeamAnalysisResponse)
async def get_team_analyses(company_id: str, lead_id: str):
    """Get all team formation analyses for a lead"""
    try:
        agent = get_team_formation_agent(company_id, lead_id)
        analyses = agent.get_team_analyses()
        
        return TeamAnalysisResponse(
            success=True,
            analyses=analyses
        )
    except Exception as e:
        return TeamAnalysisResponse(
            success=False,
            error=str(e)
        )

@router.get("/health")
async def health_check():
    """Health check for team formation agent"""
    return {"status": "healthy", "agent": "Team Formation Agent"}
