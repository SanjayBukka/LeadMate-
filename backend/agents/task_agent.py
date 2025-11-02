"""
Task Agent - Generates project tasks based on requirements and team formation
"""
import os
import uuid
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import chromadb
from crewai import Agent, Task, Crew, Process
from services.gemini_service import gemini_service
import logging

logger = logging.getLogger(__name__)


class TaskAgent:
    """
    Task Agent analyzes project requirements and team formation to generate
    actionable tasks with assignments, priorities, and timelines.
    
    Links with:
    - Document Agent (for requirements)
    - Stack Agent (for team members and roles)
    """
    
    def __init__(self, company_id: str, lead_id: str, base_path: str = "./chroma_db"):
        self.company_id = company_id
        self.lead_id = lead_id
        self.base_path = Path(base_path)
        
        # Use same directory structure
        self.company_lead_path = self.base_path / f"company_{company_id}" / f"lead_{lead_id}"
        self.company_lead_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.company_lead_path)
        )
        
        # Get existing collections from other agents
        try:
            self.docs_collection = self.chroma_client.get_collection("documents")
            self.doc_chat_collection = self.chroma_client.get_collection("doc_chat")
            self.resumes_collection = self.chroma_client.get_collection("resumes")
            self.stack_iterations_collection = self.chroma_client.get_collection("stack_iterations")
        except:
            self.docs_collection = None
            self.doc_chat_collection = None
            self.resumes_collection = None
            self.stack_iterations_collection = None
        
        # Create tasks collection
        self.tasks_collection = self.chroma_client.get_or_create_collection(
            name="tasks",
            metadata={"description": "Project tasks generated from requirements"}
        )
        
        # Initialize LLM (Gemini with Ollama fallback)
        try:
            self.llm = gemini_service.get_llm()
            logger.info(f"✅ LLM initialized: {gemini_service.llm_type} ({gemini_service.model})")
        except Exception as e:
            self.llm = None
            logger.error(f"⚠️ LLM initialization failed: {e}. Using fallback logic.")
        
        # Create CrewAI agent
        self.agent = self._create_agent()
    
    def _create_agent(self):
        """Create Task Generation Agent with CrewAI"""
        if not self.llm:
            return None
            
        return Agent(
            role='Senior Project Manager & Task Planner',
            goal='''Break down project requirements into actionable tasks, assign them to 
                    appropriate team members based on their roles and skills, set realistic 
                    priorities and timelines. Create a comprehensive task breakdown that ensures 
                    project success.''',
            backstory='''You are an expert project manager with 15+ years of experience in 
                        software development. You excel at:
                        - Breaking down complex requirements into manageable tasks
                        - Understanding technical dependencies
                        - Assigning tasks to team members based on their expertise
                        - Setting realistic timelines and priorities
                        - Identifying critical path items
                        - Planning sprints and milestones
                        
                        You create detailed, actionable tasks that developers can immediately 
                        start working on. You understand Agile methodologies and know how to 
                        balance workload across team members.''',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def generate_tasks(self, project_name: str = "Project") -> Dict:
        """
        Generate comprehensive task breakdown based on:
        - Project documents (from Document Agent)
        - Requirements clarifications (from Document Agent chat)
        - Team composition (from Stack Agent)
        """
        try:
            # Get context from other agents
            project_context = self._get_project_context()
            team_info = self._get_team_info()
            
            if not team_info:
                return {"success": False, "error": "No team formed yet. Run Stack Agent first."}
            
            # Generate tasks using CrewAI
            if self.agent:
                task = Task(
                    description=f'''Generate a comprehensive task breakdown for the project.
                                   
                                   PROJECT REQUIREMENTS & CONTEXT:
                                   {project_context}
                                   
                                   TEAM COMPOSITION:
                                   {team_info}
                                   
                                   Generate tasks following these guidelines:
                                   
                                   1. **Comprehensive Coverage**: Break down ALL requirements into tasks
                                   2. **Appropriate Granularity**: Tasks should be 1-5 days of work
                                   3. **Clear Dependencies**: Order tasks logically
                                   4. **Balanced Assignment**: Distribute work across team members
                                   5. **Skill Matching**: Assign tasks to members with relevant skills
                                   6. **Realistic Timelines**: Set achievable due dates
                                   7. **Priority Setting**: Mark critical path items as high priority
                                   
                                   For each task, provide:
                                   - **Title**: Clear, action-oriented (e.g., "Implement user authentication")
                                   - **Description**: Detailed requirements and acceptance criteria
                                   - **Assignee**: Team member name (match from team list)
                                   - **Priority**: high/medium/low (based on criticality)
                                   - **Estimated Days**: 1-5 days
                                   - **Dependencies**: Tasks that must be completed first
                                   - **Category**: frontend/backend/devops/qa/design
                                   
                                   Return as structured JSON array of tasks.
                                   
                                   Example format:
                                   [
                                     {{
                                       "title": "Setup PostgreSQL database schema",
                                       "description": "Create database tables for users, projects, tasks. Include indexes and constraints.",
                                       "assignee": "Alice Smith",
                                       "priority": "high",
                                       "estimated_days": 2,
                                       "dependencies": [],
                                       "category": "backend"
                                     }},
                                     {{
                                       "title": "Implement user login API",
                                       "description": "Create REST endpoint for user authentication with JWT tokens. Include validation and error handling.",
                                       "assignee": "Alice Smith",
                                       "priority": "high",
                                       "estimated_days": 3,
                                       "dependencies": ["Setup PostgreSQL database schema"],
                                       "category": "backend"
                                     }}
                                   ]
                                   
                                   Generate 15-30 tasks covering the entire project scope.''',
                    expected_output='JSON array of comprehensive task breakdown',
                    agent=self.agent
                )
                
                crew = Crew(
                    agents=[self.agent],
                    tasks=[task],
                    verbose=False,
                    process=Process.sequential
                )
                
                result = str(crew.kickoff())
                
                # Parse JSON from result
                import re
                json_match = re.search(r'\[.*\]', result, re.DOTALL)
                if json_match:
                    tasks_data = json.loads(json_match.group())
                else:
                    # Fallback if JSON not found
                    tasks_data = self._generate_fallback_tasks(team_info)
            else:
                # No LLM - use fallback
                tasks_data = self._generate_fallback_tasks(team_info)
            
            # Process and store tasks
            stored_tasks = []
            start_date = datetime.now()
            
            for i, task_data in enumerate(tasks_data):
                # Calculate due date
                estimated_days = task_data.get('estimated_days', 3)
                due_date = (start_date + timedelta(days=estimated_days + i)).strftime('%Y-%m-%d')
                
                # Create task object
                task_obj = {
                    "id": str(uuid.uuid4()),
                    "title": task_data.get('title', 'Task'),
                    "description": task_data.get('description', ''),
                    "status": "todo",  # All start as "todo"
                    "assignee": task_data.get('assignee', 'Unassigned'),
                    "priority": task_data.get('priority', 'medium'),
                    "dueDate": due_date,
                    "category": task_data.get('category', 'general'),
                    "dependencies": task_data.get('dependencies', []),
                    "estimated_days": estimated_days,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "company_id": self.company_id,
                    "lead_id": self.lead_id,
                    "project_name": project_name
                }
                
                # Store in ChromaDB
                self.tasks_collection.add(
                    documents=[json.dumps(task_obj)],
                    ids=[task_obj["id"]],
                    metadatas={
                        "task_id": task_obj["id"],
                        "title": task_obj["title"],
                        "status": task_obj["status"],
                        "assignee": task_obj["assignee"],
                        "priority": task_obj["priority"],
                        "company_id": self.company_id,
                        "lead_id": self.lead_id,
                        "project_name": project_name
                    }
                )
                
                stored_tasks.append(task_obj)
            
            return {
                "success": True,
                "tasks_generated": len(stored_tasks),
                "tasks": stored_tasks
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_all_tasks(self, project_name: Optional[str] = None) -> List[Dict]:
        """Get all tasks for this lead, optionally filtered by project"""
        try:
            where_filter = {
                "company_id": self.company_id,
                "lead_id": self.lead_id
            }
            
            if project_name:
                where_filter["project_name"] = project_name
            
            results = self.tasks_collection.get(where=where_filter)
            
            tasks = []
            for doc in results['documents']:
                task = json.loads(doc)
                tasks.append(task)
            
            # Sort by due date
            tasks.sort(key=lambda x: x.get('dueDate', '9999-12-31'))
            return tasks
            
        except Exception as e:
            print(f"Error getting tasks: {e}")
            return []
    
    def update_task_status(self, task_id: str, new_status: str) -> Dict:
        """Update task status (for drag & drop in frontend)"""
        try:
            # Get task
            result = self.tasks_collection.get(ids=[task_id])
            
            if not result['documents']:
                return {"success": False, "error": "Task not found"}
            
            # Update task
            task = json.loads(result['documents'][0])
            task['status'] = new_status
            task['updated_at'] = datetime.now().isoformat()
            
            # If completed, record completion time
            if new_status == 'completed' and 'completed_at' not in task:
                task['completed_at'] = datetime.now().isoformat()
            
            # Update in ChromaDB
            self.tasks_collection.update(
                ids=[task_id],
                documents=[json.dumps(task)],
                metadatas={
                    "task_id": task["id"],
                    "title": task["title"],
                    "status": task["status"],
                    "assignee": task["assignee"],
                    "priority": task["priority"],
                    "company_id": self.company_id,
                    "lead_id": self.lead_id,
                    "project_name": task.get("project_name", "Project")
                }
            )
            
            return {
                "success": True,
                "task": task
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_task(self, task_id: str) -> Dict:
        """Delete a task"""
        try:
            self.tasks_collection.delete(ids=[task_id])
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def regenerate_tasks(self, project_name: str = "Project") -> Dict:
        """Clear all tasks and regenerate"""
        try:
            # Delete all existing tasks for this lead
            existing_tasks = self.get_all_tasks(project_name)
            for task in existing_tasks:
                self.delete_task(task['id'])
            
            # Generate new tasks
            return self.generate_tasks(project_name)
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_task_statistics(self) -> Dict:
        """Get task statistics for dashboard"""
        try:
            tasks = self.get_all_tasks()
            
            total = len(tasks)
            todo = len([t for t in tasks if t['status'] == 'todo'])
            in_progress = len([t for t in tasks if t['status'] == 'inprogress'])
            completed = len([t for t in tasks if t['status'] == 'completed'])
            
            high_priority = len([t for t in tasks if t['priority'] == 'high'])
            overdue = len([t for t in tasks if t.get('dueDate', '9999-12-31') < datetime.now().strftime('%Y-%m-%d') and t['status'] != 'completed'])
            
            # Group by assignee
            by_assignee = {}
            for task in tasks:
                assignee = task.get('assignee', 'Unassigned')
                if assignee not in by_assignee:
                    by_assignee[assignee] = {"total": 0, "completed": 0}
                by_assignee[assignee]["total"] += 1
                if task['status'] == 'completed':
                    by_assignee[assignee]["completed"] += 1
            
            return {
                "total_tasks": total,
                "todo": todo,
                "in_progress": in_progress,
                "completed": completed,
                "completion_rate": round((completed / total * 100) if total > 0 else 0, 1),
                "high_priority": high_priority,
                "overdue": overdue,
                "by_assignee": by_assignee
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _get_project_context(self) -> str:
        """Get project context from Document Agent (INITIAL SOURCE)"""
        context_parts = []
        
        # Get documents (INITIAL SOURCE)
        if self.docs_collection:
            try:
                docs = self.docs_collection.get()
                if docs['documents']:
                    context_parts.append("UPLOADED PROJECT DOCUMENTS (INITIAL SOURCE):")
                    context_parts.append("\n\n".join(docs['documents'][:10]))
                else:
                    context_parts.append("No project documents available - please upload project requirements first")
            except:
                context_parts.append("No project documents available - please upload project requirements first")
        
        # Get chat history (CONTINUING SOURCE)
        if self.doc_chat_collection:
            try:
                chats = self.doc_chat_collection.get()
                if chats['documents']:
                    context_parts.append("\n\nCONVERSATION HISTORY (CONTINUING SOURCE):")
                    context_parts.append("\n\n".join(chats['documents'][:5]))
            except:
                pass
        
        return "\n\n".join(context_parts) if context_parts else "No project context available"
    
    def _get_team_info(self) -> str:
        """Get team information from Stack Agent"""
        team_parts = []
        
        # Get team members from resumes
        if self.resumes_collection:
            try:
                resumes = self.resumes_collection.get()
                if resumes['metadatas']:
                    team_parts.append("TEAM MEMBERS:")
                    for metadata in resumes['metadatas']:
                        team_parts.append(f"- {metadata.get('candidate_name', 'Unknown')}")
            except:
                pass
        
        # Get team formation (roles and assignments)
        if self.stack_iterations_collection:
            try:
                iterations = self.stack_iterations_collection.get()
                if iterations['metadatas']:
                    # Get latest iteration
                    latest = iterations['metadatas'][-1]
                    team_recommendation = latest.get('team_recommendation', '')
                    if team_recommendation:
                        team_parts.append("\n\nTEAM ROLES & ASSIGNMENTS:")
                        team_parts.append(team_recommendation[:1000])  # First 1000 chars
            except:
                pass
        
        return "\n\n".join(team_parts) if team_parts else None
    
    def _generate_fallback_tasks(self, team_info: str) -> List[Dict]:
        """Generate basic fallback tasks if LLM not available"""
        # Extract team member names
        import re
        members = re.findall(r'- ([A-Z][a-z]+ [A-Z][a-z]+)', team_info)
        if not members:
            members = ["Developer"]
        
        fallback_tasks = [
            {
                "title": "Setup development environment",
                "description": "Configure local development environment with required tools and dependencies",
                "assignee": members[0] if members else "Developer",
                "priority": "high",
                "estimated_days": 1,
                "category": "setup"
            },
            {
                "title": "Design database schema",
                "description": "Create comprehensive database schema based on requirements",
                "assignee": members[0] if members else "Developer",
                "priority": "high",
                "estimated_days": 2,
                "category": "backend"
            },
            {
                "title": "Implement authentication system",
                "description": "Build user authentication with JWT tokens",
                "assignee": members[0] if members else "Developer",
                "priority": "high",
                "estimated_days": 3,
                "category": "backend"
            },
            {
                "title": "Create frontend components",
                "description": "Develop reusable React components for the application",
                "assignee": members[1] if len(members) > 1 else "Developer",
                "priority": "medium",
                "estimated_days": 4,
                "category": "frontend"
            },
            {
                "title": "Setup CI/CD pipeline",
                "description": "Configure automated testing and deployment",
                "assignee": members[2] if len(members) > 2 else "Developer",
                "priority": "medium",
                "estimated_days": 2,
                "category": "devops"
            }
        ]
        
        return fallback_tasks
    
    def chat_with_agent(self, message: str) -> dict:
        """Simple chat interface for the frontend"""
        try:
            # Check if we have project documents (INITIAL SOURCE)
            project_context = self._get_project_context()
            if "No project documents available" in project_context:
                response = f"""I'd love to help you manage your project tasks! However, I need access to your project documentation first to provide the most accurate task generation and management.

**Please upload your project documents such as:**
• Project requirements and specifications
• Technical documentation
• User stories and use cases
• Architecture diagrams
• Business requirements

Once you upload documents, I can:
• Generate comprehensive task lists based on your project requirements
• Create realistic timelines and schedules
• Assign tasks to appropriate team members
• Set priorities based on project dependencies
• Track progress and identify bottlenecks

Would you like to upload some project documents now, or do you have any general questions about task management?"""
                
                return {
                    "response": response,
                    "agent": "Task Agent",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Create a more dynamic response based on the message
            if "generate" in message.lower() or "create" in message.lower() or "task" in message.lower():
                response = f"I can help you generate and organize project tasks! Here's what I can do:\n\n📋 **Task Generation**: Break down your project into actionable tasks\n⏰ **Timeline Planning**: Create realistic schedules and deadlines\n👥 **Task Assignment**: Match tasks to team members based on skills\n🎯 **Priority Setting**: Categorize tasks by importance and urgency\n📊 **Progress Tracking**: Monitor task completion and project health\n\nTo get started, tell me about your project:\n• What type of project is it? (web app, mobile app, API, etc.)\n• What are the main features or requirements?\n• What's your timeline and team size?"
            elif "assign" in message.lower() or "team" in message.lower():
                response = f"I can help you assign tasks to the right team members! For effective task assignment, I need to know:\n\n👥 **Team Composition**: Who's on your team and their skills\n📝 **Task Requirements**: What each task involves\n⏱️ **Availability**: Team members' time and capacity\n🎯 **Skills Match**: Matching tasks to people's expertise\n\nWhat's your team structure and what tasks need to be assigned?"
            elif "timeline" in message.lower() or "schedule" in message.lower() or "deadline" in message.lower():
                response = f"I can help you create realistic project timelines! I'll consider:\n\n📅 **Project Scope**: Size and complexity of deliverables\n👥 **Team Capacity**: Available resources and skills\n🔗 **Dependencies**: Tasks that must be completed in sequence\n⚡ **Risk Factors**: Potential delays and bottlenecks\n📊 **Milestones**: Key checkpoints and deliverables\n\nWhat's your project timeline and what are the key milestones you need to hit?"
            elif "priority" in message.lower() or "urgent" in message.lower() or "important" in message.lower():
                response = f"I can help you prioritize tasks effectively! I'll help you:\n\n🎯 **Categorize by Impact**: High, medium, low priority tasks\n⏰ **Urgency Assessment**: Time-sensitive vs. flexible deadlines\n📊 **Effort Estimation**: Quick wins vs. complex tasks\n🔄 **Dependency Mapping**: Tasks that block others\n⚖️ **Resource Balancing**: Matching priorities with available capacity\n\nWhat tasks do you need help prioritizing and what are your main project goals?"
            else:
                response = f"I'm the Task Agent, your project management assistant! I can help you with:\n\n📋 **Task Management**: Generate, organize, and track project tasks\n👥 **Team Coordination**: Assign tasks and manage workloads\n⏰ **Timeline Planning**: Create realistic schedules and deadlines\n🎯 **Priority Management**: Focus on what matters most\n📊 **Progress Monitoring**: Track completion and identify bottlenecks\n\nWhat aspect of task management would you like help with today?"
            
            return {
                "response": response,
                "agent": "Task Agent",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "response": f"I encountered an error: {str(e)}",
                "agent": "Task Agent",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_chat_history(self) -> List[Dict]:
        """Get chat history as a list of dictionaries"""
        if not self.doc_chat_collection:
            return []
        
        try:
            results = self.doc_chat_collection.get(
                where={
                    "$and": [
                        {"company_id": self.company_id},
                        {"lead_id": self.lead_id}
                    ]
                }
            )
            
            history = []
            if results and 'documents' in results and 'metadatas' in results:
                for i, doc in enumerate(results['documents']):
                    metadata = results['metadatas'][i] if i < len(results['metadatas']) else {}
                    history.append({
                        "id": metadata.get("chat_id", results.get('ids', [None])[i] if results.get('ids') else None),
                        "lead_message": metadata.get("lead_message", ""),
                        "agent_response": metadata.get("agent_response", doc if isinstance(doc, str) else ""),
                        "timestamp": metadata.get("timestamp", datetime.now().isoformat()),
                        "agent": "Task Agent"
                    })
            
            # Sort by timestamp (most recent first)
            history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return history
            
        except Exception as e:
            print(f"Error getting chat history: {e}")
            return []

