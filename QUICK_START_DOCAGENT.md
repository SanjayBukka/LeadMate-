# 🚀 Quick Start Guide - DocAgent

## ✅ **Prerequisites:**

1. **Ollama must be running:**
   ```bash
   ollama serve
   ```

2. **Pull the model (if not already):**
   ```bash
   ollama pull llama3.2:3b
   ```

3. **Backend and Frontend should be running:**
   ```bash
   # Terminal 1 - Backend
   cd backend
   uvicorn main:app --reload --port 8000
   
   # Terminal 2 - Frontend  
   cd frontend
   npm run dev
   ```

---

## 📝 **Step-by-Step Usage:**

### **1. Upload Documents (Manager)**

1. Login as Manager: `http://localhost:5173/login`
2. Go to Manager Dashboard: `http://localhost:5173/manager`
3. Click on a project card (e.g., "SmartFleet")
4. In the Edit Project modal:
   - Scroll to "Project Documents"
   - Click "Choose files" and select a PDF/DOCX/TXT
   - Click "Upload Files" button
   - Wait for success message
5. Close the modal

**What happens behind the scenes:**
- File is saved to `backend/uploads/{project_id}/`
- Text is extracted from the document
- Text is chunked (1000 chars with 200 overlap)
- Embeddings are created and stored in ChromaDB
- Document is linked to the project

---

### **2. Chat with DocAgent (Team Lead)**

1. Login as Team Lead: `http://localhost:5173/login`
   - Email: `nikunj@leadmate.com`
   - Password: `nikunj123`

2. Go to AI Agents: Click "AI Agents" in the sidebar
3. Click "Launch Agent" on the **DocAgent** card
4. You'll see the DocAgent interface with 3 sections:
   - Left: Documents list & Summary
   - Right: Chat interface

**Ask Questions:**
- Type a question in the chat input
- Examples:
  - "What is this project about?"
  - "What are the main technical requirements?"
  - "What risks should we be aware of?"
  - "What technologies are needed?"
- Press Enter or click "Send"
- Wait for DocAgent's response

**What happens:**
- Question is sent to backend
- ChromaDB searches for relevant document chunks
- CrewAI agent analyzes the question + context
- Agent generates strategic answer
- Conversation is stored in ChromaDB
- Answer is displayed in chat

---

### **3. Generate Project Summary**

1. In the same DocAgent interface
2. Click "Generate Project Summary" button (left sidebar)
3. Wait 10-30 seconds (depending on document size)
4. Summary will appear below the button

**Summary Includes:**
- 📋 Project Overview & Objectives
- 🔧 Key Technical Requirements
- ⚠️ Potential Risks & Challenges
- 💡 Strategic Recommendations
- ❓ Critical Questions for Stakeholders

---

## 🐛 **Troubleshooting:**

### **Problem: "No documents uploaded yet"**
**Solution:** Manager needs to upload documents first in Edit Project modal

### **Problem: DocAgent not responding**
**Solution:**
1. Check if Ollama is running: `ollama list`
2. Check backend logs for errors
3. Verify model is available: `ollama pull llama3.2:3b`

### **Problem: "Failed to get response from DocAgent"**
**Solution:**
1. Check backend is running on port 8000
2. Check browser console for errors (F12)
3. Verify ChromaDB directory exists: `backend/chroma_db/`

### **Problem: Empty/irrelevant answers**
**Solution:**
1. Ensure documents were uploaded successfully
2. Check if embeddings were created (check backend logs)
3. Try more specific questions

### **Problem: Chat history not loading**
**Solution:**
1. Verify ChromaDB is writable
2. Check backend logs for storage errors
3. Refresh the page

---

## 📊 **Check if Everything Works:**

### **Backend Health Check:**
```bash
curl http://localhost:8000/api/agents/doc-agent/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "message": "DocAgent is ready"
}
```

### **Check ChromaDB:**
```
backend/chroma_db/
└── startup_{your_startup_id}/
    └── (ChromaDB files)
```

### **Check Ollama:**
```bash
ollama list
```

Should show `llama3.2:3b` in the list.

---

## 💡 **Tips for Best Results:**

### **Document Upload:**
- Upload clear, well-structured documents
- PDFs work best when they're text-based (not scanned images)
- DOCX files extract perfectly
- TXT files work instantly

### **Asking Questions:**
- Be specific: "What are the authentication requirements?" vs "Tell me about auth"
- Reference context: "Based on the requirements, what database should we use?"
- Follow-up: DocAgent maintains conversation context

### **Generating Summaries:**
- Generate summary first to get project overview
- Then ask specific questions for details
- Regenerate summary after uploading new documents

---

## 🎯 **Example Conversation:**

```
You: What is this project about?

DocAgent: Based on the project documentation, SmartFleet is an AI-powered Fleet Management Platform designed for TransLogix, a company operating over 2,000 vehicles across India. The main objectives are to:

1. Track real-time vehicle data (GPS, speed, fuel, maintenance)
2. Predict vehicle breakdowns using machine learning
3. Optimize delivery routes for cost and time efficiency
4. Generate performance reports for drivers and vehicles

Would you like me to elaborate on any specific aspect?
```

```
You: What are the main technical challenges?

DocAgent: Based on my analysis, here are the key technical challenges:

1. **Real-time Data Processing**: Handling data from 2,000+ vehicles simultaneously
2. **Machine Learning Accuracy**: Building reliable breakdown prediction models
3. **Route Optimization**: Complex algorithm for multiple constraints
4. **Scalability**: System must handle growth to more vehicles
5. **Data Integration**: Connecting GPS, fuel sensors, maintenance systems

I'd recommend focusing on scalability architecture first. What's your team's experience with real-time data pipelines?
```

---

## ✅ **Success Indicators:**

- ✅ Documents appear in the left sidebar
- ✅ Questions get relevant answers
- ✅ Summary includes all 5 sections
- ✅ Chat history loads on page refresh
- ✅ No errors in browser console
- ✅ Backend logs show successful operations

---

## 🚀 **You're Ready!**

DocAgent is now fully functional and ready to help your team leads understand project requirements, identify risks, and make strategic decisions!

**Next Steps:**
1. Upload more project documents
2. Explore different types of questions
3. Generate summaries for all projects
4. Share insights with your team

Happy coding! 🎉

