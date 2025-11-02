# Backend Models Comprehensive Guide

## Overview

This document provides a complete understanding of all models in the LeadMate application. There are two main directories:
1. **`backend/models/`** - Database models (Pydantic models for MongoDB)
2. **`backend models/`** - Agent systems and reference implementations

---

## Part 1: Database Models (`backend/models/`)

These are Pydantic models that define the data structure for MongoDB collections. All models follow a consistent pattern with Base, Create, Update, and InDB variants.

### 1. **Startup Model** (`startup.py`)

**Purpose**: Represents companies/startups that register on the platform.

**Collections**: `startups`

**Key Fields**:
- `companyName` (str): Name of the company
- `companyEmail` (EmailStr): Company email (unique)
- `industry` (Optional[str]): Industry sector
- `companySize` (Optional[str]): Size ranges (1-10, 11-50, 51-200, 201-500, 500+)
- `website` (Optional[str]): Company website
- `description` (Optional[str]): Company description
- `registrationDate` (datetime): When company registered
- `status` (str): active, suspended, inactive
- `totalUsers` (int): Count of users in this startup
- `totalProjects` (int): Count of projects

**Model Variants**:
- `StartupBase`: Base fields
- `StartupCreate`: For registration (includes manager details)
- `Startup`: Response model (with id)
- `StartupInDB`: Database model (with ObjectId)

**Relationships**:
- Has many Users (managers and team leads)
- Has many Projects

---

### 2. **User Model** (`user.py`)

**Purpose**: Represents managers and team leads in the system.

**Collections**: `users`

**Key Fields**:
- `name` (str): User's full name
- `email` (EmailStr): Email address (unique)
- `role` (str): Either "manager" or "teamlead"
- `startupId` (str): Reference to parent startup
- `hashedPassword` (str): Bcrypt hashed password (InDB only)
- `initials` (str): User initials for avatar
- `isActive` (bool): Account status
- `createdAt` (datetime): Account creation date
- `lastLogin` (Optional[datetime]): Last login timestamp
- `createdBy` (Optional[str]): User ID who created this user

**Model Variants**:
- `UserBase`: Base fields (name, email, role)
- `UserCreate`: For creating users (includes password and startupId)
- `UserUpdate`: For updating users (all fields optional)
- `User`: Response model
- `UserInDB`: Database model with hashed password
- `UserLogin`: For login requests
- `Token`: JWT token response
- `TokenData`: Token payload

**Relationships**:
- Belongs to one Startup
- Managers can create Projects
- Team Leads can be assigned to Projects

---

### 3. **Project Model** (`project.py`)

**Purpose**: Represents projects created by managers and assigned to team leads.

**Collections**: `projects`

**Key Fields**:
- `title` (str): Project name
- `description` (str): Project description
- `deadline` (Optional[datetime]): Project deadline
- `status` (str): active, completed, on_hold, cancelled
- `startupId` (str): Parent company
- `managerId` (str): Manager who created the project
- `teamLeadId` (Optional[str]): Assigned team lead
- `progress` (int): 0-100 completion percentage
- `documents` (List[str]): Array of document IDs
- `techStackId` (Optional[str]): Reference to tech stack recommendation
- `teamFormationId` (Optional[str]): Reference to team formation
- `createdAt` (datetime): Creation timestamp
- `updatedAt` (Optional[datetime]): Last update timestamp

**Model Variants**:
- `ProjectBase`: Base fields
- `ProjectCreate`: For creating projects
- `ProjectUpdate`: For updating projects (all optional)
- `Project`: Response model (includes team lead name)
- `ProjectInDB`: Database model

**Relationships**:
- Belongs to one Startup
- Belongs to one Manager (creator)
- Can have one Team Lead (assigned)
- Has many Documents
- Can have one Tech Stack
- Can have one Team Formation

---

### 4. **Team Member Model** (`team_member.py`)

**Purpose**: Represents team members added to projects (extracted from resumes).

