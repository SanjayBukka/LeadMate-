# Project-Centric API Guide

## Overview

All APIs now require `project_id` to ensure data is properly scoped to projects. This ensures complete data isolation and proper agent functionality.

## API Endpoints

### Document Management

#### Upload Documents for a Project
```http
POST /api/documents/upload/{project_id}
Content-Type: multipart/form-data

files: [File, File, ...] (Manager only)
```

**Response:**
```json
{
  "message": "Successfully uploaded 2 document(s)",
  "documents": [
    {
      "id": "doc_id_1",
      "filename": "requirements.pdf",
      "size": 1024000,
      "uploadedAt": "2025-01-15T10:30:00"
    }
  ]
}
```

**What Happens:**
1. Files saved to `uploads/{project_id}/`
2. Text extracted from documents
3. Metadata stored in MongoDB with `projectId`
4. **Embeddings created** in ChromaDB: `startup_{id}_project_{id}_documents`
5. Ready for Document Agent queries

---

#### Get Project Documents
```http
GET /api/documents/project/{project_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "projectId": "project_123",
  "totalDocuments": 3,
  "documents": [
    {
      "id": "doc_id",
      "filename": "requirements.pdf",
      "size": 1024000,
      "uploadedBy": "Manager Name",
      "uploadedAt": "2025-01-15T10:30:00",
      "extractedContent": "..."
    }
  ]
}
```

---

### Resume Management

#### Upload Resume for a Project
```http
POST /api/team-members/upload-resume
Content-Type: multipart/form-data

project_id: {project_id}
file: {resume.pdf} (Team Lead only)
```

**Response:**
```json
{
  "message": "Resume uploaded and processed successfully",
  "teamMember": {
    "id": "member_id",
    "name": "John Doe",
    "email": "john@example.com",
    "techStack": ["Python", "React", "MongoDB"],
    "skills": {...},
    "projectId": "project_123"
  }
}
```

**What Happens:**
1. Resume saved to `uploads/{project_id}/resumes/`
2. Skills extracted using Gemini/Ollama
3. Stored in MongoDB `team_members` with `projectId`
4. **Embeddings created** in ChromaDB: `startup_{id}_project_{id}_resumes`
5. Ready for Team Formation Agent

---

### Document Agent (Project-Scoped)

#### Chat with Document Agent
```http
POST /api/project-agents/doc/chat/{project_id}
Content-Type: application/x-www-form-urlencoded

message: "What are the main requirements for this project?"
```

**Response:**
```json
{
  "project_id": "project_123",
  "response": "Based on the project documents...",
  "message": "What are the main requirements?"
}
```

**What It Does:**
- Searches **only** this project's documents
- Uses **only** this project's chat history
- Returns insights specific to this project

---

#### Get Document Chat History
```http
GET /api/project-agents/doc/chat-history/{project_id}
```

**Response:**
```json
{
  "project_id": "project_123",
  "chat_history": [
    {
      "user_message": "What are the requirements?",
      "agent_response": "Based on documents...",
      "timestamp": "2025-01-15T10:30:00"
    }
  ]
}
```

---

#### Get Project Document Summary
```http
GET /api/project-agents/doc/summary/{project_id}
```

**Response:**
```json
{
  "project_id": "project_123",
  "summary": "Project Overview:\n1. Main objectives...\n2. Technical requirements..."
}
```

---

### Stack Agent (Project-Scoped)

#### Recommend Tech Stack
```http
POST /api/project-agents/stack/recommend/{project_id}
Content-Type: application/x-www-form-urlencoded

feedback: "Need more cloud-native solutions" (optional)
```

**Response:**
```json
{
  "iteration_id": "iter_123",
  "stack_recommendation": {
    "frontend": "React + TypeScript",
    "backend": "FastAPI + Python",
    "database": "MongoDB Atlas",
    "reasoning": "..."
  },
  "project_id": "project_123",
  "timestamp": "2025-01-15T10:30:00"
}
```

**What It Does:**
- Analyzes **only** this project's documents
- Considers previous iterations for this project
- Stores iteration in ChromaDB: `startup_{id}_project_{id}_stack_iterations`
- Saves final stack to MongoDB `tech_stacks` with `projectId`

---

#### Get Stack Iterations
```http
GET /api/project-agents/stack/iterations/{project_id}
```

**Response:**
```json
{
  "project_id": "project_123",
  "iterations": [
    {
      "iteration_number": 1,
      "stack_summary": "React + FastAPI...",
      "timestamp": "2025-01-15T10:30:00",
      "has_feedback": false
    }
  ]
}
```

