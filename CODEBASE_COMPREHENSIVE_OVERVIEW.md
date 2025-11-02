# LeadMate - Comprehensive Codebase Overview

## 📋 Table of Contents
1. [System Architecture](#system-architecture)
2. [Backend Structure](#backend-structure)
3. [Frontend Structure](#frontend-structure)
4. [Backend Models](#backend-models)
5. [AI Agents System](#ai-agents-system)
6. [Database & Storage](#database--storage)
7. [Key Features & Workflows](#key-features--workflows)
8. [Technology Stack](#technology-stack)

---

## 🏗️ System Architecture

### High-Level Overview
**LeadMate** is a multi-tenant project management and AI-powered team formation platform that helps startups manage projects, form teams, and track progress using AI agents.

### Core Components:
1. **Backend API** (FastAPI + MongoDB)
2. **Frontend UI** (React + TypeScript + Vite)
3. **AI Agents** (CrewAI + Ollama + ChromaDB/MongoDB Vector Search)
4. **Vector Databases** (ChromaDB + MongoDB Atlas Vector Search)

---

## 🔧 Backend Structure

### `/backend` - Main Application

#### **Entry Point**: `main.py`
- FastAPI application initialization
- CORS middleware configuration
- MongoDB connection management
- Router registration for all endpoints
- Startup/shutdown event handlers

#### **Configuration**: `config.py`
- MongoDB connection string
- JWT secret keys
- Token expiration settings
- Environment configuration

#### **Database**: `database.py`
- MongoDB async connection using Motor
- Database index creation
- Connection lifecycle management

### **Models** (`/backend/models/`)
Pydantic models for data validation and serialization:

1. **`user.py`** - User management (Managers & Team Leads)
   - `UserBase`, `UserCreate`, `User`, `UserInDB`
   - Role-based access: `manager` or `teamlead`
   - JWT token models

2. **`startup.py`** - Company/Startup registration
   - `StartupBase`, `StartupCreate`, `Startup`, `StartupInDB`
   - Company information and statistics

3. **`project.py`** - Project management
   - `ProjectBase`, `ProjectCreate`, `Project`, `ProjectInDB`
   - Project status, progress tracking, document linking

4. **`team_member.py`** - Team member profiles
   - Resume upload, skills tracking
   - Project assignments

5. **`notification.py`** - Notification system
   - Real-time notifications via WebSocket

### **Routers** (`/backend/routers/`)
FastAPI route handlers organized by feature:

1. **`auth.py`** - Authentication & User Management
   - `/api/auth/register-startup` - Startup registration
   - `/api/auth/login` - User login with JWT
   - `/api/auth/me` - Get current user
   - `/api/auth/users/add-lead` - Manager adds team lead
   - `/api/auth/users/team-leads` - List team leads

2. **`projects.py`** - Project Management
   - CRUD operations for projects
   - Role-based access (manager sees all, teamlead sees assigned)

3. **`agents.py`** - Multi-Agent System API
   - Document Agent endpoints (`/api/agents/doc/*`)
   - Stack Agent endpoints (`/api/agents/stack/*`)
   - Task Agent endpoints (`/api/agents/tasks/*`)
   - Team Agent endpoints (`/api/agents/team/*`)
   - Chat interfaces for each agent

4. **`mongodb_agents.py`** - MongoDB Vector Search Agents
   - Alternative document agent using MongoDB Atlas Vector Search
   - Better integration with MongoDB ecosystem

5. **`doc_agent.py`** - DocAgent Service Router
   - Document Q&A, summarization
   - Chat history management

6. **`team_formation.py`** - Team Formation with CrewAI
   - Advanced team formation orchestration

7. **`team_members.py`** - Team member management
8. **`notifications.py`** - Notification CRUD
9. **`notifications_ws.py`** - WebSocket real-time notifications
10. **`workflow.py`** - Git repository analysis
11. **`reports.py`** - Progress reports & analytics
12. **`document_sync.py`** - Document synchronization endpoints

### **Services** (`/backend/services/`)
Business logic layer:

1. **`document_sync_service.py`** - Synchronizes MongoDB documents to ChromaDB
   - Resolves user IDs to startup IDs
   - Chunks documents for vector search
   - Manages sync state

2. **`vector_store_service.py`** - Vector database abstraction
   - ChromaDB operations
   - Document embedding and storage

3. **`mongodb_vector_service.py`** - MongoDB Vector Search operations

4. **`doc_agent_service.py`** - DocAgent business logic
   - CrewAI agent initialization
   - RAG (Retrieval Augmented Generation) operations

5. **`ollama_service.py`** - Ollama LLM integration
   - Model configuration
   - LLM initialization

6. **`document_extractor.py`** - Document text extraction
   - PDF, DOCX, TXT parsing

7. **`resume_processor.py`** - Resume analysis

8. **`notification_service.py`** - Notification management

9. **`git_service.py`** - Git repository analysis

### **Agents** (`/backend/agents/`)
AI Agent implementations using CrewAI:

1. **`document_agent.py`** - Document Analysis Agent
   - Analyzes project documents
   - Maintains conversation history
   - Exports context for Stack Agent
   - Uses ChromaDB for document storage

2. **`stack_agent.py`** - Team Formation Agent
   - Analyzes requirements and resumes
   - Forms optimal teams
   - Iterative refinement with lead feedback
   - Generates comprehensive reports

3. **`task_agent.py`** - Task Generation Agent
   - Breaks down projects into tasks
   - Assigns tasks to team members
   - Manages task status (todo/in-progress/completed)

4. **`team_agent.py`** - Team Management Agent
   - Team coordination and optimization

5. **`team_formation_agent.py`** - Advanced Team Formation
   - CrewAI orchestration with multiple agents
   - Skills matching, timeline coordination

6. **`mongodb_document_agent.py`** - MongoDB-based Document Agent
   - Alternative implementation using MongoDB Vector Search

### **Utils** (`/backend/utils/`)
Utility functions:

- **`auth.py`** - Authentication utilities
  - Password hashing (bcrypt)
  - JWT token creation/validation
  - User dependency injection for routes
  - Role-based access control (manager/teamlead)

- **`text_chunker.py`** - Text chunking for RAG

---

## 🎨 Frontend Structure

### `/frontend` - React Application

#### **Entry Points**:
- **`main.tsx`** - React app initialization
- **`App.tsx`** - Route configuration

#### **Tech Stack**:
- React 18 with TypeScript
- Vite for build tooling
- React Router v7 for routing
- TailwindCSS for styling
- Lucide React for icons

### **Pages** (`/frontend/src/pages/`)

#### **Manager Pages** (`/Manager/`):
1. **`ManagerDashboard.tsx`** - Manager's main dashboard
   - View all projects
   - Create/edit projects
   - Assign team leads

2. **`TeamManagement.tsx`** - Team lead management
   - Add/remove team leads
   - View team lead list

3. **`CreateProjectModal.tsx`** - Project creation form
4. **`EditProjectModal.tsx`** - Project editing form

#### **Team Lead Pages** (`/TeamLead/`):
1. **`Dashboard.tsx`** - Team lead dashboard
   - View assigned projects
   - Project statistics
   - Quick actions

2. **`TaskBoard.tsx`** - Kanban-style task board
   - Drag & drop task management
   - Task status updates

3. **`TeamMembers.tsx`** - Team member management
   - Upload resumes
   - View team profiles

4. **`AgentsHub.tsx`** - AI Agents overview
5. **`AIAgents.tsx`** - Agent selection interface

6. **Agent-Specific Pages** (`/Agents/`):
   - **`DocAgent.tsx`** - Document Agent interface
     - Document upload
     - Chat with documents
     - Document analysis

7. **`AIAssistant.tsx`** - General AI assistant interface
8. **`Workflow.tsx`** - Git repository analysis workflow
9. **`ProgressReports.tsx`** - Progress tracking and reports

### **Components** (`/frontend/src/components/`)
Reusable UI components:

- **`Navbar.tsx`** - Top navigation bar
- **`Sidebar.tsx`** - Side navigation menu
- **`ProjectCard.tsx`** - Project display card
- **`ProjectDetailModal.tsx`** - Project details modal
- **`TaskCard.tsx`** - Task display card
- **`TeamMemberCard.tsx`** - Team member profile card
- **`DocumentAnalysis.tsx`** - Document analysis UI
- **`ChatBubble.tsx`** - Chat message component
- **`NotificationDropdown.tsx`** - Notifications dropdown
- **`ProfileDropdown.tsx`** - User profile menu
- **`LoadingIndicator.tsx`** - Loading spinner
- **`ProtectedRoute.tsx`** - Route protection by role

### **Contexts** (`/frontend/src/contexts/`)
React Context providers:

- **`AuthContext.tsx`** - Authentication state management
  - User login/logout
  - Token management
  - Role-based permissions

- **`ThemeContext.tsx`** - Dark/light theme management

### **Data** (`/frontend/src/data/`)
- **`mockData.ts`** - Mock data for development

---

## 📚 Backend Models

### `/backend models` - Reference Models & Documentation

This folder contains:
1. **Reference implementations** from earlier development
2. **Documentation PDFs** for various components
3. **Isolated model implementations** (DocAgent, Stack Agent, Team Formation)

#### **Key Folders**:

1. **`/DocAgent/`** - Standalone DocAgent implementation
   - `doc_agent_system.py` - Complete document analysis system
   - Uses ChromaDB for vector storage
   - Streamlit app for testing

2. **`/stack/`** - Stack Agent implementation
   - `stack_agent_system.py` - Tech stack analysis

3. **`/managemnet/`** - Management utilities
   - Repository analysis tools

4. **`/Team/`** - Team formation logic
   - `team_formation_agent.py` - CrewAI team formation

**Note**: These are reference implementations. The main application uses the agents in `/backend/agents/`.

---

## 🤖 AI Agents System

### Architecture Overview

The system uses **CrewAI** for agent orchestration and **Ollama** for local LLM inference.

### Agent Types:

1. **Document Agent** (`DocumentAgent`)
   - **Purpose**: Analyze project documents and clarify requirements
   - **Storage**: ChromaDB or MongoDB Vector Search
   - **Features**:
     - Document upload (PDF, DOCX, TXT)
     - Semantic search over documents
     - Chat interface for Q&A
     - Context export for Stack Agent

2. **Stack Agent** (`StackAgent`)
   - **Purpose**: Form optimal teams based on requirements and resumes
   - **Features**:
     - Resume upload and analysis
     - Initial team recommendation
     - Iterative refinement based on feedback
     - Final team report generation

3. **Task Agent** (`TaskAgent`)
   - **Purpose**: Generate actionable tasks from project requirements
   - **Features**:
     - Task breakdown by requirements
     - Team member assignment
     - Priority and dependency management
     - Status tracking (todo/in-progress/completed)

4. **Team Agent** (`TeamAgent`)
   - **Purpose**: Team coordination and optimization

5. **Team Formation Agent** (`TeamFormationAgent`)
   - **Purpose**: Advanced multi-agent team formation
   - Uses CrewAI with multiple specialized agents:
     - Team Analyst
     - Skills Matcher
     - Project Coordinator

### Agent Communication Flow:

```
Manager Creates Project
    ↓
Team Lead Uploads Documents → Document Agent
    ↓
Document Agent Analyzes → Chat with Lead (Requirements Clarification)
    ↓
Context Export → Stack Agent
    ↓
Team Lead Uploads Resumes → Stack Agent
    ↓
Stack Agent Forms Team → Iterative Refinement
    ↓
Stack Agent Exports Team → Task Agent
    ↓
Task Agent Generates Tasks → Task Board
```

### Vector Storage:

1. **ChromaDB** - Primary vector store
   - Per-company/lead isolation
   - Document embeddings
   - Chat history storage

2. **MongoDB Atlas Vector Search** - Alternative
   - Better MongoDB integration
   - Unified storage solution

---

## 🗄️ Database & Storage

### MongoDB (Primary Database)
**Collections**:
- `startups` - Company information
- `users` - Managers and team leads
- `projects` - Project data
- `documents` - Uploaded project documents
- `team_members` - Team member profiles
- `notifications` - User notifications
- `chat_sessions` - Agent chat history

### ChromaDB (Vector Database)
**Structure**:
```
chroma_db/
  company_{company_id}/
    lead_{lead_id}/
      documents/      # Document embeddings
      doc_chat/       # Chat history
      resumes/        # Resume embeddings
      stack_iterations/ # Team formation iterations
```

### MongoDB Vector Search
- Alternative to ChromaDB
- Uses MongoDB Atlas vector search indexes
- Better integration with main database

---

## 🔑 Key Features & Workflows

### 1. **Startup Registration**
- Company registers with manager account
- Manager can add team leads
- Each startup is isolated (multi-tenant)

### 2. **Project Management**
- Manager creates projects
- Assigns team lead to project
- Team lead views only assigned projects
- Progress tracking and status updates

### 3. **Document Analysis Workflow**
1. Team lead uploads project documents
2. Documents are extracted and chunked
3. Embedded into vector database
4. Team lead chats with Document Agent
5. Requirements are clarified through conversation

### 4. **Team Formation Workflow**
1. Team lead uploads team member resumes
2. Stack Agent analyzes resumes and requirements
3. Generates initial team recommendation
4. Team lead provides feedback
5. Stack Agent iteratively refines team
6. Final team formation report generated

### 5. **Task Generation Workflow**
1. Task Agent receives:
   - Project requirements (from Document Agent)
   - Team composition (from Stack Agent)
2. Generates comprehensive task breakdown
3. Assigns tasks to team members
4. Tasks appear in Task Board

### 6. **Real-time Notifications**
- WebSocket-based notifications
- Project assignments
- Task updates
- Agent responses

---

## 🛠️ Technology Stack

### Backend:
- **FastAPI** - Modern Python web framework
- **MongoDB** - NoSQL database (Motor for async)
- **Pydantic** - Data validation
- **CrewAI** - AI agent orchestration
- **Ollama** - Local LLM inference
- **ChromaDB** - Vector database
- **LangChain** - LLM framework
- **PyPDF2** - PDF processing
- **python-docx** - DOCX processing
- **JWT** - Authentication tokens
- **bcrypt** - Password hashing

### Frontend:
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **React Router v7** - Routing
- **TailwindCSS** - Styling
- **Lucide React** - Icons

### AI/ML:
- **CrewAI** - Multi-agent orchestration
- **Ollama** - LLM server (llama3.1:8b, llama3.2:3b)
- **ChromaDB** - Vector embeddings
- **LangChain** - LLM integration
- **MongoDB Vector Search** - Alternative vector storage

---

## 📁 Important File Locations

### Configuration:
- `backend/config.py` - Application settings
- `backend/database.py` - Database connection
- `frontend/vite.config.ts` - Frontend build config

### Entry Points:
- `backend/main.py` - Backend server entry
- `frontend/src/main.tsx` - Frontend entry
- `frontend/src/App.tsx` - React app routes

### Key Services:
- `backend/services/document_sync_service.py` - Document sync
- `backend/services/vector_store_service.py` - Vector operations
- `backend/services/doc_agent_service.py` - DocAgent service

### Key Agents:
- `backend/agents/document_agent.py` - Document analysis
- `backend/agents/stack_agent.py` - Team formation
- `backend/agents/task_agent.py` - Task generation

### Authentication:
- `backend/utils/auth.py` - Auth utilities
- `backend/routers/auth.py` - Auth endpoints
- `frontend/src/contexts/AuthContext.tsx` - Frontend auth

---

## 🔄 Data Flow Example

### Document Upload & Analysis:
```
1. Frontend → POST /api/documents/upload
2. Router → Document Sync Service
3. Service → Extract text from PDF/DOCX
4. Service → Chunk text (1000 chars, 200 overlap)
5. Service → Create embeddings (via Ollama/LangChain)
6. Service → Store in ChromaDB/MongoDB Vector Search
7. Service → Update MongoDB documents collection
8. Response → Document ID & metadata
```

### Chat with Document Agent:
```
1. Frontend → POST /api/agents/doc/chat
2. Router → Document Agent
3. Agent → Retrieve relevant document chunks (RAG)
4. Agent → Build context from chunks + chat history
5. Agent → Send to CrewAI Agent with Ollama LLM
6. Agent → Store chat history
7. Response → AI-generated answer
```

---

## 🎯 Key Design Patterns

1. **Multi-Tenancy**: Company-based isolation (startupId)
2. **Role-Based Access**: Manager vs Team Lead permissions
3. **Agent Pattern**: CrewAI agents with specific roles
4. **Service Layer**: Business logic separated from routes
5. **Repository Pattern**: Database abstraction
6. **RAG Pattern**: Retrieval Augmented Generation for document Q&A
7. **Async/Await**: Full async support in backend

---

## 📝 Notes

- **Development**: Uses Ollama for local LLM (requires Ollama server running)
- **Production**: Can switch to OpenAI or other LLM providers via CrewAI
- **Vector Storage**: Supports both ChromaDB and MongoDB Vector Search
- **File Upload**: Documents stored in MongoDB with extracted content
- **Authentication**: JWT tokens with 24-hour expiration
- **Real-time**: WebSocket notifications for live updates

---

## 🚀 Getting Started

1. **Backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

2. **Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Ollama** (for AI agents):
   ```bash
   ollama serve
   ollama pull llama3.1:8b
   ```

4. **MongoDB**: Configure connection in `backend/config.py`

---

This overview provides a comprehensive understanding of the entire LeadMate codebase structure, architecture, and key components. Each section can be explored in detail by examining the specific files mentioned.

