"""
WebSocket Router for Real-time Notifications
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List
import json
import logging
from services.notification_service import NotificationService
from services.data_service import DataService
from utils.auth import get_current_user_ws

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])

# Initialize services
data_service = DataService()
notification_service = NotificationService(data_service)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, company_id: str, lead_id: str):
        await websocket.accept()
        user_key = f"{company_id}_{lead_id}"
        if user_key not in self.active_connections:
            self.active_connections[user_key] = []
        self.active_connections[user_key].append(websocket)
        logger.info(f"WebSocket connected for {user_key}")
    
    def disconnect(self, websocket: WebSocket, company_id: str, lead_id: str):
        user_key = f"{company_id}_{lead_id}"
        if user_key in self.active_connections:
            try:
                self.active_connections[user_key].remove(websocket)
                if not self.active_connections[user_key]:
                    del self.active_connections[user_key]
            except ValueError:
                pass
        logger.info(f"WebSocket disconnected for {user_key}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast_to_user(self, message: str, company_id: str, lead_id: str):
        user_key = f"{company_id}_{lead_id}"
        if user_key in self.active_connections:
            for connection in self.active_connections[user_key]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Failed to send message to client: {str(e)}")

manager = ConnectionManager()

@router.websocket("/notifications/{company_id}/{lead_id}")
async def websocket_endpoint(websocket: WebSocket, company_id: str, lead_id: str):
    """WebSocket endpoint for real-time notifications"""
    await manager.connect(websocket, company_id, lead_id)
    
    try:
        # Send initial notifications
        notifications = await notification_service.get_notifications(company_id, lead_id, unread_only=True)
        if notifications:
            await websocket.send_text(json.dumps({
                "type": "initial_notifications",
                "data": notifications
            }, default=str))
        
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "mark_read":
                notification_id = message.get("notification_id")
                if notification_id:
                    await notification_service.mark_notification_read(notification_id)
                    await websocket.send_text(json.dumps({
                        "type": "notification_read",
                        "notification_id": notification_id
                    }))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, company_id, lead_id)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket, company_id, lead_id)

@router.get("/notifications/{company_id}/{lead_id}")
async def get_notifications(company_id: str, lead_id: str, unread_only: bool = False):
    """Get notifications for a user"""
    try:
        notifications = await notification_service.get_notifications(company_id, lead_id, unread_only)
        return {"notifications": notifications}
    except Exception as e:
        logger.error(f"Failed to get notifications: {str(e)}")
        return {"notifications": []}

@router.post("/notifications/{company_id}/{lead_id}/mark-read")
async def mark_notification_read(company_id: str, lead_id: str, notification_id: str):
    """Mark a notification as read"""
    try:
        success = await notification_service.mark_notification_read(notification_id)
        return {"success": success}
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {str(e)}")
        return {"success": False}
