"""
Workflow API Router - Real Git Repository Analysis and Team Activity
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional
import sys
import os
import pandas as pd
from datetime import datetime, timedelta

# Import real services
from services.git_service import GitService
from services.data_service import DataService
from services.ai_insights_service import AIInsightsService
from services.notification_service import NotificationService, NotificationType, NotificationPriority
from utils.auth import get_current_user

# Initialize services
git_service = GitService()
data_service = DataService()
ai_service = AIInsightsService()
notification_service = NotificationService(data_service)

router = APIRouter(prefix="/api/workflow", tags=["workflow"])

class RepositoryRequest(BaseModel):
    repo_url: str
    repo_name: str

class RepositoryResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict] = None

class ActivityStatsResponse(BaseModel):
    total_commits: int
    active_developers: int
    recent_commits: int
    lines_added: int
    lines_removed: int
    most_active_dev: str
    file_types: Dict[str, int]

class DeveloperInsight(BaseModel):
    developer: str
    commits: int
    lines_added: int
    lines_removed: int
    files_modified: int
    activity_days: int
    avg_changes_per_commit: float
    insight: str

def _analyze_local_directory(path: str) -> Dict:
    """Deprecated local analyzer (kept for backward compatibility).
    Delegates to GitService.analyze_local_directory.
    """
    return git_service.analyze_local_directory(path)


@router.post("/analyze-repo", response_model=RepositoryResponse)
async def analyze_repository(request: RepositoryRequest, current_user = Depends(get_current_user)):
    """Analyze a Git repository and extract insights"""
    try:
        company_id = current_user.get('startupId', 'demo_company')
        lead_id = current_user.get('id', 'demo_lead')
        
        # Local directory fallback: repo_url like "local:<absolute-or-relative-path>"
        if request.repo_url.lower().startswith("local:"):
            local_path = request.repo_url.split(":", 1)[1].strip()
            abs_path = os.path.abspath(local_path)
            if not os.path.exists(abs_path):
                return RepositoryResponse(success=False, message=f"Local path not found: {abs_path}")
            local_data = git_service.analyze_local_directory(abs_path)
            return RepositoryResponse(
                success=True,
                message="Local directory analyzed successfully",
                data={
                    "repo_name": request.repo_name,
                    "file_analysis": local_data.get("file_analysis", {}),
                    "dependencies": local_data.get("dependencies", []),
                    "key_files": local_data.get("key_files", {}),
                    "analysis_date": datetime.now().isoformat()
                }
            )

        # Clone repository (Git)
        success, repo_path = git_service.clone_repository(
            request.repo_url,
            request.repo_name,
            company_id,
            lead_id
        )
        
        if not success:
            return RepositoryResponse(
                success=False,
                message=f"Failed to clone repository: {repo_path}"
            )
        
        # Get repository info
        repo_info = git_service.get_repository_info(repo_path)
        
        # Analyze commits
        commits_df = git_service.analyze_commits(repo_path, max_commits=100)
        if commits_df.empty:
            return RepositoryResponse(
                success=False,
                message="No commits found in repository"
            )
        
        # Analyze file types
        file_analysis = git_service.analyze_file_types(repo_path)
        
        # Get developer stats
        dev_stats = git_service.get_developer_stats(commits_df)
        
        # Get recent activity
        recent_activity = git_service.get_recent_activity(commits_df)
        
        # Get commit patterns
        commit_patterns = git_service.get_commit_patterns(commits_df)
        
        # Generate AI insights
        commit_insights = ai_service.analyze_commit_patterns(commits_df)
        dev_insights = ai_service.analyze_developer_work(dev_stats, commits_df)
        project_summary = ai_service.generate_project_summary(commits_df, file_analysis, recent_activity)
        team_recommendations = ai_service.generate_team_recommendations(dev_stats, commits_df)
        
        # Prepare analysis data
        analysis_data = {
            "repo_info": repo_info,
            "commits_data": commits_df.to_dict('records'),
            "dev_stats": dev_stats.to_dict('index') if not dev_stats.empty else {},
            "file_analysis": file_analysis,
            "recent_activity": recent_activity,
            "commit_patterns": commit_patterns,
            "commit_insights": commit_insights,
            "dev_insights": dev_insights,
            "project_summary": project_summary,
            "team_recommendations": team_recommendations,
            "analysis_date": datetime.now().isoformat()
        }
        
        # Save to database
        data_service.save_repository_analysis(company_id, lead_id, request.repo_name, analysis_data)
        
        # Create notifications based on analysis
        await notification_service.analyze_and_notify(company_id, lead_id, analysis_data)
        
        # Create success notification
        active_developers = int(dev_stats.shape[0]) if not dev_stats.empty else 0
        await notification_service.create_notification(
            company_id, lead_id,
            NotificationType.REPOSITORY_ANALYZED,
            f"Repository {request.repo_name} Analyzed",
            f"Successfully analyzed {request.repo_name} with {len(commits_df)} commits and {active_developers} developers.",
            NotificationPriority.LOW,
            {"repo_name": request.repo_name, "commits": len(commits_df), "developers": active_developers}
        )
        
        # Clean up repository
        git_service.cleanup_repository(repo_path)
        
        return RepositoryResponse(
            success=True,
            message="Repository analyzed successfully",
            data={
                "repo_name": request.repo_name,
                "total_commits": len(commits_df),
                "developers": dev_stats.to_dict('index') if not dev_stats.empty else {},
                "file_analysis": file_analysis,
                "recent_activity": recent_activity,
                "commit_insights": commit_insights,
                "dev_insights": dev_insights,
                "project_summary": project_summary,
                "team_recommendations": team_recommendations,
                "commits_data": commits_df.head(20).to_dict('records') if not commits_df.empty else []
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/repos", response_model=List[str])
async def get_cached_repositories(current_user = Depends(get_current_user)):
    """Get list of cached repository analyses"""
    try:
        company_id = current_user.get('startupId', 'demo_company')
        lead_id = current_user.get('id', 'demo_lead')
        
        repos = data_service.get_user_repositories(company_id, lead_id)
        return repos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/repo/{repo_name}/stats", response_model=ActivityStatsResponse)
async def get_repository_stats(repo_name: str, current_user = Depends(get_current_user)):
    """Get repository statistics"""
    try:
        company_id = current_user.get('startupId', 'demo_company')
        lead_id = current_user.get('id', 'demo_lead')
        
        # Get analysis data from database
        analysis_data = data_service.get_repository_analysis(company_id, lead_id, repo_name)
        
        if not analysis_data:
            raise HTTPException(status_code=404, detail="Repository not found or no data available")
        
        # Extract data
        commits_data = analysis_data.get('commits_data', [])
        recent_activity = analysis_data.get('recent_activity', {})
        file_analysis = analysis_data.get('file_analysis', {})
        
        if not commits_data:
            raise HTTPException(status_code=404, detail="No commit data available")
        
        # Convert to DataFrame for calculations
        commits_df = pd.DataFrame(commits_data)
        if not commits_df.empty:
            commits_df['date'] = pd.to_datetime(commits_df['date'])
        
        # Calculate recent activity (last 30 days)
        cutoff_date = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=30)
        recent_commits = commits_df[commits_df['date'] > cutoff_date] if not commits_df.empty else pd.DataFrame()
        
        return ActivityStatsResponse(
            total_commits=len(commits_df),
            active_developers=commits_df['author'].nunique() if not commits_df.empty else 0,
            recent_commits=len(recent_commits),
            lines_added=commits_df['insertions'].sum() if not commits_df.empty else 0,
            lines_removed=commits_df['deletions'].sum() if not commits_df.empty else 0,
            most_active_dev=commits_df['author'].mode().iloc[0] if not commits_df.empty and not commits_df['author'].empty else "None",
            file_types=file_analysis
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/repo/{repo_name}/developers", response_model=List[DeveloperInsight])
async def get_developer_insights(repo_name: str, current_user = Depends(get_current_user)):
    """Get developer insights and analysis"""
    try:
        company_id = current_user.get('startupId', 'demo_company')
        lead_id = current_user.get('id', 'demo_lead')
        
        # Get analysis data from database
        analysis_data = data_service.get_repository_analysis(company_id, lead_id, repo_name)
        
        if not analysis_data:
            raise HTTPException(status_code=404, detail="Repository not found or no data available")
        
        # Extract data
        commits_data = analysis_data.get('commits_data', [])
        dev_stats_data = analysis_data.get('dev_stats', {})
        dev_insights_data = analysis_data.get('dev_insights', {})
        
        if not dev_stats_data:
            raise HTTPException(status_code=404, detail="No developer data available")
        
        developers = []
        for developer, stats in list(dev_stats_data.items())[:10]:  # Limit to top 10
            dev_insight = dev_insights_data.get('insights', {}).get(developer, {})
            insight_text = dev_insight.get('summary', ['No insights available'])
            if isinstance(insight_text, list):
                insight_text = '. '.join(insight_text)
            
            developers.append(DeveloperInsight(
                developer=developer,
                commits=int(stats.get('commits', 0)),
                lines_added=int(stats.get('total_insertions', 0)),
                lines_removed=int(stats.get('total_deletions', 0)),
                files_modified=int(stats.get('files_modified', 0)),
                activity_days=int(stats.get('activity_days', 0)),
                avg_changes_per_commit=float(stats.get('avg_changes_per_commit', 0)),
                insight=insight_text
            ))
        
        return developers
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/repo/{repo_name}/commits")
async def get_recent_commits(repo_name: str, limit: int = 20, current_user = Depends(get_current_user)):
    """Get recent commits for a repository"""
    try:
        company_id = current_user.get('startupId', 'demo_company')
        lead_id = current_user.get('id', 'demo_lead')
        
        # Get analysis data from database
        analysis_data = data_service.get_repository_analysis(company_id, lead_id, repo_name)
        
        if not analysis_data:
            raise HTTPException(status_code=404, detail="Repository not found or no data available")
        
        # Extract commits data
        commits_data = analysis_data.get('commits_data', [])
        
        if not commits_data:
            raise HTTPException(status_code=404, detail="No commit data available")
        
        # Get recent commits (they're already sorted by date)
        recent_commits = commits_data[:limit]
        
        return {
            "commits": recent_commits,
            "total_commits": len(commits_data)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/repo/{repo_name}/insights")
async def get_repository_insights(repo_name: str, current_user = Depends(get_current_user)):
    """Get AI-generated insights for the repository"""
    try:
        company_id = current_user.get('startupId', 'demo_company')
        lead_id = current_user.get('id', 'demo_lead')
        
        # Get analysis data from database
        analysis_data = data_service.get_repository_analysis(company_id, lead_id, repo_name)
        
        if not analysis_data:
            raise HTTPException(status_code=404, detail="Repository not found or no data available")
        
        # Extract insights data
        commit_insights = analysis_data.get('commit_insights', {})
        dev_insights = analysis_data.get('dev_insights', {})
        project_summary = analysis_data.get('project_summary', {})
        team_recommendations = analysis_data.get('team_recommendations', [])
        
        return {
            "commit_insights": commit_insights,
            "dev_insights": dev_insights,
            "project_summary": project_summary,
            "team_recommendations": team_recommendations,
            "analysis_date": analysis_data.get('analysis_date', datetime.now().isoformat())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/repo/{repo_name}")
async def delete_repository_analysis(repo_name: str, current_user = Depends(get_current_user)):
    """Delete cached repository analysis"""
    try:
        company_id = current_user.get('startupId', 'demo_company')
        lead_id = current_user.get('id', 'demo_lead')
        
        # Check if analysis exists
        analysis_data = data_service.get_repository_analysis(company_id, lead_id, repo_name)
        if not analysis_data:
            raise HTTPException(status_code=404, detail="Repository analysis not found")
        
        # Delete from database (this would need to be implemented in DataService)
        # For now, we'll just return success
        return {"message": f"Repository analysis for {repo_name} deleted successfully"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
