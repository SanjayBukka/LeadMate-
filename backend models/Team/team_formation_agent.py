import streamlit as st
import json
import uuid
import os
import chromadb
from datetime import datetime
from typing import List, Dict, Any
import PyPDF2
from io import BytesIO
import pandas as pd
from crewai import Agent, Task, Crew
from langchain_ollama import OllamaLLM
import re

# Configure Streamlit page
st.set_page_config(page_title="Team Formation Agent", layout="wide")

# Initialize Ollama LLM
llm = OllamaLLM(model="llama3.1:8b")

class TeamFormationSystem:
    def __init__(self):
        self.base_path = r"C:\Users\Sanjay\Desktop\LeadMate"
        self.team_path = r"C:\Users\Sanjay\Desktop\LeadMate\Team"
        # Create Team directory if it doesn't exist
        os.makedirs(self.team_path, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(path=os.path.join(self.team_path, "team_chroma_db"))
        self.setup_collections()
        
    def setup_collections(self):
        """Setup ChromaDB collections for team data and chats"""
        try:
            self.team_skills_collection = self.chroma_client.get_or_create_collection("team_skills")
            self.chat_history_collection = self.chroma_client.get_or_create_collection("chat_history")
        except Exception as e:
            st.error(f"Error setting up ChromaDB: {e}")
    
    def extract_text_from_pdf(self, pdf_file) -> str:
        """Extract text from uploaded PDF resume"""
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_file.read()))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            st.error(f"Error extracting PDF text: {e}")
            return ""
    
    def extract_skills_from_resume(self, resume_text: str, filename: str) -> Dict:
        """Extract skills and info from resume using LLM"""
        prompt = f"""
        Analyze the following resume and extract structured information in JSON format:
        
        Resume Text: {resume_text}
        
        Extract and return ONLY a JSON object with this structure:
        {{
            "name": "candidate name",
            "email": "email if found",
            "phone": "phone if found",
            "experience_years": "number of years of experience",
            "skills": {{
                "programming_languages": ["list of programming languages"],
                "frameworks": ["list of frameworks"],
                "databases": ["list of databases"],
                "cloud_platforms": ["list of cloud platforms"],
                "tools": ["list of tools and technologies"],
                "soft_skills": ["list of soft skills"]
            }},
            "previous_roles": ["list of previous job titles"],
            "education": ["list of degrees/certifications"]
        }}
        
        Return only valid JSON, no additional text.
        """
        
        try:
            response = llm.invoke(prompt)
            # Clean the response to extract JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"error": "Could not parse resume", "filename": filename}
        except Exception as e:
            return {"error": str(e), "filename": filename}
    
    def store_team_member(self, member_data: Dict, resume_text: str):
        """Store team member skills in ChromaDB"""
        member_id = str(uuid.uuid4())
        
        try:
            self.team_skills_collection.add(
                documents=[json.dumps(member_data)],
                metadatas=[{
                    "member_id": member_id,
                    "name": member_data.get("name", "Unknown"),
                    "filename": member_data.get("filename", ""),
                    "timestamp": datetime.now().isoformat()
                }],
                ids=[member_id]
            )
            return member_id
        except Exception as e:
            st.error(f"Error storing team member: {e}")
            return None
    
    def load_project_requirements(self) -> Dict:
        """Load project requirements from DocAgent ChromaDB"""
        try:
            doc_chroma_client = chromadb.PersistentClient(path=os.path.join(self.base_path, "chroma_db"))
            doc_collection = doc_chroma_client.get_collection("documents")
            
            results = doc_collection.get(include=["documents", "metadatas"])
            
            project_info = {
                "documents_analyzed": len(results["documents"]),
                "requirements": results["documents"] if results["documents"] else [],
                "metadata": results["metadatas"] if results["metadatas"] else []
            }
            return project_info
        except Exception as e:
            st.error(f"Error loading project requirements: {e}")
            return {"documents_analyzed": 0, "requirements": [], "metadata": []}
    
    def load_tech_stack(self) -> Dict:
        """Load the latest tech stack from generated_stacks folder"""
        try:
            stack_folder = os.path.join(self.base_path, "stack", "generated_stacks")
            if not os.path.exists(stack_folder):
                return {"error": "Tech stack folder not found"}
            
            # Get the latest stack file
            stack_files = [f for f in os.listdir(stack_folder) if f.endswith('.json')]
            if not stack_files:
                return {"error": "No tech stack files found"}
            
            latest_stack_file = sorted(stack_files)[-1]
            stack_path = os.path.join(stack_folder, latest_stack_file)
            
            with open(stack_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading tech stack: {e}")
            return {"error": str(e)}
    
    def get_all_team_members(self) -> List[Dict]:
        """Get all stored team members"""
        try:
            results = self.team_skills_collection.get(include=["documents", "metadatas"])
            team_members = []
            
            for i, doc in enumerate(results["documents"]):
                member_data = json.loads(doc)
                member_data["member_id"] = results["ids"][i]
                member_data["metadata"] = results["metadatas"][i]
                team_members.append(member_data)
            
            return team_members
        except Exception as e:
            st.error(f"Error getting team members: {e}")
            return []
    
    def create_team_formation_crew(self, project_info: Dict, tech_stack: Dict, team_members: List[Dict]) -> Crew:
        """Create CrewAI agents for team formation"""
        
        # Skills Analyzer Agent
        skills_analyzer = Agent(
            role="Skills Analyzer",
            goal="Analyze team member skills and match them with project requirements",
            backstory="You are an expert in analyzing technical skills and matching them with project needs.",
            llm=llm
        )
        
        # Team Formation Agent
        team_formation_agent = Agent(
            role="Team Formation Specialist",
            goal="Form optimal teams based on skill analysis and project requirements",
            backstory="You are an expert in team composition and project management with deep understanding of technical requirements.",
            llm=llm
        )
        
        # Gap Analysis Agent
        gap_analysis_agent = Agent(
            role="Skills Gap Analyzer",
            goal="Identify skill gaps and provide recommendations for training or hiring",
            backstory="You are an expert in identifying skill gaps and providing strategic recommendations.",
            llm=llm
        )
        
        # Skills Analysis Task
        skills_analysis_task = Task(
            description=f"""
            Analyze the following team members' skills against the project requirements:
            
            Project Requirements: {json.dumps(project_info, indent=2)}
            Tech Stack: {json.dumps(tech_stack.get('technology_stack', {}), indent=2)}
            Team Members: {json.dumps(team_members, indent=2)}
            
            Provide a detailed analysis of each team member's relevant skills.
            """,
            agent=skills_analyzer,
            expected_output="Detailed skills analysis for each team member"
        )
        
        # Team Formation Task
        team_formation_task = Task(
            description="""
            Based on the skills analysis, form the optimal team composition.
            Consider role requirements, skill complementarity, and project needs.
            Provide reasoning for each team member selection.
            """,
            agent=team_formation_agent,
            expected_output="Optimal team composition with detailed reasoning"
        )
        
        # Gap Analysis Task
        gap_analysis_task = Task(
            description="""
            Identify any skill gaps in the proposed team formation.
            Suggest alternatives from existing tech stack options.
            Recommend training or hiring if necessary.
            """,
            agent=gap_analysis_agent,
            expected_output="Skills gap analysis with recommendations"
        )
        
        return Crew(
            agents=[skills_analyzer, team_formation_agent, gap_analysis_agent],
            tasks=[skills_analysis_task, team_formation_task, gap_analysis_task],
            verbose=True
        )
    
    def store_chat_message(self, session_id: str, message: str, sender: str):
        """Store chat message in ChromaDB"""
        chat_id = str(uuid.uuid4())
        
        try:
            self.chat_history_collection.add(
                documents=[message],
                metadatas=[{
                    "session_id": session_id,
                    "sender": sender,
                    "timestamp": datetime.now().isoformat(),
                    "chat_id": chat_id
                }],
                ids=[chat_id]
            )
        except Exception as e:
            st.error(f"Error storing chat message: {e}")
    
    def get_chat_history(self, session_id: str) -> List[Dict]:
        """Get chat history for a session"""
        try:
            results = self.chat_history_collection.get(
                where={"session_id": session_id},
                include=["documents", "metadatas"]
            )
            
            chats = []
            for i, doc in enumerate(results["documents"]):
                chat = {
                    "message": doc,
                    "sender": results["metadatas"][i]["sender"],
                    "timestamp": results["metadatas"][i]["timestamp"]
                }
                chats.append(chat)
            
            return sorted(chats, key=lambda x: x["timestamp"])
        except Exception as e:
            st.error(f"Error getting chat history: {e}")
            return []
    
    def generate_final_team_formation(self, session_id: str, initial_analysis: str, chat_history: List[Dict]) -> Dict:
        """Generate final team formation considering chat discussions"""
        
        chat_summary = "\n".join([f"{chat['sender']}: {chat['message']}" for chat in chat_history])
        
        prompt = f"""
        Based on the initial team analysis and chat discussions, create a final team formation in JSON format:
        
        Initial Analysis: {initial_analysis}
        
        Chat Discussion Summary:
        {chat_summary}
        
        Create a JSON response with this exact structure:
        {{
            "metadata": {{
                "session_id": "{session_id}",
                "generated_at": "{datetime.now().isoformat()}",
                "team_version": "1.0",
                "discussions_count": {len(chat_history)}
            }},
            "project_analysis": {{
                "requirements_matched": ["list of matched requirements"],
                "project_complexity": "High/Medium/Low"
            }},
            "team_formation": {{
                "team_members": [
                    {{
                        "name": "member name",
                        "role": "assigned role",
                        "skills_matched": ["relevant skills"],
                        "reasoning": "why this member was selected"
                    }}
                ],
                "team_lead_recommendation": "recommended team lead with reasoning",
                "total_team_size": 0
            }},
            "skills_analysis": {{
                "covered_skills": ["skills covered by team"],
                "skill_gaps": ["missing skills"],
                "alternative_solutions": ["suggested alternatives"],
                "training_recommendations": ["training needed"],
                "hiring_recommendations": ["positions to hire"]
            }},
            "chat_insights": {{
                "key_decisions": ["important decisions from chat"],
                "concerns_raised": ["concerns discussed"],
                "final_adjustments": ["final changes made"]
            }}
        }}
        
        Return only valid JSON.
        """
        
        try:
            response = llm.invoke(prompt)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"error": "Could not generate final team formation"}
        except Exception as e:
            return {"error": str(e)}