---

### Team Formation Agent (Project-Scoped)

#### Form Team for Project
```http
POST /api/project-agents/team/form/{project_id}
```

**Response:**
```json
{
  "formation_id": "formation_123",
  "team_recommendation": {
    "recommended_roles": [
      {
        "role": "Full Stack Developer",
        "assignee": "John Doe",
        "reasoning": "Has React and Python experience"
      }
    ],
    "skill_gaps": [],
    "team_structure": {...}
  },
  "project_id": "project_123",
  "timestamp": "2025-01-15T10:30:00"
}
```

**What It Does:**
- Uses **only** this project's documents (requirements)
- Uses **only** this project's resumes (candidates)
- Uses this project's tech stack (if available)
- Matches candidates to project needs
- Stores in ChromaDB: `startup_{id}_project_{id}_team_formation`
- Saves to MongoDB `team_formations` with `projectId`

---

### Tasks Designer Agent (NEW)

#### Generate Tasks for Project
```http
POST /api/project-agents/tasks/generate/{project_id}
```

**Response:**
```json
{
  "project_id": "project_123",
  "tasks_generated": 15,
  "tasks": [
    {
      "id": "task_123",
      "title": "Set up development environment",
      "status": "pending",
      "priority": "high"
    }
  ],
  "timestamp": "2025-01-15T10:30:00"
}
```

**What It Does:**
- Uses **only** this project's documents (requirements)
- Uses **only** this project's tech stack (implementation approach)
- Uses **only** this project's team formation (assignments)
- Generates actionable tasks with dependencies
- Stores in MongoDB `tasks` collection with `projectId`

---

#### Get Project Tasks
```http
GET /api/project-agents/tasks/{project_id}
```

**Response:**
```json
{
  "project_id": "project_123",
  "tasks": [
    {
      "id": "task_123",
      "title": "Set up environment",
      "description": "...",
      "status": "in_progress",
      "priority": "high",
      "assignedTo": "member_id",
      "deadline": "2025-01-20T00:00:00"
    }
  ],
  "total": 15
}
```

---

### Project Data Summary

#### Get All Project Data Summary
```http
GET /api/project-agents/summary/{project_id}
```

**Response:**
```json
{
  "projectId": "project_123",
  "startupId": "startup_456",
  "documents": {
    "count": 5,
    "embedded": 5
  },
  "resumes": {
    "count": 3,
    "embedded": 3
  },
  "tasks": {
    "count": 15
  },
  "techStackId": "stack_789",
  "teamFormationId": "formation_101"
}
```

---

## Complete Workflow Example

### 1. Manager Creates Project
```http
POST /api/projects
{
  "title": "E-Commerce Platform",
  "description": "Build online shopping platform",
  "teamLeadId": "lead_123"
}
```

### 2. Manager Uploads Documents
```http
POST /api/documents/upload/project_123
files: [requirements.pdf, specifications.docx]
```
✅ Documents stored with embeddings in project-specific collection

### 3. Team Lead Chats with Document Agent
```http
POST /api/project-agents/doc/chat/project_123
message: "What are the payment requirements?"
```
✅ Agent queries only project_123's documents

### 4. Team Lead Gets Stack Recommendation
```http
POST /api/project-agents/stack/recommend/project_123
```
✅ Agent analyzes only project_123's documents

### 5. Team Lead Uploads Resumes
```http
POST /api/team-members/upload-resume?project_id=project_123
file: john_resume.pdf
```
✅ Resume stored with embeddings in project-specific collection

### 6. Team Lead Forms Team
```http
POST /api/project-agents/team/form/project_123
```
✅ Agent uses project_123's documents + resumes + stack

### 7. Team Lead Generates Tasks
```http
POST /api/project-agents/tasks/generate/project_123
```
✅ Agent uses project_123's documents + stack + team

**Result**: All data is isolated to project_123. No mixing with other projects!

---

## Key Points

1. **All endpoints require `project_id`**
2. **All data stored with `projectId`**
3. **All embeddings in project-specific ChromaDB collections**
4. **All agents use project-specific data only**
5. **Complete data isolation per project**

---

## Data Isolation Guarantees

✅ Document Agent: Can only see project's documents  
✅ Stack Agent: Can only analyze project's documents  
✅ Team Formation: Can only use project's resumes + documents  
✅ Tasks Designer: Can only use project's data  
✅ Embeddings: Scoped to project  
✅ Chat History: Scoped to project  
✅ File Storage: Organized by project  

**No data leakage between projects!** 🔒

