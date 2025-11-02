"""
MongoDB Document Agent
Uses MongoDB Atlas Vector Search instead of ChromaDB for better integration
"""
import os
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import uuid
from crewai import Agent, Task, Crew, Process
from services.gemini_service import gemini_service

from services.mongodb_vector_service import MongoDBVectorService
from database import get_database
from bson import ObjectId

logger = logging.getLogger(__name__)


class MongoDocumentAgent:
    """Document Agent using MongoDB Vector Search"""
    
    def __init__(self, company_id: str, lead_id: str):
        """Initialize MongoDB Document Agent"""
        self.company_id = company_id
        self.lead_id = lead_id
        
        # Initialize MongoDB Vector Service
        self.vector_service = MongoDBVectorService()
        
        # Initialize LLM (Gemini with Ollama fallback)
        try:
            self.llm = gemini_service.get_llm()
            logger.info(f"✅ LLM initialized: {gemini_service.llm_type} ({gemini_service.model})")
            
            # Create CrewAI agent
            self.agent = Agent(
                role="Document Analysis Expert",
                goal="Analyze project documents and provide detailed insights to help team leads understand their project requirements",
                backstory="""You are an expert document analyst with deep knowledge of project management, 
                technical documentation, and business requirements. You excel at extracting key insights 
                from project documents and providing actionable recommendations.""",
                verbose=False,
                allow_delegation=False,
                llm=self.llm
            )
            
            logger.info("MongoDB Document Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            self.llm = None
            self.agent = None
    
    def upload_document(self, file_data: bytes, filename: str, file_type: str) -> Dict:
        """Upload and process a document"""
        try:
            # Extract text based on file type
            if file_type == "application/pdf":
                text = self._extract_text_from_pdf(file_data)
            elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                text = self._extract_text_from_docx(file_data)
            elif file_type == "text/plain":
                text = file_data.decode("utf-8")
            else:
                return {"success": False, "error": "Unsupported file type"}
            
            if not text:
                return {"success": False, "error": "No text extracted from document"}
            
            # Add document to MongoDB Vector Service
            result = self.vector_service.add_document(
                startup_id=self.company_id,
                project_id=self.lead_id,
                filename=filename,
                content=text,
                file_type=file_type.split('/')[-1]
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            return {"success": False, "error": str(e)}
    
    def search_documents(self, query: str, n_results: int = 5) -> List[str]:
        """Search for relevant document content"""
        try:
            results = self.vector_service.search_documents(
                startup_id=self.company_id,
                project_id=self.lead_id,
                query=query,
                limit=n_results
            )
            
            return [result.get('content', '') for result in results]
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def has_uploaded_documents(self) -> bool:
        """Check if any documents have been uploaded"""
        return self.vector_service.has_documents(self.company_id, self.lead_id)
    
    def get_documents(self) -> List[Dict]:
        """Get all uploaded documents"""
        return self.vector_service.get_documents(self.company_id, self.lead_id)
    
    def get_stats(self) -> Dict:
        """Get document statistics"""
        return self.vector_service.get_stats(self.company_id, self.lead_id)
    
    def chat_with_agent(self, message: str) -> Dict:
        """Chat interface for document queries"""
        try:
            # Check if we have uploaded documents
            if not self.has_uploaded_documents():
                response = """I notice you haven't uploaded any project documents yet. To provide you with the most accurate and helpful analysis, I need access to your project documentation.

**Please upload your project documents such as:**
• Project requirements and specifications
• Technical documentation  
• User stories and use cases
• Architecture diagrams
• Business requirements
• Any other relevant project materials

Once you upload documents, I can:
• Analyze your project requirements in detail
• Answer specific questions about your project
• Provide recommendations based on your documentation
• Help identify potential issues or improvements
• Guide you through project planning and execution

Would you like to upload some documents now, or do you have any general questions about project management?"""
                
                return {
                    "response": response,
                    "agent": "Document Agent",
                    "timestamp": datetime.now().isoformat(),
                    "chat_id": str(uuid.uuid4())
                }
            
            # Get relevant document context
            context_docs = self.search_documents(message, n_results=5)
            context = "\n\n".join(context_docs) if context_docs else "No relevant documents found."
            
            # Get chat history
            chat_history = self._get_chat_history()
            history_text = "\n".join([
                f"Lead: {msg['lead_message']}\nAgent: {msg['agent_response']}"
                for msg in chat_history[-3:]  # Last 3 exchanges
            ])
            
            # Create task for agent
            if self.agent:
                task = Task(
                    description=f'''Based on the uploaded project documentation and conversation history, 
                                   respond to the lead's question or comment.
                                   
                                   UPLOADED PROJECT DOCUMENTS (INITIAL SOURCE):
                                   {context}
                                   
                                   CONVERSATION HISTORY (CONTINUING SOURCE):
                                   {history_text}
                                   
                                   LEAD'S CURRENT MESSAGE: {message}
                                   
                                   Instructions:
                                   1. First, reference the uploaded documents to provide context
                                   2. Use the conversation history to understand the ongoing discussion
                                   3. Provide specific, actionable responses based on the project documentation
                                   4. If you need clarification, ask specific questions
                                   5. If you identify requirements or issues, reference the relevant document sections
                                   6. Always maintain context from both the documents and conversation history
                                   
                                   Provide a comprehensive response that combines insights from both the uploaded documents and our conversation history.''',
                    expected_output='A comprehensive response that references specific document content and builds upon conversation history',
                    agent=self.agent
                )
                
                crew = Crew(
                    agents=[self.agent],
                    tasks=[task],
                    verbose=False,
                    process=Process.sequential
                )
                
                response = str(crew.kickoff())
            else:
                # Fallback response without LLM
                response = f"I've analyzed the documents. Based on the context, I can help clarify: {context[:200]}..."
            
            # Store conversation
            chat_id = self._store_chat(message, response)
            
            return {
                "response": response,
                "agent": "Document Agent",
                "timestamp": datetime.now().isoformat(),
                "chat_id": chat_id
            }
            
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return {
                "response": f"I encountered an error: {str(e)}",
                "agent": "Document Agent",
                "timestamp": datetime.now().isoformat(),
                "chat_id": str(uuid.uuid4())
            }
    
    def _extract_text_from_pdf(self, file_data: bytes) -> str:
        """Extract text from PDF file"""
        try:
            import PyPDF2
            import io
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_data))
            text = ""
            
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return ""
    
    def _extract_text_from_docx(self, file_data: bytes) -> str:
        """Extract text from DOCX file"""
        try:
            import docx
            import io
            
            doc = docx.Document(io.BytesIO(file_data))
            text = ""
            
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {e}")
            return ""
    
    def _get_chat_history(self) -> List[Dict]:
        """Get chat history from database"""
        try:
            db = get_database()
            history = db.document_chats.find({
                "startup_id": self.company_id,
                "project_id": self.lead_id
            }).sort("timestamp", -1).limit(10)
            
            return list(history)
            
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []
    
    def _store_chat(self, lead_message: str, agent_response: str) -> str:
        """Store chat exchange in database"""
        try:
            chat_id = str(uuid.uuid4())
            
            db = get_database()
            db.document_chats.insert_one({
                "_id": chat_id,
                "startup_id": self.company_id,
                "project_id": self.lead_id,
                "lead_message": lead_message,
                "agent_response": agent_response,
                "timestamp": datetime.utcnow(),
                "created_at": datetime.utcnow()
            })
            
            return chat_id
            
        except Exception as e:
            logger.error(f"Error storing chat: {e}")
            return str(uuid.uuid4())
    
    def get_chat_history(self) -> List[Dict]:
        """Get chat history for this project"""
        return self._get_chat_history()
    
    def debug_info(self) -> Dict:
        """Get debug information about documents and setup"""
        try:
            stats = self.get_stats()
            has_docs = self.has_uploaded_documents()
            
            return {
                "company_id": self.company_id,
                "lead_id": self.lead_id,
                "has_documents": has_docs,
                "stats": stats,
                "vector_service_available": self.vector_service is not None,
                "llm_available": self.llm is not None,
                "agent_available": self.agent is not None
            }
            
        except Exception as e:
            return {"error": str(e)}
