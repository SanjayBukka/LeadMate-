# Agent Connection Verification Guide

## Overview
This document helps verify that all AI agents are properly connected to the frontend and can respond to requests.

## Agent Endpoints

The frontend expects these endpoints:
- **Document Agent**: `POST /api/agents/doc/chat`
- **Stack Agent**: `POST /api/agents/stack/chat`
- **Task Agent**: `POST /api/agents/tasks/chat`
- **Team Agent**: `POST /api/agents/team/chat`

## Backend Configuration

### ✅ Router Registration
The agents router is registered in `backend/main.py` at line 78:
```python
app.include_router(agents_router)  # Multi-Agent System
```

### ✅ Endpoint Definitions
All chat endpoints are defined in `backend/routers/agents.py`:
- Line 440: `/doc/chat` - Document Agent
- Line 521: `/stack/chat` - Stack Agent
- Line 553: `/tasks/chat` - Task Agent
- Line 573: `/team/chat` - Team Agent

## Frontend Configuration

### ✅ API Calls
Frontend sends requests from `frontend/src/pages/TeamLead/AIAgents.tsx`:
- Line 230: POST request to `${API_BASE_URL}${selectedAgent.endpoint}`
- Request body format: `{ message, company_id, lead_id, project_id? }`
- Expected response: `{ response, agent, timestamp }`

### ✅ Response Handling
Frontend extracts response at line 248:
```typescript
content: data.response || data.message || 'I received your message but couldn\'t generate a response.'
```

## Verification Steps

### Step 1: Start Backend Server
```bash
cd backend
python main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Step 2: Check Server Health
Visit: http://localhost:8000/api/health

Expected response:
```json
{"status": "healthy"}
```

### Step 3: Check Agents Health
Visit: http://localhost:8000/api/agents/health

Expected response:
```json
{
  "status": "healthy",
  "active_agents": 0,
  "document_agents": 0,
  "stack_agents": 0,
  "task_agents": 0
}
```

### Step 4: Test Agent Endpoints

Run the test script:
```bash
python test_agents_connection.py
```

Or manually test with curl:

**Document Agent:**
```bash
curl -X POST http://localhost:8000/api/agents/doc/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, can you help me?",
    "company_id": "test_company",
    "lead_id": "test_lead"
  }'
```

**Stack Agent:**
```bash
curl -X POST http://localhost:8000/api/agents/stack/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What tech stack should I use?",
    "company_id": "test_company",
    "lead_id": "test_lead"
  }'
```

**Task Agent:**
```bash
curl -X POST http://localhost:8000/api/agents/tasks/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What tasks should I create?",
    "company_id": "test_company",
    "lead_id": "test_lead"
  }'
```

**Team Agent:**
```bash
curl -X POST http://localhost:8000/api/agents/team/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Help me with team management",
    "company_id": "test_company",
    "lead_id": "test_lead"
  }'
```

### Step 5: Test from Frontend

1. Start frontend:
```bash
cd frontend
npm run dev
```

2. Navigate to: http://localhost:5173/teamlead/agents (or your route)
3. Select an agent
4. Send a test message
5. Check browser console for any errors

## Potential Issues

### Issue 1: Backend Not Running
**Symptom**: Connection error or timeout
**Solution**: Start backend server on port 8000

### Issue 2: CORS Error
**Symptom**: Browser console shows CORS errors
**Solution**: Check `backend/main.py` CORS configuration (lines 60-69)
- Ensure frontend URL (localhost:5173) is in allowed origins

### Issue 3: Agent Initialization Error
**Symptom**: 500 error with agent-specific error message
**Solution**: Check agent dependencies:
- LLM service (Ollama/Gemini) is running
- Vector database (ChromaDB) is accessible
- Required environment variables are set

### Issue 4: Response Format Mismatch
**Symptom**: Frontend shows "I received your message but couldn't generate a response"
**Solution**: Check that agent's `chat_with_agent` method returns:
```python
{
    'response': str,
    'agent': str,
    'timestamp': str
}
```

### Issue 5: Authentication Issues
**Symptom**: 401 Unauthorized errors
**Solution**: Ensure auth token is included in requests (frontend handles this automatically)

## Expected Response Format

All agents should return:
```json
{
  "response": "Agent's response text here",
  "agent": "Agent Name",
  "timestamp": "2024-01-01T00:00:00"
}
```

## Testing Checklist

- [ ] Backend server is running on port 8000
- [ ] `/api/health` endpoint returns 200
- [ ] `/api/agents/health` endpoint returns 200
- [ ] All 4 agent chat endpoints are accessible
- [ ] Each agent can generate a response
- [ ] Frontend can connect to backend
- [ ] Frontend can send messages to agents
- [ ] Frontend displays agent responses correctly
- [ ] No CORS errors in browser console
- [ ] No errors in backend logs

## Quick Test Commands

```bash
# Test backend health
curl http://localhost:8000/api/health

# Test agents health
curl http://localhost:8000/api/agents/health

# Run automated tests
python test_agents_connection.py
```

