"""
Notification API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from bson import ObjectId

from database import get_database
from models.notification import Notification, NotificationCreate, NotificationInDB
from models.user import User
from utils.auth import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("", response_model=List[Notification])
async def get_notifications(
    current_user: User = Depends(get_current_user),
    unread_only: bool = False
):
    """Get all notifications for the current user"""
    db = get_database()
    
    query = {
        "userId": str(current_user.id),
        "startupId": current_user.startupId
    }
    
    if unread_only:
        query["isRead"] = False
    
    notifications_cursor = db.notifications.find(query).sort("createdAt", -1).limit(50)
    notifications = []
    
    async for notif_data in notifications_cursor:
        # Convert ObjectId to string
        if "_id" in notif_data and isinstance(notif_data["_id"], ObjectId):
            notif_data["_id"] = str(notif_data["_id"])
        notifications.append(Notification(**notif_data))
    
    return notifications


@router.get("/count", response_model=dict)
async def get_unread_count(current_user: User = Depends(get_current_user)):
    """Get count of unread notifications"""
    db = get_database()
    
    count = await db.notifications.count_documents({
        "userId": str(current_user.id),
        "startupId": current_user.startupId,
        "isRead": False
    })
    
    return {"count": count}


@router.put("/{notification_id}/read", response_model=Notification)
async def mark_notification_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read"""
    db = get_database()
    
    if not ObjectId.is_valid(notification_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid notification ID format"
        )
    
    # Verify notification belongs to current user
    notification = await db.notifications.find_one({
        "_id": ObjectId(notification_id),
        "userId": str(current_user.id),
        "startupId": current_user.startupId
    })
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Update notification
    await db.notifications.update_one(
        {"_id": ObjectId(notification_id)},
        {"$set": {"isRead": True}}
    )
    
    updated_notification = await db.notifications.find_one({"_id": ObjectId(notification_id)})
    
    # Convert ObjectId to string
    if "_id" in updated_notification and isinstance(updated_notification["_id"], ObjectId):
        updated_notification["_id"] = str(updated_notification["_id"])
    
    return Notification(**updated_notification)


@router.put("/mark-all-read", response_model=dict)
async def mark_all_as_read(current_user: User = Depends(get_current_user)):
    """Mark all notifications as read for the current user"""
    db = get_database()
    
    result = await db.notifications.update_many(
        {
            "userId": str(current_user.id),
            "startupId": current_user.startupId,
            "isRead": False
        },
        {"$set": {"isRead": True}}
    )
    
    return {"modified_count": result.modified_count}


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a notification"""
    db = get_database()
    
    if not ObjectId.is_valid(notification_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid notification ID format"
        )
    
    # Verify notification belongs to current user
    result = await db.notifications.delete_one({
        "_id": ObjectId(notification_id),
        "userId": str(current_user.id),
        "startupId": current_user.startupId
    })
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return {"message": "Notification deleted successfully"}

