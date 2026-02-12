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
    repo_url = request.repo_url.strip()
    
    # For local repos, run synchronously and return data immediately
    if repo_url.startswith("local:"):
        try:
            repo_path = repo_url.replace("local:", "").strip()
            import git
            analyzer = RepoAnalyzer(repo_path)
            
            # Check if it's a git repo
            is_git_repo = os.path.exists(os.path.join(repo_path, ".git"))
            
            commits_json = []
            dev_stats_json = []
            recent_activity = {}
            
            if is_git_repo:
                analyzer.repo = git.Repo(repo_path)
                commits_df = analyzer.get_commits_data(request.max_commits)
                dev_stats = analyzer.get_developer_stats()
                recent_activity = analyzer.get_recent_activity()
                
                # Convert to JSON-serializable format
                for _, c in commits_df.iterrows():
                    commits_json.append({
                        "hash": c.get('hash'),
                        "author": c.get('author'),
                        "date": c.get('date').isoformat() if hasattr(c.get('date'), 'isoformat') else str(c.get('date')),
                        "message": c.get('message'),
                        "insertions": int(c.get('insertions', 0)),
                        "deletions": int(c.get('deletions', 0)),
                        "files_changed": int(c.get('files_changed', 0)),
                    })
                
                for dev_name in dev_stats.index:
                    stats = dev_stats.loc[dev_name]
                    dev_stats_json.append({
                        "author": dev_name,
                        "commits": int(stats.get("commits", 0)),
                        "insertions": int(stats.get("insertions", 0)),
                        "deletions": int(stats.get("deletions", 0)),
                        "files_modified": int(stats.get("files_modified", 0)),
                    })
            
            # File analysis works for any folder
            file_analysis = analyzer.get_file_analysis()
            
            return {
                "success": True, 
                "repo_name": repo_name,
                "is_git_repo": is_git_repo,
                "commits": commits_json,
                "developer_stats": dev_stats_json,
                "file_analysis": file_analysis,
                "recent_activity": recent_activity
            }
        except Exception as e:
            logger.error(f"Local analysis failed for {repo_name}: {e}", exc_info=True)
            raise HTTPException(status_code=400, detail=str(e))
    
    # For remote repos, run synchronously (clone and analyze)
    try:
        import git
        repo_path = os.path.join(APP_CONFIG.repos_dir, repo_name)
        
        # Clone or open the repo
        if os.path.exists(repo_path):
            repo = git.Repo(repo_path)
            repo.remotes.origin.pull()
        else:
            os.makedirs(APP_CONFIG.repos_dir, exist_ok=True)
            repo = git.Repo.clone_from(repo_url, repo_path, depth=1)
        
        analyzer = RepoAnalyzer(repo_path)
        analyzer.repo = repo
        
        commits_df = analyzer.get_commits_data(request.max_commits)
        dev_stats = analyzer.get_developer_stats()
        file_analysis = analyzer.get_file_analysis()
        recent_activity = analyzer.get_recent_activity()
        
        data_manager.save_analysis_data(repo_name, commits_df, dev_stats, file_analysis)
        
        # Convert to JSON-serializable format
        commits_json = []
        for _, c in commits_df.iterrows():
            commits_json.append({
                "hash": c.get('hash'),
                "author": c.get('author'),
                "date": c.get('date').isoformat() if hasattr(c.get('date'), 'isoformat') else str(c.get('date')),
                "message": c.get('message'),
                "insertions": int(c.get('insertions', 0)),
                "deletions": int(c.get('deletions', 0)),
                "files_changed": int(c.get('files_changed', 0)),
            })
        
        dev_stats_json = []
        for dev_name in dev_stats.index:
            stats = dev_stats.loc[dev_name]
            dev_stats_json.append({
                "author": dev_name,
                "commits": int(stats.get("commits", 0)),
                "insertions": int(stats.get("insertions", 0)),
                "deletions": int(stats.get("deletions", 0)),
                "files_modified": int(stats.get("files_modified", 0)),
            })
        
        return {
            "success": True, 
            "repo_name": repo_name,
            "is_git_repo": True,
            "commits": commits_json,
            "developer_stats": dev_stats_json,
            "file_analysis": file_analysis,
            "recent_activity": recent_activity
        }
    except Exception as e:
        logger.error(f"Remote analysis failed for {repo_name}: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

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


@router.get("/repo/{repo_name}/clarity")
async def get_code_clarity(repo_name: str, current_user: Any = Depends(get_current_user)):
    """Generate code clarity recommendations based on repository analysis"""
    commits_df, dev_stats, file_analysis = data_manager.load_analysis_data(repo_name)
    if commits_df.empty:
        raise HTTPException(status_code=404, detail="Repository not found in cache")
    
    # Calculate metrics
    total_commits = len(commits_df)
    contributors = commits_df['author'].nunique() if not commits_df.empty else 0
    
    # Recent activity (last 30 days)
    from datetime import datetime, timedelta
    recent_date = datetime.now() - timedelta(days=30)
    recent_commits = 0
    if not commits_df.empty and 'date' in commits_df.columns:
        try:
            recent_commits = len(commits_df[commits_df['date'] >= recent_date])
        except:
            recent_commits = 0
    
    # Generate recommendations based on analysis
    recommendations = []
    
    # Commit frequency analysis
    if recent_commits < 5:
        recommendations.append("Low recent activity detected. Consider increasing commit frequency for better code visibility.")
    elif recent_commits > 50:
        recommendations.append("High commit frequency. Consider batching smaller changes into larger, meaningful commits.")
    
    # Contributor analysis
    if contributors == 1:
        recommendations.append("Single contributor detected. Consider code reviews or pair programming for better code quality.")
    elif contributors > 5:
        recommendations.append("Multiple active contributors. Ensure consistent coding standards across the team.")
    
    # File type analysis
    if file_analysis:
        py_files = file_analysis.get('.py', 0)
        js_files = file_analysis.get('.js', 0) + file_analysis.get('.jsx', 0) + file_analysis.get('.ts', 0) + file_analysis.get('.tsx', 0)
        
        if py_files > 0 and js_files > 0:
            recommendations.append("Mixed Python and JavaScript codebase. Consider clear separation of frontend/backend concerns.")
        
        if file_analysis.get('.md', 0) == 0:
            recommendations.append("No markdown documentation found. Add README.md and documentation files.")
        
        total_files = sum(file_analysis.values())
        if total_files > 100:
            recommendations.append(f"Large codebase ({total_files} files). Consider modular architecture and proper testing.")
    
    # Default recommendations if none generated
    if not recommendations:
        recommendations = [
            "Maintain consistent commit messages",
            "Add unit tests for critical functionality",
            "Document public APIs and complex functions",
            "Use linting tools for code consistency"
        ]
    
    return {
        "repo_name": repo_name,
        "metrics": {
            "total_commits": total_commits,
            "contributors": contributors,
            "recent_commits_30d": recent_commits,
            "file_types": len(file_analysis) if file_analysis else 0
        },
        "recommendations": recommendations
    }
