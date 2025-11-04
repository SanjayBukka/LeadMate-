"""
Project Team Formation Agent
Redesigned to be project-centric - uses project's documents and resumes
"""
import logging
import json
import uuid
from typing import Dict, List, Optional
from datetime import datetime
from crewai import Agent, Task, Crew, Process
from services.gemini_service import gemini_service
from services.project_data_service import project_data_service
from database import get_database
from bson import ObjectId

logger = logging.getLogger(__name__)


class ProjectTeamFormationAgent:
    """
    Team Formation Agent scoped to a specific project
    Uses project's documents, resumes, and tech stack to form optimal teams
    """
    
    def __init__(self, startup_id: str, project_id: str):
        """
        Initialize Team Formation Agent for a specific project
        
        Args:
            startup_id: Startup identifier
            project_id: Project identifier (REQUIRED)
        """
        self.startup_id = startup_id
        self.project_id = project_id
        
        # Get project-specific collections
        self.docs_collection = project_data_service.get_project_documents_collection(
            startup_id, project_id
        )
        self.resumes_collection = project_data_service.get_project_resumes_collection(
            startup_id, project_id
        )
        self.team_formation_collection = project_data_service.get_project_team_formation_collection(
            startup_id, project_id
        )
        
        # Initialize LLM
        try:
            self.llm = gemini_service.get_llm()
            logger.info(f"✅ Project Team Formation Agent initialized for project {project_id}")
        except Exception as e:
            self.llm = None
            logger.error(f"⚠️ LLM initialization failed: {e}")
        
        # Create CrewAI agents
        self.team_analyst = self._create_team_analyst()
        self.skills_matcher = self._create_skills_matcher()
    
    def _create_team_analyst(self):
        """Create Team Analyst Agent"""
        if not self.llm:
            return None
            
        return Agent(
            role='Team Composition Analyst',
            goal=f'''Analyze team composition for project {self.project_id} based on 
                    requirements and available candidates. Recommend optimal team structure.''',
            backstory='''You are an expert team analyst with 15+ years of experience in 
                        organizational psychology and team dynamics. You excel at matching 
                        skills to project needs and forming high-performing teams.''',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def _create_skills_matcher(self):
        """Create Skills Matcher Agent"""
        if not self.llm:
            return None
            
        return Agent(
            role='Technical Skills Matcher',
            goal=f'''Match candidate skills to project {self.project_id} technical requirements 
                    and recommend role assignments.''',
            backstory='''You are a technical recruitment specialist with deep knowledge of 
                        software development roles and required skills. You excel at identifying 
                        skill gaps and recommending training or hiring strategies.''',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    async def get_project_requirements(self) -> str:
        """Get project requirements from documents"""
        try:
            # Query documents for requirements
            context_docs = self.docs_collection.query(
                query_texts=["project requirements objectives features functionality"],
                n_results=min(10, self.docs_collection.count())
            )
            return "\n\n".join(context_docs['documents'][0]) if context_docs['documents'] else "No requirements documents found."
        except Exception as e:
            logger.error(f"Error getting requirements: {e}")
            return ""
    
    async def get_project_tech_stack(self) -> Dict:
        """Get tech stack for this project"""
        try:
            db = get_database()
            project = await db.projects.find_one({"_id": ObjectId(self.project_id)})
            
            if project and project.get("techStackId"):
                tech_stack = await db.tech_stacks.find_one({"_id": ObjectId(project["techStackId"])})
                if tech_stack:
                    return tech_stack.get("recommendations", {})
            
            return {}
        except Exception as e:
            logger.error(f"Error getting tech stack: {e}")
            return {}
    
    async def get_available_resumes(self) -> List[Dict]:
        """Get all resumes for this project"""
        try:
            # Get from MongoDB first (more reliable)
            db = get_database()
            cursor = db.team_members.find({"projectId": self.project_id})
            resumes = []
            async for member in cursor:
                resumes.append({
                    "id": str(member["_id"]),
                    "name": member.get("name", "Unknown"),
                    "email": member.get("email"),
                    "techStack": member.get("techStack", []),
                    "skills": member.get("skills", {}),
                    "experience": member.get("experience"),
                    "education": member.get("education", []),
                    "recentProjects": member.get("recentProjects", [])
                })
            
            # Also try to get from ChromaDB for additional context
            try:
                results = self.resumes_collection.get()
                # Use ChromaDB data to enrich if available
                for doc, metadata in zip(
                    results.get('documents', []),
                    results.get('metadatas', [])
                ):
                    try:
                        resume_data = json.loads(doc) if isinstance(doc, str) else doc
                        # Match with MongoDB data and enrich
                        for resume in resumes:
                            if resume.get("name") == resume_data.get("name"):
                                resume.update(resume_data)
                                break
                    except:
                        pass
            except:
                pass  # ChromaDB is optional, MongoDB is source of truth
            
            return resumes
        except Exception as e:
            logger.error(f"Error getting resumes: {e}")
            return []
    
    async def form_team(self) -> Dict:
        """
        Form optimal team for this project
        
        Returns:
            Team formation recommendation
        """
        try:
            # Get all project data
            requirements = await self.get_project_requirements()
            tech_stack = await self.get_project_tech_stack()
            resumes = await self.get_available_resumes()
            
            if not resumes:
                return {
                    "error": "No resumes available for this project",
                    "project_id": self.project_id
                }
            
            # Format resumes for context
            resumes_context = ""
            for i, resume in enumerate(resumes[:10]):  # Limit to 10 resumes
                resumes_context += f"\n\nResume {i+1}:\n{json.dumps(resume, indent=2)}"
            
            tech_stack_context = json.dumps(tech_stack, indent=2) if tech_stack else "Tech stack not yet determined."
            
            # Create team formation task
            task = Task(
                description=f'''Based on project {self.project_id}:
                               
                               Requirements:
                               {requirements}
                               
                               Technology Stack:
                               {tech_stack_context}
                               
                               Available Candidates:
                               {resumes_context}
                               
                               Recommend an optimal team composition:
                               1. Team structure and roles needed
                               2. Candidate assignments to roles
                               3. Skill gaps and recommendations
                               4. Team hierarchy and reporting
                               5. Communication structure
                               
                               Provide reasoning for each assignment and identify any missing roles.''',
                expected_output='''A detailed team formation recommendation with role assignments, 
                                  skill matching, and gap analysis in JSON format.''',
                agent=self.team_analyst
            )
            
            # Execute task
            crew = Crew(
                agents=[self.team_analyst, self.skills_matcher],
                tasks=[task],
                verbose=False,
                process=Process.sequential
            )
            
            result = crew.kickoff()
            response_text = str(result)
            
            # Try to parse JSON
            try:
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    team_data = json.loads(json_match.group())
                else:
                    team_data = {"raw_response": response_text}
            except:
                team_data = {"raw_response": response_text}
            
            # Store team formation
            formation_id = str(uuid.uuid4())
            self.team_formation_collection.add(
                documents=[response_text],
                ids=[formation_id],
                metadatas=[{
                    "project_id": self.project_id,
                    "startup_id": self.startup_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "team_size": len(resumes)
                }]
            )
            
            # Save to MongoDB
            await self._save_team_formation(team_data, response_text)
            
            return {
                "formation_id": formation_id,
                "team_recommendation": team_data,
                "project_id": self.project_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error forming team: {e}")
            return {
                "error": str(e),
                "project_id": self.project_id
            }
    
    async def _save_team_formation(self, team_data: Dict, full_response: str):
        """Save team formation to MongoDB"""
        try:
            db = get_database()
            formation_doc = {
                "projectId": self.project_id,
                "startupId": self.startup_id,
                "teamRecommendation": team_data,
                "fullResponse": full_response,
                "createdAt": datetime.utcnow(),
                "status": "draft"
            }
            
            result = await db.team_formations.insert_one(formation_doc)
            
            # Update project with team formation reference
            await db.projects.update_one(
                {"_id": ObjectId(self.project_id)},
                {"$set": {
                    "teamFormationId": str(result.inserted_id),
                    "updatedAt": datetime.utcnow()
                }}
            )
            
            logger.info(f"✅ Saved team formation for project {self.project_id}")
        except Exception as e:
            logger.error(f"Error saving team formation: {e}")

