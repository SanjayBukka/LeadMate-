# System Architecture Plan: Document Agent Initialization

## Problem Analysis
1. **ID Mismatch**: Frontend sends `user.id` but documents are stored with `startupId`
2. **Storage Disconnect**: MongoDB (project docs) ≠ ChromaDB (agent storage)
3. **No Initialization**: Agent doesn't sync documents on first use
4. **Poor Error Visibility**: Can't see what's happening during sync

## Solution Architecture

### Layer 1: API Gateway (routers/agents.py)
- Receives request with `company_id` and `lead_id`
- Resolves IDs: `user.id` → `startupId` using JWT token
- Calls Document Initialization Service
- Returns response

### Layer 2: Document Initialization Service (services/document_sync_service.py)
- NEW: Dedicated service for document synchronization
- Responsibilities:
  - Resolve user IDs to startupId
  - Query MongoDB for documents
  - Sync to ChromaDB with proper metadata
  - Track sync status
  - Handle errors gracefully

### Layer 3: Document Agent (agents/document_agent.py)
- Uses initialized ChromaDB collection
- Searches documents efficiently
- Doesn't handle sync (separation of concerns)

### Layer 4: Storage
- MongoDB: Source of truth (documents collection)
- ChromaDB: Fast vector search (synced from MongoDB)

## Implementation Steps

1. Create `DocumentSyncService` with proper ID resolution
2. Modify router to use auth context (get startupId from JWT)
3. Add initialization endpoint for manual sync
4. Fix React duplicate key warning
5. Add comprehensive logging
6. Create cleanup script for testing

