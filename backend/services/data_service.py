"""
Data Service - Real Data Persistence and Caching
"""
import os
import json
import pickle
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging
from pymongo import MongoClient
from bson import ObjectId
import hashlib

logger = logging.getLogger(__name__)

class DataService:
    def __init__(self, mongo_uri: str = "mongodb://localhost:27017", db_name: str = "leadmate_db"):
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.client = None
        self.db = None
        self._connect()
    
    def _connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.db_name]
            logger.info(f"Connected to MongoDB: {self.db_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            self.client = None
            self.db = None
    
    def save_repository_analysis(self, company_id: str, lead_id: str, repo_name: str, 
                               analysis_data: Dict) -> bool:
        """Save repository analysis to database"""
        try:
            if not self.db:
                return False
            
            # Create document
            document = {
                "company_id": company_id,
                "lead_id": lead_id,
                "repo_name": repo_name,
                "analysis_data": analysis_data,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "status": "completed"
            }
            
            # Check if analysis exists
            existing = self.db.repository_analyses.find_one({
                "company_id": company_id,
                "lead_id": lead_id,
                "repo_name": repo_name
            })
            
            if existing:
                # Update existing
                result = self.db.repository_analyses.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {
                        "analysis_data": analysis_data,
                        "updated_at": datetime.now()
                    }}
                )
            else:
                # Insert new
                result = self.db.repository_analyses.insert_one(document)
            
            return result.acknowledged
            
        except Exception as e:
            logger.error(f"Failed to save repository analysis: {str(e)}")
            return False

    def save_analysis_files(self, repo_name: str, commits_df: pd.DataFrame, dev_stats_df: pd.DataFrame,
                            base_dir: str = "data") -> bool:
        """Save analysis results to CSV and Excel like management app.
        - Writes commits.csv and developer_stats.csv
        - Also writes analysis.xlsx with two sheets: commits, developer_stats
        """
        try:
            export_dir = Path(base_dir) / repo_name
            export_dir.mkdir(parents=True, exist_ok=True)

            # CSV exports
            commits_path = export_dir / "commits.csv"
            dev_stats_path = export_dir / "developer_stats.csv"
            if commits_df is not None:
                (commits_df if not commits_df.empty else pd.DataFrame()).to_csv(commits_path, index=False)
            if dev_stats_df is not None:
                (dev_stats_df if not dev_stats_df.empty else pd.DataFrame()).to_csv(dev_stats_path)

            # Excel export (best-effort)
            try:
                xlsx_path = export_dir / "analysis.xlsx"
                with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:  # type: ignore
                    (commits_df if commits_df is not None else pd.DataFrame()).to_excel(writer, sheet_name="commits", index=False)
                    (dev_stats_df if dev_stats_df is not None else pd.DataFrame()).to_excel(writer, sheet_name="developer_stats")
            except Exception as e:
                logger.warning(f"Failed to write Excel export: {e}")

            logger.info(f"Saved analysis files to {export_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to save analysis files: {e}")
            return False
    
    def get_repository_analysis(self, company_id: str, lead_id: str, repo_name: str) -> Optional[Dict]:
        """Get repository analysis from database"""
        try:
            if not self.db:
                return None
            
            analysis = self.db.repository_analyses.find_one({
                "company_id": company_id,
                "lead_id": lead_id,
                "repo_name": repo_name
            })
            
            if analysis:
                return analysis.get("analysis_data")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get repository analysis: {str(e)}")
            return None
    
    def get_user_repositories(self, company_id: str, lead_id: str) -> List[str]:
        """Get list of repositories for a user"""
        try:
            if not self.db:
                return []
            
            repos = self.db.repository_analyses.find(
                {"company_id": company_id, "lead_id": lead_id},
                {"repo_name": 1, "updated_at": 1}
            ).sort("updated_at", -1)
            
            return [repo["repo_name"] for repo in repos]
            
        except Exception as e:
            logger.error(f"Failed to get user repositories: {str(e)}")
            return []
    
    def save_team_metrics(self, company_id: str, lead_id: str, metrics: Dict) -> bool:
        """Save team performance metrics"""
        try:
            if not self.db:
                return False
            
            document = {
                "company_id": company_id,
                "lead_id": lead_id,
                "metrics": metrics,
                "date": datetime.now().date(),
                "created_at": datetime.now()
            }
            
            # Check if metrics exist for today
            existing = self.db.team_metrics.find_one({
                "company_id": company_id,
                "lead_id": lead_id,
                "date": datetime.now().date()
            })
            
            if existing:
                result = self.db.team_metrics.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {"metrics": metrics, "created_at": datetime.now()}}
                )
            else:
                result = self.db.team_metrics.insert_one(document)
            
            return result.acknowledged
            
        except Exception as e:
            logger.error(f"Failed to save team metrics: {str(e)}")
            return False
    
    def get_team_metrics(self, company_id: str, lead_id: str, days: int = 30) -> List[Dict]:
        """Get team metrics for the last N days"""
        try:
            if not self.db:
                return []
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            metrics = self.db.team_metrics.find({
                "company_id": company_id,
                "lead_id": lead_id,
                "created_at": {"$gte": cutoff_date}
            }).sort("created_at", -1)
            
            return list(metrics)
            
        except Exception as e:
            logger.error(f"Failed to get team metrics: {str(e)}")
            return []
    
    def save_progress_report(self, company_id: str, lead_id: str, report: Dict) -> bool:
        """Save progress report"""
        try:
            if not self.db:
                return False
            
            document = {
                "company_id": company_id,
                "lead_id": lead_id,
                "report": report,
                "created_at": datetime.now(),
                "report_type": report.get("type", "weekly")
            }
            
            result = self.db.progress_reports.insert_one(document)
            return result.acknowledged
            
        except Exception as e:
            logger.error(f"Failed to save progress report: {str(e)}")
            return False
    
    def get_progress_reports(self, company_id: str, lead_id: str, report_type: str = None) -> List[Dict]:
        """Get progress reports"""
        try:
            if not self.db:
                return []
            
            query = {"company_id": company_id, "lead_id": lead_id}
            if report_type:
                query["report_type"] = report_type
            
            reports = self.db.progress_reports.find(query).sort("created_at", -1)
            return list(reports)
            
        except Exception as e:
            logger.error(f"Failed to get progress reports: {str(e)}")
            return []
    
    def save_notification(self, company_id: str, lead_id: str, notification: Dict) -> bool:
        """Save notification"""
        try:
            if not self.db:
                return False
            
            document = {
                "company_id": company_id,
                "lead_id": lead_id,
                "notification": notification,
                "created_at": datetime.now(),
                "read": False
            }
            
            result = self.db.notifications.insert_one(document)
            return result.acknowledged
            
        except Exception as e:
            logger.error(f"Failed to save notification: {str(e)}")
            return False
    
    def get_notifications(self, company_id: str, lead_id: str, unread_only: bool = False) -> List[Dict]:
        """Get notifications"""
        try:
            if not self.db:
                return []
            
            query = {"company_id": company_id, "lead_id": lead_id}
            if unread_only:
                query["read"] = False
            
            notifications = self.db.notifications.find(query).sort("created_at", -1)
            return list(notifications)
            
        except Exception as e:
            logger.error(f"Failed to get notifications: {str(e)}")
            return []
    
    def mark_notification_read(self, notification_id: str) -> bool:
        """Mark notification as read"""
        try:
            if not self.db:
                return False
            
            result = self.db.notifications.update_one(
                {"_id": ObjectId(notification_id)},
                {"$set": {"read": True}}
            )
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {str(e)}")
            return False
    
    def cleanup_old_data(self, days: int = 90) -> bool:
        """Clean up old data"""
        try:
            if not self.db:
                return False
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Clean up old repository analyses
            self.db.repository_analyses.delete_many({
                "updated_at": {"$lt": cutoff_date}
            })
            
            # Clean up old team metrics
            self.db.team_metrics.delete_many({
                "created_at": {"$lt": cutoff_date}
            })
            
            # Clean up old notifications
            self.db.notifications.delete_many({
                "created_at": {"$lt": cutoff_date},
                "read": True
            })
            
            logger.info(f"Cleaned up data older than {days} days")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {str(e)}")
            return False
    
    def get_analytics_summary(self, company_id: str, lead_id: str) -> Dict:
        """Get analytics summary for dashboard"""
        try:
            if not self.db:
                return {}
            
            # Get repository count
            repo_count = self.db.repository_analyses.count_documents({
                "company_id": company_id,
                "lead_id": lead_id
            })
            
            # Get recent activity
            recent_activity = self.db.repository_analyses.find({
                "company_id": company_id,
                "lead_id": lead_id,
                "updated_at": {"$gte": datetime.now() - timedelta(days=7)}
            }).count()
            
            # Get unread notifications
            unread_notifications = self.db.notifications.count_documents({
                "company_id": company_id,
                "lead_id": lead_id,
                "read": False
            })
            
            # Get latest reports
            latest_reports = self.db.progress_reports.find({
                "company_id": company_id,
                "lead_id": lead_id
            }).sort("created_at", -1).limit(5)
            
            return {
                "total_repositories": repo_count,
                "recent_activity": recent_activity,
                "unread_notifications": unread_notifications,
                "latest_reports": list(latest_reports)
            }
            
        except Exception as e:
            logger.error(f"Failed to get analytics summary: {str(e)}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
