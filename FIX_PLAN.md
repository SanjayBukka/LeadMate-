# LeadMate Agent System - Critical Fix Plan

## 🚨 Issues Identified

1. **ID Resolution Problem (CRITICAL)**
   - Frontend sends `user.id` as both `company_id` and `lead_id`
   - Should send `startupId` as `company_id` and `user.id` as `lead_id`
   - AuthContext doesn't store `startupId`

2. **Document Agent Not Finding Documents**
   - Documents exist in MongoDB but ChromaDB sync fails
   - Wrong IDs prevent document discovery
   - Document Agent gives generic response instead of analyzing docs

3. **Missing Chat History Endpoints**
   - `/api/agents/stack/history/{company_id}/{lead_id}` returns 404
   - `/api/agents/tasks/history/{company_id}/{lead_id}` returns 404

4. **ChromaDB Cleanup Needed**
   - Need to clear all ChromaDB data for fresh start
   - Old corrupted data might interfere

## ✅ Fix Strategy

### Phase 1: Fix ID Resolution
1. Update AuthContext to store `startupId` from `/api/auth/me` response
2. Update AIAgents.tsx to use `startupId` for `company_id` and `user.id` for `lead_id`
3. Ensure all agent calls use correct IDs

### Phase 2: Clear ChromaDB
1. Create cleanup script to delete all ChromaDB data
2. Test that agents start with clean state

### Phase 3: Fix Document Sync
1. Ensure Document Agent properly syncs MongoDB documents to ChromaDB
2. Fix document detection logic
3. Ensure document context is actually used in agent responses

### Phase 4: Add Missing Endpoints
1. Add chat history endpoints for Stack Agent
2. Add chat history endpoints for Task Agent
3. Add chat history endpoints for Team Agent

### Phase 5: Test Complete Flow
1. Upload document → MongoDB
2. Sync to ChromaDB
3. Chat with Document Agent → Should use document context
4. Verify all agents work correctly

