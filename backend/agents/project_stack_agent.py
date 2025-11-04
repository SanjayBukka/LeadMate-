"""
Project Stack Agent
Redesigned to be project-centric - uses project's documents to recommend tech stack
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


class ProjectStackAgent:
    """
    Stack Agent scoped to a specific project
    Uses only project's documents to recommend technology stacks
    """
    
    def __init__(self, startup_id: str, project_id: str):
        """
        Initialize Stack Agent for a specific project
        
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
        self.iterations_collection = project_data_service.get_project_stack_iterations_collection(
            startup_id, project_id
        )
        
        # Initialize LLM
        try:
            self.llm = gemini_service.get_llm()
            logger.info(f"✅ Project Stack Agent initialized for project {project_id}")
        except Exception as e:
            self.llm = None
            logger.error(f"⚠️ LLM initialization failed: {e}")
        
        # Create CrewAI agent
        self.agent = self._create_agent()
    
    def _create_agent(self):
        """Create Stack Recommendation Agent"""
        if not self.llm:
            return None
            
        return Agent(
            role='Technology Stack Architect',
            goal=f'''Analyze project {self.project_id} requirements and recommend optimal 
                    technology stacks. Consider scalability, performance, team skills, and budget.''',
            backstory='''You are a senior technology architect with 15+ years of experience 
                        selecting optimal tech stacks for projects. You excel at analyzing 
                        requirements and recommending technologies that balance performance, 
                        scalability, developer experience, and cost.''',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def get_project_context(self, query: str = "technology stack requirements features", n_results: int = 10) -> List[str]:
        """Get project's document context"""
        try:
            results = self.docs_collection.query(
                query_texts=[query],
                n_results=min(n_results, self.docs_collection.count())
            )
            return results['documents'][0] if results['documents'] else []
        except Exception as e:
            logger.error(f"Error getting project context: {e}")
            return []
    
    async def recommend_stack(self, team_lead_feedback: Optional[str] = None) -> Dict:
        """
        Recommend technology stack for this project
        
        Args:
            team_lead_feedback: Optional feedback from team lead for iteration
            
        Returns:
            Stack recommendation dictionary
        """
        try:
            # Get project documents
            context_docs = self.get_project_context(n_results=15)
            context = "\n\n".join(context_docs) if context_docs else "No documents available."
            
            # Get previous iterations if any
            iterations = self.get_iterations()
            previous_iterations = ""
            if iterations:
                previous_iterations = "\n\nPrevious recommendations:\n"
                for iter in iterations[-2:]:  # Last 2 iterations
                    previous_iterations += f"- {iter.get('stack_summary', '')}\n"
            
            feedback_context = f"\n\nTeam Lead Feedback: {team_lead_feedback}" if team_lead_feedback else ""
            
            # Create task
            task = Task(
                description=f'''Based on project {self.project_id} requirements:
                               
                               {context}
                               {previous_iterations}
                               {feedback_context}
                               
                               Recommend a comprehensive technology stack including:
                               1. Frontend framework
                               2. Backend framework
                               3. Database(s)
                               4. Cloud infrastructure
                               5. DevOps tools
                               6. Testing frameworks
                               7. Authentication/Authorization
                               8. API design approach
                               9. Third-party services
                               10. Development tools
                               
                               Provide reasoning for each choice and consider:
                               - Project requirements
                               - Scalability needs
                               - Team expertise
                               - Budget constraints
                               - Future maintenance
                               
                               Format the response as structured JSON.''',
                expected_output='''A detailed technology stack recommendation in JSON format 
                                  with categories and reasoning for each technology choice.''',
                agent=self.agent
            )
            
            # Execute task
            crew = Crew(
                agents=[self.agent],
                tasks=[task],
                verbose=False,
                process=Process.sequential
            )
            
            result = crew.kickoff()
            response_text = str(result)
            
            # Try to parse JSON from response
            try:
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    stack_data = json.loads(json_match.group())
                else:
                    stack_data = {"raw_response": response_text}
            except:
                stack_data = {"raw_response": response_text}
            
            # Store iteration
            iteration_id = str(uuid.uuid4())
            self.iterations_collection.add(
                documents=[response_text],
                ids=[iteration_id],
                metadatas=[{
                    "project_id": self.project_id,
                    "startup_id": self.startup_id,
                    "iteration_number": len(iterations) + 1,
                    "timestamp": datetime.utcnow().isoformat(),
                    "has_feedback": bool(team_lead_feedback)
                }]
            )
            
            # Store final stack in MongoDB if this is the approved version
            if not team_lead_feedback:  # First recommendation
                await self._save_final_stack(stack_data, response_text)
            
            return {
                "iteration_id": iteration_id,
                "stack_recommendation": stack_data,
                "project_id": self.project_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error recommending stack: {e}")
            return {
                "error": str(e),
                "project_id": self.project_id
            }
    
    async def _save_final_stack(self, stack_data: Dict, full_response: str):
        """Save final stack to MongoDB"""
        try:
            db = get_database()
            tech_stack_doc = {
                "projectId": self.project_id,
                "startupId": self.startup_id,
                "recommendations": stack_data,
                "fullResponse": full_response,
                "createdAt": datetime.utcnow(),
                "status": "draft"
            }
            
            result = await db.tech_stacks.insert_one(tech_stack_doc)
            
            # Update project with tech stack reference
            await db.projects.update_one(
                {"_id": ObjectId(self.project_id)},
                {"$set": {
                    "techStackId": str(result.inserted_id),
                    "updatedAt": datetime.utcnow()
                }}
            )
            
            logger.info(f"✅ Saved tech stack for project {self.project_id}")
        except Exception as e:
            logger.error(f"Error saving tech stack: {e}")
    
    def get_iterations(self) -> List[Dict]:
        """Get all stack iterations for this project"""
        try:
            results = self.iterations_collection.get()
            
            iterations = []
            for doc, metadata in zip(
                results.get('documents', []),
                results.get('metadatas', [])
            ):
                iterations.append({
                    "iteration_number": metadata.get("iteration_number", 0),
                    "stack_summary": doc[:200] + "..." if len(doc) > 200 else doc,
                    "timestamp": metadata.get("timestamp"),
                    "has_feedback": metadata.get("has_feedback", False)
                })
            
            return sorted(iterations, key=lambda x: x.get("iteration_number", 0))
        except Exception as e:
            logger.error(f"Error getting iterations: {e}")
            return []

