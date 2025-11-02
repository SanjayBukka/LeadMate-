"""
Notification Service - Real-time Notifications and Updates
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from enum import Enum
import json

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    REPOSITORY_ANALYZED = "repository_analyzed"
    TEAM_ACTIVITY = "team_activity"
    PERFORMANCE_ALERT = "performance_alert"
    MILESTONE_ACHIEVED = "milestone_achieved"
    CODE_QUALITY_ISSUE = "code_quality_issue"
    TEAM_MEMBER_JOINED = "team_member_joined"
    PROJECT_UPDATE = "project_update"

class NotificationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class NotificationService:
    def __init__(self, data_service):
        self.data_service = data_service
        self.active_connections: Dict[str, List] = {}
        
    async def create_notification(self, company_id: str, lead_id: str, 
                                notification_type: NotificationType,
                                title: str, message: str, 
                                priority: NotificationPriority = NotificationPriority.MEDIUM,
                                data: Optional[Dict] = None) -> bool:
        """Create a new notification"""
        try:
            notification = {
                "type": notification_type.value,
                "title": title,
                "message": message,
                "priority": priority.value,
                "data": data or {},
                "created_at": datetime.now(),
                "read": False
            }
            
            # Save to database
            success = self.data_service.save_notification(company_id, lead_id, notification)
            
            if success:
                # Send real-time update to connected clients
                await self._broadcast_notification(company_id, lead_id, notification)
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to create notification: {str(e)}")
            return False
    
    async def _broadcast_notification(self, company_id: str, lead_id: str, notification: Dict):
        """Broadcast notification to connected clients"""
        try:
            user_key = f"{company_id}_{lead_id}"
            if user_key in self.active_connections:
                message = {
                    "type": "notification",
                    "data": notification
                }
                
                # Send to all connected clients for this user
                for websocket in self.active_connections[user_key]:
                    try:
                        await websocket.send_text(json.dumps(message, default=str))
                    except Exception as e:
                        logger.error(f"Failed to send notification to client: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Failed to broadcast notification: {str(e)}")
    
    async def get_notifications(self, company_id: str, lead_id: str, 
                              unread_only: bool = False) -> List[Dict]:
        """Get notifications for a user"""
        try:
            notifications = self.data_service.get_notifications(company_id, lead_id, unread_only)
            return notifications
        except Exception as e:
            logger.error(f"Failed to get notifications: {str(e)}")
            return []
    
    async def mark_notification_read(self, notification_id: str) -> bool:
        """Mark a notification as read"""
        try:
            return self.data_service.mark_notification_read(notification_id)
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {str(e)}")
            return False
    
    async def analyze_and_notify(self, company_id: str, lead_id: str, 
                               analysis_data: Dict) -> None:
        """Analyze data and create relevant notifications"""
        try:
            # Check for significant changes in activity
            commits_data = analysis_data.get('commits_data', [])
            if commits_data:
                recent_commits = [c for c in commits_data 
                               if datetime.fromisoformat(c['date'].replace('Z', '+00:00')) > 
                               datetime.now() - timedelta(days=1)]
                
                if len(recent_commits) > 10:
                    await self.create_notification(
                        company_id, lead_id,
                        NotificationType.TEAM_ACTIVITY,
                        "High Development Activity",
                        f"Your team has made {len(recent_commits)} commits in the last 24 hours!",
                        NotificationPriority.MEDIUM,
                        {"commits": len(recent_commits)}
                    )
            
            # Check for performance issues
            recent_activity = analysis_data.get('recent_activity', {})
            if recent_activity:
                total_commits = recent_activity.get('total_commits', 0)
                if total_commits < 5:
                    await self.create_notification(
                        company_id, lead_id,
                        NotificationType.PERFORMANCE_ALERT,
                        "Low Activity Alert",
                        "Development activity has been low recently. Consider checking for blockers.",
                        NotificationPriority.HIGH,
                        {"commits": total_commits}
                    )
            
            # Check for code quality issues
            dev_insights = analysis_data.get('dev_insights', {})
            if dev_insights:
                for developer, insights in dev_insights.get('insights', {}).items():
                    if 'Low code output' in str(insights.get('summary', [])):
                        await self.create_notification(
                            company_id, lead_id,
                            NotificationType.CODE_QUALITY_ISSUE,
                            f"Code Quality Alert - {developer}",
                            f"Code output has been low for {developer}. Consider providing support.",
                            NotificationPriority.MEDIUM,
                            {"developer": developer}
                        )
            
            # Check for milestones
            project_summary = analysis_data.get('project_summary', {})
            if project_summary:
                health_score = project_summary.get('health_score', 0)
                if health_score > 80:
                    await self.create_notification(
                        company_id, lead_id,
                        NotificationType.MILESTONE_ACHIEVED,
                        "Excellent Project Health",
                        f"Your project has achieved a health score of {health_score}%!",
                        NotificationPriority.LOW,
                        {"health_score": health_score}
                    )
                elif health_score < 40:
                    await self.create_notification(
                        company_id, lead_id,
                        NotificationType.PERFORMANCE_ALERT,
                        "Project Health Warning",
                        f"Project health score is {health_score}%. Consider reviewing processes.",
                        NotificationPriority.HIGH,
                        {"health_score": health_score}
                    )
            
        except Exception as e:
            logger.error(f"Failed to analyze and notify: {str(e)}")
    
    async def create_team_activity_notification(self, company_id: str, lead_id: str,
                                              developer: str, activity: str) -> bool:
        """Create team activity notification"""
        return await self.create_notification(
            company_id, lead_id,
            NotificationType.TEAM_ACTIVITY,
            f"Team Activity - {developer}",
            f"{developer} {activity}",
            NotificationPriority.LOW,
            {"developer": developer, "activity": activity}
        )
    
    async def create_milestone_notification(self, company_id: str, lead_id: str,
                                          milestone: str) -> bool:
        """Create milestone achievement notification"""
        return await self.create_notification(
            company_id, lead_id,
            NotificationType.MILESTONE_ACHIEVED,
            "Milestone Achieved",
            f"Congratulations! {milestone}",
            NotificationPriority.MEDIUM,
            {"milestone": milestone}
        )
    
    async def create_performance_alert(self, company_id: str, lead_id: str,
                                      alert_type: str, message: str) -> bool:
        """Create performance alert notification"""
        return await self.create_notification(
            company_id, lead_id,
            NotificationType.PERFORMANCE_ALERT,
            f"Performance Alert - {alert_type}",
            message,
            NotificationPriority.HIGH,
            {"alert_type": alert_type}
        )
    
    def add_connection(self, company_id: str, lead_id: str, websocket):
        """Add a WebSocket connection for real-time updates"""
        user_key = f"{company_id}_{lead_id}"
        if user_key not in self.active_connections:
            self.active_connections[user_key] = []
        self.active_connections[user_key].append(websocket)
    
    def remove_connection(self, company_id: str, lead_id: str, websocket):
        """Remove a WebSocket connection"""
        user_key = f"{company_id}_{lead_id}"
        if user_key in self.active_connections:
            try:
                self.active_connections[user_key].remove(websocket)
                if not self.active_connections[user_key]:
                    del self.active_connections[user_key]
            except ValueError:
                pass  # Connection not found
