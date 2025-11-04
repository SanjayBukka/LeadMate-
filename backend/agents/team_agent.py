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
from services.vector_store_service import vector_store_service
from langchain_community.llms import Ollama
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
        
        # Initialize LLM (prefer Ollama, fallback to Gemini if explicitly enabled)
        self.llm = None
        self.crewai_llm = None
        force_ollama = os.getenv("FORCE_OLLAMA", "").lower() in ("1", "true", "yes")
        use_gemini = os.getenv("USE_GEMINI", "").lower() in ("1", "true", "yes")
        google_key = os.getenv("GOOGLE_API_KEY", "").strip()
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        ollama_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        try:
            if force_ollama or not (use_gemini and google_key):
                self.crewai_llm = f"ollama/{ollama_model}"
                try:
                    self.llm = Ollama(model=ollama_model, base_url=ollama_base)
                except Exception:
                    self.llm = None
                logger.info(f"Using Ollama for TeamAgent: model={ollama_model} base={ollama_base}")
            else:
                try:
                    self.llm = gemini_service.get_llm()
                    self.crewai_llm = getattr(gemini_service, "crewai_model", None)
                    logger.info(f"Using Gemini for TeamAgent: {gemini_service.llm_type} ({gemini_service.model})")
                except Exception as ge:
                    logger.warning(f"Gemini init failed for TeamAgent ({ge}), falling back to Ollama")
                    self.crewai_llm = f"ollama/{ollama_model}"
                    try:
                        self.llm = Ollama(model=ollama_model, base_url=ollama_base)
                    except Exception:
                        self.llm = None
        except Exception as e:
            logger.error(f"LLM initialization failed for TeamAgent: {e}")
            self.llm = None
            self.crewai_llm = None
        
        # Create CrewAI agent
        llm_for_crewai = self.crewai_llm if self.crewai_llm else self.llm
        self.agent = Agent(
            role="Team Management Expert",
            goal="Help with team building, role assignments, and team dynamics optimization",
            backstory="""You are an expert team manager with extensive experience in building high-performing teams. 
            You excel at analyzing team dynamics, assigning roles, and optimizing team performance. 
            You understand the importance of diverse skills, clear communication, and effective collaboration.""",
            llm=llm_for_crewai,
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
            
            # Build contextual inputs from VectorStore (documents + resumes)
            try:
                doc_collection = vector_store_service.get_or_create_collection(
                    startup_id=self.company_id,
                    project_id=self.lead_id,
                    collection_type="documents"
                )
                dc = doc_collection.get()
                doc_snippets = (dc.get('documents') or [])[:5]
                doc_ctx = "\n\n".join(doc_snippets) if doc_snippets else "No documents found"
            except Exception:
                doc_ctx = "No documents found"

            # Build resumes context including candidate names and a short snippet
            candidate_list = []
            try:
                resumes_collection = vector_store_service.get_or_create_collection(
                    startup_id=self.company_id,
                    project_id=self.lead_id,
                    collection_type="resumes"
                )
                rc = resumes_collection.get()
                resume_docs = rc.get('documents') or []
                resume_metas = rc.get('metadatas') or []
                preview_lines = []
                for i, doc in enumerate(resume_docs[:3]):
                    meta = resume_metas[i] if i < len(resume_metas) else {}
                    name = meta.get('candidate_name', 'Unknown')
                    candidate_list.append(name)
                    preview = (doc or '')[:300]
                    preview_lines.append(f"- {name}: {preview}")
                resumes_ctx = "\n".join(preview_lines) if preview_lines else "No resumes found"
            except Exception:
                resumes_ctx = "No resumes found"
                candidate_list = []

            candidates_str = ", ".join(candidate_list) if candidate_list else "(none)"
            context = (
                f"PROJECT DOCUMENTS:\n{doc_ctx}\n\n"
                f"UPLOADED RESUMES (previews):\n{resumes_ctx}\n\n"
                f"CANDIDATES (names): {candidates_str}"
            )
            
            # Get chat history for context (CONTINUING SOURCE)
            chat_history = self.get_chat_history()
            history_text = "\n".join([
                f"Lead: {msg['lead_message']}\nAgent: {msg['agent_response']}"
                for msg in chat_history[-3:]  # Last 3 exchanges
            ])
            
            # Create task for agent with document context
            if self.agent:
                task = Task(
                    description=(
                        f"Use the project documents and uploaded resumes to recommend team structure and roles.\n\n"
                        f"{context}\n\nCONVERSATION HISTORY:\n{history_text}\n\nLEAD'S MESSAGE: {message}\n\n"
                        "Provide: (1) role assignments mapping each role to a specific candidate name from CANDIDATES;"
                        " if no suitable candidate exists, explicitly state 'Hiring Required' or 'Training Required' and the skill gap."
                        " (2) a short skill-match rationale per assignment; (3) key risks & mitigations;"
                        " (4) 2-3 clarifying questions if needed. Return a concise, scannable plan."
                    ),
                    expected_output='A concise team plan with role->candidate mapping (or Hiring/Training Required), rationale, risks/mitigations, and clarifying questions.',
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
