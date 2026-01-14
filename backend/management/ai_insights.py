import pandas as pd
from typing import Dict, List, Optional
import logging
from ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class AIInsights:
    """Generate AI-powered insights from repository data"""
    
    def __init__(self):
        self.ollama = OllamaClient()
    
    def analyze_commit_patterns(self, commits_df: pd.DataFrame) -> Optional[str]:
        """Analyze commit patterns and generate insights"""
        if commits_df.empty:
            return "No commit data available for analysis."
        
        # Prepare data summary for AI
        total_commits = len(commits_df)
        unique_authors = commits_df['author'].nunique()
        date_range = f"{commits_df['date'].min().date()} to {commits_df['date'].max().date()}"
        
        # Get top contributors
        top_contributors = commits_df['author'].value_counts().head(3)
        
        # Recent activity
        recent_commits = commits_df.head(10)
        recent_messages = "\n".join([f"- {row['author']}: {row['message'][:100]}..." 
                                   for _, row in recent_commits.iterrows()])
        
        prompt = f"""
        Analyze this Git repository activity and provide insights:
        
        Repository Stats:
        - Total commits: {total_commits}
        - Contributors: {unique_authors}
        - Date range: {date_range}
        
        Top Contributors:
        {top_contributors.to_string()}
        
        Recent Commit Messages:
        {recent_messages}
        
        Please provide:
        1. Overall development patterns
        2. Team collaboration insights
        3. Code quality observations from commit messages
        4. Recommendations for the team
        
        Keep the response concise and actionable.
        """
        
        response = self.ollama.generate(prompt, task_type="balanced")
        return response or "Unable to generate insights at this time."
    
    def analyze_developer_work(self, dev_stats: pd.DataFrame, commits_df: pd.DataFrame) -> Dict[str, str]:
        """Analyze what each developer has been working on"""
        insights = {}
        
        if dev_stats.empty or commits_df.empty:
            return {"error": "No data available for developer analysis"}
        
        for developer in dev_stats.head(5).index:  # Top 5 developers
            dev_commits = commits_df[commits_df['author'] == developer].head(10)
            
            if dev_commits.empty:
                continue
            
            commit_messages = "\n".join([f"- {row['message'][:150]}..." 
                                       for _, row in dev_commits.iterrows()])
            
            stats = dev_stats.loc[developer]
            
            prompt = f"""
            Analyze this developer's recent work:
            
            Developer: {developer}
            Stats:
            - Commits: {stats['commits']}
            - Lines added: {stats['insertions']}
            - Lines removed: {stats['deletions']}
            - Files modified: {stats['files_modified']}
            
            Recent commit messages:
            {commit_messages}
            
            Summarize in 2-3 sentences:
            1. What this developer has been working on
            2. Their main contributions/focus areas
            3. Their working style (small frequent commits vs large changes)
            """
            
            response = self.ollama.generate(prompt, task_type="quick")
            insights[developer] = response or f"Analysis unavailable for {developer}"
        
        return insights
    
    def generate_project_summary(self, commits_df: pd.DataFrame, file_analysis: Dict[str, int], 
                                recent_activity: Dict[str, any]) -> Optional[str]:
        """Generate overall project summary"""
        
        # Prepare project overview
        file_types = ", ".join([f"{ext}: {count}" for ext, count in file_analysis.items()])
        
        prompt = f"""
        Create a project summary based on this repository analysis:
        
        Repository Overview:
        - Total commits analyzed: {len(commits_df)}
        - File types: {file_types}
        - Contributors: {commits_df['author'].nunique() if not commits_df.empty else 0}
        
        Recent Activity (30 days):
        - Commits: {recent_activity.get('total_commits', 0)}
        - Active developers: {recent_activity.get('active_developers', 0)}
        - Most active: {recent_activity.get('most_active_dev', 'None')}
        - Lines changed: +{recent_activity.get('lines_added', 0)} -{recent_activity.get('lines_removed', 0)}
        
        Provide a brief executive summary covering:
        1. Project activity level
        2. Team size and engagement
        3. Development velocity
        4. Overall health assessment
        
        Keep it under 200 words and business-focused.
        """
        
        response = self.ollama.generate(prompt, task_type="balanced")
        return response or "Unable to generate project summary."
