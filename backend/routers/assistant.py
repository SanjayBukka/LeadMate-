from fastapi import APIRouter, Form
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/assistant", tags=["assistant"])

class ChatMessage(BaseModel):
    id: str
    message: str
    is_bot: bool
    timestamp: str

class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None

class ChatResponse(BaseModel):
    messages: List[ChatMessage]

@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(request: ChatRequest):
    """Chat with the AI assistant"""
    # This will integrate with the actual AI assistant
    user_message = ChatMessage(
        id=str(uuid.uuid4()),
        message=request.message,
        is_bot=False,
        timestamp=datetime.now().isoformat()
    )
    
    bot_response = ChatMessage(
        id=str(uuid.uuid4()),
        message="I'm your LeadMate AI assistant. I can help you with project management, team coordination, and technical decisions. How can I assist you today?",
        is_bot=True,
        timestamp=datetime.now().isoformat()
    )
    
    return ChatResponse(messages=[user_message, bot_response])

@router.get("/suggestions")
async def get_assistant_suggestions():
    """Get suggestions from the AI assistant"""
    # This will integrate with the actual AI assistant
    return {
        "suggestions": [
            "Review your project timeline and identify potential bottlenecks",
            "Consider organizing a team retrospective to discuss improvements",
            "Check if all team members have the necessary resources to complete their tasks",
            "Review the latest progress reports to ensure you're on track"
        ]
    }