**Collections**: `team_members`

**Key Fields**:
- `name` (str): Team member name
- `email` (str): Email address
- `role` (str): Job role/title
- `phone` (Optional[str]): Phone number
- `techStack` (List[str]): Technologies they know
- `recentProjects` (List[str]): Previous project names
- `experience` (Optional[str]): Years/description of experience
- `education` (Optional[List[str]]): Education history
- `skills` (Optional[dict]): Detailed skills object
- `avatarUrl` (Optional[str]): Profile picture URL
- `resumeFilePath` (Optional[str]): Path to uploaded resume
- `projectId` (str): Project they're assigned to
- `startupId` (str): Parent company
- `createdAt` (datetime): When added
- `updatedAt` (datetime): Last update

**Model Variants**:
- `TeamMemberBase`: Base fields
- `TeamMemberCreate`: For creating team members
- `TeamMember`: Response model
- `TeamMemberInDB`: Database model

**Relationships**:
- Belongs to one Project
- Belongs to one Startup
- Created by Team Formation Agent from resumes

---

### 5. **Notification Model** (`notification.py`)

**Purpose**: Represents notifications sent to team leads.

**Collections**: `notifications`

**Key Fields**:
- `userId` (str): Team lead who receives notification
- `startupId` (str): Parent company
- `type` (Literal): One of:
  - `project_assigned`: Project assigned to team lead
  - `project_updated`: Project details updated
  - `project_completed`: Project marked complete
  - `team_added`: Team members added
- `title` (str): Notification title
- `message` (str): Notification message
- `relatedId` (Optional[str]): Related project/document ID
- `isRead` (bool): Read status
- `createdAt` (datetime): When created

**Model Variants**:
- `NotificationBase`: Base fields
- `NotificationCreate`: For creating notifications
- `Notification`: Response model
- `NotificationInDB`: Database model

**Relationships**:
- Belongs to one User (team lead)
- Belongs to one Startup

---

## Part 2: Agent Systems (`backend models/`)

These are reference implementations and documentation for the AI agent systems.

### 1. **DocAgent** (`DocAgent/`)

**Purpose**: Document processing and RAG (Retrieval-Augmented Generation) system.

**Technology Stack**:
- CrewAI for agent orchestration
- ChromaDB for vector storage
- Ollama (llama3.1:8b) for LLM
- Streamlit for UI
- PyPDF2, python-docx for document extraction

**Key Features**:
- Upload and process documents (PDF, DOCX, TXT)
- Text chunking and vectorization
- Document search and retrieval
- Chat interface for document queries
- Persistent storage in ChromaDB

**Collections Used**:
- `project_documents`: Chunked document content
- `chat_history`: Conversation history

**Main Components**:
- `DocumentProcessor`: Handles document processing
- `DocAgent`: CrewAI agent for document analysis
- Streamlit UI for interaction

**PDF Documentation**:
- `DocAgent_ Complete Technical Documentation.pdf`: Complete guide

---

### 2. **Stack Agent** (`stack/`)

**Purpose**: Technology stack recommendation system.

**Technology Stack**:
- CrewAI for agent orchestration
- ChromaDB for context storage
- Ollama (llama3.1:8b) for LLM
- Streamlit for UI

**Key Features**:
- Analyzes project requirements from DocAgent
- Recommends technology stacks
- Iterative refinement with team lead feedback
- Stores final stack recommendations

**Collections Used**:
- `project_documents`: Reads from DocAgent
- `stack_discussions`: Team lead conversations
- `final_stacks`: Approved technology stacks

**Main Components**:
- `StackAnalyzer`: Handles stack analysis
- `StackAgent`: CrewAI agent for recommendations
- Outputs JSON files in `generated_stacks/`

**PDF Documentation**:
- `StackAgent_ Complete Technical Documentation.pdf`: Complete guide

---

### 3. **Team Formation Agent** (`Team/`)

