import streamlit as st
import os
import uuid
from datetime import datetime
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from crewai import Agent, Task, Crew, Process
from langchain_community.llms import Ollama
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import PyPDF2
from docx import Document as DocxDocument
import io
import json

# Initialize ChromaDB
@st.cache_resource
def init_chromadb():
    """Initialize ChromaDB with persistent storage"""
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Create collections
    docs_collection = client.get_or_create_collection(
        name="project_documents",
        metadata={"description": "Project documents for RAG"}
    )
    
    chat_collection = client.get_or_create_collection(
        name="chat_history",
        metadata={"description": "Chat conversations storage"}
    )
    
    return client, docs_collection, chat_collection

# Initialize Ollama LLM
@st.cache_resource
def init_llm():
    """Initialize Ollama LLM"""
    return Ollama(
        model="llama3.1:8b",
        base_url="http://localhost:11434"
    )

class DocumentProcessor:
    """Handle document processing and RAG operations"""
    
    def __init__(self, docs_collection, chat_collection):
        self.docs_collection = docs_collection
        self.chat_collection = chat_collection
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def extract_text_from_pdf(self, pdf_file) -> str:
        """Extract text from PDF file"""
        try:
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            st.error(f"Error reading PDF: {str(e)}")
            return ""
    
    def extract_text_from_docx(self, docx_file) -> str:
        """Extract text from DOCX file"""
        try:
            doc = DocxDocument(docx_file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            st.error(f"Error reading DOCX: {str(e)}")
            return ""
    
    def process_document(self, uploaded_file) -> bool:
        """Process uploaded document and store in ChromaDB"""
        try:
            # Extract text based on file type
            if uploaded_file.type == "application/pdf":
                text = self.extract_text_from_pdf(uploaded_file)
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                text = self.extract_text_from_docx(uploaded_file)
            elif uploaded_file.type == "text/plain":
                text = str(uploaded_file.read(), "utf-8")
            else:
                st.error("Unsupported file type")
                return False
            
            if not text:
                st.error("No text extracted from document")
                return False
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            
            # Create documents
            documents = []
            ids = []
            metadatas = []
            
            for i, chunk in enumerate(chunks):
                doc_id = f"{uploaded_file.name}_{i}_{uuid.uuid4().hex[:8]}"
                ids.append(doc_id)
                documents.append(chunk)
                metadatas.append({
                    "filename": uploaded_file.name,
                    "chunk_index": i,
                    "upload_time": datetime.now().isoformat()
                })
            
            # Add to ChromaDB
            self.docs_collection.add(
                documents=documents,
                ids=ids,
                metadatas=metadatas
            )
            
            return True
            
        except Exception as e:
            st.error(f"Error processing document: {str(e)}")
            return False
    
    def search_documents(self, query: str, n_results: int = 5) -> List[str]:
        """Search documents in ChromaDB"""
        try:
            results = self.docs_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            return results['documents'][0] if results['documents'] else []
        except Exception as e:
            st.error(f"Error searching documents: {str(e)}")
            return []
    
    def store_chat(self, user_message: str, agent_response: str, session_id: str):
        """Store chat conversation in ChromaDB"""
        try:
            chat_id = f"chat_{session_id}_{uuid.uuid4().hex[:8]}"
            conversation = f"User: {user_message}\nDocAgent: {agent_response}"
            
            self.chat_collection.add(
                documents=[conversation],
                ids=[chat_id],
                metadatas=[{
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "user_message": user_message,
                    "agent_response": agent_response
                }]
            )
        except Exception as e:
            st.error(f"Error storing chat: {str(e)}")
    
    def get_chat_history(self, session_id: str) -> List[Dict]:
        """Retrieve chat history for a session"""
        try:
            results = self.chat_collection.get(
                where={"session_id": session_id}
            )
            
            chat_history = []
            if results['metadatas']:
                for metadata in results['metadatas']:
                    chat_history.append({
                        "timestamp": metadata['timestamp'],
                        "user_message": metadata['user_message'],
                        "agent_response": metadata['agent_response']
                    })
            
            # Sort by timestamp
            chat_history.sort(key=lambda x: x['timestamp'])
            return chat_history
            
        except Exception as e:
            st.error(f"Error retrieving chat history: {str(e)}")
            return []

class DocAgentCreator:
    """Create and manage the DocAgent using CrewAI"""
    
    def __init__(self, llm, document_processor):
        self.llm = llm
        self.doc_processor = document_processor
        self.agent = self._create_agent()
    
    def _create_agent(self):
        """Create the DocAgent with specific role and capabilities"""
        return Agent(
            role='Technical Project Lead & Document Analyst',
            goal='''Analyze project documents thoroughly and provide strategic insights. 
                    Act as an experienced team lead who asks probing questions, 
                    identifies potential issues, and provides detailed technical analysis.''',
            backstory='''You are DocAgent, a highly experienced technical project lead with expertise 
                        in project analysis, risk assessment, and strategic planning. You have a keen eye 
                        for detail and always ask the right questions to ensure project success. 
                        You combine technical depth with strategic thinking.''',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_summary_task(self, context_docs: List[str]) -> Task:
        """Create a task for document summarization"""
        context = "\n\n".join(context_docs) if context_docs else "No relevant documents found."
        
        return Task(
            description=f'''Analyze and summarize the following project documentation:
                           
                           {context}
                           
                           Provide a comprehensive summary that includes:
                           1. Project Overview & Objectives
                           2. Key Technical Requirements
                           3. Potential Risks & Challenges
                           4. Strategic Recommendations
                           5. Critical Questions that need clarification
                           
                           Think like a technical project lead and be probing in your analysis.''',
            expected_output='''A detailed project summary with strategic insights, 
                              potential concerns, and probing questions for the team.''',
            agent=self.agent
        )
    
    def create_qa_task(self, question: str, context_docs: List[str]) -> Task:
        """Create a task for answering specific questions"""
        context = "\n\n".join(context_docs) if context_docs else "No relevant documents found."
        
        return Task(
            description=f'''Based on the project documentation context:
                           
                           {context}
                           
                           Answer this question: {question}
                           
                           Provide a detailed, technical response and if applicable:
                           - Ask follow-up questions for clarification
                           - Identify any concerns or risks
                           - Suggest actionable next steps
                           - Reference specific parts of the documentation''',
            expected_output='''A comprehensive answer with technical details, 
                              strategic insights, and probing follow-up questions.''',
            agent=self.agent
        )
    
    def execute_task(self, task: Task) -> str:
        """Execute a task using CrewAI"""
        try:
            crew = Crew(
                agents=[self.agent],
                tasks=[task],
                verbose=True,
                process=Process.sequential
            )
            
            result = crew.kickoff()
            return str(result)
        except Exception as e:
            st.error(f"Error executing task: {str(e)}")
            return f"Error: {str(e)}"

def main():
    """Main Streamlit application"""
    
    st.set_page_config(
        page_title="DocAgent - AI Project Lead Assistant",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 DocAgent - AI Project Lead Assistant")
    st.markdown("*Your AI-powered technical project lead for document analysis and strategic insights*")
    
    # Initialize session state
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Initialize components
    try:
        client, docs_collection, chat_collection = init_chromadb()
        llm = init_llm()
        doc_processor = DocumentProcessor(docs_collection, chat_collection)
        doc_agent = DocAgentCreator(llm, doc_processor)
    except Exception as e:
        st.error(f"Error initializing system: {str(e)}")
        st.stop()
    
    # Sidebar for document upload
    with st.sidebar:
        st.header("📄 Document Management")
        
        uploaded_file = st.file_uploader(
            "Upload Project Document",
            type=['pdf', 'docx', 'txt'],
            help="Upload project documents for analysis"
        )
        
        if uploaded_file is not None:
            if st.button("Process Document"):
                with st.spinner("Processing document..."):
                    if doc_processor.process_document(uploaded_file):
                        st.success(f"✅ {uploaded_file.name} processed successfully!")
                    else:
                        st.error("❌ Failed to process document")
        
        st.divider()
        
        # Document summary section
        st.header("📋 Project Summary")
        if st.button("Generate Project Summary"):
            with st.spinner("Generating comprehensive project summary..."):
                # Get relevant documents for summary
                context_docs = doc_processor.search_documents("project overview requirements objectives", n_results=10)
                
                # Create and execute summary task
                summary_task = doc_agent.create_summary_task(context_docs)
                summary = doc_agent.execute_task(summary_task)
                
                st.session_state.last_summary = summary
                st.rerun()
        
        if hasattr(st.session_state, 'last_summary'):
            with st.expander("📄 Latest Project Summary", expanded=False):
                st.write(st.session_state.last_summary)
    
    # Main chat interface
    st.header("💬 Chat with DocAgent")
    st.markdown("Ask questions about your project documents. DocAgent will provide detailed, strategic insights.")
    
    # Display chat history
    if st.session_state.chat_history:
        st.subheader("Conversation History")
        for i, (user_msg, agent_msg) in enumerate(st.session_state.chat_history):
            with st.container():
                st.markdown(f"**🧑 You:** {user_msg}")
                st.markdown(f"**🤖 DocAgent:** {agent_msg}")
                st.divider()
    
    # Chat input
    user_question = st.text_input(
        "Ask DocAgent about your project:",
        placeholder="e.g., What are the main risks in this project? What technical challenges should we expect?",
        key="user_input"
    )
    
    col1, col2, col3 = st.columns([1, 1, 4])
    
    with col1:
        send_button = st.button("Send", type="primary")
    
    with col2:
        clear_button = st.button("Clear Chat")
    
    if clear_button:
        st.session_state.chat_history = []
        st.rerun()
    
    if send_button and user_question:
        with st.spinner("DocAgent is analyzing and thinking..."):
            # Search for relevant documents
            context_docs = doc_processor.search_documents(user_question, n_results=5)
            
            # Create and execute QA task
            qa_task = doc_agent.create_qa_task(user_question, context_docs)
            agent_response = doc_agent.execute_task(qa_task)
            
            # Store conversation
            st.session_state.chat_history.append((user_question, agent_response))
            doc_processor.store_chat(user_question, agent_response, st.session_state.session_id)
            
            st.rerun()
    
    # Footer
    st.divider()
    st.markdown("*Powered by CrewAI, Ollama (Llama3.1:8B), and ChromaDB*")

if __name__ == "__main__":
    main()