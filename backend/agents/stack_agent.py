"""
Stack Agent - Forms teams based on document analysis and maintains iteration history
"""
import os
import uuid
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import chromadb
from crewai import Agent, Task, Crew, Process
import PyPDF2
import io
from services.gemini_service import gemini_service
from services.vector_store_service import vector_store_service
from langchain_community.llms import Ollama
import logging

logger = logging.getLogger(__name__)


class StackAgent:
    """
    Stack Agent analyzes requirements and team member resumes to form optimal teams.
    Supports iterative refinement and generates final comprehensive reports.
    """
    
    def __init__(self, company_id: str, lead_id: str, base_path: str = "./chroma_db"):
        self.company_id = company_id
        self.lead_id = lead_id
        self.base_path = Path(base_path)
        
        # Use same directory structure as Document Agent
        self.company_lead_path = self.base_path / f"company_{company_id}" / f"lead_{lead_id}"
        self.company_lead_path.mkdir(parents=True, exist_ok=True)
        
        # Create output directories
        self.iterations_path = self.company_lead_path / "stack_iterations"
        self.iterations_path.mkdir(exist_ok=True)
        
        self.reports_path = self.company_lead_path / "final_reports"
        self.reports_path.mkdir(exist_ok=True)
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.company_lead_path)
        )
        
        # Get existing collections from Document Agent
        try:
            self.docs_collection = self.chroma_client.get_collection("documents")
            self.doc_chat_collection = self.chroma_client.get_collection("doc_chat")
        except:
            self.docs_collection = None
            self.doc_chat_collection = None
        
        # Create collections for Stack Agent
        self.resumes_collection = self.chroma_client.get_or_create_collection(
            name="resumes",
            metadata={"description": "Team member resumes"}
        )
        
        self.iterations_collection = self.chroma_client.get_or_create_collection(
            name="stack_iterations",
            metadata={"description": "Team formation iterations with lead"}
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
                logger.info(f"Using Ollama for StackAgent: model={ollama_model} base={ollama_base}")
            else:
                try:
                    self.llm = gemini_service.get_llm()
                    self.crewai_llm = getattr(gemini_service, "crewai_model", None)
                    logger.info(f"Using Gemini for StackAgent: {gemini_service.llm_type} ({gemini_service.model})")
                except Exception as ge:
                    logger.warning(f"Gemini init failed for StackAgent ({ge}), falling back to Ollama")
                    self.crewai_llm = f"ollama/{ollama_model}"
                    try:
                        self.llm = Ollama(model=ollama_model, base_url=ollama_base)
                    except Exception:
                        self.llm = None
        except Exception as e:
            self.llm = None
            self.crewai_llm = None
            logger.error(f"LLM initialization failed for StackAgent: {e}")
        
        # Create CrewAI agent
        self.agent = self._create_agent()
        
        # Track current iteration
        self.current_iteration = 0
        self.current_team = None
    
    def _create_agent(self):
        """Create Team Formation Agent with CrewAI"""
        llm_for_crewai = self.crewai_llm if self.crewai_llm else self.llm
        if not llm_for_crewai:
            return None
            
        return Agent(
            role='Senior Team Formation Specialist',
            goal='''Analyze project requirements, team member skills, and form optimal teams. 
                    Iteratively refine team composition based on lead feedback and maintain 
                    complete reasoning for all decisions.''',
            backstory='''You are an expert in team formation with 15+ years of experience building 
                        successful development teams. You understand skill matching, team dynamics, 
                        project requirements, and can identify skill gaps. You excel at explaining 
                        your reasoning and adapting teams based on feedback while maintaining 
                        project success criteria.''',
            verbose=True,
            allow_delegation=False,
            llm=llm_for_crewai
        )
    
    def upload_resume(self, file_data: bytes, filename: str, candidate_name: str) -> Dict:
        """Upload and process a team member resume"""
        try:
            # Extract text from PDF resume
            text = self._extract_text_from_pdf(file_data)
            
            if not text:
                return {"success": False, "error": "No text extracted from resume"}
            
            # Create resume ID
            resume_id = str(uuid.uuid4())
            
            # Store full resume in ChromaDB
            self.resumes_collection.add(
                documents=[text],
                ids=[resume_id],
                metadatas=[{
                    "resume_id": resume_id,
                    "filename": filename,
                    "candidate_name": candidate_name,
                    "upload_time": datetime.now().isoformat(),
                    "company_id": self.company_id,
                    "lead_id": self.lead_id
                }]
            )
            
            # Extract skills using LLM
            skills = self._extract_skills(text, candidate_name)
            
            return {
                "success": True,
                "resume_id": resume_id,
                "candidate_name": candidate_name,
                "skills_extracted": skills
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _extract_text_from_pdf(self, file_data: bytes) -> str:
        """Extract text from PDF resume"""
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(file_data))
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            print(f"Error reading PDF: {str(e)}")
            return ""
    
    def _extract_skills(self, resume_text: str, candidate_name: str) -> Dict:
        """Extract skills from resume using LLM"""
        if not self.llm:
            return {"skills": ["Programming"], "experience_years": 3}
        
        try:
            prompt = f"""Analyze this resume and extract structured information in JSON format:
            
            {resume_text}
            
            Extract:
            - programming_languages: list of languages
            - frameworks: list of frameworks
            - databases: list of databases
            - cloud: cloud platforms
            - experience_years: total years of experience
            - specialization: primary area of expertise
            
            Return ONLY valid JSON."""
            
            response = self.llm.invoke(prompt)
            
            # Try to parse JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            return {"skills": ["Programming"], "experience_years": 3}
            
        except Exception as e:
            print(f"Error extracting skills: {e}")
            return {"skills": ["Programming"], "experience_years": 3}
    
    def get_all_resumes(self) -> List[Dict]:
        """Get all uploaded resumes for this lead"""
        try:
            results = self.resumes_collection.get(
                where={
                    "company_id": self.company_id,
                    "lead_id": self.lead_id
                }
            )
            
            resumes = []
            for i, metadata in enumerate(results['metadatas']):
                resumes.append({
                    "resume_id": metadata['resume_id'],
                    "candidate_name": metadata['candidate_name'],
                    "filename": metadata['filename'],
                    "upload_time": metadata['upload_time'],
                    "resume_text": results['documents'][i]
                })
            
            return resumes
            
        except Exception as e:
            print(f"Error getting resumes: {e}")
            return []
    
    def generate_initial_team(self) -> Dict:
        """
        Generate initial team recommendation based on:
        - Project documents (from Document Agent)
        - Chat history (clarifications)
        - Uploaded resumes
        """
        try:
            # Get context from Document Agent
            doc_context = self._get_document_context()
            chat_history = self._get_chat_history()
            resumes = self.get_all_resumes()
            
            if not resumes:
                return {"success": False, "error": "No resumes uploaded"}
            
            # Create team formation task
            if self.agent:
                task = Task(
                    description=f'''Form an optimal development team based on project requirements 
                                   and available team members.
                                   
                                   PROJECT CONTEXT:
                                   {doc_context}
                                   
                                   REQUIREMENTS CLARIFICATIONS (from Document Agent chat):
                                   {chat_history}
                                   
                                   AVAILABLE TEAM MEMBERS:
                                   {self._format_resumes(resumes)}
                                   
                                   Provide:
                                   1. Recommended team composition with role assignments
                                   2. Skills match analysis for each member
                                   3. Identified skill gaps
                                   4. Reasoning for each selection
                                   5. Risk assessment
                                   
                                   Format as structured JSON.''',
                    expected_output='JSON team recommendation with detailed reasoning',
                    agent=self.agent
                )
                
                crew = Crew(
                    agents=[self.agent],
                    tasks=[task],
                    verbose=False,
                    process=Process.sequential
                )
                
                recommendation = str(crew.kickoff())
            else:
                # Fallback recommendation
                recommendation = json.dumps({
                    "team": [{"name": r["candidate_name"], "role": "Developer"} for r in resumes[:3]],
                    "reasoning": "Initial team based on available candidates"
                })
            
            # Store iteration
            iteration_id = self._store_iteration("initial", recommendation, "Initial team generation")
            
            self.current_iteration = 1
            self.current_team = recommendation
            
            return {
                "success": True,
                "iteration_id": iteration_id,
                "team_recommendation": recommendation,
                "iteration_number": 1
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def iterate_team(self, lead_feedback: str) -> Dict:
        """
        Refine team based on lead feedback
        
        Args:
            lead_feedback: Lead's request for changes (e.g., "Replace Alice with someone else")
        """
        try:
            if not self.current_team:
                return {"success": False, "error": "No initial team generated yet"}
            
            # Get iteration history
            iterations = self._get_iteration_history()
            
            if self.agent:
                task = Task(
                    description=f'''Refine the team composition based on lead feedback.
                                   
                                   CURRENT TEAM:
                                   {self.current_team}
                                   
                                   PREVIOUS ITERATIONS:
                                   {self._format_iterations(iterations)}
                                   
                                   LEAD FEEDBACK: {lead_feedback}
                                   
                                   AVAILABLE TEAM MEMBERS:
                                   {self._format_resumes(self.get_all_resumes())}
                                   
                                   Analyze the request and:
                                   1. Update team composition if feasible
                                   2. Explain changes made and reasoning
                                   3. Flag any concerns or trade-offs
                                   4. Suggest alternatives if request cannot be fulfilled
                                   
                                   Return updated team as JSON with reasoning.''',
                    expected_output='JSON updated team with change explanation',
                    agent=self.agent
                )
                
                crew = Crew(
                    agents=[self.agent],
                    tasks=[task],
                    verbose=False,
                    process=Process.sequential
                )
                
                updated_team = str(crew.kickoff())
            else:
                updated_team = self.current_team
            
            # Store iteration
            iteration_id = self._store_iteration(lead_feedback, updated_team, f"Iteration {self.current_iteration + 1}")
            
            self.current_iteration += 1
            self.current_team = updated_team
            
            return {
                "success": True,
                "iteration_id": iteration_id,
                "team_recommendation": updated_team,
                "iteration_number": self.current_iteration
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def finalize_team(self) -> Dict:
        """
        Generate comprehensive final report synthesizing all context and iterations
        """
        try:
            if not self.current_team:
                return {"success": False, "error": "No team to finalize"}
            
            # Get all context
            doc_context = self._get_document_context()
            chat_history = self._get_chat_history()
            iterations = self._get_iteration_history()
            resumes = self.get_all_resumes()
            
            # Generate final report
            if self.agent:
                task = Task(
                    description=f'''Generate a comprehensive final team formation report.
                                   
                                   INITIAL PROJECT REQUIREMENTS:
                                   {doc_context}
                                   
                                   REQUIREMENTS CLARIFICATIONS:
                                   {chat_history}
                                   
                                   ALL TEAM ITERATIONS:
                                   {self._format_iterations(iterations)}
                                   
                                   FINAL TEAM:
                                   {self.current_team}
                                   
                                   TEAM MEMBER DETAILS:
                                   {self._format_resumes(resumes)}
                                   
                                   Create a comprehensive report including:
                                   
                                   ## Executive Summary
                                   - Final team composition
                                   - Key strengths
                                   - Primary risks and mitigations
                                   
                                   ## Team Members & Roles
                                   - Detailed role assignments
                                   - Skills alignment with requirements
                                   - Experience levels
                                   
                                   ## Decision Journey
                                   - Initial recommendation reasoning
                                   - All changes made and why
                                   - Trade-offs and decisions
                                   
                                   ## Skills Analysis
                                   - Requirements coverage
                                   - Skill gaps and mitigation strategies
                                   - Growth opportunities
                                   
                                   ## Team Dynamics
                                   - Predicted collaboration patterns
                                   - Potential challenges
                                   - Success factors
                                   
                                   ## Implementation Recommendations
                                   - Onboarding priorities
                                   - Risk management
                                   - Timeline considerations
                                   
                                   Format as detailed markdown report.''',
                    expected_output='Comprehensive final team formation report',
                    agent=self.agent
                )
                
                crew = Crew(
                    agents=[self.agent],
                    tasks=[task],
                    verbose=False,
                    process=Process.sequential
                )
                
                final_report = str(crew.kickoff())
            else:
                final_report = f"# Final Team Report\n\n{self.current_team}"
            
            # Save report to file
            report_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_filename = f"final_team_report_{timestamp}.md"
            report_path = self.reports_path / report_filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(final_report)
            
            # Save JSON metadata
            metadata = {
                "report_id": report_id,
                "company_id": self.company_id,
                "lead_id": self.lead_id,
                "timestamp": datetime.now().isoformat(),
                "total_iterations": self.current_iteration,
                "final_team": self.current_team,
                "report_path": str(report_path),
                "report_filename": report_filename
            }
            
            json_path = self.reports_path / f"final_team_report_{timestamp}.json"
            with open(json_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return {
                "success": True,
                "report_id": report_id,
                "report_path": str(report_path),
                "report_content": final_report,
                "metadata": metadata
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def chat_with_agent(self, message: str) -> dict:
        """Simple chat interface for the frontend"""
        try:
            # Get document context (from VectorStore/Chroma) and recent chat history
            doc_context = self._get_document_context()
            chat_history = self._get_chat_history()

            # If we have an LLM agent, generate a contextual response using CrewAI
            if self.agent:
                task = Task(
                    description=(
                        f"You are assisting a team lead with technology stack and team formation.\n\n"
                        f"PROJECT DOCUMENT CONTEXT (summaries/snippets):\n{doc_context}\n\n"
                        f"RECENT CONVERSATION (if any):\n{chat_history}\n\n"
                        f"LEAD'S QUESTION: {message}\n\n"
                        "Provide a specific, actionable response grounded in the project context.\n"
                        "If requirements are ambiguous, ask 2-3 targeted clarifying questions."
                    ),
                    expected_output="A concise, contextual answer that references the project where relevant.",
                    agent=self.agent
                )
                crew = Crew(agents=[self.agent], tasks=[task], process=Process.sequential, verbose=False)
                response = str(crew.kickoff())
            else:
                # Fallback: compose a contextual message from available context
                base = (
                    "I'm the Stack Agent. Here's what I gather from your project documents, and how I can help next:\n\n"
                )
                ctx = doc_context if doc_context and doc_context != "No documents found" else "(no document context available)"
                response = (
                    f"{base}Document context: {ctx[:600]}...\n\n"
                    f"Your question: {message}\n\n"
                    "I can recommend frontend/backend, database, cloud, and propose team roles based on the above."
                )
            
            return {
                "response": response,
                "agent": "Stack Agent",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "response": f"I encountered an error: {str(e)}",
                "agent": "Stack Agent",
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_document_context(self) -> str:
        """Get document context prioritizing shared VectorStore (project-based)."""
        # VectorStore (startup_id=company_id, project_id=lead_id)
        try:
            collection = vector_store_service.get_or_create_collection(
                startup_id=self.company_id,
                project_id=self.lead_id,
                collection_type="documents"
            )
            res = collection.get()
            docs = res.get('documents') or []
            if docs:
                return "\n\n".join(docs[:5])
        except Exception:
            pass

        # Fallback: local Chroma mirror if present
        try:
            if not self.docs_collection:
                return "No documents available"
            docs = self.docs_collection.get()
            if docs.get('documents'):
                return "\n\n".join(docs['documents'][:5])
            return "No documents found"
        except Exception:
            return "Error retrieving documents"
    
    def _get_chat_history(self) -> str:
        """Get chat history from Document Agent"""
        if not self.doc_chat_collection:
            return "No chat history available"
        
        try:
            chats = self.doc_chat_collection.get()
            if chats['documents']:
                return "\n\n".join(chats['documents'])
            return "No chat history"
        except:
            return "Error retrieving chat history"
    
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
                        "agent": "Stack Agent"
                    })
            
            # Sort by timestamp (most recent first)
            history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return history
            
        except Exception as e:
            print(f"Error getting chat history: {e}")
            return []
    
    def _format_resumes(self, resumes: List[Dict]) -> str:
        """Format resumes for LLM consumption"""
        formatted = []
        for resume in resumes:
            formatted.append(f"### {resume['candidate_name']}\n{resume['resume_text'][:500]}...")
        return "\n\n".join(formatted)
    
    def _format_iterations(self, iterations: List[Dict]) -> str:
        """Format iteration history"""
        formatted = []
        for i, iteration in enumerate(iterations, 1):
            formatted.append(f"## Iteration {i}\n**Feedback:** {iteration['lead_feedback']}\n**Team:** {iteration['team_recommendation'][:300]}...")
        return "\n\n".join(formatted)
    
    def _store_iteration(self, lead_feedback: str, team_recommendation: str, iteration_type: str) -> str:
        """Store iteration in ChromaDB"""
        iteration_id = str(uuid.uuid4())
        
        self.iterations_collection.add(
            documents=[f"Feedback: {lead_feedback}\nTeam: {team_recommendation}"],
            ids=[iteration_id],
            metadatas=[{
                "iteration_id": iteration_id,
                "iteration_number": self.current_iteration,
                "iteration_type": iteration_type,
                "lead_feedback": lead_feedback,
                "team_recommendation": team_recommendation,
                "timestamp": datetime.now().isoformat(),
                "company_id": self.company_id,
                "lead_id": self.lead_id
            }]
        )
        
        return iteration_id
    
    def _get_iteration_history(self) -> List[Dict]:
        """Get all iteration history"""
        try:
            results = self.iterations_collection.get(
                where={
                    "company_id": self.company_id,
                    "lead_id": self.lead_id
                }
            )
            
            iterations = []
            for metadata in results['metadatas']:
                iterations.append({
                    "iteration_id": metadata['iteration_id'],
                    "iteration_number": metadata['iteration_number'],
                    "iteration_type": metadata['iteration_type'],
                    "lead_feedback": metadata['lead_feedback'],
                    "team_recommendation": metadata['team_recommendation'],
                    "timestamp": metadata['timestamp']
                })
            
            # Sort by iteration number
            iterations.sort(key=lambda x: x['iteration_number'])
            return iterations
            
        except Exception as e:
            print(f"Error getting iterations: {e}")
            return []

