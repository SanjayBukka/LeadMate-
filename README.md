# LeadMate - AI-Powered Project Management Platform

LeadMate is a comprehensive AI-powered project management platform that helps companies manage projects, teams, and documentation through intelligent AI agents.

## 🚀 Features

### Core Features
- **Company & Team Management**: Multi-tenant system with managers and team leads
- **Project Management**: Create and manage projects with assigned team leads
- **Document Processing**: Upload and analyze project documents (PDF, DOCX, TXT)
- **AI Agents**: Intelligent agents powered by Gemini AI for various tasks
- **Team Formation**: AI-powered team recommendations based on resumes and requirements
- **Task Generation**: Automated task creation from project requirements

### AI Agents
1. **Document Agent**: Analyzes project documentation and provides insights
2. **Stack Agent**: Recommends technology stacks based on project requirements
3. **Task Agent**: Generates actionable tasks from project requirements
4. **Team Formation Agent**: Forms optimal teams from resumes and skills

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI
- **Database**: MongoDB Atlas
- **Vector Database**: ChromaDB
- **AI Framework**: CrewAI
- **LLM**: Google Gemini 2.5 Flash (with Ollama fallback)
- **Authentication**: JWT tokens

### Frontend
- **Framework**: React + TypeScript
- **Build Tool**: Vite
- **Styling**: TailwindCSS
- **State Management**: React Query, Context API
- **Routing**: React Router

## 📋 Prerequisites

- Python 3.10+
- Node.js 18+
- MongoDB Atlas account
- Google Gemini API keys (optional - falls back to Ollama)

## 🔧 Installation

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
```

### Environment Configuration

1. Update `backend/config.py` with your MongoDB connection string
2. Add Gemini API keys in `backend/config.py` (optional)
3. If using Ollama, ensure it's running on `http://localhost:11434`

## 🚀 Running the Application

### Backend
```bash
cd backend
python main.py
```
Backend runs on `http://localhost:8000`

### Frontend
```bash
cd frontend
npm run dev
```
Frontend runs on `http://localhost:5173`

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🔐 Authentication Flow

1. **Company Registration**: Company registers with manager details
2. **Manager Login**: Manager logs in and can add team leads
3. **Team Lead Login**: Team leads login and manage their projects
4. **Project Creation**: Managers create projects and assign to team leads

## 🤖 AI Agents Overview

### Document Agent
- Uploads and processes project documents
- Extracts key information and requirements
- Provides Q&A interface for document queries
- Maintains conversation history

### Stack Agent
- Analyzes project requirements
- Recommends technology stacks
- Iterative refinement with team lead feedback

### Task Agent
- Generates tasks from project requirements
- Assigns tasks to team members
- Tracks task progress and status

### Team Formation Agent
- Processes resumes (PDF extraction)
- Extracts skills and experience
- Matches candidates to project needs
- Forms optimal teams

## 📖 Documentation

Comprehensive documentation is available in the root directory:
- `BACKEND_MODELS_COMPREHENSIVE_GUIDE.md` - Complete model documentation
- `GEMINI_MIGRATION_SUMMARY.md` - AI integration details
- `API_TEST_RESULTS.md` - API testing results

## 🧪 Testing

Run API tests:
```bash
cd backend
python test_api.py
```

## 📝 License

This project is proprietary software.

## 👥 Contributing

This is a private project. Contact the repository owner for contribution guidelines.

## 📧 Contact

For questions or support, please contact the project maintainer.

---

**Built with ❤️ using AI-powered technologies**

