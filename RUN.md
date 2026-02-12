# Lead Mate - Quick Run Commands

## 🚀 Start the Application (3 Steps)

### Step 1️⃣: Verify Ollama is Running

```powershell
ollama list
```

**Expected output:** You should see `llama3.2:3b` in the list.

If Ollama is not running, you'll see an error. Start it with:
```powershell
ollama serve
```

> **Note:** If you get "port already in use" error, Ollama is already running - that's good! ✅

---

### Step 2️⃣: Start Backend Server

Open a **PowerShell terminal** and run:

```powershell
cd "C:\Users\Sanjay\Desktop\Lead Mate full Application\backend"
python -m uvicorn main:app --host 127.0.0.1 --port 8001
```

**Wait for this message:**
```
✅ LeadMate API Started Successfully
INFO:     Uvicorn running on http://127.0.0.1:8001
```

> **Keep this terminal running!** Don't close it.

---

### Step 3️⃣: Start Frontend Server

Open a **NEW PowerShell terminal** and run:

```powershell
cd "C:\Users\Sanjay\Desktop\Lead Mate full Application\frontend"
npm run dev
```

**Wait for this message:**
```
VITE v5.4.8  ready in 633 ms
➜  Local:   http://localhost:5173/
```

---

## 🌐 Access the Application

Open your browser and go to:
```
http://localhost:5173/
```

---

## 📝 Configuration

### Backend Configuration (backend/.env)
```env
FORCE_OLLAMA=true
USE_GEMINI=false
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

MONGODB_URL=mongodb+srv://LeadMate_1:mvbuEfnYmKyCwPEM@cluster0.pslm64p.mongodb.net/
DATABASE_NAME=leadmate_db

SECRET_KEY=leadmate-secret-key-change-in-production-09876543210abcdef
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

CORS_ORIGINS=http://localhost:5173,http://localhost:5174,http://localhost:5175
```

### Frontend Configuration (frontend/.env)
```env
VITE_API_BASE_URL=http://localhost:8001
```

---

## 🛑 Stop the Application

Press `Ctrl+C` in both terminal windows to stop the servers.

---

## 🔧 Troubleshooting

### Backend won't start?

**Issue:** Missing dependencies
```powershell
cd "C:\Users\Sanjay\Desktop\Lead Mate full Application\backend"
pip install -r requirements.txt
```

**Issue:** Port 8001 already in use
```powershell
netstat -ano | findstr :8001
# Then kill the process using: taskkill /PID <PID> /F
```

### Frontend won't start?

**Issue:** Missing dependencies
```powershell
cd "C:\Users\Sanjay\Desktop\Lead Mate full Application\frontend"
npm install
```

### Ollama not working?

**Issue:** Model not found
```powershell
ollama pull llama3.2:3b
```

---

## 💡 Quick Copy-Paste Commands

**Terminal 1 - Backend:**
```powershell
cd "C:\Users\Sanjay\Desktop\Lead Mate full Application\backend" ; python -m uvicorn main:app --host 127.0.0.1 --port 8001
```

**Terminal 2 - Frontend:**
```powershell
cd "C:\Users\Sanjay\Desktop\Lead Mate full Application\frontend" ; npm run dev
```

---

## 📍 Server URLs

- **Frontend:** http://localhost:5173/
- **Backend API:** http://127.0.0.1:8001
- **API Docs:** http://127.0.0.1:8001/docs
- **Ollama:** http://localhost:11434
