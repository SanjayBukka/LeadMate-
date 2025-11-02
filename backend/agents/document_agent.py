"""
Document Agent - Analyzes project documentation and maintains chat with lead
"""
import os
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from bson import ObjectId
from pathlib import Path
import chromadb
from chromadb.config import Settings
from crewai import Agent, Task, Crew, Process
from langchain.text_splitter import RecursiveCharacterTextSplitter
import PyPDF2
from docx import Document as DocxDocument
import io
from services.gemini_service import gemini_service

logger = logging.getLogger(__name__)


class DocumentAgent:
    """
    Document Agent analyzes project documentation and maintains conversation history with lead
    to clarify requirements before team formation.
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
        self.docs_collection = self.chroma_client.get_or_create_collection(
            name="documents",
            metadata={"description": "Project documents"}
        )
        
        self.chat_collection = self.chroma_client.get_or_create_collection(
            name="doc_chat",
            metadata={"description": "Lead conversation with Document Agent"}
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Initialize LLM (Gemini with Ollama fallback)
        try:
            self.llm = gemini_service.get_llm()
            logger.info(f"✅ LLM initialized: {gemini_service.llm_type} ({gemini_service.model})")
        except Exception as e:
            self.llm = None
            logger.error(f"⚠️ LLM initialization failed: {e}. Agent will use fallback responses.")
        
        # Create CrewAI agent
        self.agent = self._create_agent()
        
        # Note: Document sync will happen on first document check or search
        # This avoids blocking initialization with async operations
        # Sync is also triggered automatically in the router via DocumentSyncService
    
    def _create_agent(self):
        """Create Document Analysis Agent with CrewAI"""
        if not self.llm:
            return None
            
        return Agent(
            role='Project Documentation Analyst',
            goal='''Analyze project documentation thoroughly and help the lead understand all 
                    requirements, constraints, and technical specifications. Ask clarifying 
                    questions and maintain detailed conversation history.''',
            backstory='''You are an expert project analyst with deep experience in understanding 
                        complex technical requirements. You excel at extracting key information 
                        from documentation and helping leads make informed decisions about team 
                        formation. You ask probing questions to ensure complete understanding.''',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def extract_text_from_pdf(self, file_data: bytes) -> str:
        """Extract text from PDF file"""
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(file_data))
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            print(f"Error reading PDF: {str(e)}")
            return ""
    
    def extract_text_from_docx(self, file_data: bytes) -> str:
        """Extract text from DOCX file"""
        try:
            doc = DocxDocument(io.BytesIO(file_data))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            print(f"Error reading DOCX: {str(e)}")
            return ""
    
    def upload_document(self, file_data: bytes, filename: str, file_type: str) -> Dict:
        """
        Upload and process a document
        
        Returns:
            Dict with status and document_id
        """
        try:
            # Extract text based on file type
            if file_type == "application/pdf":
                text = self.extract_text_from_pdf(file_data)
            elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                text = self.extract_text_from_docx(file_data)
            elif file_type == "text/plain":
                text = file_data.decode("utf-8")
            else:
                return {"success": False, "error": "Unsupported file type"}
            
            if not text:
                return {"success": False, "error": "No text extracted from document"}
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            
            # Create document ID
            doc_id = str(uuid.uuid4())
            
            # Store chunks in ChromaDB
            documents = []
            ids = []
            metadatas = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                ids.append(chunk_id)
                documents.append(chunk)
                metadatas.append({
                    "document_id": doc_id,
                    "filename": filename,
                    "chunk_index": i,
                    "upload_time": datetime.now().isoformat(),
                    "company_id": self.company_id,
                    "lead_id": self.lead_id
                })
            
            self.docs_collection.add(
                documents=documents,
                ids=ids,
                metadatas=metadatas
            )
            
            return {
                "success": True,
                "document_id": doc_id,
                "filename": filename,
                "chunks": len(chunks)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def search_documents(self, query: str, n_results: int = 5, project_id: Optional[str] = None) -> List[str]:
        """
        Search documents - tries VectorStoreService ChromaDB first, falls back to Document Agent's collection, then MongoDB
        
        Args:
            query: Search query
            n_results: Number of results to return
            project_id: Optional project ID to filter documents
        """
        try:
            from services.vector_store_service import vector_store_service
            from database import get_database
            from bson import ObjectId
            
            startup_id = self.company_id
            document_contents = []
            
            # Use project_id if provided, otherwise use lead_id
            context_id = project_id if project_id else self.lead_id
            
            # Strategy 1: Try VectorStoreService collection (used by sync service)
            try:
                vs_collection = vector_store_service.get_or_create_collection(
                    startup_id=startup_id,
                    project_id=context_id,
                    collection_type="documents"
                )
                
                results = vs_collection.query(
                    query_texts=[query],
                    n_results=n_results
                )
                
                if results and results.get('documents') and len(results['documents'][0]) > 0:
                    for i, doc in enumerate(results['documents'][0]):
                        metadata = results.get('metadatas', [{}])[0][i] if results.get('metadatas') else {}
                        filename = metadata.get('filename', 'Unknown')
                        document_contents.append(f"Document: {filename}\nContent: {doc}")
                    
                    if document_contents:
                        logger.info(f"Found {len(document_contents)} documents via VectorStore search")
                        return document_contents
            except Exception as vs_error:
                logger.debug(f"VectorStore search failed (non-fatal): {vs_error}")
            
            # Strategy 2: Try Document Agent's own collection (legacy)
            try:
                results = self.docs_collection.query(
                    query_texts=[query],
                    n_results=n_results
                )
                
                if results and results.get('documents') and len(results['documents'][0]) > 0:
                    for i, doc in enumerate(results['documents'][0]):
                        metadata = results.get('metadatas', [{}])[0][i] if results.get('metadatas') else {}
                        filename = metadata.get('filename', 'Unknown')
                        document_contents.append(f"Document: {filename}\nContent: {doc}")
                    
                    if document_contents:
                        logger.info(f"Found {len(document_contents)} documents via Document Agent collection")
                        return document_contents
            except Exception as da_error:
                logger.debug(f"Document Agent collection search failed (non-fatal): {da_error}")
            
            # Strategy 3: Fallback to MongoDB (source of truth) - get full document content
            db = get_database()
            
            # Ensure sync happens if needed
            from services.document_sync_service import document_sync_service
            try:
                await document_sync_service.sync_documents_to_chromadb(
                    startup_id=startup_id,
                    lead_id=self.lead_id,
                    force_resync=False
                )
            except Exception as sync_err:
                logger.debug(f"Sync during search failed (non-fatal): {sync_err}")
            
            # Get documents from MongoDB
            # If project_id provided, filter by it
            mongo_query = {"startupId": startup_id}
            if project_id:
                mongo_query["projectId"] = project_id
                
            async for doc in db.documents.find(mongo_query).limit(n_results):
                content = doc.get('extractedContent', '')
                if content and not content.startswith('[Error') and len(content.strip()) > 10:
                    # Use query matching for relevance
                    if query.lower() in content.lower():
                        document_contents.append(
                            f"Document: {doc.get('originalFilename', 'Unknown')}\n"
                            f"Content: {content[:2000]}"  # First 2000 chars
                        )
            
            # Strategy 4: If no results and company_id might be user.id, resolve and try again
            if len(document_contents) == 0 and ObjectId.is_valid(self.company_id):
                user = await db.users.find_one({"_id": ObjectId(self.company_id)})
                if user and user.get("startupId"):
                    actual_startup_id = user["startupId"]
                    self.company_id = actual_startup_id  # Update for future operations
                    
                    async for doc in db.documents.find({
                        "startupId": actual_startup_id
                    }).limit(n_results):
                        content = doc.get('extractedContent', '')
                        if content and not content.startswith('[Error') and len(content.strip()) > 10:
                            if query.lower() in content.lower():
                                document_contents.append(
                                    f"Document: {doc.get('originalFilename', 'Unknown')}\n"
                                    f"Content: {content[:2000]}"
                                )
            
            if document_contents:
                logger.info(f"Found {len(document_contents)} documents via MongoDB fallback")
            else:
                logger.warning(f"No documents found for query: {query[:50]}...")
            
            return document_contents
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}", exc_info=True)
            return []
    
    async def _sync_project_documents(self):
        """
        Sync documents from MongoDB (project documents) to ChromaDB for faster access.
        This bridges the gap between documents uploaded through the project system
        and the Document Agent's vector store.
        """
        try:
            from database import get_database
            from bson import ObjectId
            
            db = get_database()
            
            # Check if we already have documents in ChromaDB
            existing_count = self.docs_collection.count()
            if existing_count > 0:
                # Already synced, skip
                return
            
            # Find all projects for this startup
            # Note: company_id might be user.id, but we need to find the actual startupId
            # Try to find documents with startupId matching company_id first
            sync_count = 0
            
            # Strategy 1: Find documents where startupId matches company_id
            async for doc in db.documents.find({
                "startupId": self.company_id
            }):
                # Check if this document is already in ChromaDB
                doc_id = str(doc.get("_id", ""))
                existing = self.docs_collection.get(
                    ids=None,
                    where={"mongodb_doc_id": doc_id}
                )
                
                if existing and len(existing['ids']) > 0:
                    continue  # Already synced
                
                # Get extracted content
                content = doc.get("extractedContent")
                if not content or content.startswith('[Error') or len(content.strip()) < 10:
                    continue
                
                # Extract text and chunk it
                chunks = self.text_splitter.split_text(content)
                
                # Store chunks in ChromaDB
                documents = []
                ids = []
                metadatas = []
                
                for i, chunk in enumerate(chunks):
                    chunk_id = f"sync_{doc_id}_chunk_{i}_{uuid.uuid4().hex[:8]}"
                    ids.append(chunk_id)
                    documents.append(chunk)
                    metadatas.append({
                        "document_id": doc_id,
                        "filename": doc.get("originalFilename", "Unknown"),
                        "chunk_index": i,
                        "upload_time": doc.get("uploadedAt", datetime.now()).isoformat() if hasattr(doc.get("uploadedAt", datetime.now()), 'isoformat') else str(doc.get("uploadedAt", datetime.now())),
                        "company_id": self.company_id,
                        "lead_id": self.lead_id,
                        "project_id": doc.get("projectId", ""),
                        "mongodb_doc_id": doc_id,  # Track source document
                        "synced_from_mongodb": True
                    })
                
                if documents:
                    self.docs_collection.add(
                        documents=documents,
                        ids=ids,
                        metadatas=metadatas
                    )
                    sync_count += len(documents)
            
            # Strategy 2: If company_id looks like user.id, try to find user's startupId
            if sync_count == 0:
                user = await db.users.find_one({"_id": ObjectId(self.company_id) if ObjectId.is_valid(self.company_id) else None})
                if user and user.get("startupId"):
                    actual_startup_id = user["startupId"]
                    # Now find documents for this startup
                    async for doc in db.documents.find({
                        "startupId": actual_startup_id
                    }):
                        doc_id = str(doc.get("_id", ""))
                        existing = self.docs_collection.get(
                            ids=None,
                            where={"mongodb_doc_id": doc_id}
                        )
                        
                        if existing and len(existing['ids']) > 0:
                            continue
                        
                        content = doc.get("extractedContent")
                        if not content or content.startswith('[Error') or len(content.strip()) < 10:
                            continue
                        
                        chunks = self.text_splitter.split_text(content)
                        
                        documents = []
                        ids = []
                        metadatas = []
                        
                        for i, chunk in enumerate(chunks):
                            chunk_id = f"sync_{doc_id}_chunk_{i}_{uuid.uuid4().hex[:8]}"
                            ids.append(chunk_id)
                            documents.append(chunk)
                            metadatas.append({
                                "document_id": doc_id,
                                "filename": doc.get("originalFilename", "Unknown"),
                                "chunk_index": i,
                                "upload_time": doc.get("uploadedAt", datetime.now()).isoformat() if hasattr(doc.get("uploadedAt", datetime.now()), 'isoformat') else str(doc.get("uploadedAt", datetime.now())),
                                "company_id": actual_startup_id,
                                "lead_id": self.lead_id,
                                "project_id": doc.get("projectId", ""),
                                "mongodb_doc_id": doc_id,
                                "synced_from_mongodb": True
                            })
                        
                        if documents:
                            self.docs_collection.add(
                                documents=documents,
                                ids=ids,
                                metadatas=metadatas
                            )
                            sync_count += len(documents)
            
            if sync_count > 0:
                print(f"✅ Synced {sync_count} document chunks from MongoDB to ChromaDB")
            
        except Exception as e:
            print(f"Warning: Could not sync documents from MongoDB: {e}")
            # Don't fail initialization if sync fails
    
    async def _has_uploaded_documents(self, project_id: Optional[str] = None) -> bool:
        """Check if any documents have been uploaded"""
        try:
            from services.vector_store_service import vector_store_service
            from database import get_database
            from bson import ObjectId
            
            db = get_database()
            
            # Use company_id as startupId (should be resolved by router now)
            startup_id = self.company_id
            context_id = project_id if project_id else self.lead_id
            
            # Strategy 1: Check VectorStoreService collection (used by sync service)
            try:
                vs_collection = vector_store_service.get_or_create_collection(
                    startup_id=startup_id,
                    project_id=context_id,
                    collection_type="documents"
                )
                vs_count = vs_collection.count()
                if vs_count > 0:
                    logger.info(f"Found {vs_count} documents in VectorStore collection")
                    return True
            except Exception as vs_error:
                logger.debug(f"VectorStore check failed (non-fatal): {vs_error}")
            
            # Strategy 2: Check Document Agent's own collection (legacy)
            try:
                doc_count = self.docs_collection.count()
                if doc_count > 0:
                    logger.info(f"Found {doc_count} documents in Document Agent collection")
                    return True
            except Exception as da_error:
                logger.debug(f"Document Agent collection check failed (non-fatal): {da_error}")
            
            # Strategy 3: Check MongoDB directly (source of truth)
            doc_count = 0
            mongo_query = {"startupId": startup_id}
            if project_id:
                mongo_query["projectId"] = project_id
            elif ObjectId.is_valid(self.lead_id):
                # Check if lead_id is actually a project_id
                project = await db.projects.find_one({"_id": ObjectId(self.lead_id)})
                if project:
                    mongo_query["projectId"] = self.lead_id
            
            async for doc in db.documents.find(mongo_query).limit(1):
                if doc.get('extractedContent') and not doc.get('extractedContent', '').startswith('[Error'):
                    doc_count += 1
                    if doc_count > 0:
                        logger.info(f"Found documents in MongoDB for startup_id: {startup_id}")
                        # Trigger sync via sync service
                        try:
                            from services.document_sync_service import document_sync_service
                            sync_result = await document_sync_service.sync_documents_to_chromadb(
                                startup_id=startup_id,
                                lead_id=context_id,
                                project_id=project_id if project_id else (self.lead_id if ObjectId.is_valid(self.lead_id) else None),
                                force_resync=False
                            )
                            logger.info(f"Sync result: {sync_result.get('message', 'Unknown')}")
                            return True
                        except Exception as sync_err:
                            logger.warning(f"Sync failed but documents exist: {sync_err}")
                            return True  # Documents exist in MongoDB, even if sync failed
            
            # Strategy 4: If company_id looks like user.id, get user's startupId
            if doc_count == 0 and ObjectId.is_valid(self.company_id):
                user = await db.users.find_one({"_id": ObjectId(self.company_id)})
                if user and user.get("startupId"):
                    actual_startup_id = user["startupId"]
                    logger.info(f"Resolved user_id {self.company_id} to startup_id {actual_startup_id}")
                    self.company_id = actual_startup_id  # Update for future operations
                    
                    # Check MongoDB with resolved startup_id
                    async for doc in db.documents.find({
                        "startupId": actual_startup_id
                    }).limit(1):
                        if doc.get('extractedContent') and not doc.get('extractedContent', '').startswith('[Error'):
                            logger.info(f"Found documents with resolved startup_id: {actual_startup_id}")
                            # Trigger sync
                            try:
                                from services.document_sync_service import document_sync_service
                                await document_sync_service.sync_documents_to_chromadb(
                                    startup_id=actual_startup_id,
                                    lead_id=self.lead_id,
                                    force_resync=False
                                )
                                return True
                            except Exception as sync_err:
                                logger.warning(f"Sync failed but documents exist: {sync_err}")
                                return True
            
            logger.info(f"No documents found for startup_id: {startup_id}, lead_id: {self.lead_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error checking for documents: {str(e)}", exc_info=True)
            # Fallback: check Document Agent's own collection
            try:
                return self.docs_collection.count() > 0
            except:
                return False
    
    def debug_documents(self) -> dict:
        """Debug method to check document storage"""
        try:
            # Get all documents for this company/lead from ChromaDB
            results = self.docs_collection.get(
                where={
                    "$and": [
                        {"company_id": self.company_id},
                        {"lead_id": self.lead_id}
                    ]
                }
            )
            
            # Also try without the where clause to see all documents
            all_results = self.docs_collection.get()
            
            # Check MongoDB for documents
            from database import get_database
            from bson import ObjectId
            
            db = get_database()
            project = None
            mongodb_docs = 0
            documents_collection_docs = 0
            
            try:
                # Check documents collection (where frontend stores documents)
                documents_collection_docs = len(list(db.documents.find({
                    "startupId": self.company_id,
                    "projectId": self.lead_id
                })))
                
                project = db.projects.find_one({
                    "startupId": self.company_id,
                    "_id": ObjectId(self.lead_id) if ObjectId.is_valid(self.lead_id) else None
                })
                if project and project.get('documents'):
                    mongodb_docs = len(project['documents'])
            except Exception as e:
                print(f"MongoDB check error: {e}")
            
            return {
                "company_id": self.company_id,
                "lead_id": self.lead_id,
                "chromadb_filtered_count": len(results['metadatas']),
                "chromadb_total_count": len(all_results['metadatas']),
                "mongodb_docs_count": mongodb_docs,
                "documents_collection_count": documents_collection_docs,
                "project_found": project is not None,
                "sample_metadata": results['metadatas'][:2] if results['metadatas'] else [],
                "all_sample_metadata": all_results['metadatas'][:3] if all_results['metadatas'] else []
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def chat(self, message: str, project_id: Optional[str] = None) -> Tuple[str, str]:
        """
        Chat with Document Agent about project requirements
        
        Args:
            message: User's message
            project_id: Optional project ID to focus search on specific project
            
        Returns:
            Tuple of (response, chat_id)
        """
        try:
            # Determine project_id from lead_id if it looks like a project_id
            # Otherwise try to extract from self.lead_id
            actual_project_id = project_id
            
            # If lead_id looks like a project ObjectId, use it
            if not actual_project_id and ObjectId.is_valid(self.lead_id):
                from database import get_database
                db = get_database()
                # Check if lead_id is actually a project_id
                project = await db.projects.find_one({"_id": ObjectId(self.lead_id)})
                if project:
                    actual_project_id = self.lead_id
            
            # Ensure documents are synced before checking
            # This is a fallback in case router-level sync didn't work
            try:
                await self._sync_project_documents()
            except Exception as sync_err:
                # Non-fatal - sync might have already happened or MongoDB might be unreachable
                logger.debug(f"Note: Could not sync during chat (non-fatal): {sync_err}")
            
            # Check if we have uploaded documents (INITIAL SOURCE)
            has_documents = await self._has_uploaded_documents(project_id=actual_project_id)
            
            if not has_documents:
                # No documents uploaded yet - provide guidance
                response = f"""I notice you haven't uploaded any project documents yet. To provide you with the most accurate and helpful analysis, I need access to your project documentation.

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
                
                chat_id = self._store_chat(message, response)
                return response, chat_id
            
            # Search for relevant document context (INITIAL SOURCE)
            context_docs = await self.search_documents(message, n_results=5, project_id=actual_project_id)
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
            
            return response, chat_id
            
        except Exception as e:
            error_response = f"I encountered an error: {str(e)}"
            chat_id = self._store_chat(message, error_response)
            return error_response, chat_id
    
    async def chat_with_agent(self, message: str, project_id: Optional[str] = None) -> dict:
        """Simple chat interface for the frontend"""
        try:
            response, chat_id = await self.chat(message, project_id=project_id)
            return {
                "response": response,
                "agent": "Document Agent",
                "timestamp": datetime.now().isoformat(),
                "chat_id": chat_id
            }
        except Exception as e:
            logger.error(f"Error in chat_with_agent: {e}", exc_info=True)
            return {
                "response": f"I encountered an error: {str(e)}",
                "agent": "Document Agent",
                "timestamp": datetime.now().isoformat(),
                "chat_id": ""
            }
    
    def _store_chat(self, lead_message: str, agent_response: str) -> str:
        """Store chat exchange in ChromaDB"""
        chat_id = str(uuid.uuid4())
        
        conversation = f"Lead: {lead_message}\nDocument Agent: {agent_response}"
        
        self.chat_collection.add(
            documents=[conversation],
            ids=[chat_id],
            metadatas=[{
                "chat_id": chat_id,
                "lead_message": lead_message,
                "agent_response": agent_response,
                "timestamp": datetime.now().isoformat(),
                "company_id": self.company_id,
                "lead_id": self.lead_id
            }]
        )
        
        return chat_id
    
    def get_chat_history(self) -> List[Dict]:
        """Get complete chat history for this lead"""
        try:
            results = self.chat_collection.get(
                where={
                    "$and": [
                        {"company_id": self.company_id},
                        {"lead_id": self.lead_id}
                    ]
                }
            )
            
            if not results['metadatas']:
                return []
            
            chats = []
            for metadata in results['metadatas']:
                chats.append({
                    "chat_id": metadata['chat_id'],
                    "lead_message": metadata['lead_message'],
                    "agent_response": metadata['agent_response'],
                    "timestamp": metadata['timestamp']
                })
            
            # Sort by timestamp
            chats.sort(key=lambda x: x['timestamp'])
            return chats
            
        except Exception as e:
            print(f"Error retrieving chat history: {str(e)}")
            return []
    
    def get_all_documents_summary(self) -> Dict:
        """Get summary of all uploaded documents"""
        try:
            all_docs = self.docs_collection.get(
                where={
                    "company_id": self.company_id,
                    "lead_id": self.lead_id
                }
            )
            
            # Group by document_id
            doc_map = {}
            for metadata in all_docs['metadatas']:
                doc_id = metadata['document_id']
                if doc_id not in doc_map:
                    doc_map[doc_id] = {
                        "document_id": doc_id,
                        "filename": metadata['filename'],
                        "upload_time": metadata['upload_time'],
                        "chunks": 0
                    }
                doc_map[doc_id]["chunks"] += 1
            
            return {
                "total_documents": len(doc_map),
                "documents": list(doc_map.values())
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def export_context_for_stack_agent(self) -> Dict:
        """
        Export all context for Stack Agent to use
        
        Returns:
            Dict containing documents summary, complete chat history, and key requirements
        """
        return {
            "documents_summary": self.get_all_documents_summary(),
            "chat_history": self.get_chat_history(),
            "document_embeddings_path": str(self.company_lead_path / "documents"),
            "company_id": self.company_id,
            "lead_id": self.lead_id,
            "export_time": datetime.now().isoformat()
        }

