# Step-by-Step Testing Guide - LeadMate Agent System

## 🎯 Testing Goal
Verify that:
1. ✅ Document Agent detects uploaded documents
2. ✅ Document Agent uses document content in responses
3. ✅ All chat history endpoints work (no 404 errors)
4. ✅ All agents respond correctly with proper IDs

---

## 📋 Pre-Testing Setup

### Step 1: Clear ChromaDB (Fresh Start)
```bash
# Navigate to backend directory
cd backend

# Run cleanup script
python clear_chromadb.py

# When prompted, press ENTER to confirm deletion
```

**Expected Output:**
```
⚠️  WARNING: This will delete ALL ChromaDB data!
Press Enter to continue, or Ctrl+C to cancel...
[Press Enter]
✅ ChromaDB cleanup complete! Removed X items...
```

---

### Step 2: Start Backend Server
```bash
# Make sure you're in the backend directory
cd backend

# Start the FastAPI server
uvicorn main:app --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
✅ LeadMate API Started Successfully
```

**Keep this terminal window open!**

---

### Step 3: Start Frontend Server
```bash
# Open a NEW terminal window
# Navigate to frontend directory
cd frontend

# Start the React development server
npm run dev
```

**Expected Output:**
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

**Keep this terminal window open too!**

---

## 🧪 Testing Steps

### Test 1: Login & Verify User Data

1. **Open Browser**
   - Go to: `http://localhost:5173/login`

2. **Login as Team Lead**
   - Enter your team lead email
   - Enter your password
   - Click "Login"

3. **Verify Login Success**
   - Should redirect to dashboard
   - Check browser console (F12) for:
     ```
     User data fetched: {name: '...', email: '...', role: 'teamlead', startupId: '...', _id: '...'}
     ```
   - ✅ Verify `startupId` is present (NOT the same as `_id`)

4. **Check API Response**
   - Open Network tab (F12 → Network)
   - Look for `/api/auth/me` request
   - Verify response contains `startupId` field

---

### Test 2: Verify Document Upload (If Needed)

**Skip this if you already have documents uploaded!**

1. **Navigate to Project**
   - Go to Dashboard
   - Click on a project

2. **Upload Document**
   - Find document upload section
   - Upload a PDF or DOCX file (project requirements document)
   - Wait for upload to complete

3. **Verify Document in MongoDB**
   ```bash
   # In backend, you can check:
   # Documents should be in MongoDB with extractedContent field
   ```

---

### Test 3: Test Document Agent - Basic Chat

1. **Navigate to AI Agents**
   - Click "AI Agents" in sidebar
   - Or go to: `http://localhost:5173/lead/agents`

2. **Select Document Agent**
   - Click on "Document Agent" card (blue, with FileText icon)

3. **Check Browser Console (F12)**
   - Should see:
     ```
     Loading chat history from: http://localhost:8000/api/agents/doc/history/STARTUP_ID/LEAD_ID
     Chat history response status: 200
     ```
   - ✅ Verify NO 404 errors
   - ✅ Verify correct IDs (startupId for company_id, user.id for lead_id)

4. **Send Test Message: "hello"**
   - Type "hello" in chat input
   - Click Send or press Enter

5. **Expected Response:**
   - ✅ If documents exist: Should mention documents or ask specific questions
   - ✅ If no documents: Should ask to upload documents
   - ✅ Should NOT say "no documents uploaded" if documents actually exist

6. **Check Backend Logs**
   - Look in backend terminal for:
     ```
     Doc Agent chat request - company_id: STARTUP_ID, lead_id: LEAD_ID
     Document initialization: ...
     Found X documents in MongoDB/VectorStore
     Agent response generated successfully
     ```

---

### Test 4: Test Document Agent - Document Analysis

1. **Send Message: "summarize the document"**
   - Type this in Document Agent chat
   - Send message

2. **Expected Response:**
   - ✅ Should reference actual document content
   - ✅ Should provide specific details from uploaded documents
   - ✅ Should mention document filename or content snippets
   - ✅ Should NOT be a generic template response

3. **Check Response Quality:**
   - Response should contain information that's clearly from your document
   - If you asked about a specific feature, response should reference it

4. **Send Another Message: "What are the project requirements?"**
   - Verify response uses document context
   - Response should be specific, not generic

---

### Test 5: Test Stack Agent

1. **Select Stack Agent**
   - Click on "Stack Agent" card (green, with Users icon)

2. **Check Chat History**
   - Open browser console (F12)
   - Should see:
     ```
     Loading chat history from: http://localhost:8000/api/agents/stack/history/STARTUP_ID/LEAD_ID
     Chat history response status: 200
     ```
   - ✅ NO 404 error (this was broken before)

3. **Send Message: "What are the project requirements?"**
   - Type and send

4. **Expected Response:**
   - Should respond about tech stack
   - Should reference project documents if available
   - Should be contextual

