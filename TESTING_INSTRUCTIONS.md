# LeadMate Agent System - Testing Instructions

## 🚀 Quick Start - Fresh Testing

### Step 1: Clear ChromaDB Data
```bash
cd backend
python clear_chromadb.py
```
**Press Enter** when prompted to confirm deletion.

### Step 2: Start Backend
```bash
cd backend
uvicorn main:app --reload
```
Backend should start on `http://localhost:8000`

### Step 3: Start Frontend
```bash
cd frontend
npm run dev
```
Frontend should start on `http://localhost:5173`

### Step 4: Test Complete Flow

#### A. Login as Team Lead
1. Go to `http://localhost:5173/login`
2. Login with your team lead credentials
3. Verify you're redirected to dashboard

#### B. Upload Document (If not already done)
1. Go to a project
2. Upload a PDF/DOCX document
3. Verify document is saved in MongoDB

#### C. Test Document Agent
1. Navigate to `/lead/agents`
2. Select "Document Agent"
3. **Test 1**: Chat "hello" - Should detect documents or ask to upload
4. **Test 2**: If documents exist, chat "summarize the document"
   - Expected: Agent should reference document content
5. **Test 3**: Check chat history endpoint
   - Should return chat history without 404 error

#### D. Test Other Agents
1. **Stack Agent**:
   - Select Stack Agent
   - Chat: "What are the project requirements?"
   - Check history endpoint works (no 404)

2. **Task Agent**:
   - Select Task Agent
   - Chat: "Generate tasks for this project"
   - Check history endpoint works (no 404)

3. **Team Agent**:
   - Select Team Agent
   - Chat: "Form a team"
   - Should respond appropriately

## 🔍 Verification Checklist

### ✅ Fixed Issues
- [x] Frontend sends correct IDs (`startupId` as `company_id`, `user.id` as `lead_id`)
- [x] Chat history endpoints exist for all agents (no 404 errors)
- [x] ChromaDB cleanup script available

### ⚠️ Issues to Verify
- [ ] Document Agent detects uploaded documents correctly
- [ ] Document Agent uses document context in responses
- [ ] Document sync from MongoDB to ChromaDB works
- [ ] All agent responses are contextual (not generic)

## 🐛 Troubleshooting

### Issue: Document Agent says "no documents uploaded"
**Solution**:
1. Check MongoDB has documents:
   ```python
   # In backend Python shell
   from database import get_database
   db = get_database()
   # Replace with your startup_id
   docs = await db.documents.find({"startupId": "YOUR_STARTUP_ID"}).to_list(length=10)
   print(f"Found {len(docs)} documents")
   ```

2. Force document sync:
   ```python
   from services.document_sync_service import document_sync_service
   result = await document_sync_service.sync_documents_to_chromadb(
       startup_id="YOUR_STARTUP_ID",
       lead_id="YOUR_LEAD_ID",
       force_resync=True
   )
   print(result)
   ```

### Issue: 404 on chat history endpoints
**Solution**: 
- Already fixed! Verify backend is restarted with new code
- Check browser console for correct endpoint URLs

### Issue: Generic agent responses
**Solution**:
- Ensure Ollama is running: `ollama serve`
- Check document sync completed successfully
- Verify documents have extracted content in MongoDB

## 📊 Expected Behavior

### Document Agent:
- **With Documents**: Should reference document content, provide summaries, answer questions
- **Without Documents**: Should prompt user to upload documents

### Stack Agent:
- Should help with tech stack decisions
- Should reference project documents if available

### Task Agent:
- Should generate tasks based on project requirements
- Should use team information from Stack Agent

### Team Agent:
- Should help with team management
- Should coordinate with other agents

## 🎯 Success Criteria

✅ All agents respond (no errors)  
✅ Chat history endpoints return 200 (not 404)  
✅ Document Agent detects and uses documents  
✅ Agent responses are contextual (not generic templates)  
✅ Frontend correctly sends startupId/leadId  

## 📝 Next Steps After Testing

If Document Agent still doesn't detect documents:
1. Check Document Sync Service logs
2. Verify document extraction worked (check MongoDB `extractedContent` field)
3. Test sync manually using debug commands above
4. May need to improve document detection logic

If responses are still generic:
1. Verify Ollama is running and accessible
2. Check document context is being retrieved correctly
3. Verify CrewAI agent is receiving document context
4. May need to improve prompt/context formatting

