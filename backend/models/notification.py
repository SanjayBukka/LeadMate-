"""
Notification Model
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from bson import ObjectId
from .startup import PyObjectId


class NotificationBase(BaseModel):
    """Base notification fields"""
    userId: str  # Team lead who receives the notification
    startupId: str
    type: Literal["project_assigned", "project_updated", "project_completed", "team_added"]
    title: str
    message: str
    relatedId: Optional[str] = None  # Related project/document ID
    isRead: bool = False


class NotificationCreate(NotificationBase):
    """Notification creation schema"""
    pass


class Notification(NotificationBase):
    """Notification response schema"""
    id: str = Field(alias="_id")
    createdAt: datetime

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str}
    }


class NotificationInDB(NotificationBase):
    """Notification stored in database"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    createdAt: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

