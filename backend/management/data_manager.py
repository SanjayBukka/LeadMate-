import pandas as pd
import os
import logging
from pathlib import Path
import importlib.util

# Import config from the same directory (managemnet)
# to avoid conflicts with backend/config.py
_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.py')
_spec = importlib.util.spec_from_file_location("managemnet_config", _config_file)
_config_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_config_module)
APP_CONFIG = _config_module.APP_CONFIG

from typing import List


logger = logging.getLogger(__name__)

class DataManager:
    """Handle data persistence and caching"""
    
    def __init__(self):
        self.data_dir = Path(APP_CONFIG.data_dir)
        self.data_dir.mkdir(exist_ok=True)
    
    def save_analysis_data(self, repo_name: str, commits_df: pd.DataFrame, 
                          dev_stats: pd.DataFrame, file_analysis: dict) -> bool:
        """Save analysis results to CSV files"""
        try:
            repo_dir = self.data_dir / repo_name
            repo_dir.mkdir(exist_ok=True)
            
            # Save commits data
            if not commits_df.empty:
                commits_df.to_csv(repo_dir / "commits.csv", index=False)
            
            # Save developer stats
            if not dev_stats.empty:
                dev_stats.to_csv(repo_dir / "developer_stats.csv")
            
            # Save file analysis
            if file_analysis:
                file_df = pd.DataFrame(list(file_analysis.items()), 
                                     columns=['file_type', 'count'])
                file_df.to_csv(repo_dir / "file_analysis.csv", index=False)
            
            logger.info(f"Analysis data saved for {repo_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save analysis data: {e}")
            return False
    
    def load_analysis_data(self, repo_name: str) -> tuple:
        """Load analysis results from CSV files"""
        try:
            repo_dir = self.data_dir / repo_name
            
            commits_df = pd.DataFrame()
            dev_stats = pd.DataFrame()
            file_analysis = {}
            
            # Load commits data
            commits_file = repo_dir / "commits.csv"
            if commits_file.exists():
                commits_df = pd.read_csv(commits_file)
                # Fix timezone issue when loading from CSV
                if 'date' in commits_df.columns and not commits_df.empty:
                    commits_df['date'] = pd.to_datetime(commits_df['date'], utc=True)
            
            # Load developer stats
            dev_stats_file = repo_dir / "developer_stats.csv"
            if dev_stats_file.exists():
                dev_stats = pd.read_csv(dev_stats_file, index_col=0)
                # Fix timezone issue for datetime columns in dev_stats
                if 'first_commit' in dev_stats.columns:
                    dev_stats['first_commit'] = pd.to_datetime(dev_stats['first_commit'], utc=True)
                if 'last_commit' in dev_stats.columns:
                    dev_stats['last_commit'] = pd.to_datetime(dev_stats['last_commit'], utc=True)
            
            # Load file analysis
            file_analysis_file = repo_dir / "file_analysis.csv"
            if file_analysis_file.exists():
                file_df = pd.read_csv(file_analysis_file)
                file_analysis = dict(zip(file_df['file_type'], file_df['count']))
            
            return commits_df, dev_stats, file_analysis
            
        except Exception as e:
            logger.error(f"Failed to load analysis data: {e}")
            return pd.DataFrame(), pd.DataFrame(), {}
    
    def get_cached_repos(self) -> List[str]:
        """Get list of cached repository analyses"""
        try:
            return [d.name for d in self.data_dir.iterdir() if d.is_dir()]
        except:
            return []