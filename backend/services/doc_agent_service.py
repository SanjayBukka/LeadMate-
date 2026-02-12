"""
DocAgent Service
AI-powered document analyst using CrewAI and RAG
"""
import os
# Set environment variables BEFORE importing CrewAI
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', 'sk-dummy-not-used')
os.environ['CREWAI_DISABLE_TELEMETRY'] = 'true'
# Set Ollama API base for litellm
os.environ['OLLAMA_API_BASE'] = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')

from crewai import Agent, Task, Crew, Process
from typing import List, Dict, Optional, AsyncGenerator
import logging
import asyncio
import json
import ollama
from services.gemini_service import gemini_service
from services.vector_store_service import vector_store_service
from services.cache_service import llm_cache

logger = logging.getLogger(__name__)


class DocAgentService:
    """
    Document Analysis Agent using CrewAI
    Provides Q&A, summarization, and strategic insights
    """
    
    def __init__(self):
        self.llm = None
        self.agent = None
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the DocAgent with CrewAI"""
        try:
            # Get model string for CrewAI (uses litellm format: "ollama/llama3.2:3b")
            model_name = gemini_service.get_llm()
            
            logger.info(f"Initializing DocAgent with model: {model_name}")
            
            # Create the DocAgent - pass model string (CrewAI will use litellm)
            self.agent = Agent(
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
                llm=model_name  # Pass model string (e.g., "ollama/llama3.2:3b")
            )
            
            logger.info(f"DocAgent initialized successfully with model: {model_name}")
        except Exception as e:
            logger.error(f"Error initializing DocAgent: {e}")
            raise
    
    def _get_relevant_context(
        self, 
        startup_id: str, 
        project_id: str, 
        query: str, 
        n_results: int = 5
    ) -> List[str]:
        """
        Get relevant document context from ChromaDB
        
        Args:
            startup_id: Startup identifier
            project_id: Project identifier  
            query: Search query
            n_results: Number of documents to retrieve
        
        Returns:
            List of relevant document chunks
        """
        try:
            documents = vector_store_service.search_documents(
                startup_id=startup_id,
                project_id=project_id,
                query=query,
                n_results=n_results
            )
            
            if not documents:
                logger.warning(f"No documents found for query: {query}")
                return ["No relevant documents found. Please upload project documents first."]
            
            return documents
        except Exception as e:
            logger.error(f"Error getting relevant context: {e}")
            return ["Error retrieving documents from database."]
    
    def answer_question(
        self,
        startup_id: str,
        project_id: str,
        question: str,
        chat_history: Optional[List[Dict]] = None,
        use_cache: bool = True
    ) -> str:
        """
        Answer a question about project documents using RAG with caching
        
        Args:
            startup_id: Startup identifier
            project_id: Project identifier
            question: User's question
            chat_history: Optional previous chat messages
            use_cache: Whether to use cached responses (default: True)
        
        Returns:
            Agent's answer
        """
        try:
            # Get relevant documents
            context_docs = self._get_relevant_context(
                startup_id=startup_id,
                project_id=project_id,
                query=question,
                n_results=5
            )
            
            # Build context string
            context = "\n\n".join(context_docs)
            
            # Check cache first
            if use_cache:
                cached_response = llm_cache.get(
                    prompt=question,
                    context="",  # Don't include context in cache key for better hit rate
                    model=gemini_service.model
                )
                if cached_response:
                    logger.info("✅ Returning cached response")
                    return cached_response
            
            # Add chat history if available
            history_context = ""
            if chat_history and len(chat_history) > 0:
                history_context = "\n\nPrevious conversation:\n"
                for msg in chat_history[-3:]:  # Last 3 messages for context
                    history_context += f"User: {msg.get('user_message', '')}\n"
                    history_context += f"DocAgent: {msg.get('agent_response', '')}\n\n"
            
            # Create QA task
            task = Task(
                description=f'''Based on the project documentation context:
                               
                               {context}
                               
                               {history_context}
                               
                               Answer this question: {question}
                               
                               Provide a detailed, technical response and if applicable:
                               - Ask follow-up questions for clarification
                               - Identify any concerns or risks
                               - Suggest actionable next steps
                               - Reference specific parts of the documentation
                               
                               Be conversational and helpful. If the documents don't contain 
                               enough information to answer fully, acknowledge that and suggest 
                               what additional information might be needed.''',
                expected_output='''A comprehensive answer with technical details, 
                                  strategic insights, and probing follow-up questions.''',
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
            
            # Cache the response
            if use_cache:
                llm_cache.set(
                    prompt=question,
                    response=response,
                    context="",  # Don't include context in cache key for better hit rate
                    model=gemini_service.model
                )
            
            # Store in chat history
            vector_store_service.store_chat_message(
                startup_id=startup_id,
                project_id=project_id,
                user_message=question,
                agent_response=response
            )
            
            logger.info(f"DocAgent answered question successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return f"I encountered an error while processing your question: {str(e)}. Please try again or rephrase your question."
    
    async def answer_question_stream(
        self,
        startup_id: str,
        project_id: str,
        question: str,
        chat_history: Optional[List[Dict]] = None,
        use_cache: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        Stream answer to a question using SSE (Server-Sent Events)
        
        Args:
            startup_id: Startup identifier
            project_id: Project identifier
            question: User's question
            chat_history: Optional previous chat messages
            use_cache: Whether to check cache first
        
        Yields:
            Token chunks as they're generated
        """
        try:
            # Get relevant documents
            context_docs = self._get_relevant_context(
                startup_id=startup_id,
                project_id=project_id,
                query=question,
                n_results=5
            )
            
            context = "\n\n".join(context_docs)
            
            # Check cache first
            if use_cache:
                cached_response = llm_cache.get(
                    prompt=question,
                    context="",  # Don't include context in cache key for better hit rate
                    model=gemini_service.model
                )
                if cached_response:
                    logger.info("✅ Streaming cached response")
                    # Stream cached response word by word for smooth UX with proper spacing
                    words = cached_response.split()
                    for i, word in enumerate(words):
                        # Add space after word except for the last one
                        token = word + (" " if i < len(words) - 1 else "")
                        yield f"data: {json.dumps(token)}\n\n"
                        await asyncio.sleep(0.02)  # Simulate streaming
                    yield "data: [DONE]\n\n"
                    return
            
            # Build prompt
            history_context = ""
            if chat_history and len(chat_history) > 0:
                history_context = "\n\nPrevious conversation:\n"
                for msg in chat_history[-3:]:
                    history_context += f"User: {msg.get('user_message', '')}\n"
                    history_context += f"DocAgent: {msg.get('agent_response', '')}\n\n"
            
            prompt = f'''Based on the project documentation context:
            
{context}

{history_context}

Answer this question: {question}

Provide a detailed, technical response and if applicable:
- Ask follow-up questions for clarification
- Identify any concerns or risks
- Suggest actionable next steps
- Reference specific parts of the documentation

Be conversational and helpful.'''
            
            # Stream from Ollama directly
            full_response = ""
            stream = ollama.chat(
                model='llama3.2:3b',
                messages=[{'role': 'user', 'content': prompt}],
                stream=True
            )
            
            for chunk in stream:
                token = chunk['message']['content']
                if token:  # Only send non-empty tokens
                    full_response += token
                    # Send token as JSON to properly preserve spaces and special characters
                    yield f"data: {json.dumps(token)}\n\n"
            
            # Cache the full response
            if use_cache:
                llm_cache.set(
                    prompt=question,
                    response=full_response,
                    context="",  # Don't include context in cache key for better hit rate
                    model=gemini_service.model
                )
            
            # Store in chat history
            vector_store_service.store_chat_message(
                startup_id=startup_id,
                project_id=project_id,
                user_message=question,
                agent_response=full_response
            )
            
            yield "data: [DONE]\n\n"
            logger.info(f"✅ DocAgent streamed answer successfully")
            
        except Exception as e:
            logger.error(f"Error streaming answer: {e}")
            yield f"data: Error: {str(e)}\n\n"
            yield "data: [DONE]\n\n"
    
    def generate_project_summary(
        self,
        startup_id: str,
        project_id: str
    ) -> str:
        """
        Generate a comprehensive project summary
        
        Args:
            startup_id: Startup identifier
            project_id: Project identifier
        
        Returns:
            Project summary
        """
        try:
            # Get broad context documents
            context_docs = self._get_relevant_context(
                startup_id=startup_id,
                project_id=project_id,
                query="project overview requirements objectives features functionality",
                n_results=10
            )
            
            context = "\n\n".join(context_docs)
            
            # Create summary task
            task = Task(
                description=f'''Analyze and summarize the following project documentation:
                               
                               {context}
                               
                               Provide a comprehensive summary that includes:
                               1. **Project Overview & Objectives**: What is the project trying to achieve?
                               2. **Key Technical Requirements**: What are the main technical specifications?
                               3. **Potential Risks & Challenges**: What could go wrong? What are the concerns?
                               4. **Strategic Recommendations**: What should the team focus on?
                               5. **Critical Questions**: What needs clarification from stakeholders?
                               
                               Think like a technical project lead and be probing in your analysis.
                               Use clear headings and bullet points for readability.''',
                expected_output='''A detailed project summary with strategic insights, 
                                  potential concerns, and probing questions for the team.
                                  Format with clear sections and bullet points.''',
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
            summary = str(result)
            
            logger.info(f"DocAgent generated project summary successfully")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"I encountered an error while generating the summary: {str(e)}. Please ensure project documents are uploaded and try again."
    
    def get_chat_history(
        self,
        startup_id: str,
        project_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get chat history for a project
        
        Args:
            startup_id: Startup identifier
            project_id: Project identifier
            limit: Maximum number of messages
        
        Returns:
            List of chat messages
        """
        try:
            return vector_store_service.get_chat_history(
                startup_id=startup_id,
                project_id=project_id,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []


# Global instance
doc_agent_service = DocAgentService()

