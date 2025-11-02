"""
Team Formation Agent with CrewAI Orchestration
Analyzes team members, document discussions, and tech stack to form optimal teams
"""
import os
import sys
import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from crewai import Agent, Task, Crew, Process
from services.gemini_service import gemini_service
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class TeamFormationAgent:
    """Advanced Team Formation Agent with CrewAI orchestration"""
    
    def __init__(self, company_id: str, lead_id: str):
        self.company_id = company_id
        self.lead_id = lead_id
        self.chroma_path = os.path.join(os.getcwd(), "chroma_db")
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=self.chroma_path)
        
        # Get collections
        self.team_collection = self.client.get_or_create_collection("team_formation")
        self.chat_collection = self.client.get_or_create_collection("chat_history")
        self.docs_collection = self.client.get_or_create_collection("project_documents")
        self.stack_collection = self.client.get_or_create_collection("tech_stack")
        
        # Initialize LLM (Gemini with Ollama fallback)
        try:
            self.llm = gemini_service.get_llm()
            logger.info(f"✅ LLM initialized: {gemini_service.llm_type} ({gemini_service.model})")
        except Exception as e:
            logger.error(f"⚠️ LLM initialization failed: {e}")
            self.llm = None
        
        # Initialize CrewAI agents
        self._initialize_crew_agents()
    
    def _initialize_crew_agents(self):
        """Initialize CrewAI agents for team formation orchestration"""
        
        # Team Analyst Agent
        self.team_analyst = Agent(
            role="Team Analyst",
            goal="Analyze team composition, skills, and dynamics to recommend optimal team structures",
            backstory="""You are an expert team analyst with 15+ years of experience in organizational psychology, 
            team dynamics, and project management. You excel at understanding team member strengths, 
            identifying skill gaps, and recommending team compositions that maximize productivity and collaboration.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Skills Matcher Agent
        self.skills_matcher = Agent(
            role="Skills Matcher",
            goal="Match team member skills with project requirements and tech stack needs",
            backstory="""You are a technical recruitment specialist with deep knowledge of software development 
            roles, required skills, and how different technologies map to specific competencies. 
            You excel at identifying skill gaps and recommending training or hiring strategies.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Project Coordinator Agent
        self.project_coordinator = Agent(
            role="Project Coordinator",
            goal="Coordinate team formation recommendations with project requirements and timeline",
            backstory="""You are a senior project manager with expertise in team coordination, 
            resource allocation, and project planning. You understand how team composition affects 
            project success and can recommend team structures that align with project goals and constraints.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def analyze_team_formation(self, project_requirements: str, available_team_members: List[Dict]) -> Dict:
        """Analyze and recommend team formation based on project requirements and available members"""
        try:
            # Get context from other agents
            doc_context = self._get_document_context()
            stack_context = self._get_tech_stack_context()
            chat_context = self._get_chat_history()
            
            # Create analysis task
            analysis_task = Task(
                description=f"""
                Analyze team formation for the following project:
                
                PROJECT REQUIREMENTS:
                {project_requirements}
                
                AVAILABLE TEAM MEMBERS:
                {json.dumps(available_team_members, indent=2)}
                
                DOCUMENT CONTEXT:
                {doc_context}
                
                TECH STACK CONTEXT:
                {stack_context}
                
                CHAT HISTORY CONTEXT:
                {chat_context}
                
                Based on this information, provide:
                1. Recommended team structure
                2. Role assignments for each team member
                3. Skill gaps identified
                4. Training recommendations
                5. Team dynamics analysis
                6. Potential challenges and solutions
                """,
                agent=self.team_analyst,
                expected_output="Comprehensive team formation analysis with specific recommendations"
            )
            
            # Create skills matching task
            skills_task = Task(
                description=f"""
                Match team member skills with project requirements:
                
                PROJECT REQUIREMENTS: {project_requirements}
                TEAM MEMBERS: {json.dumps(available_team_members, indent=2)}
                TECH STACK: {stack_context}
                
                Provide:
                1. Skill-to-requirement mapping
                2. Missing skills identification
                3. Training recommendations
                4. Role optimization suggestions
                """,
                agent=self.skills_matcher,
                expected_output="Detailed skills analysis and matching recommendations"
            )
            
            # Create coordination task
            coordination_task = Task(
                description=f"""
                Coordinate team formation with project timeline and constraints:
                
                TEAM ANALYSIS: [From previous tasks]
                PROJECT REQUIREMENTS: {project_requirements}
                
                Provide:
                1. Timeline-optimized team structure
                2. Resource allocation recommendations
                3. Risk mitigation strategies
                4. Success metrics and KPIs
                """,
                agent=self.project_coordinator,
                expected_output="Project-coordinated team formation plan"
            )
            
            # Create and run crew
            crew = Crew(
                agents=[self.team_analyst, self.skills_matcher, self.project_coordinator],
                tasks=[analysis_task, skills_task, coordination_task],
                process=Process.sequential,
                verbose=True
            )
            
            # Execute crew
            result = crew.kickoff()
            
            # Save analysis
            analysis_id = str(uuid.uuid4())
            self._save_team_analysis(analysis_id, {
                "project_requirements": project_requirements,
                "team_members": available_team_members,
                "analysis_result": str(result),
                "timestamp": datetime.now().isoformat(),
                "company_id": self.company_id,
                "lead_id": self.lead_id
            })
            
            return {
                "success": True,
                "analysis_id": analysis_id,
                "recommendations": str(result),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def chat_with_agent(self, message: str) -> Dict:
        """Chat interface for team formation queries"""
        try:
            # Get context from other agents
            doc_context = self._get_document_context()
            stack_context = self._get_tech_stack_context()
            chat_context = self._get_chat_history()
            
            # Check if we have project documents (INITIAL SOURCE)
            if "No project documents available" in doc_context:
                response = f"""I'd love to help you form the perfect team for your project! However, I need access to your project documentation first to provide the most accurate team formation recommendations.

**Please upload your project documents such as:**
• Project requirements and specifications
• Technical documentation
• User stories and use cases
• Architecture diagrams
• Business requirements

Once you upload documents, I can:
• Analyze your project requirements to determine team needs
• Match team member skills with project requirements
• Recommend optimal team composition and roles
• Identify skill gaps and training needs
• Coordinate with other agents for comprehensive analysis

Would you like to upload some project documents now, or do you have any general questions about team formation?"""
                
                # Save chat
                chat_id = str(uuid.uuid4())
                self._save_chat(chat_id, message, response)
                
                return {
                    "response": response,
                    "agent": "Team Formation Agent",
                    "timestamp": datetime.now().isoformat(),
                    "chat_id": chat_id
                }
            
            # Create dynamic response based on message
            if "team" in message.lower() and "form" in message.lower():
                response = f"""I can help you form the perfect team for your project! Here's what I analyze:

🔍 **Team Analysis Capabilities:**
• **Skills Assessment**: Match team member skills with project requirements
• **Role Optimization**: Assign roles based on strengths and project needs
• **Dynamics Analysis**: Understand team collaboration patterns
• **Gap Identification**: Find missing skills and training needs
• **Resource Planning**: Optimize team size and composition

📊 **Integration with Other Agents:**
• **Document Analysis**: Uses project requirements from Document Agent
• **Tech Stack**: Considers technology needs from Stack Agent
• **Task Planning**: Coordinates with Task Agent for workload distribution

To get started, tell me:
• What type of project are you working on?
• Who are your available team members?
• What are your main project goals and constraints?"""

            elif "skill" in message.lower() or "competency" in message.lower():
                response = f"""I can help you analyze and match team skills! Here's what I do:

🎯 **Skills Analysis:**
• **Current Skills**: Assess what your team already knows
• **Required Skills**: Identify what the project needs
• **Skill Gaps**: Find missing competencies
• **Training Plans**: Recommend skill development paths
• **Role Matching**: Match people to roles based on skills

💡 **Smart Recommendations:**
• Cross-training opportunities
• External hiring needs
• Skill development priorities
• Team balance optimization

What specific skills or competencies are you concerned about?"""

            elif "recommend" in message.lower() or "suggest" in message.lower():
                response = f"""I can provide comprehensive team formation recommendations! I'll analyze:

👥 **Team Composition:**
• Optimal team size and structure
• Role assignments and responsibilities
• Leadership and coordination needs
• Communication and collaboration patterns

⚡ **Performance Optimization:**
• Team dynamics and chemistry
• Workload distribution
• Skill complementarity
• Growth and development opportunities

📈 **Success Metrics:**
• Project delivery timelines
• Quality and efficiency measures
• Team satisfaction and retention
• Learning and development outcomes

What specific aspects of team formation would you like me to focus on?"""

            else:
                response = f"""I'm the Team Formation Agent, your expert in building high-performing teams! I can help with:

🤝 **Team Formation**: Build optimal teams for your projects
🎯 **Skills Matching**: Match team members to project requirements  
📊 **Performance Analysis**: Optimize team dynamics and productivity
🔄 **Continuous Improvement**: Monitor and improve team effectiveness

I work closely with:
• **Document Agent**: Uses project requirements and specifications
• **Stack Agent**: Considers technology and tool requirements
• **Task Agent**: Coordinates workload and task assignments

What would you like to know about team formation for your project?"""

            # Save chat
            chat_id = str(uuid.uuid4())
            self._save_chat(chat_id, message, response)
            
            return {
                "response": response,
                "agent": "Team Formation Agent",
                "timestamp": datetime.now().isoformat(),
                "chat_id": chat_id
            }
            
        except Exception as e:
            return {
                "response": f"I encountered an error: {str(e)}",
                "agent": "Team Formation Agent",
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_document_context(self) -> str:
        """Get document context from Document Agent (INITIAL SOURCE)"""
        try:
            results = self.docs_collection.get(
                where={
                    "$and": [
                        {"company_id": self.company_id},
                        {"lead_id": self.lead_id}
                    ]
                },
                limit=5
            )
            
            if not results['metadatas']:
                return "No project documents available - please upload project requirements first"
            
            context = "UPLOADED PROJECT DOCUMENTS (INITIAL SOURCE):\n"
            for i, metadata in enumerate(results['metadatas']):
                context += f"{i+1}. {metadata.get('title', 'Untitled')}: {metadata.get('summary', 'No summary')}\n"
            
            return context
        except Exception as e:
            return f"Error retrieving documents: {str(e)}"
    
    def _get_tech_stack_context(self) -> str:
        """Get tech stack context from Stack Agent"""
        try:
            results = self.stack_collection.get(
                where={
                    "$and": [
                        {"company_id": self.company_id},
                        {"lead_id": self.lead_id}
                    ]
                },
                limit=3
            )
            
            if not results['metadatas']:
                return "No tech stack recommendations available"
            
            context = "Technology Stack:\n"
            for metadata in results['metadatas']:
                context += f"- {metadata.get('stack_name', 'Unknown')}: {metadata.get('description', 'No description')}\n"
            
            return context
        except Exception as e:
            return f"Error retrieving tech stack: {str(e)}"
    
    def _get_chat_history(self) -> str:
        """Get recent chat history for context"""
        try:
            results = self.chat_collection.get(
                where={
                    "$and": [
                        {"company_id": self.company_id},
                        {"lead_id": self.lead_id}
                    ]
                },
                limit=5
            )
            
            if not results['metadatas']:
                return "No recent conversations"
            
            context = "Recent Conversations:\n"
            for metadata in results['metadatas']:
                context += f"Q: {metadata.get('lead_message', '')}\nA: {metadata.get('agent_response', '')}\n\n"
            
            return context
        except Exception as e:
            return f"Error retrieving chat history: {str(e)}"
    
    def _save_team_analysis(self, analysis_id: str, analysis_data: Dict):
        """Save team analysis to ChromaDB"""
        try:
            self.team_collection.add(
                documents=[json.dumps(analysis_data)],
                metadatas=[{
                    "analysis_id": analysis_id,
                    "company_id": self.company_id,
                    "lead_id": self.lead_id,
                    "timestamp": datetime.now().isoformat(),
                    "type": "team_analysis"
                }],
                ids=[analysis_id]
            )
        except Exception as e:
            print(f"Error saving team analysis: {str(e)}")
    
    def _save_chat(self, chat_id: str, message: str, response: str):
        """Save chat conversation"""
        try:
            self.chat_collection.add(
                documents=[f"Lead: {message}\nAgent: {response}"],
                metadatas=[{
                    "chat_id": chat_id,
                    "company_id": self.company_id,
                    "lead_id": self.lead_id,
                    "lead_message": message,
                    "agent_response": response,
                    "timestamp": datetime.now().isoformat(),
                    "agent_type": "team_formation"
                }],
                ids=[chat_id]
            )
        except Exception as e:
            print(f"Error saving chat: {str(e)}")
    
    def get_team_analyses(self) -> List[Dict]:
        """Get all team analyses for this lead"""
        try:
            results = self.team_collection.get(
                where={
                    "$and": [
                        {"company_id": self.company_id},
                        {"lead_id": self.lead_id}
                    ]
                }
            )
            
            analyses = []
            for i, metadata in enumerate(results['metadatas']):
                analyses.append({
                    "analysis_id": metadata['analysis_id'],
                    "timestamp": metadata['timestamp'],
                    "data": json.loads(results['documents'][i]) if results['documents'] else {}
                })
            
            return analyses
        except Exception as e:
            print(f"Error retrieving team analyses: {str(e)}")
            return []
