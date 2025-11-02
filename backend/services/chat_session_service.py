"""
Chat Session Service
Manages separate chat sessions for each agent
"""
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from database import get_database


class ChatSessionService:
    """Service for managing chat sessions for each agent"""
    
    def __init__(self):
        self.db = get_database()
    
    async def create_session(self, company_id: str, lead_id: str, agent_type: str) -> str:
        """Create a new chat session for an agent"""
        try:
            session_id = str(uuid.uuid4())
            session_data = {
                "session_id": session_id,
                "company_id": company_id,
                "lead_id": lead_id,
                "agent_type": agent_type,
                "created_at": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "messages": [],
                "is_active": True
            }
            
            await self.db.chat_sessions.insert_one(session_data)
            return session_id
            
        except Exception as e:
            print(f"Error creating chat session: {e}")
            return str(uuid.uuid4())
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Get a chat session by ID"""
        try:
            session = await self.db.chat_sessions.find_one({"session_id": session_id})
            return session
        except Exception as e:
            print(f"Error getting chat session: {e}")
            return None
    
    async def get_active_sessions(self, company_id: str, lead_id: str) -> List[Dict]:
        """Get all active chat sessions for a company/lead"""
        try:
            sessions = []
            async for session in self.db.chat_sessions.find({
                "company_id": company_id,
                "lead_id": lead_id,
                "is_active": True
            }).sort("last_activity", -1):
                sessions.append(session)
            return sessions
        except Exception as e:
            print(f"Error getting active sessions: {e}")
            return []
    
    async def add_message(self, session_id: str, message: str, response: str, agent: str) -> bool:
        """Add a message to a chat session"""
        try:
            message_data = {
                "message": message,
                "response": response,
                "agent": agent,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.db.chat_sessions.update_one(
                {"session_id": session_id},
                {
                    "$push": {"messages": message_data},
                    "$set": {"last_activity": datetime.utcnow()}
                }
            )
            return True
            
        except Exception as e:
            print(f"Error adding message to session: {e}")
            return False
    
    async def get_session_messages(self, session_id: str) -> List[Dict]:
        """Get all messages from a chat session"""
        try:
            session = await self.get_session(session_id)
            if session:
                return session.get("messages", [])
            return []
        except Exception as e:
            print(f"Error getting session messages: {e}")
            return []
    
    async def close_session(self, session_id: str) -> bool:
        """Close a chat session"""
        try:
            await self.db.chat_sessions.update_one(
                {"session_id": session_id},
                {"$set": {"is_active": False, "closed_at": datetime.utcnow()}}
            )
            return True
        except Exception as e:
            print(f"Error closing session: {e}")
            return False
    
    async def get_or_create_session(self, company_id: str, lead_id: str, agent_type: str) -> str:
        """Get existing session or create new one for an agent"""
        try:
            # Check if there's an active session for this agent
            existing_session = await self.db.chat_sessions.find_one({
                "company_id": company_id,
                "lead_id": lead_id,
                "agent_type": agent_type,
                "is_active": True
            })
            
            if existing_session:
                return existing_session["session_id"]
            else:
                return await self.create_session(company_id, lead_id, agent_type)
                
        except Exception as e:
            print(f"Error getting or creating session: {e}")
            return await self.create_session(company_id, lead_id, agent_type)


# Global instance
chat_session_service = ChatSessionService()
