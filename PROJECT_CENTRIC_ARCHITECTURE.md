# Project-Centric Architecture Design

## Overview
All data (documents, resumes, embeddings, agent data) is scoped to individual projects. Each project has isolated storage and agent instances.

## Architecture Flow

```
Project (MongoDB)
├── Documents (MongoDB + File Storage)
│   ├── Raw files stored in: uploads/{project_id}/
│   ├── Metadata in: documents collection
│   └── Embeddings in: ChromaDB startup_{startup_id}_project_{project_id}_documents
│
├── Resumes (MongoDB + File Storage)
│   ├── Raw files stored in: uploads/{project_id}/resumes/
│   ├── Metadata in: team_members collection
│   └── Embeddings in: ChromaDB startup_{startup_id}_project_{project_id}_resumes
│
├── Agent Data (ChromaDB + MongoDB)
│   ├── Document Agent Chat: startup_{startup_id}_project_{project_id}_doc_chat
│   ├── Stack Iterations: startup_{startup_id}_project_{project_id}_stack_iterations
│   ├── Team Formation: startup_{startup_id}_project_{project_id}_team_formation
│   └── Tasks: MongoDB tasks collection (filtered by projectId)
│
└── Project Metadata (MongoDB)
    ├── techStackId: Reference to generated stack
    ├── teamFormationId: Reference to team formation
    └── tasks: Array of task IDs
```

## Data Flow

### 1. Document Upload Flow
```
Manager Uploads Document
  ↓
Store in: uploads/{project_id}/{filename}
  ↓
Extract text content
  ↓
Store metadata in MongoDB: documents collection (with projectId)
  ↓
Create embeddings
  ↓
Store in ChromaDB: startup_{startup_id}_project_{project_id}_documents
  ↓
Document Agent can now query this project's documents
```

### 2. Resume Upload Flow
```
Manager/Team Lead Uploads Resume
  ↓
Store in: uploads/{project_id}/resumes/{filename}
  ↓
Extract text and skills
  ↓
Store in MongoDB: team_members collection (with projectId)
  ↓
Create embeddings
  ↓
Store in ChromaDB: startup_{startup_id}_project_{project_id}_resumes
  ↓
Team Formation Agent can query this project's resumes
```

### 3. Document Agent Flow
```
Query comes in for Project X
  ↓
Get project-specific collection: startup_{startup_id}_project_X_documents
  ↓
Search embeddings for relevant context
  ↓
Use project's document chat history
  ↓
Return project-specific response
```

### 4. Stack Agent Flow
```
Stack Agent called for Project X
  ↓
Query project's documents: startup_{startup_id}_project_X_documents
  ↓
Generate stack recommendation
  ↓
Store iteration in: startup_{startup_id}_project_X_stack_iterations
  ↓
Save final stack to MongoDB: techStacks collection (with projectId)
```

### 5. Team Formation Agent Flow
```
Team Formation called for Project X
  ↓
Query project's documents: startup_{startup_id}_project_X_documents
  ↓
Query project's resumes: startup_{startup_id}_project_X_resumes
  ↓
Query project's tech stack
  ↓
Generate team recommendations
  ↓
Store in: startup_{startup_id}_project_X_team_formation
```

### 6. Tasks Designer Agent Flow
```
Tasks Designer called for Project X
  ↓
Query project's documents: startup_{startup_id}_project_X_documents
  ↓
Query project's tech stack
  ↓
Query project's team formation
  ↓
Generate tasks
  ↓
Store in MongoDB: tasks collection (with projectId)
```

## Storage Structure

### MongoDB Collections

1. **projects**
   - `_id`: Project ID
   - `startupId`: Startup ID
   - `documents`: Array of document IDs
   - `techStackId`: Reference to tech stack
   - `teamFormationId`: Reference to team formation
   - `resumes`: Array of resume IDs (or team member IDs)

2. **documents**
   - `_id`: Document ID
   - `projectId`: Project ID (REQUIRED)
   - `startupId`: Startup ID
   - `originalFilename`: Original filename
   - `storedFilename`: Stored filename
   - `filePath`: Path to file
   - `extractedContent`: Extracted text
   - `uploadedBy`: User ID
   - `uploadedAt`: Timestamp

3. **team_members**
   - `_id`: Team member ID
   - `projectId`: Project ID (REQUIRED)
   - `startupId`: Startup ID
   - `name`: Member name
   - `resumeFilePath`: Path to resume file
   - `skills`: Extracted skills
   - `uploadedAt`: Timestamp

4. **tasks**
   - `_id`: Task ID
   - `projectId`: Project ID (REQUIRED)
   - `startupId`: Startup ID
   - `title`: Task title
   - `description`: Task description
   - `assignedTo`: Team member ID
   - `status`: Task status
   - `priority`: Priority level

5. **tech_stacks** (NEW)
   - `_id`: Tech stack ID
   - `projectId`: Project ID (REQUIRED)
   - `startupId`: Startup ID
   - `recommendations`: Tech stack data
   - `iterations`: Array of iteration IDs
   - `finalStack`: Final approved stack

### ChromaDB Collections

All collections follow pattern: `startup_{startup_id}_project_{project_id}_{type}`

1. **Documents**: `startup_{id}_project_{id}_documents`
2. **Resumes**: `startup_{id}_project_{id}_resumes`
3. **Doc Chat**: `startup_{id}_project_{id}_doc_chat`
4. **Stack Iterations**: `startup_{id}_project_{id}_stack_iterations`
5. **Team Formation**: `startup_{id}_project_{id}_team_formation`

### File Storage

```
uploads/
├── {project_id}/
│   ├── {document1}.pdf
│   ├── {document2}.docx
│   └── resumes/
│       ├── {resume1}.pdf
│       └── {resume2}.pdf
└── {project_id_2}/
    └── ...
```

## Agent Architecture

### All Agents Now Require:
1. `startup_id`: For isolation
2. `project_id`: For project-specific data access
3. Project-scoped ChromaDB collections
4. Project-scoped MongoDB queries

### Agent Initialization Pattern:
```python
agent = DocumentAgent(
    startup_id=startup_id,
    project_id=project_id  # NEW: Required
)
```

## Benefits

1. **Data Isolation**: Each project's data is completely isolated
2. **Scalability**: Easy to add/remove projects without affecting others
3. **Performance**: Smaller collections = faster queries
4. **Security**: Projects can't access other projects' data
5. **Maintenance**: Easy to archive/delete project data
6. **Multi-tenancy**: Clean separation for SaaS deployment

## Migration Plan

1. Update document storage to always require projectId
2. Update resume storage to always require projectId
3. Update all agents to require projectId
4. Update ChromaDB collection naming
5. Create Tasks Designer Agent
6. Update all API endpoints to require projectId
7. Add data validation to ensure projectId is always present

