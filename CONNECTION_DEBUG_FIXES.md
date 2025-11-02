# Connection Issue Debugging & Fixes

## Issues Found and Fixed

### 1. **Duplicate Endpoint Definition** ✅ FIXED
   - **Problem**: Two `/doc/chat` endpoints were defined in `backend/routers/agents.py` (lines 101 and 460)
   - **Impact**: The second definition was overriding the first, and it was missing `await` for async document agent calls
   - **Fix**: Removed the duplicate endpoint and fixed async handling

### 2. **Missing Authentication Headers** ✅ FIXED
   - **Problem**: Frontend wasn't sending authentication tokens with API requests
   - **Impact**: Some endpoints might reject unauthenticated requests
   - **Fix**: Added `Authorization: Bearer ${token}` header to all API calls in `AIAgents.tsx`

### 3. **Insufficient Error Logging** ✅ FIXED
   - **Problem**: Limited logging made debugging difficult
   - **Impact**: Hard to identify where requests were failing
   - **Fix**: 
     - Added comprehensive `console.log` statements in frontend
     - Added detailed logging in backend endpoints
     - Improved error messages to show actual error details

### 4. **Poor Error Handling** ✅ FIXED
   - **Problem**: Generic error messages didn't help diagnose issues
   - **Impact**: Users couldn't see what went wrong
   - **Fix**: 
     - Enhanced error parsing to extract detailed error messages from backend
     - Display actual error messages to users instead of generic ones

### 5. **Async/Await Mismatch** ✅ FIXED
   - **Problem**: Document agent's `chat_with_agent` is async but wasn't awaited
   - **Impact**: Requests would fail or return incorrect results
   - **Fix**: Added proper `await` for async agent methods

## Backend Configuration

### Port
- **Backend runs on**: `http://localhost:8000` (default)
- Verified in `backend/main.py` line 98

### CORS Configuration
- **Allowed origins**: `http://localhost:5173`, `http://localhost:5174`, `http://localhost:5175`
- **Status**: ✅ Configured correctly in `backend/main.py`

### Endpoints Available
- `/api/agents/doc/chat` - Document Agent chat
- `/api/agents/stack/chat` - Stack Agent chat
- `/api/agents/tasks/chat` - Task Agent chat
- `/api/agents/team/chat` - Team Agent chat

## Frontend Configuration

### API Base URL
- **Default**: `http://localhost:8000`
- Can be overridden with `VITE_API_BASE_URL` environment variable

### Frontend Port
- **Default**: `5173` (Vite default)
- Matches CORS allowed origins ✅

## How to Test

### 1. Start the Backend
```bash
cd backend
python main.py
```
Or:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start the Frontend
```bash
cd frontend
npm run dev
```

### 3. Check Browser Console
When you type a query, you should now see:
- `Sending request to: http://localhost:8000/api/agents/doc/chat`
- `Request body: { message: "...", company_id: "...", lead_id: "..." }`
- `Response status: 200` (or error code)
- `Response data: { response: "...", agent: "...", timestamp: "..." }`

### 4. Check Backend Logs
You should see:
- `INFO: Doc Agent chat request - company_id: ..., lead_id: ..., message length: ...`
- `INFO: Agent response generated successfully`

## Common Issues & Solutions

### Issue: "Network Error" or "Failed to fetch"
**Possible Causes:**
1. Backend not running
2. Wrong port (check if backend is on 8000)
3. CORS error (check browser console for CORS errors)

**Solution:**
- Verify backend is running: `curl http://localhost:8000/api/health`
- Check frontend port matches CORS allowed origins
- Check browser console for specific error messages

### Issue: "401 Unauthorized" or "403 Forbidden"
**Possible Causes:**
1. Missing or invalid auth token
2. Token expired

**Solution:**
- Check if user is logged in
- Check `localStorage.getItem('authToken')` in browser console
- Try logging out and back in

### Issue: "500 Internal Server Error"
**Possible Causes:**
1. Agent initialization error
2. Database connection issue
3. Missing dependencies (Ollama, ChromaDB, etc.)

**Solution:**
- Check backend console logs for detailed error
- Verify Ollama is running: `curl http://localhost:11434/api/tags`
- Check MongoDB connection
- Review `backend/backend_errors.txt` for error details

### Issue: "Response format error"
**Possible Causes:**
1. Backend returning unexpected format
2. Response parsing issue

**Solution:**
- Check console logs for actual response format
- Verify backend endpoint is returning `ChatResponse` model
- Check `data.response` vs `data.message` in frontend

## Debugging Checklist

When you type a query and don't get a response:

1. ✅ **Open Browser Console** (F12 → Console tab)
   - Look for request logs
   - Check for JavaScript errors
   - Look for network errors (red entries)

2. ✅ **Open Network Tab** (F12 → Network tab)
   - Filter by "Fetch/XHR"
   - Click on the request to `/api/agents/.../chat`
   - Check:
     - Request URL
     - Request Method (should be POST)
     - Request Headers (should include Content-Type and Authorization)
     - Request Payload (should have message, company_id, lead_id)
     - Response Status (200 = success, anything else = error)
     - Response Preview/Response (should show the actual response)

3. ✅ **Check Backend Console**
   - Look for incoming request logs
   - Check for error messages
   - Verify agent is initializing correctly

4. ✅ **Verify Environment**
   - Backend running on port 8000
   - Frontend running on port 5173 (or 5174/5175)
   - Ollama running on port 11434 (for agents)
   - MongoDB running (for data storage)

## What Was Changed

### Backend Files Modified:
- `backend/routers/agents.py`
  - Removed duplicate `/doc/chat` endpoint
  - Fixed async/await for document agent
  - Added comprehensive logging
  - Improved error handling

### Frontend Files Modified:
- `frontend/src/pages/TeamLead/AIAgents.tsx`
  - Added authentication headers
  - Enhanced error handling and logging
  - Added console.log statements for debugging
  - Improved response parsing
  - Better error messages for users

## Next Steps

1. **Test the Connection**
   - Start both backend and frontend
   - Open the AI Agents page
   - Type a query
   - Check browser console for logs
   - Check backend console for logs

2. **Review Logs**
   - All requests/responses are now logged
   - Error messages are more descriptive
   - You can trace the entire flow

3. **If Still Not Working**
   - Share the browser console logs
   - Share the backend console logs
   - Share any error messages you see

## Additional Notes

- The frontend will now show actual error messages instead of generic ones
- All API calls include authentication tokens
- Logging is comprehensive for debugging
- Error handling is more robust

If issues persist, check:
- Backend dependencies (requirements.txt)
- Ollama service running
- MongoDB connection
- Network connectivity between frontend and backend

