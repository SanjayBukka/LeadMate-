"""
Project Document Agent
Redesigned to be project-centric - uses project-specific data only
"""
import logging
from typing import Dict, List, Optional
from bson import ObjectId
from crewai import Agent, Task, Crew, Process
from services.gemini_service import gemini_service
from services.project_data_service import project_data_service
from database import get_database

logger = logging.getLogger(__name__)


class ProjectDocumentAgent:
    """
    Document Agent scoped to a specific project
    Uses only project's documents and maintains project-specific chat history
    """
    
    def __init__(self, startup_id: str, project_id: str):
        """
        Initialize Document Agent for a specific project
        
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
        self.chat_collection = project_data_service.get_project_doc_chat_collection(
            startup_id, project_id
        )
        
        # Initialize LLM
        try:
            self.llm = gemini_service.get_llm()
            logger.info(f"✅ Project Document Agent initialized for project {project_id}")
        except Exception as e:
            self.llm = None
            logger.error(f"⚠️ LLM initialization failed: {e}")
        
        # Create CrewAI agent
        self.agent = self._create_agent()
    
    def _create_agent(self):
        """Create Document Analysis Agent with CrewAI"""
        if not self.llm:
            return None
            
        return Agent(
            role='Project Documentation Analyst',
            goal=f'''Analyze project documentation for project {self.project_id} thoroughly and help 
                    the team lead understand all requirements, constraints, and technical specifications. 
                    Ask clarifying questions and maintain detailed conversation history.''',
            backstory='''You are an expert project analyst with deep experience in understanding 
                        complex technical requirements. You excel at extracting key information 
                        from documentation and helping team leads make informed decisions. 
                        You only use information from THIS specific project's documents.''',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def search_documents(self, query: str, n_results: int = 5) -> List[str]:
        """Search project's documents using embeddings"""
        try:
            results = self.docs_collection.query(
                query_texts=[query],
                n_results=min(n_results, self.docs_collection.count())
            )
            return results['documents'][0] if results['documents'] else []
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    async def chat(self, message: str, chat_history: Optional[List[Dict]] = None) -> str:
        """
        Chat with Document Agent about project's documents
        
        Args:
            message: User's question
            chat_history: Previous chat messages
            
        Returns:
            Agent's response
        """
        try:
            # Get relevant documents from project
            context_docs = self.search_documents(message, n_results=5)
            context = "\n\n".join(context_docs) if context_docs else "No relevant documents found for this project."
            
            # Add chat history if available
            history_context = ""
            if chat_history and len(chat_history) > 0:
                history_context = "\n\nPrevious conversation:\n"
                for msg in chat_history[-3:]:
                    history_context += f"User: {msg.get('user_message', '')}\n"
                    history_context += f"Agent: {msg.get('agent_response', '')}\n\n"
            
            # Create task
            task = Task(
                description=f'''Based on the project {self.project_id} documentation:
                               
                               {context}
                               
                               {history_context}
                               
                               Answer this question: {message}
                               
                               Provide a detailed response based ONLY on this project's documents.
                               If information is not available in the project documents, say so clearly.''',
                expected_output='''A comprehensive answer based on project documentation.''',
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
            response = str(result)
            
            # Store in chat history
            import uuid
            from datetime import datetime
            chat_id = f"chat_{uuid.uuid4().hex[:8]}"
            conversation = f"User: {message}\nAgent: {response}"
            
            self.chat_collection.add(
                documents=[conversation],
                ids=[chat_id],
                metadatas=[{
                    "project_id": self.project_id,
                    "startup_id": self.startup_id,
                    "timestamp": datetime.utcnow().isoformat()
                }]
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return f"I encountered an error: {str(e)}"
    
    async def get_chat_history(self, limit: int = 10) -> List[Dict]:
        """Get chat history for this project"""
        try:
            results = self.chat_collection.get(limit=limit)
            
            chat_history = []
            for i, (doc, metadata) in enumerate(zip(
                results.get('documents', []),
                results.get('metadatas', [])
            )):
                # Parse conversation
                lines = doc.split('\n')
                if len(lines) >= 2:
                    user_msg = lines[0].replace('User: ', '')
                    agent_msg = '\n'.join(lines[1:]).replace('Agent: ', '')
                    chat_history.append({
                        "user_message": user_msg,
                        "agent_response": agent_msg,
                        "timestamp": metadata.get("timestamp")
                    })
            
            return chat_history
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []
    
    async def get_document_summary(self) -> str:
        """Get summary of all documents in this project"""
        try:
            # Get all documents from collection
            all_docs = self.docs_collection.get()
            documents = all_docs.get('documents', [])
            
            if not documents:
                return "No documents uploaded for this project yet."
            
            # Create summary task
            task = Task(
                description=f'''Summarize the following project documents:
                               
                               {chr(10).join(documents[:10])}  # First 10 chunks
                               
                               Provide a comprehensive summary covering:
                               1. Project overview
                               2. Key requirements
                               3. Technical specifications
                               4. Important details''',
                expected_output='''A detailed project summary.''',
                agent=self.agent
            )
            
            crew = Crew(
                agents=[self.agent],
                tasks=[task],
                verbose=False,
                process=Process.sequential
            )
            
            result = crew.kickoff()
            return str(result)
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"Error generating summary: {str(e)}"

