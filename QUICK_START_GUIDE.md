# 🚀 LeadMate - Quick Start Guide

**Status:** Backend ✅ Complete | Frontend ⏳ Needs Integration  
**Your Services:** Running on http://localhost:5174 (Frontend) & http://localhost:8000 (Backend)

---

## ⚡ **What You Have Now**

### **3 AI Agents Working Together:**

```
1. 📄 Document Agent → Analyzes docs, chats to clarify requirements
2. 👥 Stack Agent   → Forms teams, iterates with feedback  
3. ✅ Task Agent    → Generates tasks automatically
```

### **21 API Endpoints:**
- 5 for Document Agent
- 6 for Stack Agent
- 6 for Task Agent (NEW!)
- 4 utility endpoints

### **Complete Workflow:**
```
Upload Docs → Chat → Upload Resumes → Generate Team → 
Iterate Team → Finalize → Generate Tasks → Drag & Drop Tasks
```

---

## 🎯 **How to Use Right Now**

### **Option 1: Test via API Docs (Easiest)**

1. Open: **http://localhost:8000/docs**
2. You'll see all 21 endpoints
3. Click any endpoint → "Try it out" → Fill in data → Execute
4. See real AI responses!

**Try This First:**
```
1. Find: POST /api/agents/doc/chat
2. Click "Try it out"
3. Enter:
   {
     "message": "Hello, what can you help me with?",
     "company_id": "test_company",
     "lead_id": "test_lead"
   }
4. Click "Execute"
5. See AI response!
```

### **Option 2: Use Frontend (Current State)**

**Go to:** http://localhost:5174

**Login as:**
- Manager: `manager@example.com` / `manager123`
- Team Lead: `lead@example.com` / `lead123`

**What Works:**
- ✅ Beautiful UI with dark mode
- ✅ Task Board (drag & drop) - but uses mock data
- ✅ AI Assistant chat - connects to backend!
- ✅ All navigation

**What Needs Connection:**
- ⏳ Task Board → Task Agent API
- ⏳ Document Agent page (not built yet)
- ⏳ Stack Agent page (not built yet)

---

## 📊 **Complete Agent System**

### **Agent 1: Document Agent**

**Purpose:** Understand project requirements

**Endpoints:**
```http
POST /api/agents/doc/upload           # Upload project docs
POST /api/agents/doc/chat             # Chat to clarify
GET  /api/agents/doc/history/{id}/{id} # View conversation
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/agents/doc/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the technical requirements?",
    "company_id": "acme",
    "lead_id": "john"
  }'
```

### **Agent 2: Stack Agent**

**Purpose:** Form optimal teams

**Endpoints:**
```http
POST /api/agents/stack/upload-resume        # Upload resume
POST /api/agents/stack/generate-initial-team # Get team recommendation
POST /api/agents/stack/iterate-team         # Refine team
POST /api/agents/stack/finalize-team        # Generate final report
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/agents/stack/generate-initial-team \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "acme",
    "lead_id": "john"
  }'
```

### **Agent 3: Task Agent (NEW!)**

**Purpose:** Auto-generate project tasks

**Endpoints:**
```http
POST /api/agents/tasks/generate      # Generate tasks from requirements
GET  /api/agents/tasks/{id}/{id}     # Get all tasks
PUT  /api/agents/tasks/status        # Update task (drag & drop)
GET  /api/agents/tasks/stats/{id}/{id} # Get statistics
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/agents/tasks/generate \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "acme",
    "lead_id": "john",
    "project_name": "My Project"
  }'
```

---

## 🗂️ **Storage Structure**

**Where Data Lives:**
```
chroma_db/
└── company_acme/
    └── lead_john/
        ├── documents/       # Project docs (Document Agent)
        ├── doc_chat/        # Conversation history
        ├── resumes/         # Team member resumes (Stack Agent)
        ├── stack_iterations/ # Team iterations
        ├── tasks/           # Generated tasks (Task Agent)
        └── final_reports/   # Final team reports
```

**Each company + lead = Isolated storage!**

---

## 🔄 **Complete Workflow Example**

### **Step-by-Step:**

```bash
# 1. Upload project requirements
curl -X POST http://localhost:8000/api/agents/doc/upload \
  -F "file=@requirements.pdf" \
  -F "company_id=acme" \
  -F "lead_id=john"

# 2. Chat to clarify requirements
curl -X POST http://localhost:8000/api/agents/doc/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the expected user scale?",
    "company_id": "acme",
    "lead_id": "john"
  }'

# 3. Upload team member resumes
curl -X POST http://localhost:8000/api/agents/stack/upload-resume \
  -F "file=@alice_resume.pdf" \
  -F "candidate_name=Alice Smith" \
  -F "company_id=acme" \
  -F "lead_id=john"

# (Upload more resumes...)

# 4. Generate initial team
curl -X POST http://localhost:8000/api/agents/stack/generate-initial-team \
  -H "Content-Type: application/json" \
  -d '{"company_id": "acme", "lead_id": "john"}'

# 5. Iterate team (if needed)
curl -X POST http://localhost:8000/api/agents/stack/iterate-team \
  -H "Content-Type: application/json" \
  -d '{
    "lead_feedback": "Replace Bob with someone else",
    "company_id": "acme",
    "lead_id": "john"
  }'

# 6. Finalize team
curl -X POST http://localhost:8000/api/agents/stack/finalize-team \
  -H "Content-Type: application/json" \
  -d '{"company_id": "acme", "lead_id": "john"}'

# 7. Generate tasks automatically!
curl -X POST http://localhost:8000/api/agents/tasks/generate \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "acme",
    "lead_id": "john",
    "project_name": "My Project"
  }'

# 8. Get all tasks
curl http://localhost:8000/api/agents/tasks/acme/john

# 9. Update task status (when dragging in UI)
curl -X PUT http://localhost:8000/api/agents/tasks/status \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "task-123",
    "new_status": "inprogress",
    "company_id": "acme",
    "lead_id": "john"
  }'

# 10. Get statistics
curl http://localhost:8000/api/agents/tasks/stats/acme/john
```

