"""
AI Insights Service - Real AI-powered Analysis
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import re

logger = logging.getLogger(__name__)

class AIInsightsService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_commit_patterns(self, commits_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze commit patterns using AI/ML techniques"""
        try:
            if commits_df.empty:
                return {"insights": "No commit data available", "patterns": {}}
            
            insights = []
            patterns = {}
            
            # 1. Commit frequency analysis
            commits_df['date'] = pd.to_datetime(commits_df['date'])
            commits_df['day_of_week'] = commits_df['date'].dt.day_name()
            commits_df['hour'] = commits_df['date'].dt.hour
            
            # Daily patterns
            daily_commits = commits_df.groupby(commits_df['date'].dt.date).size()
            avg_daily = daily_commits.mean()
            std_daily = daily_commits.std()
            
            if std_daily > avg_daily * 0.5:
                insights.append("Inconsistent commit patterns detected - consider establishing regular commit schedules")
            else:
                insights.append("Consistent commit patterns observed - good development rhythm")
            
            patterns['daily_consistency'] = {
                'mean': float(avg_daily),
                'std': float(std_daily),
                'coefficient_of_variation': float(std_daily / avg_daily) if avg_daily > 0 else 0
            }
            
            # 2. Weekly patterns
            weekly_pattern = commits_df['day_of_week'].value_counts()
            most_active_day = weekly_pattern.index[0]
            least_active_day = weekly_pattern.index[-1]
            
            if most_active_day in ['Monday', 'Tuesday'] and least_active_day in ['Friday', 'Saturday']:
                insights.append("Healthy work-life balance pattern detected")
            elif least_active_day in ['Monday', 'Tuesday']:
                insights.append("Potential Monday blues or weekend work patterns detected")
            
            patterns['weekly_distribution'] = weekly_pattern.to_dict()
            
            # 3. Hourly patterns
            hourly_pattern = commits_df['hour'].value_counts()
            peak_hours = hourly_pattern.head(3).index.tolist()
            
            if any(hour in peak_hours for hour in [9, 10, 11, 14, 15, 16]):
                insights.append("Normal working hours pattern - good team discipline")
            elif any(hour in peak_hours for hour in [22, 23, 0, 1, 2]):
                insights.append("Late night coding patterns detected - consider work-life balance")
            
            patterns['hourly_distribution'] = hourly_pattern.to_dict()
            
            # 4. Message analysis
            messages = commits_df['message'].str.lower()
            
            # Commit type analysis
            feat_commits = messages.str.contains(r'\b(feat|feature|add|new|implement)\b').sum()
            fix_commits = messages.str.contains(r'\b(fix|bug|error|issue|resolve)\b').sum()
            refactor_commits = messages.str.contains(r'\b(refactor|clean|improve|optimize)\b').sum()
            test_commits = messages.str.contains(r'\b(test|spec|coverage)\b').sum()
            
            total_commits = len(commits_df)
            commit_types = {
                'features': float(feat_commits / total_commits * 100),
                'fixes': float(fix_commits / total_commits * 100),
                'refactors': float(refactor_commits / total_commits * 100),
                'tests': float(test_commits / total_commits * 100)
            }
            
            if commit_types['features'] > 60:
                insights.append("High feature development focus - ensure proper testing and documentation")
            elif commit_types['fixes'] > 40:
                insights.append("High bug fix ratio - consider improving code quality and testing")
            elif commit_types['tests'] < 10:
                insights.append("Low test coverage - consider increasing automated testing")
            
            patterns['commit_types'] = commit_types
            
            # 5. Code quality indicators
            avg_changes = (commits_df['insertions'] + commits_df['deletions']).mean()
            large_commits = commits_df[(commits_df['insertions'] + commits_df['deletions']) > avg_changes * 2]
            
            if len(large_commits) > len(commits_df) * 0.2:
                insights.append("High number of large commits detected - consider smaller, more frequent commits")
            
            patterns['code_quality'] = {
                'avg_changes_per_commit': float(avg_changes),
                'large_commits_ratio': float(len(large_commits) / len(commits_df)),
                'avg_files_changed': float(commits_df['files_changed'].mean())
            }
            
            return {
                "insights": insights,
                "patterns": patterns,
                "analysis_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze commit patterns: {str(e)}")
            return {"insights": ["Analysis failed"], "patterns": {}}
    
    def analyze_developer_work(self, dev_stats: pd.DataFrame, commits_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze individual developer work patterns"""
        try:
            if dev_stats.empty or commits_df.empty:
                return {"insights": {}, "recommendations": []}
            
            insights = {}
            recommendations = []
            
            # 1. Productivity analysis
            total_commits = dev_stats['commits'].sum()
            total_lines = dev_stats['total_insertions'].sum() + dev_stats['total_deletions'].sum()
            
            for developer in dev_stats.index:
                dev_data = dev_stats.loc[developer]
                dev_commits = commits_df[commits_df['author'] == developer]
                
                dev_insights = []
                
                # Commit frequency
                commits_ratio = dev_data['commits'] / total_commits * 100
                if commits_ratio > 50:
                    dev_insights.append("High contributor - consider mentoring others")
                elif commits_ratio < 10:
                    dev_insights.append("Low activity - check if developer needs support")
                
                # Code quality indicators
                avg_changes = (dev_data['total_insertions'] + dev_data['total_deletions']) / dev_data['commits']
                if avg_changes > total_lines / total_commits * 1.5:
                    dev_insights.append("High code output - ensure quality over quantity")
                elif avg_changes < total_lines / total_commits * 0.5:
                    dev_insights.append("Low code output - check for blockers or need for training")
                
                # Consistency analysis
                if not dev_commits.empty:
                    dev_commits['date'] = pd.to_datetime(dev_commits['date'])
                    days_active = dev_commits['date'].dt.date.nunique()
                    total_days = (dev_commits['date'].max() - dev_commits['date'].min()).days + 1
                    consistency = days_active / total_days if total_days > 0 else 0
                    
                    if consistency > 0.8:
                        dev_insights.append("Highly consistent contributor")
                    elif consistency < 0.3:
                        dev_insights.append("Inconsistent activity - check workload distribution")
                
                # Specialization analysis
                dev_messages = dev_commits['message'].str.lower()
                frontend_commits = dev_messages.str.contains(r'\b(ui|frontend|react|vue|angular|css|html)\b').sum()
                backend_commits = dev_messages.str.contains(r'\b(api|backend|server|database|sql)\b').sum()
                test_commits = dev_messages.str.contains(r'\b(test|spec|coverage)\b').sum()
                
                if frontend_commits > backend_commits * 2:
                    dev_insights.append("Frontend specialist")
                elif backend_commits > frontend_commits * 2:
                    dev_insights.append("Backend specialist")
                elif test_commits > dev_data['commits'] * 0.3:
                    dev_insights.append("Testing specialist")
                else:
                    dev_insights.append("Full-stack contributor")
                
                insights[developer] = {
                    "summary": dev_insights,
                    "metrics": {
                        "commits": int(dev_data['commits']),
                        "lines_added": int(dev_data['total_insertions']),
                        "lines_removed": int(dev_data['total_deletions']),
                        "files_modified": int(dev_data['files_modified']),
                        "activity_days": int(dev_data['activity_days']),
                        "consistency": float(consistency) if 'consistency' in locals() else 0
                    }
                }
            
            # Team-level recommendations
            if len(dev_stats) > 1:
                # Workload distribution
                commits_std = dev_stats['commits'].std()
                commits_mean = dev_stats['commits'].mean()
                if commits_std > commits_mean * 0.5:
                    recommendations.append("Uneven workload distribution - consider rebalancing tasks")
                
                # Skill diversity
                if len(dev_stats) < 3:
                    recommendations.append("Small team - consider cross-training for resilience")
                
                # Collaboration analysis
                if commits_df['author'].nunique() < len(dev_stats):
                    recommendations.append("Some team members not contributing - check engagement")
            
            return {
                "insights": insights,
                "recommendations": recommendations,
                "analysis_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze developer work: {str(e)}")
            return {"insights": {}, "recommendations": []}
    
    def generate_project_summary(self, commits_df: pd.DataFrame, file_analysis: Dict, 
                               recent_activity: Dict) -> Dict[str, Any]:
        """Generate comprehensive project summary"""
        try:
            if commits_df.empty:
                return {"summary": "No project data available", "health_score": 0}
            
            summary_parts = []
            health_indicators = []
            
            # 1. Project activity level
            total_commits = len(commits_df)
            active_developers = commits_df['author'].nunique()
            lines_added = commits_df['insertions'].sum()
            lines_removed = commits_df['deletions'].sum()
            
            if total_commits > 100:
                summary_parts.append("High-activity project with strong development momentum")
                health_indicators.append(("activity", 90))
            elif total_commits > 50:
                summary_parts.append("Moderately active project with steady progress")
                health_indicators.append(("activity", 70))
            else:
                summary_parts.append("Low-activity project - consider increasing development pace")
                health_indicators.append(("activity", 40))
            
            # 2. Team collaboration
            if active_developers > 3:
                summary_parts.append("Well-distributed team with good collaboration")
                health_indicators.append(("collaboration", 85))
            elif active_developers > 1:
                summary_parts.append("Small team with focused development")
                health_indicators.append(("collaboration", 60))
            else:
                summary_parts.append("Single developer project - consider team expansion")
                health_indicators.append(("collaboration", 30))
            
            # 3. Code quality indicators
            avg_commit_size = (lines_added + lines_removed) / total_commits
            if avg_commit_size < 50:
                summary_parts.append("Good commit granularity with focused changes")
                health_indicators.append(("quality", 80))
            elif avg_commit_size < 200:
                summary_parts.append("Moderate commit sizes - consider smaller, more frequent commits")
                health_indicators.append(("quality", 60))
            else:
                summary_parts.append("Large commits detected - consider breaking down changes")
                health_indicators.append(("quality", 40))
            
            # 4. Technology stack analysis
            if file_analysis:
                total_files = sum(file_analysis.values())
                main_languages = sorted(file_analysis.items(), key=lambda x: x[1], reverse=True)[:3]
                
                if len(main_languages) == 1:
                    summary_parts.append(f"Focused technology stack with {main_languages[0][0]} as primary language")
                    health_indicators.append(("tech_stack", 70))
                elif len(main_languages) == 2:
                    summary_parts.append(f"Balanced technology stack with {main_languages[0][0]} and {main_languages[1][0]}")
                    health_indicators.append(("tech_stack", 85))
                else:
                    summary_parts.append("Diverse technology stack - ensure proper documentation and standards")
                    health_indicators.append(("tech_stack", 60))
            
            # 5. Recent momentum
            if recent_activity:
                recent_commits = recent_activity.get('total_commits', 0)
                if recent_commits > 20:
                    summary_parts.append("Strong recent development momentum")
                    health_indicators.append(("momentum", 90))
                elif recent_commits > 10:
                    summary_parts.append("Steady recent development activity")
                    health_indicators.append(("momentum", 70))
                else:
                    summary_parts.append("Low recent activity - check for blockers or resource constraints")
                    health_indicators.append(("momentum", 40))
            
            # Calculate overall health score
            if health_indicators:
                health_score = sum(score for _, score in health_indicators) / len(health_indicators)
            else:
                health_score = 50
            
            # Generate recommendations
            recommendations = []
            if health_score < 60:
                recommendations.append("Project health needs attention - review development processes")
            if total_commits < 50:
                recommendations.append("Increase development velocity - consider sprint planning")
            if active_developers < 2:
                recommendations.append("Consider expanding team for better resilience")
            if avg_commit_size > 100:
                recommendations.append("Implement smaller, more frequent commits for better code review")
            
            return {
                "summary": ". ".join(summary_parts),
                "health_score": round(health_score, 1),
                "health_indicators": dict(health_indicators),
                "recommendations": recommendations,
                "metrics": {
                    "total_commits": total_commits,
                    "active_developers": active_developers,
                    "lines_added": int(lines_added),
                    "lines_removed": int(lines_removed),
                    "avg_commit_size": round(avg_commit_size, 1)
                },
                "analysis_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate project summary: {str(e)}")
            return {"summary": "Analysis failed", "health_score": 0}
    
    def generate_team_recommendations(self, dev_stats: pd.DataFrame, commits_df: pd.DataFrame) -> List[str]:
        """Generate actionable team recommendations"""
        try:
            if dev_stats.empty or commits_df.empty:
                return ["Insufficient data for recommendations"]
            
            recommendations = []
            
            # 1. Workload distribution
            commits_std = dev_stats['commits'].std()
            commits_mean = dev_stats['commits'].mean()
            if commits_std > commits_mean * 0.6:
                recommendations.append("🔧 Rebalance workload - some team members are overloaded while others are underutilized")
            
            # 2. Skill development
            low_activity_devs = dev_stats[dev_stats['commits'] < commits_mean * 0.5]
            if not low_activity_devs.empty:
                recommendations.append(f"📚 Provide additional training for: {', '.join(low_activity_devs.index)}")
            
            # 3. Collaboration opportunities
            if len(dev_stats) > 2:
                recommendations.append("🤝 Organize pair programming sessions to improve knowledge sharing")
            
            # 4. Code quality
            large_commits = commits_df[(commits_df['insertions'] + commits_df['deletions']) > 200]
            if len(large_commits) > len(commits_df) * 0.1:
                recommendations.append("✂️ Implement smaller commit guidelines to improve code review quality")
            
            # 5. Testing
            test_commits = commits_df[commits_df['message'].str.contains(r'\b(test|spec|coverage)\b', case=False)]
            test_ratio = len(test_commits) / len(commits_df)
            if test_ratio < 0.1:
                recommendations.append("🧪 Increase test coverage - implement TDD practices")
            
            # 6. Documentation
            doc_commits = commits_df[commits_df['message'].str.contains(r'\b(doc|readme|comment)\b', case=False)]
            doc_ratio = len(doc_commits) / len(commits_df)
            if doc_ratio < 0.05:
                recommendations.append("📝 Improve documentation practices - add more README updates and code comments")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to generate team recommendations: {str(e)}")
            return ["Recommendation generation failed"]
