# Final Testing Instructions - Project-Based Agents

## 🎯 What We Fixed

1. ✅ **"Analyze Documents" Button** - Added to project modal
2. ✅ **Project Selection** - Dropdown in AI Agents page
3. ✅ **Project-Based Sync** - Documents synced per project
4. ✅ **Project-Aware Search** - Agents search project-specific documents
5. ✅ **Document Detection** - Fixed to detect project documents correctly

---

## 🚀 Step-by-Step Testing

### Prerequisites:
```bash
# 1. Clear ChromaDB (optional but recommended)
cd backend
python clear_chromadb.py

# 2. Start Backend
uvicorn main:app --reload

# 3. Start Frontend (new terminal)
cd frontend
npm run dev
```

---

### Test 1: Analyze Project Documents

1. **Login** as team lead
2. **Go to Dashboard**
3. **Click on a project** (e.g., "Academic Research Assistant")
4. **Scroll to "Project Documents"** section
5. **You should see:**
   - Document list (e.g., "Sample Project Document...")
   - **"Analyze Documents" button** (purple/blue gradient with sparkle icon)

6. **Click "Analyze Documents"**
   - Button shows "Analyzing..." with spinner
   - After a few seconds, shows success message:
     - ✅ Green: "Synced X documents with Y chunks"
     - ❌ Red: Error message (if something failed)

7. **Verify in Backend Logs:**
   ```
   Syncing documents for project: PROJECT_ID
   Found X valid documents for startup_id...
   Synced document FILENAME: Y chunks
   ✅ Document sync complete: Synced X documents with Y chunks
   ```

---

### Test 2: Project Selection in AI Agents

1. **Go to AI Agents page** (`/lead/agents`)
2. **Look at top section** (below "AI Agents Hub" header)
3. **You should see:**
   - 📁 Folder icon
   - "Select Project:" label
   - **Dropdown with your projects**
   - Hint text (if project selected)

4. **Select a project** from dropdown
   - Should show: "Chat will focus on this project's documents"
   - Chat history reloads for that project

5. **Switch projects** and verify chat changes per project

---

### Test 3: Document Agent with Project Context

1. **Select a project** that has documents (from Test 1)
2. **Select Document Agent** (blue card)
3. **Check browser console (F12):**
   - Should see: `Loading chat history from: .../PROJECT_ID`
   - Status: 200 (not 404)

4. **Send message: "What are the project requirements?"**
   - ✅ **Should reference actual document content**
   - ✅ **Should mention specific details from uploaded documents**
   - ✅ **Should NOT say "no documents uploaded"**

5. **Send message: "summarize the document"**
   - ✅ Response should include content from your PDF
   - ✅ Should reference specific sections
   - ✅ Should be contextual (not generic template)

---

### Test 4: Switch Projects

1. **Select Project A** (has documents)
2. **Chat with Document Agent** - Should use Project A documents
3. **Switch to Project B** (different project)
4. **Chat again** - Should use Project B documents (or show "no documents" if Project B has none)
5. **Switch back to Project A** - Should use Project A documents again

---

### Test 5: All Agents Work

1. **Select a project**
2. **Test each agent:**
   - ✅ Document Agent - Uses project documents
   - ✅ Stack Agent - Chat history works (200, not 404)
   - ✅ Task Agent - Chat history works (200, not 404)
   - ✅ Team Agent - Responds appropriately

---

## ✅ Success Criteria

### Analyze Button:
- [ ] Button appears in project modal when documents exist
- [ ] Clicking button shows "Analyzing..." state
- [ ] Success message appears after sync
- [ ] Backend logs show sync completion

### Project Selection:
- [ ] Dropdown appears at top of AI Agents page
- [ ] Shows all user's projects
- [ ] Selecting project updates chat context
- [ ] Hint text shows when project selected

### Document Agent:
- [ ] Detects documents when project has documents
- [ ] Uses actual document content in responses
- [ ] References specific details from documents
- [ ] No false "no documents" messages

### All Agents:
- [ ] All chat history endpoints return 200 (not 404)
- [ ] All agents respond appropriately
- [ ] Project context works correctly

---

## 🐛 Troubleshooting

### Issue: "Analyze Documents" button not appearing
**Check:**
- Project must have at least 1 document uploaded
- Refresh the project modal
- Check browser console for errors

### Issue: Documents still not detected after analysis
**Fix:**
1. Check backend logs for sync errors
2. Verify documents have `extractedContent` in MongoDB:
   ```python
   from database import get_database
   db = get_database()
   doc = await db.documents.find_one({"projectId": "YOUR_PROJECT_ID"})
   print(doc.get('extractedContent', 'No content'))
   ```
3. Check ChromaDB collection:
   ```python
   from services.vector_store_service import vector_store_service
   collection = vector_store_service.get_or_create_collection(
       startup_id="YOUR_STARTUP_ID",
       project_id="YOUR_PROJECT_ID",
       collection_type="documents"
   )
   print(f"Chunks: {collection.count()}")
   ```

### Issue: Wrong project documents showing
**Fix:**
- Make sure project is selected in dropdown
- Check browser console for correct `project_id` in requests
- Verify MongoDB documents have correct `projectId`

### Issue: Generic responses (not using documents)
**Fix:**
1. Verify documents were analyzed (click button again)
2. Check Ollama is running: `ollama serve`
3. Check backend logs for document search results
4. Verify `project_id` is being sent in chat requests

---

## 📊 Expected Console Output

### Browser Console (F12):
```
// When selecting project
Selected project: PROJECT_ID

// When sending message
Request body: {
  message: "...",
  company_id: "STARTUP_ID",
  lead_id: "PROJECT_ID",
  project_id: "PROJECT_ID"
}

// Successful response
Response data: {
  response: "Based on the project documentation, I can see...",
  agent: "Document Agent",
  timestamp: "..."
}
```

### Backend Logs:
```
Doc Agent chat request - company_id: STARTUP_ID, lead_id: PROJECT_ID
Syncing documents for project: PROJECT_ID
Found X valid documents for startup_id STARTUP_ID and project_id PROJECT_ID
Synced document FILENAME.pdf: Y chunks
Found X documents via VectorStore search
Agent response generated successfully
```

---

## 🎉 Success Indicators

You'll know it's working when:

1. ✅ "Analyze Documents" button syncs and shows success
2. ✅ Project dropdown appears and works
3. ✅ Document Agent detects documents (no false "no documents")
4. ✅ Responses reference actual document content
5. ✅ Specific details from your PDF appear in responses
6. ✅ Backend logs show document search results
7. ✅ All agents work without 404 errors

---

## 🚀 Ready to Test!

Follow the steps above and verify each feature works. If you see any issues, check the troubleshooting section or review the backend logs for errors.

**Good luck!** 🎯