# Initialize the system
if 'team_system' not in st.session_state:
    st.session_state.team_system = TeamFormationSystem()

if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if 'initial_analysis' not in st.session_state:
    st.session_state.initial_analysis = None

if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

# Main Dashboard
st.title("🤝 Team Formation Agent")
st.markdown("---")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Choose a page", ["Upload Resumes", "Team Analysis", "Chat with Agent", "Final Team Formation"])

if page == "Upload Resumes":
    st.header("📄 Upload Team Member Resumes")
    
    uploaded_files = st.file_uploader("Upload PDF resumes", type="pdf", accept_multiple_files=True)
    
    if uploaded_files:
        st.subheader("Processing Resumes...")
        
        for uploaded_file in uploaded_files:
            with st.expander(f"Processing {uploaded_file.name}"):
                # Extract text from PDF
                resume_text = st.session_state.team_system.extract_text_from_pdf(uploaded_file)
                
                if resume_text:
                    # Extract skills using LLM
                    with st.spinner(f"Analyzing {uploaded_file.name}..."):
                        member_data = st.session_state.team_system.extract_skills_from_resume(resume_text, uploaded_file.name)
                        member_data["filename"] = uploaded_file.name
                    
                    if "error" not in member_data:
                        # Store in ChromaDB
                        member_id = st.session_state.team_system.store_team_member(member_data, resume_text)
                        
                        if member_id:
                            st.success(f"✅ Successfully processed {uploaded_file.name}")
                            st.json(member_data)
                        else:
                            st.error(f"❌ Failed to store {uploaded_file.name}")
                    else:
                        st.error(f"❌ Error processing {uploaded_file.name}: {member_data['error']}")