**Purpose**: Team member extraction and formation from resumes.

**Technology Stack**:
- CrewAI for agent orchestration
- ChromaDB for resume storage
- Ollama (llama3.1:8b) for LLM
- Streamlit for UI
- PyPDF2 for resume parsing

**Key Features**:
- Upload resumes (PDF)
- Extract skills, experience, education
- Match candidates to project requirements
- Form teams based on tech stack
- Store team member profiles

**Collections Used**:
- `team_skills`: Resume data and skills
- `chat_history`: Conversations

**Main Components**:
- `TeamFormationSystem`: Main system class
- Resume text extraction
- LLM-based skill extraction
- Team matching algorithm

**Data Flow**:
1. Upload resumes → Extract text
2. LLM extracts structured data (JSON)
3. Store in ChromaDB
4. Match with project requirements
5. Generate team recommendations

---

### 4. **Management System** (`managemnet/`)

**Purpose**: Repository analysis and AI insights for codebase management.

**Technology Stack**:
- Streamlit for UI
- GitPython for repository analysis
- Pandas for data processing
- Ollama for AI insights
- Plotly for visualizations

**Key Features**:
- Git repository analysis
- Commit pattern analysis
- Developer activity insights
- File type analysis
- AI-powered insights generation

**Main Components**:
- `RepoAnalyzer`: Analyzes Git repositories
- `AIInsights`: Generates AI-powered insights
- `DataManager`: Manages repository data
- Streamlit dashboard

**Features**:
- Commit statistics
- Developer contributions
- Project summaries
- Activity trends
- Code quality insights

---

## Additional PDF Documentation

Located in `backend models/`:

1. **LeadMate_ Complete Understanding Guide (0 to 100).pdf**
   - Complete system overview from beginner to advanced

2. **LeadMate_ Technical Implementation Documentation.pdf**
   - Technical implementation details

3. **LeadMate_ AI Engineering Strategist - Project Documentation.pdf**
   - Project documentation and architecture

4. **CodeClarity AI_ Complete Technical Documentation.pdf**
   - Code clarity and analysis documentation

---

## Database Relationships Summary

```
Startup (1) ────< (Many) Users (managers/team leads)
  │
  ├───< (Many) Projects
  │      │
  │      ├───< (Many) Documents
  │      │
  │      ├───< (Many) Team Members
  │      │
  │      └───< (Many) Notifications
  │
  └───< (Many) Notifications
```

---

## Agent Integration Flow

```
1. Document Upload → DocAgent
   └──> Processes & stores in ChromaDB

2. Project Requirements → Stack Agent
   └──> Reads from DocAgent
   └──> Generates tech stack recommendations
   └──> Stores in MongoDB (techStackId)

3. Team Formation → Team Agent
   └──> Reads project requirements (DocAgent)
   └──> Reads tech stack (Stack Agent output)
   └──> Processes resumes
   └──> Matches candidates
   └──> Stores team members in MongoDB

4. Task Generation → Task Agent
   └──> Uses project requirements
   └──> Uses team formation
   └──> Generates tasks
   └──> Stores in MongoDB (tasks collection)
```

---

## Key Design Patterns

1. **Model Variants**: Each model has Base, Create, Update, InDB variants
2. **ObjectId Handling**: Custom `PyObjectId` class for MongoDB integration
3. **Pydantic v2**: Uses new Pydantic v2 patterns with `model_config`
4. **ChromaDB Collections**: Each agent maintains separate collections
5. **CrewAI Agents**: All agents use CrewAI for orchestration
6. **Ollama Integration**: Consistent use of llama3.1:8b model

---

## Notes

- All database models use MongoDB with Motor (async driver)
- All agents use ChromaDB for vector storage
- All agents use Ollama LLM (local, no API keys needed)
- Streamlit apps are reference implementations
- The actual backend uses FastAPI routers that integrate these concepts
- PDF documentation provides deeper insights into each system