---

## 🎨 **What Frontend Needs**

### **Task Board Integration** (Highest Priority)

**Current File:** `frontend/src/pages/TeamLead/TaskBoard.tsx`

**Changes Needed:**

```typescript
// 1. Replace mock data with API call
useEffect(() => {
  fetch(`http://localhost:8000/api/agents/tasks/${companyId}/${leadId}`)
    .then(res => res.json())
    .then(data => setTasks(data.tasks));
}, []);

// 2. Update handleDrop to call API
const handleDrop = async (taskId, newStatus) => {
  await fetch('http://localhost:8000/api/agents/tasks/status', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      task_id: taskId,
      new_status: newStatus,
      company_id: companyId,
      lead_id: leadId
    })
  });
  
  // Update local state
  setTasks(tasks.map(task =>
    task.id === taskId ? { ...task, status: newStatus } : task
  ));
};

// 3. Add "Generate Tasks" button
<button onClick={async () => {
  const res = await fetch('http://localhost:8000/api/agents/tasks/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      company_id: companyId,
      lead_id: leadId,
      project_name: 'My Project'
    })
  });
  const data = await res.json();
  setTasks(data.tasks);
}}>
  🤖 Generate Tasks from AI
</button>
```

### **New Pages Needed:**

1. **Document Agent Page** (`/lead/doc-agent`)
   - Upload documents
   - Chat interface
   - View uploaded docs

2. **Stack Agent Page** (`/lead/stack-agent`)
   - Upload resumes
   - Generate team
   - Iterate team
   - Finalize & download report

---

## 🛠️ **Tech Stack**

**Backend:**
- FastAPI (Python 3.10)
- CrewAI (Agent orchestration)
- Ollama Llama3.1:8B (LLM)
- ChromaDB (Vector database)
- LangChain (Text processing)

**Frontend:**
- React 18 + TypeScript
- Vite (Build tool)
- TailwindCSS (Styling)
- React Router (Navigation)

**Storage:**
- ChromaDB (Persistent vector DB)
- File system (Final reports)

---

## 📈 **Current Status**

| Feature | Backend | Frontend |
|---------|---------|----------|
| Document upload & analysis | ✅ | ⏳ |
| Requirements chat | ✅ | ⏳ |
| Resume upload & parsing | ✅ | ⏳ |
| Team formation | ✅ | ⏳ |
| Team iteration | ✅ | ⏳ |
| Final team report | ✅ | ⏳ |
| **Task generation** | ✅ | ⏳ |
| **Task board** | ✅ | ⚠️ (mock data) |
| **Drag & drop** | ✅ | ⚠️ (local only) |
| Authentication | ✅ | ✅ |
| Beautiful UI | - | ✅ |

---

## 🚀 **Next Steps**

### **Quick Wins (30 min each):**

1. **Connect Task Board to Backend**
   - Replace `mockTasks` with API call
   - Update drag handler to call API
   - Add "Generate Tasks" button

2. **Test Complete Flow**
   - Upload sample doc via API docs
   - Upload sample resume via API docs
   - Generate team via API docs
   - Generate tasks via API docs
   - See tasks in frontend Task Board

3. **Build Agent Pages**
   - Document Agent UI
   - Stack Agent UI

---

## 📚 **Documentation Files**

- `THREE_AGENT_SYSTEM_COMPLETE.md` - Full technical details
- `MULTI_AGENT_SYSTEM_IMPLEMENTATION.md` - Doc + Stack agents
- `SYSTEM_RUNNING_STATUS.md` - Current running services
- `APPLICATION_STATUS.md` - Overall project status
- `QUICK_START_GUIDE.md` - This file!

---

## ✅ **What's Working Right Now**

**Test It:**
1. Open http://localhost:8000/docs
2. See all 21 endpoints
3. Try POST /api/agents/doc/chat
4. See AI respond!

**Frontend:**
1. Open http://localhost:5174
2. Login as lead@example.com / lead123
3. Go to Task Board
4. Drag tasks (works locally, needs backend connection!)

---

## 🎯 **Summary**

**You Have:**
- ✅ 3 AI agents (Document, Stack, Task)
- ✅ 21 API endpoints
- ✅ Multi-tenant storage
- ✅ Beautiful frontend UI
- ✅ Complete workflow backend

**You Need:**
- ⏳ Connect Task Board to backend
- ⏳ Build Document Agent page
- ⏳ Build Stack Agent page

**The hard AI work is DONE. Just need UI integration now!** 🎉

---

**Questions? Check:**
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/agents/health
- Frontend: http://localhost:5174

