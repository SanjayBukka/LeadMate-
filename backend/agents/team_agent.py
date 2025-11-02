"""
Team Agent - Manages team members, roles, and team dynamics
"""
import os
import uuid
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import chromadb
from crewai import Agent, Task, Crew, Process
from services.gemini_service import gemini_service
import logging

logger = logging.getLogger(__name__)


class TeamAgent:
    """
    Team Agent manages team members, roles, and team dynamics.
    Helps with team building, role assignments, and team optimization.
    """
    
    def __init__(self, company_id: str, lead_id: str, base_path: str = "./chroma_db"):
        self.company_id = company_id
        self.lead_id = lead_id
        self.base_path = Path(base_path)
        
        # Create directory structure for this company/lead
        self.company_lead_path = self.base_path / f"company_{company_id}" / f"lead_{lead_id}"
        self.company_lead_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client with persistent storage
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.company_lead_path)
        )
        
        # Create collections for this lead
        self.team_collection = self.chroma_client.get_or_create_collection(
            name="team_members",
            metadata={"description": "Team members and their roles"}
        )
        
        self.chat_collection = self.chroma_client.get_or_create_collection(
            name="team_chat",
            metadata={"description": "Lead conversation with Team Agent"}
        )
        
        # Initialize LLM (Gemini with Ollama fallback)
        try:
            self.llm = gemini_service.get_llm()
            logger.info(f"✅ LLM initialized: {gemini_service.llm_type} ({gemini_service.model})")
        except Exception as e:
            logger.error(f"⚠️ LLM initialization failed: {e}")
            self.llm = None
        
        # Create CrewAI agent
        self.agent = Agent(
            role="Team Management Expert",
            goal="Help with team building, role assignments, and team dynamics optimization",
            backstory="""You are an expert team manager with extensive experience in building high-performing teams. 
            You excel at analyzing team dynamics, assigning roles, and optimizing team performance. 
            You understand the importance of diverse skills, clear communication, and effective collaboration.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
    
    async def _has_uploaded_documents(self) -> bool:
        """Check if any documents have been uploaded"""
        try:
            from database import get_database
            from bson import ObjectId
            
            db = get_database()
            
            # Check MongoDB documents collection for documents uploaded via frontend
            doc_count = 0
            async for doc in db.documents.find({
                "startupId": self.company_id,
                "projectId": self.lead_id
            }).limit(1):
                doc_count += 1
                if doc_count > 0:
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error checking for documents: {str(e)}")
            return False
    
    async def search_documents(self, query: str, n_results: int = 5) -> List[str]:
        """Search documents using MongoDB collection"""
        try:
            from database import get_database
            
            db = get_database()
            
            # Get documents from MongoDB documents collection
            document_contents = []
            async for doc in db.documents.find({
                "startupId": self.company_id,
                "projectId": self.lead_id
            }).limit(n_results):
                if doc.get('extractedContent'):
                    # Truncate content to reasonable length
                    content = doc['extractedContent'][:2000]  # First 2000 characters
                    document_contents.append(f"Document: {doc.get('originalFilename', 'Unknown')}\nContent: {content}")
            
            return document_contents
            
        except Exception as e:
            print(f"Error searching documents: {str(e)}")
            return []
    
    def get_chat_history(self) -> List[Dict]:
        """Get chat history for this lead"""
        try:
            results = self.chat_collection.get(
                where={
                    "$and": [
                        {"company_id": self.company_id},
                        {"lead_id": self.lead_id}
                    ]
                }
            )
            
            # Sort by timestamp
            chat_data = []
            for i, metadata in enumerate(results['metadatas']):
                chat_data.append({
                    'lead_message': results['documents'][i],
                    'agent_response': metadata.get('agent_response', ''),
                    'timestamp': metadata.get('timestamp', ''),
                    'chat_id': metadata.get('chat_id', '')
                })
            
            return sorted(chat_data, key=lambda x: x['timestamp'])
        except Exception as e:
            print(f"Error retrieving chat history: {str(e)}")
            return []
    
    def _store_chat(self, message: str, response: str) -> str:
        """Store chat interaction"""
        try:
            chat_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            
            self.chat_collection.add(
                documents=[message],
                ids=[chat_id],
                metadatas=[{
                    "agent_response": response,
                    "timestamp": timestamp,
                    "chat_id": chat_id,
                    "company_id": self.company_id,
                    "lead_id": self.lead_id
                }]
            )
            
            return chat_id
        except Exception as e:
            print(f"Error storing chat: {str(e)}")
            return str(uuid.uuid4())
    
    async def chat(self, message: str) -> Tuple[str, str]:
        """
        Chat with Team Agent about team management
        
        Returns:
            Tuple of (response, chat_id)
        """
        try:
            # Check if we have uploaded documents (INITIAL SOURCE)
            has_documents = await self._has_uploaded_documents()
            
            if not has_documents:
                # No documents uploaded yet - provide guidance
                response = f"""I'm the Team Agent, specialized in team management and team building. I can help you with:

👥 **Team Building**: Form effective teams based on project requirements
🎯 **Role Assignment**: Assign appropriate roles to team members
📊 **Team Dynamics**: Analyze and improve team collaboration
⚡ **Performance Optimization**: Enhance team productivity and efficiency
🤝 **Conflict Resolution**: Help resolve team conflicts and issues

**To provide the most accurate team recommendations, I need access to your project documentation.**

Please upload your project documents such as:
• Project requirements and specifications
• Team member profiles and skills
• Project scope and deliverables
• Any team-related documentation

Once you upload documents, I can:
• Analyze project requirements for team needs
• Recommend optimal team structures
• Suggest role assignments based on skills
• Help optimize team dynamics
• Provide team management strategies

Would you like to upload some documents now, or do you have any general questions about team management?"""
                
                chat_id = self._store_chat(message, response)
                return response, chat_id
            
            # Search for relevant document context (INITIAL SOURCE)
            context_docs = await self.search_documents(message, n_results=5)
            context = "\n\n".join(context_docs) if context_docs else "No relevant documents found."
            
            # Get chat history for context (CONTINUING SOURCE)
            chat_history = self.get_chat_history()
            history_text = "\n".join([
                f"Lead: {msg['lead_message']}\nAgent: {msg['agent_response']}"
                for msg in chat_history[-3:]  # Last 3 exchanges
            ])
            
            # Create task for agent with document context
            if self.agent:
                task = Task(
                    description=f'''Based on the uploaded project documentation and conversation history, 
                    provide expert team management advice for the following question: "{message}"

                    **UPLOADED PROJECT DOCUMENTS (INITIAL SOURCE):**
                    {context}

                    **CONVERSATION HISTORY (CONTINUING SOURCE):**
                    {history_text}

                    Please provide detailed, actionable team management advice based on the project requirements and context provided.''',
                    agent=self.agent
                )
                
                crew = Crew(
                    agents=[self.agent],
                    tasks=[task],
                    process=Process.sequential,
                    verbose=True
                )
                
                result = crew.kickoff()
                response = str(result)
            else:
                response = "I'm sorry, I'm having trouble processing your request right now. Please try again."
            
            chat_id = self._store_chat(message, response)
            return response, chat_id
            
        except Exception as e:
            error_response = f"I encountered an error: {str(e)}"
            chat_id = self._store_chat(message, error_response)
            return error_response, chat_id
    
    async def chat_with_agent(self, message: str) -> dict:
        """Simple chat interface for the frontend"""
        try:
            response, chat_id = await self.chat(message)
            return {
                "response": response,
                "agent": "Team Agent",
                "timestamp": datetime.now().isoformat(),
                "chat_id": chat_id
            }
        except Exception as e:
            return {
                "response": f"I encountered an error: {str(e)}",
                "agent": "Team Agent",
                "timestamp": datetime.now().isoformat(),
                "chat_id": ""
            }
