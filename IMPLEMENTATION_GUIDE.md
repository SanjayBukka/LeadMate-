# Document Agent Initialization - Implementation Guide

## ✅ What Was Built

### 1. **Document Sync Service** (`backend/services/document_sync_service.py`)
- Professional service layer for document synchronization
- Handles ID resolution (user.id → startupId)
- Syncs MongoDB → ChromaDB with proper chunking
- Comprehensive error handling and logging

### 2. **Auto-Initialization in Chat Endpoint**
- `/api/agents/doc/chat` now auto-initializes documents
- Uses sync service before processing queries
- Resolves IDs automatically
- Logs every step for debugging

### 3. **Manual Sync Endpoints** (`backend/routers/document_sync.py`)
- `POST /api/agents/doc/sync` - Manually trigger sync
- `GET /api/agents/doc/sync/status` - Check sync status

### 4. **Cleanup Script** (`backend/scripts/clean_chromadb.py`)
- Clean ChromaDB for fresh testing
- Run: `python backend/scripts/clean_chromadb.py`

### 5. **React Fix**
- Fixed duplicate key warning in AIAgents.tsx

## 🚀 How to Test from Scratch

### Step 1: Clean ChromaDB (Optional - for fresh start)
```bash
cd backend
python scripts/clean_chromadb.py
# Type 'yes' when prompted
```

### Step 2: Start Backend
```bash
cd backend
python main.py
```

### Step 3: Upload a Document
1. Login to the app
2. Go to a project
3. Upload a document through the project UI
4. Verify it's uploaded (check MongoDB if needed)

### Step 4: Test Document Agent
1. Go to AI Agents page
2. Select "Document Agent"
3. Type: "summarize the doc" or any query
4. Check backend console for logs:
   ```
   Document initialization: Synced X documents with Y chunks
   ID Resolution - provided: user_id, resolved: startup_id, was_resolved: True
   ```

### Step 5: Check Sync Status (Optional)
```bash
# Using curl or Postman
GET http://localhost:8000/api/agents/doc/sync/status
Headers: Authorization: Bearer <your_token>
```

## 📊 System Architecture

```
┌─────────────┐
│   Frontend  │
│  (React)    │
└──────┬──────┘
       │ POST /api/agents/doc/chat
       │ { company_id, lead_id, message }
       ▼
┌─────────────────────┐
│  API Router         │
│  (agents.py)        │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────────────┐
│  Document Sync Service      │
│  ┌───────────────────────┐  │
│  │ 1. Resolve IDs        │  │
│  │    user.id → startupId│  │
│  │ 2. Find Documents     │  │
│  │    (MongoDB query)    │  │
│  │ 3. Sync to ChromaDB   │  │
│  │    (chunk & index)    │  │
│  └───────────────────────┘  │
└──────┬───────────────────────┘
       │
       ▼
┌─────────────────────┐
│  Document Agent     │
│  (uses ChromaDB)    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Response to User    │
└─────────────────────┘
```

## 🔍 Debugging

### Check Backend Logs
Look for these log messages:
- `"Document initialization: ..."`
- `"ID Resolution - provided: ..., resolved: ..., was_resolved: ..."`
- `"✅ Synced X document chunks from MongoDB to ChromaDB"`

### Check MongoDB
```python
# In MongoDB shell or Python
db.documents.find({
    "startupId": "your_startup_id"
})
```

### Check ChromaDB Sync Status
```bash
GET /api/agents/doc/sync/status
```

### Manual Sync (if needed)
```bash
POST /api/agents/doc/sync
Body: { "force_resync": true }
```

## 🎯 Key Features

✅ **Automatic ID Resolution**: Converts user.id → startupId automatically
✅ **Lazy Initialization**: Syncs only when needed
✅ **Duplicate Prevention**: Won't re-sync already synced documents
✅ **Comprehensive Logging**: Track every step
✅ **Error Handling**: Graceful fallbacks at every layer
✅ **Manual Sync**: Force resync if needed

## 📝 Next Steps

1. Test the flow end-to-end
2. Check backend logs for sync messages
3. Verify documents are found and synced
4. Test querying with Document Agent
5. If issues persist, use manual sync endpoint

## 🐛 Common Issues

### "No documents found"
- Check MongoDB has documents with correct `startupId`
- Check `extractedContent` field exists and is valid
- Run manual sync endpoint

### "ID resolution failed"
- Verify user exists in database
- Check user has `startupId` field
- Check logs for resolution details

### "Sync failed"
- Check ChromaDB directory permissions
- Check MongoDB connection
- Review error logs

