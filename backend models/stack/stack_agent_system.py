import streamlit as st
import os
import uuid
import json
from datetime import datetime
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from crewai import Agent, Task, Crew, Process
import sys

# Alternative LLM import with error handling
try:
    from langchain_ollama import OllamaLLM
    OLLAMA_AVAILABLE = True
except ImportError:
    try:
        from langchain.llms import Ollama as OllamaLLM
        OLLAMA_AVAILABLE = True
    except ImportError:
        try:
            from langchain_community.llms import Ollama as OllamaLLM
            OLLAMA_AVAILABLE = True
        except ImportError:
            OLLAMA_AVAILABLE = False
            st.error("Cannot import Ollama LLM. Please check your langchain installation.")

# ChromaDB path - update this to your actual path
CHROMA_DB_PATH = r"C:\Users\Sanjay\Desktop\LeadMate\DocAgent\chroma_db"
STACKS_OUTPUT_DIR = r"C:\Users\Sanjay\Desktop\LeadMate\stack\generated_stacks"

# Create output directory if it doesn't exist
os.makedirs(STACKS_OUTPUT_DIR, exist_ok=True)

# Initialize ChromaDB with existing DocAgent data
@st.cache_resource
def init_chromadb():
    """Initialize ChromaDB with access to existing DocAgent data and new StackAgent collections"""
    try:
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        
        # Access existing DocAgent collections
        try:
            docs_collection = client.get_collection(name="project_documents")
            st.success("✅ Connected to existing project documents")
        except:
            docs_collection = client.get_or_create_collection(
                name="project_documents",
                metadata={"description": "Project documents from DocAgent"}
            )
        
        # Create new collections for StackAgent
        stack_discussions = client.get_or_create_collection(
            name="stack_discussions",
            metadata={"description": "Team lead and StackAgent discussions"}
        )
        
        final_stacks = client.get_or_create_collection(
            name="final_stacks",
            metadata={"description": "Final technology stack recommendations"}
        )
        
        return client, docs_collection, stack_discussions, final_stacks
    except Exception as e:
        st.error(f"Error connecting to ChromaDB: {str(e)}")
        st.error(f"Please ensure ChromaDB exists at: {CHROMA_DB_PATH}")
        return None, None, None, None

# Initialize Ollama LLM with error handling
@st.cache_resource
def init_llm():
    """Initialize Ollama LLM with fallback options"""
    if not OLLAMA_AVAILABLE:
        st.error("❌ Ollama LLM not available. Please fix langchain installation.")
        return None
    
    try:
        # Try different initialization methods
        llm = OllamaLLM(model="llama3.1:8b", base_url="http://localhost:11434")
        return llm
    except Exception as e:
        try:
            # Alternative initialization
            llm = OllamaLLM(model="llama3.1:8b")
            return llm
        except Exception as e2:
            st.error(f"Error initializing Ollama: {str(e)} | {str(e2)}")
            st.info("Please ensure Ollama is running: `ollama serve`")
            return None

