from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import sys
import uuid

# Add backend models to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend models', 'Team'))

# Import Team Formation Agent with error handling
try:
    from agents.team_formation_agent import TeamFormationAgent
    TEAM_AGENT_AVAILABLE = True
except Exception as e:
    print(f"Warning: Team Formation Agent not available: {e}")
    TEAM_AGENT_AVAILABLE = False

router = APIRouter(prefix="/api/team", tags=["team"])

class TeamMember(BaseModel):
    id: str
    name: str
    email: str
    skills: Dict[str, List[str]]
    experience_years: int

class TeamMemberResponse(BaseModel):
    member: TeamMember
    status: str

class TeamFormationRequest(BaseModel):
    project_id: str
    required_skills: List[str]

class TeamFormationResponse(BaseModel):
    team_members: List[TeamMember]
    team_lead: TeamMember
    skill_gaps: List[str]
    recommendations: List[str]

@router.post("/upload-resume", response_model=TeamMemberResponse)
async def upload_resume(file: UploadFile = File(...)):
    """Upload and process a team member's resume"""
    if TEAM_AGENT_AVAILABLE and team_system:
        try:
            # Read file content
            file_content = await file.read()
            
            # Create a file-like object for the team system
            import io
            file_obj = io.BytesIO(file_content)
            file_obj.name = file.filename
            
            # Extract text from PDF
            resume_text = team_system.extract_text_from_pdf(file_obj)
            
            if resume_text:
                # Extract skills using LLM
                member_data = team_system.extract_skills_from_resume(resume_text, file.filename or "unknown")
                member_data["filename"] = file.filename
                
                if "error" not in member_data:
                    # Store in ChromaDB
                    member_id = team_system.store_team_member(member_data, resume_text)
                    
                    if member_id:
                        # Return processed member data
                        return TeamMemberResponse(
                            member=TeamMember(
                                id=member_id,
                                name=member_data.get("name", "Unknown"),
                                email=member_data.get("email", ""),
                                skills=member_data.get("skills", {}),
                                experience_years=member_data.get("experience_years", 0)
                            ),
                            status="processed"
                        )
                    else:
                        raise HTTPException(status_code=500, detail="Failed to store team member")
                else:
                    raise HTTPException(status_code=500, detail=member_data.get("error", "Failed to parse resume"))
            else:
                raise HTTPException(status_code=400, detail="No text extracted from resume")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")
    else:
        # Mock response if Team Formation Agent is not available
        mock_member = TeamMember(
            id=str(uuid.uuid4()),
            name="John Doe",
            email="john.doe@example.com",
            skills={
                "programming_languages": ["Python", "JavaScript"],
                "frameworks": ["FastAPI", "React"],
                "databases": ["PostgreSQL", "MongoDB"]
            },
            experience_years=5
        )
        
        return TeamMemberResponse(
            member=mock_member,
            status="processed"
        )

@router.post("/form-team", response_model=TeamFormationResponse)
async def form_team(request: TeamFormationRequest):
    """Form a team based on project requirements"""
    if TEAM_AGENT_AVAILABLE and team_system:
        try:
            # Load project requirements and tech stack
            project_info = team_system.load_project_requirements()
            tech_stack = team_system.load_tech_stack()
            team_members = team_system.get_all_team_members()
            
            if team_members:
                # Create and run CrewAI analysis
                crew = team_system.create_team_formation_crew(project_info, tech_stack, team_members)
                result = crew.kickoff()
                
                # For now, return mock data since we need to parse the CrewAI result
                # In a full implementation, we would parse the result and extract team formation data
                mock_member1 = TeamMember(
                    id=str(uuid.uuid4()),
                    name="Alice Developer",
                    email="alice@example.com",
                    skills={
                        "programming_languages": ["Python", "JavaScript"],
                        "frameworks": ["FastAPI", "React"],
                        "databases": ["PostgreSQL"]
                    },
                    experience_years=3
                )
                
                mock_member2 = TeamMember(
                    id=str(uuid.uuid4()),
                    name="Bob Engineer",
                    email="bob@example.com",
                    skills={
                        "programming_languages": ["Java", "Python"],
                        "frameworks": ["Spring", "Django"],
                        "databases": ["MySQL", "MongoDB"]
                    },
                    experience_years=5
                )
                
                return TeamFormationResponse(
                    team_members=[mock_member1, mock_member2],
                    team_lead=mock_member1,
                    skill_gaps=["DevOps", "Cloud Architecture"],
                    recommendations=["Consider hiring a DevOps engineer", "Provide cloud training to existing team"]
                )
            else:
                raise HTTPException(status_code=400, detail="No team members available")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error forming team: {str(e)}")
    else:
        # Mock response if Team Formation Agent is not available
        mock_member1 = TeamMember(
            id=str(uuid.uuid4()),
            name="Alice Developer",
            email="alice@example.com",
            skills={
                "programming_languages": ["Python", "JavaScript"],
                "frameworks": ["FastAPI", "React"],
                "databases": ["PostgreSQL"]
            },
            experience_years=3
        )
        
        mock_member2 = TeamMember(
            id=str(uuid.uuid4()),
            name="Bob Engineer",
            email="bob@example.com",
            skills={
                "programming_languages": ["Java", "Python"],
                "frameworks": ["Spring", "Django"],
                "databases": ["MySQL", "MongoDB"]
            },
            experience_years=5
        )
        
        return TeamFormationResponse(
            team_members=[mock_member1, mock_member2],
            team_lead=mock_member1,
            skill_gaps=["DevOps", "Cloud Architecture"],
            recommendations=["Consider hiring a DevOps engineer", "Provide cloud training to existing team"]
        )