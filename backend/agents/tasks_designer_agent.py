"""
Tasks Designer Agent
Creates project tasks based on project documents, tech stack, and team formation
Project-centric design
"""
import logging
import json
import uuid
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from crewai import Agent, Task, Crew, Process
from services.gemini_service import gemini_service
from services.project_data_service import project_data_service
from database import get_database
from bson import ObjectId

logger = logging.getLogger(__name__)


class TasksDesignerAgent:
    """
    Tasks Designer Agent scoped to a specific project
    Uses project's documents, tech stack, and team formation to generate tasks
    """
    
    def __init__(self, startup_id: str, project_id: str):
        """
        Initialize Tasks Designer Agent for a specific project
        
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
        
        # Initialize LLM
        try:
            self.llm = gemini_service.get_llm()
            logger.info(f"✅ Tasks Designer Agent initialized for project {project_id}")
        except Exception as e:
            self.llm = None
            logger.error(f"⚠️ LLM initialization failed: {e}")
        
        # Create CrewAI agent
        self.agent = self._create_agent()
    
    def _create_agent(self):
        """Create Tasks Designer Agent"""
        if not self.llm:
            return None
            
        return Agent(
            role='Project Tasks Designer',
            goal=f'''Design comprehensive, actionable tasks for project {self.project_id} based on 
                    requirements, tech stack, and team composition. Break down work into manageable 
                    tasks with clear assignments and timelines.''',
            backstory='''You are an expert project manager and task designer with 15+ years of 
                        experience breaking down complex projects into actionable tasks. You excel 
                        at identifying dependencies, estimating effort, and assigning tasks based on 
                        team member skills and availability.''',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    async def get_project_context(self) -> Dict:
        """Get all project context needed for task generation"""
        try:
            # Get project documents
            context_docs = self.docs_collection.query(
                query_texts=["project requirements tasks objectives features deliverables"],
                n_results=min(15, self.docs_collection.count())
            )
            documents = "\n\n".join(context_docs['documents'][0]) if context_docs['documents'] else ""
            
            # Get tech stack
            db = get_database()
            project = await db.projects.find_one({"_id": ObjectId(self.project_id)})
            tech_stack = {}
            if project and project.get("techStackId"):
                tech_stack_doc = await db.tech_stacks.find_one({"_id": ObjectId(project["techStackId"])})
                if tech_stack_doc:
                    tech_stack = tech_stack_doc.get("recommendations", {})
            
            # Get team formation
            team_formation = {}
            if project and project.get("teamFormationId"):
                team_doc = await db.team_formations.find_one({"_id": ObjectId(project["teamFormationId"])})
                if team_doc:
                    team_formation = team_doc.get("teamRecommendation", {})
            
            # Get existing tasks
            existing_tasks = await db.tasks.find({"projectId": self.project_id}).to_list(length=50)
            existing_tasks_list = [
                {"title": t.get("title"), "status": t.get("status")}
                for t in existing_tasks
            ]
            
            return {
                "documents": documents,
                "tech_stack": tech_stack,
                "team_formation": team_formation,
                "existing_tasks": existing_tasks_list
            }
        except Exception as e:
            logger.error(f"Error getting project context: {e}")
            return {}
    
    async def generate_tasks(self) -> Dict:
        """
        Generate tasks for this project
        
        Returns:
            Generated tasks dictionary
        """
        try:
            # Get project context
            context = await self.get_project_context()
            
            if not context.get("documents"):
                return {
                    "error": "No project documents found. Please upload project documents first.",
                    "project_id": self.project_id
                }
            
            # Format context for task generation
            tech_stack_str = json.dumps(context.get("tech_stack", {}), indent=2)
            team_str = json.dumps(context.get("team_formation", {}), indent=2)
            existing_tasks_str = json.dumps(context.get("existing_tasks", []), indent=2)
            
            # Create task generation task
            task = Task(
                description=f'''Based on project {self.project_id}:
                               
                               Project Requirements:
                               {context.get('documents', '')}
                               
                               Technology Stack:
                               {tech_stack_str}
                               
                               Team Composition:
                               {team_str}
                               
                               Existing Tasks:
                               {existing_tasks_str}
                               
                               Generate comprehensive project tasks including:
                               1. Task breakdown by phase/sprint
                               2. Task titles and descriptions
                               3. Assignments to team members (based on skills)
                               4. Priority levels (High, Medium, Low)
                               5. Estimated effort (hours/days)
                               6. Dependencies between tasks
                               7. Suggested deadlines
                               8. Required skills for each task
                               
                               Ensure tasks are:
                               - Specific and actionable
                               - Properly sequenced (dependencies considered)
                               - Realistically estimated
                               - Assigned based on team member skills
                               - Covering all major project components
                               
                               Format as JSON array of tasks.''',
                expected_output='''A comprehensive list of project tasks in JSON format with 
                                  all required fields (title, description, assignee, priority, 
                                  effort, dependencies, deadline).''',
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
            
            # Try to parse JSON
            try:
                import re
                # Try to find JSON array
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    tasks_list = json.loads(json_match.group())
                else:
                    # Try to find JSON object
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        data = json.loads(json_match.group())
                        tasks_list = data.get("tasks", [])
                    else:
                        tasks_list = []
            except Exception as e:
                logger.error(f"Error parsing tasks JSON: {e}")
                tasks_list = []
            
            # Save tasks to MongoDB
            saved_tasks = await self._save_tasks(tasks_list)
            
            return {
                "project_id": self.project_id,
                "tasks_generated": len(saved_tasks),
                "tasks": saved_tasks,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating tasks: {e}")
            return {
                "error": str(e),
                "project_id": self.project_id
            }
    
    async def _save_tasks(self, tasks_list: List[Dict]) -> List[Dict]:
        """Save generated tasks to MongoDB"""
        saved_tasks = []
        
        try:
            db = get_database()
            
            for task_data in tasks_list:
                # Create task document
                task_doc = {
                    "projectId": self.project_id,
                    "startupId": self.startup_id,
                    "title": task_data.get("title", "Untitled Task"),
                    "description": task_data.get("description", ""),
                    "assignedTo": task_data.get("assignedTo"),  # Team member ID or name
                    "status": "pending",
                    "priority": task_data.get("priority", "medium").lower(),
                    "estimatedEffort": task_data.get("estimatedEffort", ""),
                    "deadline": None,  # Parse if provided
                    "dependencies": task_data.get("dependencies", []),
                    "requiredSkills": task_data.get("requiredSkills", []),
                    "createdAt": datetime.utcnow(),
                    "updatedAt": datetime.utcnow()
                }
                
                # Parse deadline if provided
                if task_data.get("deadline"):
                    try:
                        task_doc["deadline"] = datetime.fromisoformat(task_data["deadline"].replace('Z', '+00:00'))
                    except:
                        pass
                
                result = await db.tasks.insert_one(task_doc)
                saved_tasks.append({
                    "id": str(result.inserted_id),
                    "title": task_doc["title"],
                    "status": task_doc["status"]
                })
            
            logger.info(f"✅ Saved {len(saved_tasks)} tasks for project {self.project_id}")
            
        except Exception as e:
            logger.error(f"Error saving tasks: {e}")
        
        return saved_tasks
    
    async def get_project_tasks(self) -> List[Dict]:
        """Get all tasks for this project"""
        try:
            db = get_database()
            cursor = db.tasks.find({"projectId": self.project_id}).sort("createdAt", -1)
            tasks = []
            async for task in cursor:
                tasks.append({
                    "id": str(task["_id"]),
                    "title": task.get("title"),
                    "description": task.get("description"),
                    "status": task.get("status"),
                    "priority": task.get("priority"),
                    "assignedTo": task.get("assignedTo"),
                    "deadline": task.get("deadline").isoformat() if task.get("deadline") else None
                })
            return tasks
        except Exception as e:
            logger.error(f"Error getting tasks: {e}")
            return []