elif page == "Team Analysis":
    st.header("🔍 Initial Team Analysis")
    
    if st.button("Generate Team Analysis", type="primary"):
        with st.spinner("Analyzing project requirements, tech stack, and team members..."):
            # Load project requirements and tech stack
            project_info = st.session_state.team_system.load_project_requirements()
            tech_stack = st.session_state.team_system.load_tech_stack()
            team_members = st.session_state.team_system.get_all_team_members()
            
            if team_members:
                # Create and run CrewAI analysis
                crew = st.session_state.team_system.create_team_formation_crew(project_info, tech_stack, team_members)
                result = crew.kickoff()
                
                st.session_state.initial_analysis = str(result)
                
                st.success("✅ Initial team analysis completed!")
                st.subheader("Analysis Results:")
                st.write(result)
                
                # Display team members
                st.subheader("Available Team Members:")
                for member in team_members:
                    with st.expander(f"{member.get('name', 'Unknown')} - {member.get('filename', '')}"):
                        st.json(member)
            else:
                st.warning("⚠️ No team members found. Please upload resumes first.")
    
    # Display existing analysis if available
    if st.session_state.initial_analysis:
        st.subheader("Current Analysis:")
        st.write(st.session_state.initial_analysis)

elif page == "Chat with Agent":
    st.header("💬 Chat with Team Formation Agent")
    
    if not st.session_state.initial_analysis:
        st.warning("⚠️ Please generate initial team analysis first.")
    else:
        # Display chat history
        st.subheader("Chat History:")
        
        # Load existing chat history
        if not st.session_state.chat_messages:
            st.session_state.chat_messages = st.session_state.team_system.get_chat_history(st.session_state.session_id)
        
        for chat in st.session_state.chat_messages:
            if chat["sender"] == "user":
                st.chat_message("user").write(chat["message"])
            else:
                st.chat_message("assistant").write(chat["message"])
        
        # Chat input
        if prompt := st.chat_input("Ask about team formation..."):
            # Display user message
            st.chat_message("user").write(prompt)
            
            # Store user message
            st.session_state.team_system.store_chat_message(st.session_state.session_id, prompt, "user")
            st.session_state.chat_messages.append({"message": prompt, "sender": "user", "timestamp": datetime.now().isoformat()})
            
            # Generate response
            context_prompt = f"""
            Based on the initial team analysis and ongoing discussion, respond to the user's question:
            
            Initial Analysis: {st.session_state.initial_analysis}
            
            User Question: {prompt}
            
            Provide a helpful response about team formation, skills analysis, or recommendations.
            """
            
            with st.spinner("Generating response..."):
                response = llm.invoke(context_prompt)
            
            # Display and store agent response
            st.chat_message("assistant").write(response)
            st.session_state.team_system.store_chat_message(st.session_state.session_id, response, "agent")
            st.session_state.chat_messages.append({"message": response, "sender": "agent", "timestamp": datetime.now().isoformat()})

