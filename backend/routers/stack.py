from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import sys
import uuid

# Add backend models to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend models', 'stack'))

# Import Stack Agent with error handling
try:
    from agents.stack_agent import StackAgent
    STACK_AGENT_AVAILABLE = True
except Exception as e:
    print(f"Warning: Stack Agent not available: {e}")
    STACK_AGENT_AVAILABLE = False

router = APIRouter(prefix="/api/stack", tags=["stack"])

class StackRecommendationRequest(BaseModel):
    project_type: str
    requirements: List[str]
    team_skills: List[str]

class TechnologyStack(BaseModel):
    frontend: List[str]
    backend: List[str]
    database: List[str]
    infrastructure: List[str]
    monitoring: List[str]

class StackRecommendationResponse(BaseModel):
    stack: TechnologyStack
    reasoning: str
    alternatives: List[str]

class StackQueryRequest(BaseModel):
    query: str

class StackQueryResponse(BaseModel):
    results: List[str]

@router.post("/recommend", response_model=StackRecommendationResponse)
async def recommend_stack(request: StackRecommendationRequest):
    """Recommend technology stack based on project requirements"""
    # This will integrate with the actual Stack Agent
    mock_stack = TechnologyStack(
        frontend=["React", "TypeScript", "Tailwind CSS"],
        backend=["FastAPI", "Python"],
        database=["PostgreSQL"],
        infrastructure=["Docker", "Kubernetes"],
        monitoring=["Prometheus", "Grafana"]
    )
    
    return StackRecommendationResponse(
        stack=mock_stack,
        reasoning="Recommended based on modern web development practices and team skills.",
        alternatives=["Consider Node.js/Express for backend if team prefers JavaScript"]
    )

@router.post("/query", response_model=StackQueryResponse)
async def query_stack_knowledge(request: StackQueryRequest):
    """Query stack knowledge base"""
    # This will integrate with the actual Stack Agent
    return StackQueryResponse(
        results=[
            "React is recommended for frontend due to its component-based architecture",
            "FastAPI is recommended for backend due to its performance and type safety",
            "PostgreSQL is recommended for database due to its reliability and features"
        ]
    )