---

### Test 6: Test Task Agent

1. **Select Task Agent**
   - Click on "Task Agent" card (purple, with CheckSquare icon)

2. **Check Chat History**
   - Open browser console (F12)
   - Should see:
     ```
     Loading chat history from: http://localhost:8000/api/agents/tasks/history/STARTUP_ID/LEAD_ID
     Chat history response status: 200
     ```
   - ✅ NO 404 error (this was broken before)

3. **Send Message: "Generate tasks for this project"**
   - Type and send

4. **Expected Response:**
   - Should respond about task management
   - Should reference project if documents available

---

### Test 7: Test Team Agent

1. **Select Team Agent**
   - Click on "Team Agent" card (orange, with UserCheck icon)

2. **Send Message: "Form a team"**
   - Type and send

3. **Expected Response:**
   - Should respond about team management
   - Should be contextual

---

## ✅ Verification Checklist

### ID Resolution ✅
- [ ] Browser console shows correct `startupId` (different from `_id`)
- [ ] API calls use `startupId` as `company_id`
- [ ] API calls use `user.id` as `lead_id`

### Document Agent ✅
- [ ] Detects documents correctly (no false "no documents" message)
- [ ] Uses document content in responses
- [ ] Responses are contextual (reference actual document content)
- [ ] Chat history endpoint works (200, not 404)

### Other Agents ✅
- [ ] Stack Agent chat history works (200, not 404)
- [ ] Task Agent chat history works (200, not 404)
- [ ] All agents respond appropriately

### Backend Logs ✅
- [ ] Document sync happens when needed
- [ ] Documents found in VectorStore or MongoDB
- [ ] No critical errors in logs
- [ ] Agent responses generated successfully

---

## 🐛 Troubleshooting

### Issue: Document Agent says "no documents uploaded"

**Fix:**
1. Check if documents exist in MongoDB:
   ```bash
   # Check backend logs for MongoDB queries
   # Look for: "Found X documents in MongoDB"
   ```

2. Check browser console for sync messages:
   - Should see: "Document initialization: Synced X documents"

3. Check backend logs:
   - Look for: "Found X documents via VectorStore/MongoDB"

4. If still not working, manually trigger sync:
   ```python
   # In Python shell or create a test script
   from services.document_sync_service import document_sync_service
   result = await document_sync_service.sync_documents_to_chromadb(
       startup_id="YOUR_STARTUP_ID",
       lead_id="YOUR_LEAD_ID",
       force_resync=True
   )
   print(result)
   ```

### Issue: 404 on chat history endpoints

**Fix:**
- ✅ Already fixed! Make sure backend is restarted with new code
- Check browser console for correct endpoint URL
- Verify backend has the new endpoints (check `backend/routers/agents.py`)

### Issue: Generic responses (not using documents)

**Fix:**
1. Verify documents are in ChromaDB:
   ```bash
   # Check backend logs for:
   # "Found X documents via VectorStore search"
   # or
   # "Found X documents via MongoDB fallback"
   ```

2. Check Ollama is running:
   ```bash
   ollama serve
   ```

3. Check backend logs for document search results:
   - Should see document chunks being retrieved

### Issue: Wrong IDs being sent

**Fix:**
- Check `AuthContext.tsx` includes `startupId`
- Check `AIAgents.tsx` uses `user.startupId` for `company_id`
- Verify `/api/auth/me` returns `startupId` field

---

## 📊 Success Criteria

### All Tests Pass If:

✅ **Document Agent:**
- Detects documents when they exist
- Uses document content in responses
- Provides contextual answers based on documents

✅ **All Agents:**
- Chat history endpoints return 200 (not 404)
- Responses are appropriate and contextual
- No errors in browser console or backend logs

✅ **ID Resolution:**
- Frontend sends correct `startupId` and `user.id`
- Backend resolves IDs correctly
- Documents found and synced properly

---

## 🎯 Next Steps After Testing

### If Everything Works:
✅ **Great!** The system is ready. You can now:
- Use Document Agent for document Q&A
- Upload more documents as needed
- Use other agents for their respective tasks

### If Issues Found:
1. Check the troubleshooting section above
2. Review backend logs for errors
3. Check browser console for API errors
4. Verify all services are running (backend, frontend, Ollama)

---

## 📝 Quick Test Summary

**Fast Test (5 minutes):**
1. Clear ChromaDB
2. Start servers
3. Login
4. Go to Document Agent
5. Chat: "summarize the document"
6. ✅ Verify response uses document content

**Complete Test (15 minutes):**
1. All steps above
2. Test all 4 agents
3. Verify chat history for all
4. Check all verification items

---

## 🚀 Ready to Test!

Start with **Step 1** (Clear ChromaDB) and follow each step carefully. Check the ✅ boxes as you complete each test.

Good luck! 🎉

