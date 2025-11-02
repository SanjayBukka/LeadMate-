"""
Git Service - Real Git Repository Analysis
"""
import os
import subprocess
import shutil
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import git
from git import Repo
import requests
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class GitService:
    def __init__(self, base_dir: str = "repositories"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
    def clone_repository(self, repo_url: str, repo_name: str, company_id: str, lead_id: str) -> Tuple[bool, str]:
        """Clone repository to local storage"""
        try:
            # Create company/lead specific directory
            repo_dir = self.base_dir / company_id / lead_id / repo_name
            repo_dir.mkdir(parents=True, exist_ok=True)
            
            # Remove existing directory if it exists
            if repo_dir.exists():
                shutil.rmtree(repo_dir)
            
            # Clone repository
            repo = Repo.clone_from(repo_url, repo_dir)
            
            logger.info(f"Successfully cloned {repo_url} to {repo_dir}")
            return True, str(repo_dir)
            
        except Exception as e:
            logger.error(f"Failed to clone repository {repo_url}: {str(e)}")
            return False, str(e)
    
    def get_repository_info(self, repo_path: str) -> Dict:
        """Get basic repository information"""
        try:
            repo = Repo(repo_path)
            
            # Get remote URL
            remote_url = ""
            if repo.remotes.origin:
                remote_url = repo.remotes.origin.url
            
            return {
                "name": os.path.basename(repo_path),
                "remote_url": remote_url,
                "branch": repo.active_branch.name,
                "last_commit": repo.head.commit.hexsha[:8],
                "last_commit_date": repo.head.commit.committed_datetime.isoformat(),
                "total_commits": len(list(repo.iter_commits())),
                "total_branches": len(repo.branches),
                "is_dirty": repo.is_dirty()
            }
        except Exception as e:
            logger.error(f"Failed to get repository info: {str(e)}")
            return {}
    
    def analyze_commits(self, repo_path: str, max_commits: int = 100) -> pd.DataFrame:
        """Analyze commit history and return DataFrame"""
        try:
            repo = Repo(repo_path)
            commits_data = []
            
            # Get commits
            commits = list(repo.iter_commits(max_count=max_commits))
            
            for commit in commits:
                # Get commit stats
                stats = commit.stats
                
                commits_data.append({
                    'hash': commit.hexsha[:8],
                    'author': commit.author.name,
                    'email': commit.author.email,
                    'message': commit.message.strip(),
                    'date': commit.committed_datetime,
                    'files_changed': stats.total['files'],
                    'insertions': stats.total['insertions'],
                    'deletions': stats.total['deletions'],
                    'lines_changed': stats.total['lines']
                })
            
            df = pd.DataFrame(commits_data)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date', ascending=False)
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to analyze commits: {str(e)}")
            return pd.DataFrame()
    
    def analyze_file_types(self, repo_path: str) -> Dict[str, int]:
        """Analyze file types in repository"""
        try:
            repo = Repo(repo_path)
            file_types = {}
            
            # Get all files in the repository
            for item in repo.tree().traverse():
                if item.type == 'blob':  # It's a file
                    file_ext = os.path.splitext(item.name)[1].lower()
                    if file_ext:
                        file_types[file_ext] = file_types.get(file_ext, 0) + 1
            
            return file_types
            
        except Exception as e:
            logger.error(f"Failed to analyze file types: {str(e)}")
            return {}
    
    def get_developer_stats(self, commits_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate developer statistics from commits"""
        if commits_df.empty:
            return pd.DataFrame()
        
        try:
            # Group by author and calculate stats
            dev_stats = commits_df.groupby('author').agg({
                'hash': 'count',
                'insertions': 'sum',
                'deletions': 'sum',
                'files_changed': 'sum',
                'date': ['min', 'max', 'nunique']
            }).round(2)
            
            # Flatten column names
            dev_stats.columns = ['commits', 'total_insertions', 'total_deletions', 
                               'files_modified', 'first_commit', 'last_commit', 'activity_days']
            
            # Calculate additional metrics
            dev_stats['avg_changes_per_commit'] = (dev_stats['total_insertions'] + dev_stats['total_deletions']) / dev_stats['commits']
            dev_stats['net_lines'] = dev_stats['total_insertions'] - dev_stats['total_deletions']
            
            # Sort by commits
            dev_stats = dev_stats.sort_values('commits', ascending=False)
            
            return dev_stats
            
        except Exception as e:
            logger.error(f"Failed to calculate developer stats: {str(e)}")
            return pd.DataFrame()
    
    def get_recent_activity(self, commits_df: pd.DataFrame, days: int = 30) -> Dict:
        """Get recent activity summary"""
        if commits_df.empty:
            return {}
        
        try:
            # Filter recent commits
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_commits = commits_df[commits_df['date'] > cutoff_date]
            
            if recent_commits.empty:
                return {
                    'total_commits': 0,
                    'active_developers': 0,
                    'files_changed': 0,
                    'lines_added': 0,
                    'lines_removed': 0,
                    'most_active_dev': 'None'
                }
            
            # Calculate metrics
            total_commits = len(recent_commits)
            active_developers = recent_commits['author'].nunique()
            files_changed = recent_commits['files_changed'].sum()
            lines_added = recent_commits['insertions'].sum()
            lines_removed = recent_commits['deletions'].sum()
            
            # Most active developer
            dev_commits = recent_commits['author'].value_counts()
            most_active_dev = dev_commits.index[0] if not dev_commits.empty else 'None'
            
            return {
                'total_commits': int(total_commits),
                'active_developers': int(active_developers),
                'files_changed': int(files_changed),
                'lines_added': int(lines_added),
                'lines_removed': int(lines_removed),
                'most_active_dev': most_active_dev
            }
            
        except Exception as e:
            logger.error(f"Failed to get recent activity: {str(e)}")
            return {}
    
    def get_commit_patterns(self, commits_df: pd.DataFrame) -> Dict:
        """Analyze commit patterns and trends"""
        if commits_df.empty:
            return {}
        
        try:
            # Daily commit patterns
            commits_df['date_only'] = commits_df['date'].dt.date
            daily_commits = commits_df.groupby('date_only').size()
            
            # Weekly patterns
            commits_df['weekday'] = commits_df['date'].dt.day_name()
            weekly_pattern = commits_df['weekday'].value_counts()
            
            # Hourly patterns
            commits_df['hour'] = commits_df['date'].dt.hour
            hourly_pattern = commits_df['hour'].value_counts()
            
            # Message analysis
            messages = commits_df['message'].str.lower()
            feat_commits = messages.str.contains('feat|feature|add|new').sum()
            fix_commits = messages.str.contains('fix|bug|error|issue').sum()
            refactor_commits = messages.str.contains('refactor|clean|improve').sum()
            
            return {
                'daily_commits': daily_commits.to_dict(),
                'weekly_pattern': weekly_pattern.to_dict(),
                'hourly_pattern': hourly_pattern.to_dict(),
                'commit_types': {
                    'features': int(feat_commits),
                    'fixes': int(fix_commits),
                    'refactors': int(refactor_commits)
                },
                'avg_commits_per_day': float(daily_commits.mean()) if not daily_commits.empty else 0,
                'most_active_day': weekly_pattern.index[0] if not weekly_pattern.empty else 'Monday',
                'most_active_hour': int(hourly_pattern.index[0]) if not hourly_pattern.empty else 9
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze commit patterns: {str(e)}")
            return {}
    
    def cleanup_repository(self, repo_path: str) -> bool:
        """Clean up repository directory"""
        try:
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
                logger.info(f"Cleaned up repository: {repo_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to cleanup repository: {str(e)}")
            return False
