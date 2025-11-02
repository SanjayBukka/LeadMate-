# Document Agent Sync Solution

## Problem
Documents were uploaded through the project management system (stored in MongoDB), but the Document Agent couldn't see them because:
1. Documents are stored with `startupId` and `projectId` in MongoDB
2. Document Agent was being called with `company_id = user.id` and `lead_id = user.id` (wrong IDs)
3. Document Agent uses ChromaDB which was separate from MongoDB storage

## Solution Implemented

### 1. **Intelligent Document Sync** (`backend/agents/document_agent.py`)

Added `_sync_project_documents()` method that:
- Automatically syncs documents from MongoDB to ChromaDB when needed
- Handles ID mismatch: if `company_id` looks like `user.id`, it looks up the user's `startupId`
- Searches across ALL projects for the user's startup
- Prevents duplicate syncing by checking ChromaDB first
- Chunks and indexes documents for efficient vector search

### 2. **Smart Document Detection** (`_has_uploaded_documents()`)

Enhanced to:
- Check ChromaDB first (fast)
- Fall back to MongoDB (source of truth)
- Automatically trigger sync if documents found in MongoDB but not ChromaDB
- Handle ID resolution (user.id → startupId)

### 3. **Hybrid Search Strategy** (`search_documents()`)

Improved to:
- Try ChromaDB vector search first (faster, more relevant)
- Fall back to MongoDB if ChromaDB is empty
- Automatically sync documents before searching if needed
- Search across all projects for the startup

### 4. **Auto-Sync on Chat** (`backend/routers/agents.py`)

Modified `/api/agents/doc/chat` endpoint to:
- Force sync documents on first chat request
- Log sync status for debugging
- Ensure documents are always available before processing queries

## How It Works

### Flow Diagram

```
User uploads document → MongoDB (documents collection)
                            ↓
User chats with Document Agent
                            ↓
Agent checks for documents → MongoDB found → Sync to ChromaDB
                            ↓
Agent searches documents → ChromaDB (vector search)
                            ↓
Agent responds with context from documents ✅
```

### ID Resolution

1. **Frontend sends**: `company_id = user.id`, `lead_id = user.id`
2. **Backend detects**: If `company_id` is ObjectId format
3. **Backend looks up**: User's `startupId` from database
4. **Backend searches**: Documents where `startupId = actual_startup_id`
5. **Backend syncs**: Documents to ChromaDB with proper metadata

### Sync Strategy

1. **Check if already synced**: Count ChromaDB documents
2. **If empty**: Query MongoDB for documents
3. **For each document**:
   - Check if already in ChromaDB (by `mongodb_doc_id`)
   - Extract text from `extractedContent`
   - Chunk text into smaller pieces
   - Store chunks in ChromaDB with metadata
4. **Metadata includes**:
   - Original document ID
   - Filename
   - Project ID
   - Company ID (actual startupId)
   - Sync timestamp

## Key Features

✅ **Automatic Sync**: Documents sync automatically when needed
✅ **ID Resolution**: Handles user.id → startupId conversion automatically  
✅ **Duplicate Prevention**: Checks before syncing to avoid duplicates
✅ **Fast Search**: Uses ChromaDB vector search for speed
✅ **Fallback Support**: Falls back to MongoDB if ChromaDB unavailable
✅ **Multi-Project Support**: Searches across all projects for a startup
✅ **Error Handling**: Graceful fallbacks if sync fails

## Testing

To verify the solution works:

1. **Upload a document** through the project management UI
2. **Chat with Document Agent** asking "summarize the doc"
3. **Check backend logs** for:
   - "Document sync status" message
   - ChromaDB and MongoDB counts
4. **Verify response** includes content from uploaded document

## Files Modified

1. `backend/agents/document_agent.py`
   - Added `_sync_project_documents()` method
   - Enhanced `_has_uploaded_documents()` method
   - Improved `search_documents()` method

2. `backend/routers/agents.py`
   - Added sync trigger in `/doc/chat` endpoint
   - Added logging for sync status

## Future Improvements

1. **Frontend Enhancement**: Update frontend to send `startupId` instead of `user.id`
2. **Project Selection**: Add project selection in AI Agents page for project-specific chats
3. **Real-time Sync**: Sync documents immediately after upload
4. **Sync Endpoint**: Add manual sync endpoint for troubleshooting

## Debugging

If documents still aren't showing:

1. Check backend logs for sync messages
2. Check MongoDB: `db.documents.find({startupId: "..."})`
3. Check ChromaDB: Use `debug_documents()` method
4. Verify `extractedContent` field exists in MongoDB documents
5. Check if `startupId` matches between user and documents

## Notes

- Sync happens lazily (on first check/search) to avoid blocking initialization
- Documents are chunked for efficient vector search (1000 chars, 200 overlap)
- Sync is idempotent (safe to call multiple times)
- Works even if company_id is user.id (automatically resolves to startupId)

