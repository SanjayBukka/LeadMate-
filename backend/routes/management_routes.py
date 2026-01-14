"""
Management routes (workflow-style) for compatibility with existing frontend calls.
This router analyzes git repositories, caches results, and exposes stats/devs/commits/insights.
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import os

from management.repo_analyzer import RepoAnalyzer
from management.ai_insights import AIInsights
from management.data_manager import DataManager
from management.ollama_client import OllamaClient
from management.config import APP_CONFIG
from routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workflow", tags=["Management (Legacy)"])

ollama = OllamaClient()
ai_insights = AIInsights()
data_manager = DataManager()

# Simple in-memory status tracker for background jobs
analysis_status: Dict[str, Dict[str, Any]] = {}

class AnalyzeRequest(BaseModel):
    repo_url: str
    repo_name: str
    max_commits: int = 100

def run_analysis(repo_name: str, repo_url: str, max_commits: int):
    """Background task for repository analysis"""
    try:
        analysis_status[repo_name] = {"status": "processing", "start_time": datetime.now().isoformat()}
        
        # Determine target path
        if repo_url.startswith("local:"):
            repo_path = repo_url.replace("local:", "").strip()
            is_local = True
        else:
            repo_path = os.path.join(APP_CONFIG.repos_dir, repo_name)
            is_local = False

        analyzer = RepoAnalyzer(repo_path)
        if not is_local:
            # Use allowlist check
            allowed_domains = os.getenv("ALLOWED_REPO_DOMAINS", "github.com,gitlab.com").split(",")
            if not any(domain in repo_url for domain in allowed_domains):
                analysis_status[repo_name] = {"status": "failed", "message": "Repository domain not allowed"}
                return

            if not analyzer.clone_or_open_repo(repo_url, depth=1):
                analysis_status[repo_name] = {"status": "failed", "message": "Failed to clone repository"}
                return
        else:
            try:
                import git
                analyzer.repo = git.Repo(repo_path)
            except Exception as e:
                analysis_status[repo_name] = {"status": "failed", "message": f"Failed to open local repository: {e}"}
                return

        commits_df = analyzer.get_commits_data(max_commits)
        dev_stats = analyzer.get_developer_stats()
        file_analysis = analyzer.get_file_analysis()
        recent_activity = analyzer.get_recent_activity()

        data_manager.save_analysis_data(repo_name, commits_df, dev_stats, file_analysis)

        analysis_status[repo_name] = {
            "status": "completed",
            "completion_time": datetime.now().isoformat(),
            "repo_name": repo_name
        }
    except Exception as e:
        logger.error(f"Background analysis failed for {repo_name}: {e}", exc_info=True)
        analysis_status[repo_name] = {"status": "failed", "message": str(e)}

@router.get("/health")
async def check_health():
    ok = ollama.check_availability()
    return {
        "status": "healthy",
        "ollama_connected": ok,
        "available_models": ollama.get_available_models() if ok else [],
    }

@router.post("/analyze-repo")
async def analyze_repository(request: AnalyzeRequest, background_tasks: BackgroundTasks, current_user: Any = Depends(get_current_user)):
    repo_name = request.repo_name.strip()
    background_tasks.add_task(run_analysis, repo_name, request.repo_url.strip(), request.max_commits)
    return {"success": True, "message": "Analysis started in background", "repo_name": repo_name}

@router.get("/status/{repo_name}")
async def get_analysis_status(repo_name: str, current_user: Any = Depends(get_current_user)):
    status = analysis_status.get(repo_name)
    if not status:
        # Check if we have cached data
        commits_df, _, _ = data_manager.load_analysis_data(repo_name)
        if not commits_df.empty:
            return {"status": "completed", "repo_name": repo_name}
        return {"status": "not_found"}
    return status

@router.get("/repo/{repo_name}/stats")
async def get_repository_stats(repo_name: str, current_user: Any = Depends(get_current_user)):
    commits_df, dev_stats, file_analysis = data_manager.load_analysis_data(repo_name)
    if commits_df.empty:
        raise HTTPException(status_code=404, detail="Repository not found in cache")

    analyzer = RepoAnalyzer("")
    analyzer._commits_cache = commits_df
    recent_activity = analyzer.get_recent_activity()

    return {
        "total_commits": len(commits_df),
        "active_developers": commits_df['author'].nunique(),
        "file_types": file_analysis,
        "recent_commits": recent_activity.get('total_commits', 0),
        "lines_added": recent_activity.get('lines_added', 0),
        "lines_removed": recent_activity.get('lines_removed', 0),
    }

@router.get("/repo/{repo_name}/developers")
async def get_developers(repo_name: str, current_user: Any = Depends(get_current_user)):
    _, dev_stats, _ = data_manager.load_analysis_data(repo_name)
    if dev_stats.empty:
        return []
    developers = []
    for dev_name in dev_stats.index:
        stats = dev_stats.loc[dev_name]
        developers.append({
            "developer": dev_name,
            "commits": int(stats.get("commits", 0)),
            "insertions": int(stats.get("insertions", 0)),
            "deletions": int(stats.get("deletions", 0)),
            "files_changed": int(stats.get("files_modified", 0)),
            "files_modified": int(stats.get("files_modified", 0)),
        })
    return developers

@router.get("/repo/{repo_name}/commits")
async def get_commits(repo_name: str, limit: int = 100, current_user: Any = Depends(get_current_user)):
    commits_df, _, _ = data_manager.load_analysis_data(repo_name)
    if commits_df.empty:
        return {"commits": []}
    if limit > 0:
        commits_df = commits_df.head(limit)
    commits = []
    for _, c in commits_df.iterrows():
        commits.append({
            "hash": c.get('hash'),
            "author": c.get('author'),
            "date": c.get('date').isoformat() if hasattr(c.get('date'), 'isoformat') else str(c.get('date')),
            "message": c.get('message'),
            "insertions": int(c.get('insertions', 0)),
            "deletions": int(c.get('deletions', 0)),
            "files_changed": int(c.get('files_changed', 0)),
        })
    return {"commits": commits}


