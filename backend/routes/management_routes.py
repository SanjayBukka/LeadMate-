"""
Management routes (workflow-style) for compatibility with existing frontend calls.
This router analyzes git repositories, caches results, and exposes stats/devs/commits/insights.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging
import os
import sys

# Add managemnet folder to path (tools live there)
MANAGEMNET_PATH = r"C:\Users\Sanjay\Desktop\Lead Mate full Application\managemnet"
if MANAGEMNET_PATH not in sys.path:
    sys.path.insert(0, MANAGEMNET_PATH)

from repo_analyzer import RepoAnalyzer  # type: ignore
from ai_insights import AIInsights  # type: ignore
from data_manager import DataManager  # type: ignore
from ollama_client import OllamaClient  # type: ignore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workflow", tags=["Management (Legacy)"])

ollama = OllamaClient()
ai_insights = AIInsights()
data_manager = DataManager()


class AnalyzeRequest(BaseModel):
    repo_url: str
    repo_name: str
    max_commits: int = 100


@router.get("/health")
async def check_health():
    ok = ollama.check_availability()
    return {
        "status": "healthy",
        "ollama_connected": ok,
        "available_models": ollama.get_available_models() if ok else [],
    }


@router.post("/analyze-repo")
async def analyze_repository(request: AnalyzeRequest):
    try:
        repo_name = request.repo_name.strip()
        repo_url = request.repo_url.strip()
        max_commits = request.max_commits

        # Determine target path
        if repo_url.startswith("local:"):
            repo_path = repo_url.replace("local:", "").strip()
            is_local = True
        else:
            repo_path = os.path.join(MANAGEMNET_PATH, "repositories", repo_name)
            is_local = False

        analyzer = RepoAnalyzer(repo_path)
        if not is_local:
            if not analyzer.clone_or_open_repo(repo_url):
                return {"success": False, "message": "Failed to clone repository. Check URL and try again."}
        else:
            try:
                import git  # type: ignore
                analyzer.repo = git.Repo(repo_path)
            except Exception as e:
                return {"success": False, "message": f"Failed to open local repository: {e}"}

        commits_df = analyzer.get_commits_data(max_commits)
        dev_stats = analyzer.get_developer_stats()
        file_analysis = analyzer.get_file_analysis()
        recent_activity = analyzer.get_recent_activity()

        data_manager.save_analysis_data(repo_name, commits_df, dev_stats, file_analysis)

        ai_summary = None
        if ollama.check_availability():
            try:
                ai_summary = ai_insights.generate_project_summary(commits_df, file_analysis, recent_activity)
            except Exception as e:
                logger.error(f"AI summary failed: {e}")

        commits_data = commits_df.to_dict("records") if not commits_df.empty else []

        dev_stats_list = []
        if not dev_stats.empty:
            for dev_name in dev_stats.index:
                stats = dev_stats.loc[dev_name]
                dev_stats_list.append({
                    "developer": dev_name,
                    "commits": int(stats.get("commits", 0)),
                    "insertions": int(stats.get("insertions", 0)),
                    "deletions": int(stats.get("deletions", 0)),
                    "files_modified": int(stats.get("files_modified", 0)),
                })

        return {
            "success": True,
            "message": "Repository analyzed successfully",
            "data": {
                "repo_name": repo_name,
                "file_analysis": file_analysis,
                "dependencies": [],
                "key_files": {},
                "commits_data": commits_data[:100],
                "developer_stats": dev_stats_list,
                "analysis_date": datetime.now().isoformat(),
                "ai_summary": ai_summary,
            },
        }
    except Exception as e:
        logger.error(f"Error analyzing repository: {e}", exc_info=True)
        return {"success": False, "message": f"Error: {e}"}


@router.get("/repo/{repo_name}/stats")
async def get_repository_stats(repo_name: str):
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
async def get_developers(repo_name: str):
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
async def get_commits(repo_name: str, limit: int = 100):
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


