import os
import git
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
from config import APP_CONFIG

logger = logging.getLogger(__name__)

class RepoAnalyzer:
    """Analyze Git repositories and extract insights"""
    
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.repo = None
        self._commits_cache = None
        
    def clone_or_open_repo(self, repo_url: str) -> bool:
        """Clone repository or open existing one"""
        try:
            if os.path.exists(self.repo_path):
                # Try to open existing repo
                self.repo = git.Repo(self.repo_path)
                # Pull latest changes
                if self.repo.remotes:
                    self.repo.remotes.origin.pull()
            else:
                # Clone new repo
                self.repo = git.Repo.clone_from(repo_url, self.repo_path)
            
            logger.info(f"Repository ready at: {self.repo_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clone/open repository: {e}")
            return False
    
    def get_commits_data(self, max_commits: int = None) -> pd.DataFrame:
        """Extract commit data as DataFrame"""
        if not self.repo:
            return pd.DataFrame()
        
        if max_commits is None:
            max_commits = APP_CONFIG.max_commits_analysis
        
        commits_data = []
        
        try:
            commits = list(self.repo.iter_commits(max_count=max_commits))
            
            for commit in commits:
                # Get file changes
                try:
                    files_changed = commit.stats.files
                    total_insertions = commit.stats.total['insertions']
                    total_deletions = commit.stats.total['deletions']
                except:
                    files_changed = {}
                    total_insertions = 0
                    total_deletions = 0
                
                # Convert timezone-aware datetime to UTC timestamp
                commit_datetime = commit.committed_datetime
                if commit_datetime.tzinfo is not None:
                    # Convert to UTC if timezone-aware
                    commit_datetime = commit_datetime.astimezone(datetime.now().astimezone().tzinfo.utc if hasattr(datetime.now().astimezone().tzinfo, 'utc') else None)
                
                commit_data = {
                    'hash': commit.hexsha[:8],
                    'full_hash': commit.hexsha,
                    'author': commit.author.name,
                    'author_email': commit.author.email,
                    'date': commit_datetime,
                    'message': commit.message.strip(),
                    'files_changed': len(files_changed),
                    'insertions': total_insertions,
                    'deletions': total_deletions,
                    'net_changes': total_insertions - total_deletions
                }
                
                commits_data.append(commit_data)
        
        except Exception as e:
            logger.error(f"Error processing commits: {e}")
        
        df = pd.DataFrame(commits_data)
        if not df.empty:
            # Fix the timezone issue by explicitly setting utc=True
            df['date'] = pd.to_datetime(df['date'], utc=True)
            df = df.sort_values('date', ascending=False)
        
        self._commits_cache = df
        return df
    
    def get_file_analysis(self) -> Dict[str, int]:
        """Analyze file types in repository"""
        if not self.repo:
            return {}
        
        file_counts = {}
        try:
            for root, dirs, files in os.walk(self.repo_path):
                # Skip .git directory
                if '.git' in root:
                    continue
                    
                for file in files:
                    ext = Path(file).suffix.lower()
                    if ext in APP_CONFIG.supported_extensions:
                        file_counts[ext] = file_counts.get(ext, 0) + 1
        
        except Exception as e:
            logger.error(f"Error analyzing files: {e}")
        
        return file_counts
    
    def get_developer_stats(self) -> pd.DataFrame:
        """Get developer contribution statistics"""
        if self._commits_cache is None:
            self.get_commits_data()
        
        if self._commits_cache.empty:
            return pd.DataFrame()
        
        # Group by author
        dev_stats = self._commits_cache.groupby('author').agg({
            'hash': 'count',
            'insertions': 'sum',
            'deletions': 'sum',
            'net_changes': 'sum',
            'files_changed': 'sum',
            'date': ['min', 'max']
        }).round(0)
        
        # Flatten column names
        dev_stats.columns = ['commits', 'insertions', 'deletions', 'net_changes', 
                           'files_modified', 'first_commit', 'last_commit']
        
        # Calculate activity metrics
        dev_stats['activity_days'] = (dev_stats['last_commit'] - dev_stats['first_commit']).dt.days + 1
        dev_stats['avg_changes_per_commit'] = (dev_stats['net_changes'] / dev_stats['commits']).round(1)
        
        return dev_stats.sort_values('commits', ascending=False)
    
    def get_recent_activity(self, days: int = 30) -> Dict[str, any]:
        """Get recent activity summary"""
        if self._commits_cache is None:
            self.get_commits_data()
        
        if self._commits_cache.empty:
            return {}
        
        # Use timezone-aware datetime for comparison
        cutoff_date = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=days)
        recent_commits = self._commits_cache[self._commits_cache['date'] > cutoff_date]
        
        return {
            'total_commits': len(recent_commits),
            'active_developers': recent_commits['author'].nunique(),
            'files_changed': recent_commits['files_changed'].sum(),
            'lines_added': recent_commits['insertions'].sum(),
            'lines_removed': recent_commits['deletions'].sum(),
            'most_active_dev': recent_commits['author'].mode().iloc[0] if not recent_commits.empty else "None"
        }