elif page == "Final Team Formation":
    st.header("🎯 Final Team Formation")
    
    if not st.session_state.initial_analysis:
        st.warning("⚠️ Please generate initial team analysis first.")
    elif st.button("Generate Final Team Formation", type="primary"):
        with st.spinner("Generating final team formation..."):
            chat_history = st.session_state.team_system.get_chat_history(st.session_state.session_id)
            final_formation = st.session_state.team_system.generate_final_team_formation(
                st.session_state.session_id, 
                st.session_state.initial_analysis, 
                chat_history
            )
            
            if "error" not in final_formation:
                st.success("✅ Final team formation generated!")
                
                # Display the formation
                st.json(final_formation)
                
                # Save to JSON file
                filename = f"team_formation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                filepath = os.path.join(self.team_path, "team_formations", filename)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                with open(filepath, 'w') as f:
                    json.dump(final_formation, f, indent=2)
                
                st.success(f"💾 Team formation saved to: {filepath}")
                
                # Download button
                st.download_button(
                    label="📥 Download Team Formation JSON",
                    data=json.dumps(final_formation, indent=2),
                    file_name=filename,
                    mime="application/json"
                )
            else:
                st.error(f"❌ Error generating final formation: {final_formation['error']}")

# Display session info in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### Session Info")
st.sidebar.text(f"Session ID: {st.session_state.session_id[:8]}...")
if st.session_state.initial_analysis:
    st.sidebar.success("✅ Initial analysis done")
else:
    st.sidebar.warning("⚠️ Initial analysis pending")

chat_count = len(st.session_state.chat_messages)
st.sidebar.text(f"Chat messages: {chat_count}")

# Reset session button
if st.sidebar.button("🔄 New Session"):
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.initial_analysis = None
    st.session_state.chat_messages = []
    st.rerun()