class StackAnalyzer:
    """Handle stack analysis and ChromaDB operations"""
    
    def __init__(self, docs_collection, stack_discussions, final_stacks):
        self.docs_collection = docs_collection
        self.stack_discussions = stack_discussions
        self.final_stacks = final_stacks
    
    def get_project_context(self, query: str = "project requirements technology features functionality", n_results: int = 15) -> List[str]:
        """Get project context from DocAgent's document collection"""
        try:
            # Check if collection has documents
            collection_count = self.docs_collection.count()
            if collection_count == 0:
                st.warning("⚠️ No documents found in project_documents collection")
                return []
            
            results = self.docs_collection.query(
                query_texts=[query],
                n_results=min(n_results, collection_count)
            )
            
            context_docs = results['documents'][0] if results['documents'] else []
            st.info(f"📄 Retrieved {len(context_docs)} document sections for analysis")
            return context_docs
            
        except Exception as e:
            st.error(f"Error retrieving project context: {str(e)}")
            return []
    
    def get_all_project_documents(self) -> List[str]:
        """Get all project documents for comprehensive analysis"""
        try:
            # Get all documents from the collection
            all_docs = self.docs_collection.get()
            
            if not all_docs['documents']:
                st.warning("No project documents found")
                return []
            
            st.info(f"📚 Retrieved {len(all_docs['documents'])} total document sections")
            return all_docs['documents']
            
        except Exception as e:
            st.error(f"Error retrieving all documents: {str(e)}")
            return []
    
    def store_discussion(self, user_message: str, agent_response: str, session_id: str, discussion_type: str = "stack_planning"):
        """Store discussion between team lead and StackAgent"""
        try:
            discussion_id = f"discussion_{session_id}_{uuid.uuid4().hex[:8]}"
            conversation = f"Team Lead: {user_message}\nStackAgent: {agent_response}"
            
            self.stack_discussions.add(
                documents=[conversation],
                ids=[discussion_id],
                metadatas=[{
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "discussion_type": discussion_type,
                    "user_message": user_message,
                    "agent_response": agent_response
                }]
            )
            return True
        except Exception as e:
            st.error(f"Error storing discussion: {str(e)}")
            return False
    
    def get_session_discussions(self, session_id: str) -> List[Dict]:
        """Get all discussions for current session"""
        try:
            results = self.stack_discussions.get(
                where={"session_id": session_id}
            )
            
            discussions = []
            if results['metadatas']:
                for i, metadata in enumerate(results['metadatas']):
                    discussions.append({
                        "timestamp": metadata['timestamp'],
                        "user_message": metadata['user_message'],
                        "agent_response": metadata['agent_response'],
                        "full_conversation": results['documents'][i]
                    })
            
            discussions.sort(key=lambda x: x['timestamp'])
            return discussions
            
        except Exception as e:
            st.error(f"Error retrieving discussions: {str(e)}")
            return []
    
    def save_final_stack_json(self, final_stack_text: str, session_id: str, discussions_summary: Dict) -> str:
        """Save final stack as JSON file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"final_tech_stack_{timestamp}.json"
            filepath = os.path.join(STACKS_OUTPUT_DIR, filename)
            
            # Create structured JSON data
            stack_data = {
                "metadata": {
                    "session_id": session_id,
                    "generated_at": datetime.now().isoformat(),
                    "stack_version": "1.0",
                    "discussions_count": discussions_summary.get("discussions_count", 0)
                },
                "project_analysis": {
                    "documents_analyzed": discussions_summary.get("documents_count", 0),
                    "key_requirements": discussions_summary.get("key_requirements", []),
                    "project_type": discussions_summary.get("project_type", "Not specified")
                },
                "technology_stack": {
                    "recommendation_text": final_stack_text,
                    "last_updated": datetime.now().isoformat()
                },
                "discussion_summary": discussions_summary.get("discussion_highlights", []),
                "file_info": {
                    "filename": filename,
                    "file_path": filepath,
                    "format": "JSON",
                    "encoding": "UTF-8"
                }
            }
            
            # Save to JSON file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(stack_data, f, indent=2, ensure_ascii=False)
            
            # Also store in ChromaDB for searchability
            stack_id = f"final_stack_{session_id}_{timestamp}"
            self.final_stacks.add(
                documents=[final_stack_text],
                ids=[stack_id],
                metadatas=[{
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "json_file_path": filepath,
                    "filename": filename,
                    "stack_type": "final_recommendation"
                }]
            )
            
            return filepath
            
        except Exception as e:
            st.error(f"Error saving final stack JSON: {str(e)}")
            return None

class StackAgent:
    """StackAgent for technology stack prediction and recommendations"""
    
    def __init__(self, llm, stack_analyzer):
        self.llm = llm
        self.stack_analyzer = stack_analyzer
        self.agent = self._create_agent()
    
    def _create_agent(self):
        """Create the StackAgent with specialized role"""
        return Agent(
            role='Senior Technology Architect & Stack Strategist',
            goal='''Analyze project requirements from documents and discussions to recommend optimal, 
                    production-ready technology stacks. Provide detailed technical justifications, 
                    consider real-world constraints, scalability, and maintainability. Ask strategic 
                    questions to uncover hidden requirements and potential technical challenges.''',
            backstory='''You are StackAgent, a highly experienced Senior Technology Architect with 15+ years 
                        of experience building scalable systems from startups to enterprise applications. 
                        You have deep expertise in:
                        
                        • Full-stack architecture design and technology selection
                        • Cloud-native development and infrastructure planning  
                        • Performance optimization and scalability strategies
                        • Team productivity and development workflow optimization
                        • Risk assessment and technical debt management
                        
                        You excel at translating business requirements into technical solutions, 
                        balancing cutting-edge technology with proven, maintainable approaches. 
                        You always consider team capabilities, project timeline, budget constraints, 
                        and long-term maintainability when making recommendations.
                        
                        Your recommendations are detailed, practical, and include specific implementation 
                        guidance with clear reasoning for each technology choice.''',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_initial_stack_analysis_task(self, project_context: List[str]) -> Task:
        """Create task for initial comprehensive stack analysis"""
        context = "\n\n---DOCUMENT SECTION---\n\n".join(project_context) if project_context else "Limited project documentation available."
        
        return Task(
            description=f'''Analyze the project documentation and provide a comprehensive initial technology stack recommendation:
                           
                           PROJECT DOCUMENTATION:
                           {context}
                           
                           Based on the project requirements, provide detailed stack recommendations covering:
                           
                           ## 🎯 PROJECT ANALYSIS
                           - Project type and core functionality
                           - Key technical requirements identified
                           - Scalability and performance needs
                           - Integration requirements
                           
                           ## 🏗️ RECOMMENDED TECHNOLOGY STACK
                           
                           ### Frontend Stack
                           **Primary Framework:** [Specific choice - React/Vue/Angular/etc.]
                           - **Reasoning:** Why this framework fits the project requirements
                           - **UI Framework:** Material-UI/Tailwind/Bootstrap + justification
                           - **State Management:** Redux/Zustand/Context + why needed
                           - **Build Tools:** Webpack/Vite + configuration benefits
                           - **Example Use Cases:** Where this excels in your project
                           
                           ### Backend Stack  
                           **Language & Framework:** [Node.js/Python/Java/C# + specific framework]
                           - **Reasoning:** Technical benefits for this project type
                           - **API Architecture:** REST/GraphQL + why this approach
                           - **Authentication:** JWT/OAuth2/Firebase Auth + security considerations
                           - **Middleware & Libraries:** Specific packages needed
                           - **Example Implementation:** How it handles core features
                           
                           ### Database & Storage
                           **Primary Database:** [PostgreSQL/MongoDB/MySQL + specific reasoning]
                           - **Data Model Fit:** Why this database type suits the data structure
                           - **Caching Strategy:** Redis/Memcached + performance benefits
                           - **File Storage:** AWS S3/Google Cloud + integration approach
                           - **Example Queries:** How database handles key operations
                           
                           ### Infrastructure & DevOps
                           **Cloud Platform:** [AWS/Google Cloud/Azure + specific services]
                           - **Reasoning:** Why this platform suits the project needs
                           - **Containerization:** Docker + Kubernetes/Docker Compose approach
                           - **CI/CD Pipeline:** GitHub Actions/GitLab CI + deployment strategy
                           - **Monitoring:** Application and infrastructure monitoring tools
                           - **Example Architecture:** How components communicate
                           
                           ### Development Ecosystem
                           **Version Control:** Git workflow strategy
                           **Testing Framework:** Unit, integration, and e2e testing approach
                           **Code Quality:** Linting, formatting, and code review tools
                           **Documentation:** API documentation and code documentation strategy
                           
                           ## ❓ CRITICAL QUESTIONS FOR CLARIFICATION
                           List 8-10 specific questions about:
                           - Performance and scalability requirements
                           - Team size and expertise
                           - Timeline and budget constraints  
                           - Integration requirements
                           - Security and compliance needs
                           - Mobile/responsive requirements
                           - Third-party service dependencies
                           
                           ## ⚡ IMPLEMENTATION BENEFITS
                           - Why this stack combination is optimal
                           - Development velocity advantages
                           - Scalability and maintenance benefits
                           - Cost considerations
                           
                           ## ⚠️ POTENTIAL RISKS & ALTERNATIVES
                           - Possible challenges with recommended stack
                           - Alternative technology options considered
                           - Mitigation strategies for identified risks
                           
                           Provide specific, actionable recommendations with clear technical reasoning for each choice.''',
            expected_output='''Comprehensive initial technology stack analysis with detailed justifications, 
                              specific implementation guidance, strategic questions, and risk assessment.''',
            agent=self.agent
        )
    
    def create_discussion_response_task(self, question: str, project_context: List[str], discussion_history: str) -> Task:
        """Create task for responding to team lead questions"""
        context_summary = "\n".join(project_context[:5]) if project_context else "Limited project context available."
        
        return Task(
            description=f'''Respond to the team lead's question/input about the technology stack:
                           
                           TEAM LEAD INPUT: "{question}"
                           
                           PROJECT CONTEXT SUMMARY:
                           {context_summary}
                           
                           PREVIOUS DISCUSSION SUMMARY:
                           {discussion_history[-2000:] if len(discussion_history) > 2000 else discussion_history}
                           
                           Provide a comprehensive response that:
                           
                           1. **Direct Answer:** Address the specific question/concern clearly
                           
                           2. **Technical Analysis:** 
                              - Provide detailed technical reasoning
                              - Compare alternatives if applicable  
                              - Include specific implementation examples
                              - Consider performance and scalability implications
                           
                           3. **Project Fit Assessment:**
                              - How this relates to project requirements
                              - Impact on overall architecture
                              - Integration considerations
                           
                           4. **Practical Recommendations:**
                              - Specific technologies, tools, or approaches
                              - Implementation best practices
                              - Configuration or setup guidance
                           
                           5. **Strategic Follow-up Questions:**
                              Ask 2-3 clarifying questions to better understand:
                              - Specific requirements or constraints
                              - Team preferences or experience
                              - Timeline or resource limitations
                              - Performance or scalability expectations
                           
                           6. **Risk Assessment:**
                              - Potential challenges with suggested approach
                              - Mitigation strategies
                              - Alternative options if issues arise
                           
                           Be thorough, technical, and practical. Think like a senior architect balancing 
                           ideal solutions with real-world project constraints.''',
            expected_output='''Detailed technical response with specific recommendations, clear reasoning, 
                              strategic follow-up questions, and practical implementation guidance.''',
            agent=self.agent
        )
    
    def create_final_stack_task(self, all_discussions: str, project_context: List[str]) -> Task:
        """Create task for generating comprehensive final stack recommendation"""
        context_summary = "\n---DOCUMENT---\n".join(project_context[:10]) if project_context else "Limited project context."
        
        return Task(
            description=f'''Create the DEFINITIVE FINAL TECHNOLOGY STACK RECOMMENDATION based on all 
                           project analysis and team discussions:
                           
                           PROJECT DOCUMENTATION SUMMARY:
                           {context_summary}
                           
                           COMPLETE DISCUSSION HISTORY:
                           {all_discussions}
                           
                           Generate a comprehensive, production-ready technology stack specification:
                           
                           # 🎯 EXECUTIVE SUMMARY
                           
                           ## Project Overview
                           - **Project Type:** [Web App/Mobile/Desktop/API/etc.]
                           - **Core Functionality:** Key features and capabilities
                           - **Target Scale:** Expected users, data volume, performance needs
                           - **Key Technical Decisions:** Critical architectural choices made
                           
                           ## Architecture Approach
                           - **Overall Pattern:** Monolithic/Microservices/Serverless + reasoning
                           - **Communication Strategy:** API design, data flow, integration patterns
                           - **Deployment Model:** Cloud-native/hybrid/on-premise approach
                           
                           # 🏗️ COMPLETE TECHNOLOGY STACK
                           
                           ## Frontend Development
                           ### Primary Framework
                           - **Technology:** [React 18/Vue 3/Angular 16/Next.js/etc.]
                           - **Why Chosen:** Specific benefits for this project
                           - **Key Features Used:** Hooks, routing, state management approach
                           - **Performance Optimizations:** Code splitting, lazy loading, caching
                           
                           ### UI & Styling
                           - **UI Framework:** [Material-UI/Tailwind CSS/Ant Design/etc.]
                           - **Responsive Strategy:** Mobile-first/desktop-first approach
                           - **Design System:** Component library and theming approach
                           - **Accessibility:** WCAG compliance strategy
                           
                           ### State Management
                           - **Solution:** [Redux Toolkit/Zustand/React Query/etc.]
                           - **Data Flow:** How application state is managed
                           - **Caching Strategy:** Client-side data persistence
                           - **Real-time Updates:** WebSocket/Server-sent events if needed
                           
                           ### Build & Development Tools
                           - **Build Tool:** [Webpack/Vite/Parcel] + configuration approach
                           - **Development Server:** Hot reload and development workflow
                           - **Code Quality:** ESLint, Prettier, TypeScript configuration
                           - **Testing:** Jest, React Testing Library, Cypress setup
                           
                           ## Backend Development
                           ### Core Framework
                           - **Language & Framework:** [Node.js + Express/Python + FastAPI/Java + Spring/etc.]
                           - **Architecture Pattern:** MVC/Clean Architecture/Hexagonal
                           - **Why Selected:** Performance, team expertise, ecosystem benefits
                           - **Scalability Features:** Clustering, load balancing, horizontal scaling
                           
                           ### API Design
                           - **API Style:** REST/GraphQL + versioning strategy
                           - **Documentation:** OpenAPI/Swagger/GraphQL schema
                           - **Rate Limiting:** Request throttling and abuse prevention
                           - **Error Handling:** Consistent error response format
                           
                           ### Authentication & Security
                           - **Auth Strategy:** [JWT/OAuth2/Auth0/Firebase Auth/etc.]
                           - **Authorization:** Role-based access control (RBAC)
                           - **Security Headers:** CORS, CSP, security middleware
                           - **Data Validation:** Input sanitization and validation
                           
                           ### Background Processing
                           - **Job Queue:** [Redis Queue/Celery/Bull Queue/etc.]
                           - **Scheduled Tasks:** Cron jobs and recurring processes
                           - **Email/Notifications:** Service integration approach
                           - **File Processing:** Upload handling and processing pipeline
                           
                           ## Database & Storage
                           ### Primary Database
                           - **Database:** [PostgreSQL/MongoDB/MySQL/etc.] + version
                           - **Schema Design:** Data modeling approach and relationships
                           - **Indexing Strategy:** Performance optimization
                           - **Backup & Recovery:** Data protection and disaster recovery
                           
                           ### Caching Layer
                           - **Cache Solution:** [Redis/Memcached] + use cases
                           - **Caching Strategy:** Application-level and database query caching
                           - **Session Storage:** User session management
                           - **Performance Impact:** Expected performance improvements
                           
                           ### File Storage
                           - **Storage Solution:** [AWS S3/Google Cloud Storage/etc.]
                           - **CDN Integration:** Content delivery optimization
                           - **File Processing:** Image resizing, video transcoding if needed
                           - **Access Control:** Secure file access and permissions
                           
                           ## Infrastructure & DevOps
                           ### Cloud Platform
                           - **Primary Provider:** [AWS/Google Cloud/Azure] + specific services
                           - **Compute Resources:** EC2/App Engine/Azure VMs configuration
                           - **Networking:** VPC, load balancers, security groups setup
                           - **Cost Optimization:** Resource sizing and cost management
                           
                           ### Containerization & Orchestration  
                           - **Containerization:** Docker configuration and image optimization
                           - **Orchestration:** [Kubernetes/Docker Compose/ECS] + scaling strategy
                           - **Service Mesh:** If needed for microservices communication
                           - **Configuration Management:** Environment variables and secrets
                           
                           ### CI/CD Pipeline
                           - **Version Control:** Git workflow and branching strategy
                           - **CI/CD Platform:** [GitHub Actions/GitLab CI/Jenkins/etc.]
                           - **Build Process:** Automated testing and deployment pipeline
                           - **Environment Strategy:** Development/staging/production deployment
                           
                           ### Monitoring & Observability
                           - **Application Monitoring:** [New Relic/DataDog/Sentry/etc.]
                           - **Infrastructure Monitoring:** Server and database monitoring
                           - **Logging:** Centralized logging strategy and log management
                           - **Alerting:** Critical metric monitoring and alert configuration
                           
                           ## Development Workflow
                           ### Code Quality & Testing
                           - **Code Standards:** Linting rules and formatting configuration
                           - **Testing Strategy:** Unit, integration, and end-to-end testing
                           - **Code Review:** Pull request workflow and review guidelines
                           - **Documentation:** API docs, code comments, and technical documentation
                           
                           ### Development Environment
                           - **Local Development:** Docker Compose or local setup instructions
                           - **Environment Parity:** Consistent development, staging, production
                           - **Database Migrations:** Schema versioning and migration strategy
                           - **Seed Data:** Test data and development database setup
                           
                           # 📋 IMPLEMENTATION ROADMAP
                           
                           ## Phase 1: Foundation Setup (Weeks 1-2)
                           - [ ] Development environment setup and team onboarding
                           - [ ] Core infrastructure provisioning (cloud, databases, basic services)
                           - [ ] CI/CD pipeline configuration and deployment automation
                           - [ ] Basic project structure and development workflow establishment
                           
                           ## Phase 2: Core Development (Weeks 3-8)
                           - [ ] Authentication system implementation
                           - [ ] Core API endpoints and data models
                           - [ ] Frontend components and basic user interface
                           - [ ] Database schema finalization and data migration setup
                           
                           ## Phase 3: Feature Development (Weeks 9-16)
                           - [ ] Primary application features implementation
                           - [ ] Integration with third-party services
                           - [ ] Performance optimization and caching implementation
                           - [ ] Comprehensive testing suite development
                           
                           ## Phase 4: Production Preparation (Weeks 17-20)
                           - [ ] Security audit and penetration testing
                           - [ ] Performance testing and scalability validation  
                           - [ ] Monitoring and alerting system setup
                           - [ ] Documentation completion and team training
                           
                           # ⚡ KEY STRATEGIC BENEFITS
                           
                           ## Technical Advantages
                           - **Performance:** Expected application performance characteristics
                           - **Scalability:** How the stack handles growth and increased load
                           - **Maintainability:** Long-term code maintenance and technical debt management
                           - **Developer Experience:** Team productivity and development velocity benefits
                           
                           ## Business Benefits
                           - **Time to Market:** Development speed and deployment efficiency
                           - **Cost Efficiency:** Infrastructure and development cost optimization
                           - **Flexibility:** Ability to adapt to changing requirements
                           - **Risk Mitigation:** Technology stability and vendor lock-in considerations
                           
                           # ⚠️ RISK ASSESSMENT & MITIGATION
                           
                           ## Technical Risks
                           - **Risk 1:** [Specific technical challenge] → **Mitigation:** [Specific solution]
                           - **Risk 2:** [Performance/scalability concern] → **Mitigation:** [Optimization strategy]  
                           - **Risk 3:** [Integration complexity] → **Mitigation:** [Simplified approach]
                           - **Risk 4:** [Security vulnerability] → **Mitigation:** [Security measures]
                           
                           ## Project Risks
                           - **Team Expertise:** Knowledge gaps and learning curve mitigation
                           - **Timeline Pressure:** Critical path optimization and scope management
                           - **Budget Constraints:** Cost control measures and alternative options
                           - **Vendor Dependencies:** Lock-in prevention and exit strategies
                           
                           # 💰 RESOURCE REQUIREMENTS
                           
                           ## Development Team
                           - **Frontend Developers:** [Number] with [specific skills]
                           - **Backend Developers:** [Number] with [specific expertise]
                           - **DevOps Engineer:** [Allocation] for infrastructure and deployment
                           - **Database Administrator:** [Part-time/full-time] for optimization
                           
                           ## Infrastructure Costs (Monthly Estimates)
                           - **Compute Resources:** $[amount] for application hosting
                           - **Database Hosting:** $[amount] for data storage and processing
                           - **Third-party Services:** $[amount] for external APIs and services
                           - **Monitoring & Tools:** $[amount] for development and operational tools
                           
                           ## Timeline Considerations
                           - **Setup Phase:** [Duration] for infrastructure and environment preparation
                           - **Development Phase:** [Duration] for core feature implementation
                           - **Testing & Launch:** [Duration] for quality assurance and deployment
                           - **Post-launch Support:** Ongoing maintenance and feature development
                           
                           # 🔄 ALTERNATIVE OPTIONS
                           
                           ## If Budget is Constrained
                           - Alternative open-source tools and services
                           - Simplified architecture options
                           - Phased implementation approach
                           
                           ## If Timeline is Aggressive  
                           - Rapid prototyping and MVP approach
                           - Pre-built solutions and SaaS integrations
                           - Outsourcing considerations
                           
                           ## If Team Expertise Differs
                           - Technology alternatives matching team skills
                           - Training and upskilling recommendations
                           - Hybrid approaches using familiar technologies
                           
                           ---
                           
                           This technology stack provides a solid, scalable foundation for the project with 
                           clear implementation guidance and strategic considerations for long-term success.''',
            expected_output='''Complete, production-ready technology stack specification with detailed 
                              implementation roadmap, resource requirements, risk assessment, and 
                              strategic guidance for project success.''',
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
            st.error(f"Error executing StackAgent task: {str(e)}")
            return f"❌ Error: {str(e)}"

def main():
    """Main Streamlit application for StackAgent"""
    
    st.set_page_config(
        page_title="StackAgent - Technology Stack Predictor",
        page_icon="🏗️",
        layout="wide"
    )
    
    st.title("🏗️ StackAgent - AI Technology Stack Predictor")
    st.markdown("*Analyze project requirements and get comprehensive technology stack recommendations*")
    
    # Initialize session state
    if 'stack_session_id' not in st.session_state:
        st.session_state.stack_session_id = str(uuid.uuid4())
    
    if 'stack_discussions' not in st.session_state:
        st.session_state.stack_discussions = []
    
    if 'initial_analysis_done' not in st.session_state:
        st.session_state.initial_analysis_done = False
    
    if 'final_stack_generated' not in st.session_state:
        st.session_state.final_stack_generated = False
    
    # Initialize components
    client, docs_collection, stack_discussions, final_stacks = init_chromadb()
    
    if not all([client, docs_collection, stack_discussions, final_stacks]):
        st.error("❌ Failed to connect to ChromaDB. Please ensure the path is correct and DocAgent has been run first.")
        st.info(f"Expected ChromaDB path: {CHROMA_DB_PATH}")
        st.stop()
    
    try:
        llm = init_llm()
        stack_analyzer = StackAnalyzer(docs_collection, stack_discussions, final_stacks)
        stack_agent = StackAgent(llm, stack_analyzer)
    except Exception as e:
        st.error(f"Error initializing StackAgent: {str(e)}")
        st.stop()
    
    # Sidebar for project analysis and controls
    with st.sidebar:
        st.header("🎯 Stack Analysis Control")
        
        # Check document count
        try:
            doc_count = docs_collection.count()
            st.info(f"📄 Project documents available: {doc_count}")
        except:
            st.warning("⚠️ Cannot count project documents")
        
        if not st.session_state.initial_analysis_done:
            if st.button("🚀 Analyze Project & Generate Initial Stack", type="primary"):
                with st.spinner("🔍 StackAgent is analyzing project documents..."):
                    # Get comprehensive project context
                    project_context = stack_analyzer.get_all_project_documents()
                    
                    if not project_context:
                        st.error("❌ No project documents found. Please run DocAgent first and upload project documents.")
                    else:
                        st.success(f"✅ Analyzing {len(project_context)} document sections")
                        
                        # Create and execute initial analysis task
                        initial_task = stack_agent.create_initial_stack_analysis_task(project_context)
                        initial_recommendation = stack_agent.execute_task(initial_task)
                        
                        st.session_state.initial_recommendation = initial_recommendation
                        st.session_state.initial_analysis_done = True
                        st.success("✅ Initial stack analysis complete!")
                        st.rerun()
        
        if st.session_state.initial_analysis_done:
            st.success("✅ Initial Analysis Complete")
            
            # Discussion counter
            discussion_count = len(st.session_state.stack_discussions)
            st.metric("💬 Discussions", discussion_count)
            
            st.divider()
            st.header("📋 Final Stack Generation")
            
            if not st.session_state.final_stack_generated:
                if st.button("🎯 Generate Final Stack & Save JSON", type="primary"):
                    with st.spinner("🏗️ Creating comprehensive final stack..."):
                        # Get all discussions
                        discussions = stack_analyzer.get_session_discussions(st.session_state.stack_session_id)
                        
                        # Prepare discussion history
                        all_discussions = ""
                        if hasattr(st.session_state, 'initial_recommendation'):
                            all_discussions = f"=== INITIAL STACK RECOMMENDATION ===\n{st.session_state.initial_recommendation}\n\n"
                        
                        for disc in discussions:
                            all_discussions += f"{disc['full_conversation']}\n\n"
                        
                        # Get project context
                        project_context = stack_analyzer.get_project_context()
                        
                        # Generate final stack
                        final_task = stack_agent.create_final_stack_task(all_discussions, project_context)
                        final_stack = stack_agent.execute_task(final_task)
                        
                        # Prepare summary for JSON
                        discussions_summary = {
                            "discussions_count": len(discussions),
                            "documents_count": len(project_context),
                            "key_requirements": ["Extracted from project analysis"],
                            "project_type": "Analyzed from documents",
                            "discussion_highlights": [disc['user_message'][:100] + "..." for disc in discussions[-5:]]
                        }
                        
                        # Save final stack as JSON
                        json_filepath = stack_analyzer.save_final_stack_json(
                            final_stack, 
                            st.session_state.stack_session_id,
                            discussions_summary
                        )
                        
                        if json_filepath:
                            st.session_state.final_stack = final_stack
                            st.session_state.final_stack_json_path = json_filepath
                            st.session_state.final_stack_generated = True
                            st.success(f"✅ Final stack generated and saved!")
                            st.info(f"💾 Saved to: {os.path.basename(json_filepath)}")
                        else:
                            st.error("❌ Failed to save final stack JSON")
                        
                        st.rerun()
            
            if st.session_state.final_stack_generated:
                st.success("✅ Final Stack Generated & Saved")
                
                # Show JSON file info
                if hasattr(st.session_state, 'final_stack_json_path'):
                    st.info(f"📄 JSON File: {os.path.basename(st.session_state.final_stack_json_path)}")
                
                if st.button("📄 View Final Stack"):
                    st.session_state.show_final_stack = True
                    st.rerun()
                
                if st.button("💾 Download JSON"):
                    if hasattr(st.session_state, 'final_stack_json_path'):
                        try:
                            with open(st.session_state.final_stack_json_path, 'r', encoding='utf-8') as f:
                                json_data = f.read()
                            
                            st.download_button(
                                label="Download Final Stack JSON",
                                data=json_data,
                                file_name=os.path.basename(st.session_state.final_stack_json_path),
                                mime="application/json"
                            )
                        except Exception as e:
                            st.error(f"Error reading JSON file: {str(e)}")
        
        st.divider()
        
        # Session controls
        st.header("🔄 Session Controls")
        if st.button("🆕 New Stack Analysis Session"):
            # Clear session data
            for key in ['stack_session_id', 'stack_discussions', 'initial_analysis_done', 
                       'final_stack_generated', 'initial_recommendation', 'final_stack',
                       'final_stack_json_path', 'show_final_stack']:
                if key in st.session_state:
                    if key == 'stack_session_id':
                        st.session_state[key] = str(uuid.uuid4())
                    else:
                        del st.session_state[key]
            st.success("🆕 New session started!")
            st.rerun()
        
        if st.button("📂 Open Output Folder"):
            if os.path.exists(STACKS_OUTPUT_DIR):
                st.info(f"📁 Output folder: {STACKS_OUTPUT_DIR}")
                # List JSON files in directory
                json_files = [f for f in os.listdir(STACKS_OUTPUT_DIR) if f.endswith('.json')]
                if json_files:
                    st.write("**Generated Stack Files:**")
                    for file in sorted(json_files, reverse=True)[:5]:  # Show latest 5
                        st.write(f"• {file}")
            else:
                st.warning("Output folder doesn't exist yet")
    
    # Main content area
    if hasattr(st.session_state, 'show_final_stack') and st.session_state.show_final_stack:
        st.header("🎯 Final Technology Stack Recommendation")
        
        # Show JSON file info
        if hasattr(st.session_state, 'final_stack_json_path'):
            st.info(f"💾 **Saved as JSON:** `{os.path.basename(st.session_state.final_stack_json_path)}`")
            st.info(f"📁 **Location:** `{os.path.dirname(st.session_state.final_stack_json_path)}`")
        
        if hasattr(st.session_state, 'final_stack'):
            st.markdown(st.session_state.final_stack)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("← Back to Discussion"):
                st.session_state.show_final_stack = False
                st.rerun()
        
        with col2:
            if hasattr(st.session_state, 'final_stack_json_path'):
                try:
                    with open(st.session_state.final_stack_json_path, 'r', encoding='utf-8') as f:
                        json_data = f.read()
                    
                    st.download_button(
                        label="📥 Download JSON",
                        data=json_data,
                        file_name=os.path.basename(st.session_state.final_stack_json_path),
                        mime="application/json"
                    )
                except Exception as e:
                    st.error(f"Error preparing download: {str(e)}")
    
    else:
        # Initial recommendation display
        if st.session_state.initial_analysis_done and hasattr(st.session_state, 'initial_recommendation'):
            with st.expander("📋 Initial Stack Recommendation", expanded=True):
                st.markdown(st.session_state.initial_recommendation)
        
        # Discussion interface
        if st.session_state.initial_analysis_done:
            st.header("💬 Refine Stack Through Discussion")
            st.markdown("*Discuss requirements, constraints, and preferences with StackAgent to refine the technology stack*")
            
            # Display discussion history
            if st.session_state.stack_discussions:
                st.subheader("Discussion History")
                for i, (user_msg, agent_msg) in enumerate(st.session_state.stack_discussions, 1):
                    with st.container():
                        st.markdown(f"**👨‍💼 Team Lead #{i}:** {user_msg}")
                        st.markdown(f"**🏗️ StackAgent:** {agent_msg}")
                        st.divider()
            
            # Discussion input
            st.subheader("Continue Discussion")
            
            # Suggested questions for first-time users
            if not st.session_state.stack_discussions:
                st.info("💡 **Suggested discussion topics:**")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("❓ Team Experience & Preferences"):
                        st.session_state.auto_question = "What if our team is more experienced with Python/Django instead of the recommended stack? How would that change the recommendations?"
                    if st.button("⚡ Performance & Scalability"):
                        st.session_state.auto_question = "We expect to handle 10,000+ concurrent users. How should we modify the stack for high performance and scalability?"
                with col2:
                    if st.button("💰 Budget Constraints"):
                        st.session_state.auto_question = "We have a limited budget for cloud services. What are the most cost-effective alternatives in this stack?"
                    if st.button("📱 Mobile Requirements"):
                        st.session_state.auto_question = "We also need mobile apps (iOS/Android). How should this change our technology stack?"
            
            user_input = st.text_area(
                "Ask StackAgent about the technology stack:",
                value=st.session_state.get('auto_question', ''),
                placeholder="Examples:\n• 'Our team is more familiar with Java - can we use Spring Boot instead?'\n• 'What if we need real-time features like live chat?'\n• 'How would this handle 50,000 concurrent users?'\n• 'We need to integrate with legacy SAP systems'\n• 'What are the security considerations for this stack?'",
                height=120,
                key="stack_discussion_input"
            )
            
            # Clear auto question after displaying
            if 'auto_question' in st.session_state:
                del st.session_state.auto_question
            
            col1, col2, col3 = st.columns([1, 1, 4])
            
            with col1:
                send_button = st.button("Send", type="primary")
            
            with col2:
                clear_button = st.button("Clear Discussion")
            
            if clear_button:
                st.session_state.stack_discussions = []
                st.success("Discussion cleared!")
                st.rerun()
            
            if send_button and user_input.strip():
                with st.spinner("🏗️ StackAgent is analyzing your input..."):
                    # Get project context and discussion history
                    project_context = stack_analyzer.get_project_context()
                    
                    discussion_history = ""
                    for user_msg, agent_msg in st.session_state.stack_discussions:
                        discussion_history += f"Team Lead: {user_msg}\nStackAgent: {agent_msg}\n\n"
                    
                    # Create and execute discussion task
                    discussion_task = stack_agent.create_discussion_response_task(
                        user_input, project_context, discussion_history
                    )
                    agent_response = stack_agent.execute_task(discussion_task)
                    
                    # Store discussion
                    st.session_state.stack_discussions.append((user_input, agent_response))
                    
                    # Save to ChromaDB
                    success = stack_analyzer.store_discussion(
                        user_input, agent_response, st.session_state.stack_session_id
                    )
                    
                    if success:
                        st.success("💬 Discussion saved!")
                    else:
                        st.warning("⚠️ Discussion displayed but not saved to database")
                    
                    st.rerun()
        else:
            # Welcome screen
            st.header("Welcome to StackAgent! 🏗️")
            
            st.markdown("""
            **StackAgent** is your AI Technology Architect that analyzes project documents and provides 
            comprehensive technology stack recommendations.
            
            ### How it works:
            1. **📊 Analyzes** your project documents from DocAgent
            2. **🎯 Generates** initial comprehensive stack recommendation  
            3. **💬 Discusses** requirements and constraints with you
            4. **📋 Creates** final detailed technology stack specification
            5. **💾 Saves** everything as a JSON file for your team
            
            ### What you get:
            - **Complete technology stack** with detailed justifications
            - **Implementation roadmap** with phases and timelines
            - **Resource requirements** and cost estimations  
            - **Risk assessment** and mitigation strategies
            - **Alternative options** for different constraints
            
            👆 **Start by clicking "Analyze Project & Generate Initial Stack" in the sidebar**
            """)
            
            # Show available documents count
            try:
                doc_count = docs_collection.count()
                if doc_count > 0:
                    st.success(f"✅ Found {doc_count} project document sections ready for analysis")
                else:
                    st.warning("⚠️ No project documents found. Please run DocAgent first and upload project documents.")
            except Exception as e:
                st.error(f"Cannot access project documents: {str(e)}")
    
    # Footer
    st.divider()
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("*Powered by CrewAI, Ollama (Llama3.1:8B), and ChromaDB*")
    with col2:
        st.markdown(f"*Session ID: {st.session_state.stack_session_id[:8]}...*")

if __name__ == "__main__":
    main()