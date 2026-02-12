# Lead Mate - AI-Powered Project Management Platform

Lead Mate is a comprehensive AI-driven project management portal designed for Managers and Team Leads to streamline project initialization, document analysis, team formation, and resource planning.

## 🚀 Features

### Manager Portal
- **Project Management**: Create and manage projects with document uploads
- **Team Lead Assignment**: Assign and manage team leads
- **Progress Monitoring**: Track project progress and team performance
- **Document Management**: Upload and organize project requirements and documentation

### Team Lead Portal
- **AI Agents Hub**: Access specialized AI agents for project assistance
  - **DocAgent**: Analyze project documents and answer queries via chat
  - **StackAgent**: Get technology stack recommendations based on requirements
  - **TeamAgent**: Receive team formation suggestions matched to project needs
  - **TaskAgent**: Generate actionable task breakdowns and timelines
- **Task Board**: Sprint management and task tracking
- **Team Members**: Talent tracking and team composition
- **Management Dashboard**: Analyze Git repositories and view developer insights

## 📋 Prerequisites

Before running the application, ensure you have the following installed:

- **Python 3.10+** (Python 3.11+ recommended)
- **Node.js 16+** and npm
- **Ollama** (for local LLM) - [Download here](https://ollama.ai)
- **MongoDB** (or MongoDB Atlas account)

### Required Ollama Models

Install the LLM model:
```bash
ollama pull llama3.2:3b
```

Verify Ollama is running:
```bash
ollama list
```

## 🛠️ Installation

### 1. Clone or Navigate to the Repository

```bash
cd "C:\Users\Sanjay\Desktop\Lead Mate full Application"
```

### 2. Backend Setup

#### Navigate to Backend Directory
```bash
cd backend
```

#### Install Python Dependencies
```bash
pip install -r requirements.txt
```

#### Configure Environment Variables

Create or update `backend/.env` file:
```env
# LLM Configuration
FORCE_OLLAMA=true
USE_GEMINI=false
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# MongoDB Configuration
MONGODB_URL=mongodb+srv://LeadMate_1:mvbuEfnYmKyCwPEM@cluster0.pslm64p.mongodb.net/
DATABASE_NAME=leadmate_db

# JWT Configuration
SECRET_KEY=leadmate-secret-key-change-in-production-09876543210abcdef
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS Settings
CORS_ORIGINS=http://localhost:5173,http://localhost:5174,http://localhost:5175

# Gemini API Keys (Optional - for Gemini instead of Ollama)
GEMINI_API_KEYS=
```

### 3. Frontend Setup

#### Navigate to Frontend Directory
```bash
cd ../frontend
```

#### Install Node Dependencies
```bash
npm install
```

#### Configure Environment Variables

Create `frontend/.env` file:
```env
VITE_API_BASE_URL=http://localhost:8001
```

## 🚀 Running the Application

### Step 1: Start Ollama (if not already running)

```bash
ollama serve
```

**Note**: If you see "port already in use" error, Ollama is already running - this is fine!

### Step 2: Start Backend Server

Open a terminal and run:

```bash
cd "C:\Users\Sanjay\Desktop\Lead Mate full Application\backend"
python -m uvicorn main:app --host 127.0.0.1 --port 8001
```

You should see:
```
✅ LeadMate API Started Successfully
INFO:     Uvicorn running on http://127.0.0.1:8001
```

### Step 3: Start Frontend Server

Open a **new terminal** and run:

```bash
cd "C:\Users\Sanjay\Desktop\Lead Mate full Application\frontend"
npm run dev
```

You should see:
```
VITE v5.4.8  ready in 633 ms
➜  Local:   http://localhost:5173/
```

### Step 4: Access the Application

Open your browser and navigate to:
```
http://localhost:5173/
```

## 🎯 Getting Started

### First Time Setup

1. **Sign Up as Manager**
   - Click "Sign Up" on the login page
   - Create your startup account
   - You'll be automatically logged in

2. **Create Your First Project**
   - Go to Manager Dashboard
   - Click "Create Project"
   - Fill in project details
   - Upload requirement documents (optional)

3. **Assign Team Lead**
   - Add team leads from Team Management
   - Assign them to projects

4. **Use AI Agents**
   - Switch to Team Lead view
   - Navigate to "Agents Hub"
   - Upload documents and interact with AI agents

## 🏗️ Architecture

### Technology Stack

**Backend:**
- FastAPI (Python web framework)
- MongoDB with Motor (async database)
- ChromaDB (vector database for embeddings)
- Ollama / Gemini (LLM integration)
- CrewAI (multi-agent orchestration)
- LangChain (LLM application framework)

**Frontend:**
- React 18 with TypeScript
- Vite (build tool)
- Tailwind CSS (styling)
- React Router (navigation)
- Lucide React (icons)

### Project Structure

```
Lead Mate full Application/
├── backend/
│   ├── agents/               # AI agent implementations
│   ├── routers/              # FastAPI route handlers
│   ├── services/             # Business logic services
│   ├── models/               # Database models
│   ├── middleware/           # Custom middleware
│   ├── chroma_db/            # Vector database storage
│   ├── uploads/              # Uploaded documents
│   ├── config.py             # Configuration settings
│   ├── database.py           # MongoDB connection
│   ├── main.py               # Application entry point
│   └── requirements.txt      # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── pages/            # React page components
│   │   │   ├── Manager/      # Manager portal pages
│   │   │   └── TeamLead/     # Team lead portal pages
│   │   ├── components/       # Reusable components
│   │   ├── App.tsx           # Root component
│   │   └── main.tsx          # Application entry
│   ├── .env                  # Frontend environment variables
│   ├── package.json          # Node dependencies
│   └── vite.config.ts        # Vite configuration
│
└── README.md                 # This file
```

## 🤖 AI Agents Overview

### Document Agent (DocAgent)
Analyzes uploaded project documents using RAG (Retrieval-Augmented Generation):
- Answers questions about project requirements
- Extracts key information from documents
- Provides context-aware responses

### Stack Agent
Recommends optimal technology stacks:
- Analyzes project requirements
- Suggests frontend, backend, database, and DevOps tools
- Provides rationale for each recommendation

### Team Formation Agent
Matches candidates to project requirements:
- Analyzes resumes and project needs
- Suggests optimal team composition
- Ranks candidates by fit

### Task Designer Agent
Breaks down projects into actionable tasks:
- Generates task lists from requirements
- Creates timelines and milestones
- Assigns priorities and dependencies

## 🔧 Configuration Options

### Using Gemini Instead of Ollama

Edit `backend/.env`:
```env
FORCE_OLLAMA=false
USE_GEMINI=true
GEMINI_API_KEYS=your-api-key-here
```

### Changing Ports

**Backend Port:**
Edit the uvicorn command:
```bash
python -m uvicorn main:app --host 127.0.0.1 --port <YOUR_PORT>
```

Then update `frontend/.env`:
```env
VITE_API_BASE_URL=http://localhost:<YOUR_PORT>
```

**Frontend Port:**
Edit `frontend/vite.config.ts` and add:
```typescript
export default defineConfig({
  server: {
    port: 5174  // Your desired port
  }
})
```

## 🐛 Troubleshooting

### Backend Won't Start

**Issue**: "ModuleNotFoundError: No module named 'X'"
```bash
cd backend
pip install -r requirements.txt
```

**Issue**: "MongoDB connection failed"
- Check your internet connection
- Verify MongoDB credentials in `backend/.env`
- Ensure MongoDB Atlas cluster is running

**Issue**: "Port already in use"
```bash
# Check what's using the port
netstat -ano | findstr :8001

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### Ollama Issues

**Issue**: "Ollama model not found"
```bash
ollama pull llama3.2:3b
```

**Issue**: "Ollama not available"
```bash
# Start Ollama service
ollama serve
```

### Frontend Won't Start

**Issue**: "Dependencies not installed"
```bash
cd frontend
npm install
```

**Issue**: "Cannot connect to backend"
- Verify backend is running on port 8001
- Check `frontend/.env` has correct `VITE_API_BASE_URL`
- Check browser console for CORS errors

### AI Agents Not Working

**Issue**: "No LLM provider available"
- Ensure Ollama is running: `ollama list`
- Verify model is downloaded: `ollama pull llama3.2:3b`
- Check `backend/.env` has `FORCE_OLLAMA=true`

**Issue**: "ChromaDB errors"
```bash
# Create the directory if it doesn't exist
mkdir backend\chroma_db
```

## 🔒 Security Notes

### For Production Deployment:

1. **Change the SECRET_KEY** in `backend/.env`
2. **Use environment variables** instead of hardcoded credentials
3. **Enable HTTPS** for all endpoints
4. **Restrict CORS origins** to your production domain
5. **Use secure MongoDB connection** with strong passwords
6. **Implement rate limiting** on API endpoints
7. **Add authentication middleware** to protect sensitive routes

## 📚 API Documentation

Once the backend is running, access interactive API documentation at:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## 📊 Database Schema

### Collections:
- `users` - User accounts (managers, team leads)
- `projects` - Project information
- `documents` - Uploaded documents metadata
- `notifications` - System notifications
- `team_members` - Team member profiles

## 🤝 Contributing

For development:

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## 📝 License

This project is proprietary software. All rights reserved.

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs in terminal output
3. Check backend logs in `backend/backend_log.txt`
4. Review browser console for frontend errors

## 🎓 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [LangChain Documentation](https://python.langchain.com/)
- [Ollama Documentation](https://ollama.ai/docs)
- [ChromaDB Documentation](https://docs.trychroma.com/)

---

**Version**: 1.0.0  
**Last Updated**: February 11, 2026  
**Maintained By**: Lead Mate Development Team
