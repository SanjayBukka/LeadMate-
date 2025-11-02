# Quick Test Commands - Copy & Paste

## 🚀 Setup Commands (Run These First)

### Terminal 1: Backend
```bash
cd "C:\Users\Sanjay\Desktop\Lead Mate full Application\backend"
python clear_chromadb.py
# Press Enter when prompted

uvicorn main:app --reload
```

### Terminal 2: Frontend
```bash
cd "C:\Users\Sanjay\Desktop\Lead Mate full Application\frontend"
npm run dev
```

### Terminal 3: Ollama (if not running)
```bash
ollama serve
```

---

## 🧪 Quick Verification Commands

### Check MongoDB Documents (Python)
```python
# In Python shell or create check_docs.py
from database import get_database
import asyncio

async def check_docs():
    db = get_database()
    docs = await db.documents.find({}).to_list(length=10)
    print(f"Total documents: {len(docs)}")
    for doc in docs:
        print(f"- {doc.get('originalFilename')}: startupId={doc.get('startupId')}")

asyncio.run(check_docs())
```

### Force Document Sync (Python)
```python
# In Python shell
from services.document_sync_service import document_sync_service
import asyncio

async def sync():
    result = await document_sync_service.sync_documents_to_chromadb(
        startup_id="YOUR_STARTUP_ID_HERE",
        lead_id="YOUR_LEAD_ID_HERE",
        force_resync=True
    )
    print(result)

asyncio.run(sync())
```

### Check ChromaDB Status
```python
# In Python shell
from services.vector_store_service import vector_store_service

collection = vector_store_service.get_or_create_collection(
    startup_id="YOUR_STARTUP_ID_HERE",
    project_id="YOUR_LEAD_ID_HERE",
    collection_type="documents"
)
count = collection.count()
print(f"ChromaDB documents: {count}")
```

---

## 🔍 Browser Console Checks

### Check User Data
```javascript
// In browser console (F12)
const user = JSON.parse(localStorage.getItem('user') || '{}');
console.log('User:', user);
console.log('StartupId:', user.startupId);
console.log('UserId:', user.id);
```

### Check API Calls
```javascript
// In browser console (F12 → Network tab)
// Look for:
// - /api/auth/me → Should have startupId
// - /api/agents/doc/chat → Should use correct IDs
// - /api/agents/doc/history/... → Should return 200
```

---

## ✅ Quick Success Checklist

Run these in order:

1. ✅ ChromaDB cleared (no errors)
2. ✅ Backend running (port 8000)
3. ✅ Frontend running (port 5173)
4. ✅ Login successful (check console for startupId)
5. ✅ Document Agent loads (no 404 errors)
6. ✅ Chat works (gets response)
7. ✅ Response uses documents (not generic)

---

## 🐛 Common Issues & Quick Fixes

### "Module not found" errors
```bash
# In backend directory
pip install -r requirements.txt
```

### "Port already in use"
```bash
# Kill process on port 8000 (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F

# Kill process on port 5173
netstat -ano | findstr :5173
taskkill /PID <PID_NUMBER> /F
```

### Ollama connection error
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve
```

---

## 📊 Test Results Template

Copy this to track your testing:

```
Test Date: ___________
Backend Running: [ ] Yes [ ] No
Frontend Running: [ ] Yes [ ] No
Ollama Running: [ ] Yes [ ] No

Login:
- Status: [ ] Success [ ] Failed
- StartupId Present: [ ] Yes [ ] No

Document Agent:
- Documents Detected: [ ] Yes [ ] No
- Uses Document Content: [ ] Yes [ ] No
- Chat History Works: [ ] Yes [ ] No

Stack Agent:
- Chat History Works: [ ] Yes [ ] No
- Responds Correctly: [ ] Yes [ ] No

Task Agent:
- Chat History Works: [ ] Yes [ ] No
- Responds Correctly: [ ] Yes [ ] No

Issues Found:
_________________________________
_________________________________
_________________________________
```

