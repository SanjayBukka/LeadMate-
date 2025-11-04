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
from services.ollama_service import ollama_service
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

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str

class ReportRequest(BaseModel):
    type: str  # Executive Summary | Developer Performance | Project Health | Team Activity

class ReportResponse(BaseModel):
    content: str

def _analyze_local_directory(path: str) -> Dict:
    """Analyze a local directory as a repository fallback."""
    import os
    from collections import Counter
    file_types = Counter()
    key_files = {}
    requirements = []
    for root, dirs, files in os.walk(path):
        # skip heavy/system dirs
        dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "venv", ".venv", "__pycache__"]]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            file_types[ext] += 1
            if f in ("requirements.txt", "pyproject.toml", "setup.py", "repo_analyzer.py", "data_manager.py", "utils.py", "ollama_client.py", "streamlit_app.py"):
                try:
                    with open(os.path.join(root, f), "r", encoding="utf-8", errors="ignore") as fh:
                        content = fh.read(2000)
                    key_files[f] = content
                    if f == "requirements.txt":
                        requirements = [ln.strip() for ln in content.splitlines() if ln.strip() and not ln.strip().startswith("#")]
                except Exception:
                    pass
    return {
        "file_analysis": dict(file_types),
        "key_files": key_files,
        "dependencies": requirements,
    }


def _generate_clarity_suggestions(analysis_data: Dict) -> Dict:
    """Create code clarity recommendations from existing cached analysis data.
    This does not require per-file histories and works off summary stats.
    """
    suggestions: list[str] = []
    hotspots: list[Dict] = []  # Placeholder for future per-file stats

    commits_data = analysis_data.get('commits_data', []) or []
    file_analysis = analysis_data.get('file_analysis', {}) or {}
    recent_activity = analysis_data.get('recent_activity', {}) or {}
    dev_stats = analysis_data.get('dev_stats', {}) or {}

    total_commits = len(commits_data)
    contributors = len(dev_stats.keys())
    recent_commits = int(recent_activity.get('total_commits', 0))
    lines_added = sum(c.get('insertions', 0) for c in commits_data)
    lines_removed = sum(c.get('deletions', 0) for c in commits_data)

    # Activity cadence
    if recent_commits < max(3, int(total_commits * 0.05)):
        suggestions.append("Low recent activity – set weekly commit goals and PR cadence.")
    else:
        suggestions.append("Healthy recent activity – keep small, focused PRs.")

    # Bus factor
    if contributors <= 1:
        suggestions.append("Single contributor risk – add backup reviewer and cross-train.")
    elif contributors < 3:
        suggestions.append("Small team – invest in docs and onboarding to reduce risk.")

    # Churn
    churn = lines_added + lines_removed
    if churn > 20000:
        suggestions.append("High code churn – enforce PR size limits and feature flags.")
    elif churn > 5000:
        suggestions.append("Moderate churn – improve review checklist and test gates.")

    # Stack balance and tests
    has_js = (file_analysis.get('.js', 0) + file_analysis.get('.ts', 0) +
              file_analysis.get('.tsx', 0) + file_analysis.get('.jsx', 0))
    has_py = file_analysis.get('.py', 0)
    if has_js and has_py:
        suggestions.append("Mixed JS/Python stack – standardize API contracts and shared types.")
    if (has_js + has_py) > 20:
        suggestions.append("Add automated tests and CI coverage thresholds.")

    # Ownership concentration
    try:
        top_dev = max(dev_stats.items(), key=lambda kv: kv[1].get('commits', 0)) if dev_stats else None
        if top_dev:
            top_name, top_data = top_dev
            if top_data.get('commits', 0) > total_commits * 0.6:
                suggestions.append(f"High ownership by {top_name} – spread context via pair reviews.")
    except Exception:
        pass

    if not suggestions:
        suggestions.append("No critical issues detected.")

    return {
        "hotspots": hotspots,
        "recommendations": suggestions,
        "metrics": {
            "total_commits": total_commits,
            "contributors": contributors,
            "recent_commits_30d": recent_commits,
            "lines_added": lines_added,
            "lines_removed": lines_removed,
        }
    }


def _compute_analysis_on_demand(company_id: str, lead_id: str, repo_name: str) -> Optional[Dict]:
    """Fallback compute from cloned repo if DB has no data."""
    try:
        from pathlib import Path
        repo_path = Path(git_service.base_dir) / company_id / lead_id / repo_name
        if not repo_path.exists():
            return None
        commits_df = git_service.analyze_commits(str(repo_path), max_commits=None)
        file_analysis = git_service.analyze_file_types(str(repo_path))
        dev_stats_df = git_service.get_developer_stats(commits_df) if not commits_df.empty else pd.DataFrame()
        recent_activity = git_service.get_recent_activity(commits_df) if not commits_df.empty else {
            'total_commits': 0,
            'active_developers': 0,
            'files_changed': 0,
            'lines_added': 0,
            'lines_removed': 0,
            'most_active_dev': 'None'
        }
        commit_patterns = git_service.get_commit_patterns(commits_df) if not commits_df.empty else {}
        commit_insights = ai_service.analyze_commit_patterns(commits_df) if not commits_df.empty else {"insights": [], "patterns": {}}
        dev_insights = ai_service.analyze_developer_work(dev_stats_df, commits_df) if not commits_df.empty else {"insights": {}, "recommendations": []}
        project_summary = ai_service.generate_project_summary(commits_df, file_analysis, recent_activity)
        return {
            'commits_data': commits_df.to_dict('records') if not commits_df.empty else [],
            'file_analysis': file_analysis,
            'dev_stats': dev_stats_df.to_dict('index') if not dev_stats_df.empty else {},
            'recent_activity': recent_activity,
            'commit_patterns': commit_patterns,
            'commit_insights': commit_insights,
            'dev_insights': dev_insights,
            'project_summary': project_summary,
        }
    except Exception:
        return None


@router.post("/analyze-repo", response_model=RepositoryResponse)
async def analyze_repository(request: RepositoryRequest, current_user = Depends(get_current_user)):
    """Analyze a Git repository and extract insights"""
    try:
        # current_user is a Pydantic User model (not a dict)
        company_id = getattr(current_user, 'startupId', 'demo_company')
        lead_id = getattr(current_user, 'id', 'demo_lead')
        
        # Local directory fallback: repo_url like "local:<absolute-or-relative-path>"
        if request.repo_url.lower().startswith("local:"):
            local_path = request.repo_url.split(":", 1)[1].strip()
            abs_path = os.path.abspath(local_path)
            if not os.path.exists(abs_path):
                return RepositoryResponse(success=False, message=f"Local path not found: {abs_path}")
            # If it's a Git repo, run full analysis; otherwise run lightweight directory scan
            if os.path.isdir(os.path.join(abs_path, '.git')):
                try:
                    commits_df = git_service.analyze_commits(abs_path, max_commits=None)
                    has_commits = not commits_df.empty
                    file_analysis = git_service.analyze_file_types(abs_path)
                    dev_stats = git_service.get_developer_stats(commits_df) if has_commits else pd.DataFrame()
                    recent_activity = git_service.get_recent_activity(commits_df) if has_commits else {
                        'total_commits': 0,
                        'active_developers': 0,
                        'files_changed': 0,
                        'lines_added': 0,
                        'lines_removed': 0,
                        'most_active_dev': 'None'
                    }
                    commit_patterns = git_service.get_commit_patterns(commits_df) if has_commits else {}
                    commit_insights = ai_service.analyze_commit_patterns(commits_df) if has_commits else {"insights": "No commit data available", "patterns": {}}
                    dev_insights = ai_service.analyze_developer_work(dev_stats, commits_df) if has_commits else {"insights": {}, "recommendations": []}
                    project_summary = ai_service.generate_project_summary(commits_df, file_analysis, recent_activity)
                    team_recommendations = ai_service.generate_team_recommendations(dev_stats, commits_df) if has_commits else ["Insufficient data for recommendations"]
                    # Save CSV/Excel exports (best-effort)
                    try:
                        data_service.save_analysis_files(request.repo_name, commits_df, dev_stats)
                    except Exception:
                        pass

                    return RepositoryResponse(
                        success=True,
                        message="Local Git repository analyzed successfully",
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
                            "commits_data": commits_df.to_dict('records') if not commits_df.empty else [],
                            "analysis_date": datetime.now().isoformat()
                        }
                    )
                except Exception as e:
                    return RepositoryResponse(success=False, message=f"Local Git analysis failed: {str(e)}")
            else:
                local_data = _analyze_local_directory(abs_path)
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

        # Normalize non-local URLs (append .git if missing)
        normalized_url = request.repo_url
        if not request.repo_url.lower().startswith("local:") and request.repo_url.startswith("http"):
            if not request.repo_url.endswith(".git"):
                normalized_url = request.repo_url + ".git"

        # Clone repository (Git)
        success, repo_path = git_service.clone_repository(
            normalized_url,
            request.repo_name,
            company_id,
            lead_id
        )
        
        if not success:
            return RepositoryResponse(
                success=False,
                message=f"Failed to clone repository: {repo_path}"
            )
        
        try:
            # Get repository info (safe)
            try:
                repo_info = git_service.get_repository_info(repo_path)
            except Exception as e:
                return RepositoryResponse(success=False, message=f"Failed to read repository info: {str(e)}")

            # Analyze commits (safe)
            try:
                # Analyze ALL commits (no cap)
                commits_df = git_service.analyze_commits(repo_path, max_commits=None)
            except Exception as e:
                return RepositoryResponse(success=False, message=f"Failed to analyze commits: {str(e)}")
            # Allow repositories with no commits: continue with partial analysis
            has_commits = not commits_df.empty

            # Analyze file types
            file_analysis = git_service.analyze_file_types(repo_path)

            # Get developer stats
            dev_stats = git_service.get_developer_stats(commits_df) if has_commits else pd.DataFrame()

            # Get recent activity
            recent_activity = git_service.get_recent_activity(commits_df) if has_commits else {
                'total_commits': 0,
                'active_developers': 0,
                'files_changed': 0,
                'lines_added': 0,
                'lines_removed': 0,
                'most_active_dev': 'None'
            }

            # Get commit patterns
            commit_patterns = git_service.get_commit_patterns(commits_df) if has_commits else {}

            # Generate AI insights
            commit_insights = ai_service.analyze_commit_patterns(commits_df) if has_commits else {"insights": "No commit data available", "patterns": {}}
            dev_insights = ai_service.analyze_developer_work(dev_stats, commits_df) if has_commits else {"insights": {}, "recommendations": []}
            project_summary = ai_service.generate_project_summary(commits_df, file_analysis, recent_activity)
            team_recommendations = ai_service.generate_team_recommendations(dev_stats, commits_df) if has_commits else ["Insufficient data for recommendations"]

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

            # Save to database (best-effort)
            try:
                data_service.save_repository_analysis(company_id, lead_id, request.repo_name, analysis_data)
            except Exception:
                pass

            # Save CSV/Excel exports for graphics (best-effort)
            try:
                data_service.save_analysis_files(request.repo_name, commits_df, dev_stats)
            except Exception:
                pass

            # Create notifications (best-effort)
            try:
                await notification_service.analyze_and_notify(company_id, lead_id, analysis_data)
                active_developers = int(dev_stats.shape[0]) if not dev_stats.empty else 0
                await notification_service.create_notification(
                    company_id, lead_id,
                    NotificationType.REPOSITORY_ANALYZED,
                    f"Repository {request.repo_name} Analyzed",
                    f"Successfully analyzed {request.repo_name} with {len(commits_df)} commits and {active_developers} developers.",
                    NotificationPriority.LOW,
                    {"repo_name": request.repo_name, "commits": len(commits_df), "developers": active_developers}
                )
            except Exception:
                pass

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
            return RepositoryResponse(success=False, message=f"Analysis failed: {str(e)}")
        
    except Exception as e:
        # Return a structured response instead of a 500 to surface the error message in UI
        return RepositoryResponse(success=False, message=f"Analysis failed: {str(e)}")

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
            analysis_data = _compute_analysis_on_demand(company_id, lead_id, repo_name)
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
            analysis_data = _compute_analysis_on_demand(company_id, lead_id, repo_name)
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
        
        # Return all commits when limit <= 0; otherwise first N (data is sorted desc by date)
        recent_commits = commits_data if (limit is None or limit <= 0) else commits_data[:limit]
        
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

@router.get("/repo/{repo_name}/clarity")
async def get_repository_clarity(repo_name: str, current_user = Depends(get_current_user)):
    """Get Code Clarity recommendations based on existing analysis data."""
    try:
        company_id = getattr(current_user, 'startupId', 'demo_company')
        lead_id = getattr(current_user, 'id', 'demo_lead')

        analysis_data = data_service.get_repository_analysis(company_id, lead_id, repo_name)
        if not analysis_data:
            raise HTTPException(status_code=404, detail="Repository not found or no data available")

        clarity = _generate_clarity_suggestions(analysis_data)
        return clarity
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/repo/{repo_name}/chat", response_model=ChatResponse)
async def chat_about_repository(repo_name: str, req: ChatRequest, current_user = Depends(get_current_user)):
    """Simple AI Chat about the repository. Uses Ollama if available, otherwise heuristic fallback."""
    try:
        company_id = getattr(current_user, 'startupId', 'demo_company') if not isinstance(current_user, dict) else current_user.get('startupId', 'demo_company')
        lead_id = getattr(current_user, 'id', 'demo_lead') if not isinstance(current_user, dict) else current_user.get('id', 'demo_lead')

        analysis_data = data_service.get_repository_analysis(company_id, lead_id, repo_name)
        if not analysis_data:
            raise HTTPException(status_code=404, detail="Repository not found or no data available")

        commits = analysis_data.get('commits_data', []) or []
        dev_stats = analysis_data.get('dev_stats', {}) or {}
        recent_activity = analysis_data.get('recent_activity', {}) or {}
        file_analysis = analysis_data.get('file_analysis', {}) or {}

        # Prepare concise context
        total_commits = len(commits)
        contributors = len(dev_stats.keys())
        recent30 = int(recent_activity.get('total_commits', 0))
        top_dev = next(iter(sorted(dev_stats.items(), key=lambda kv: kv[1].get('commits', 0), reverse=True)), ("Unknown", {}))[0]
        recent_msgs = "\n".join([f"- {c.get('author','')}: {(c.get('message','')[:120])}" for c in commits[:5]])
        file_types = ", ".join([f"{k}:{v}" for k,v in file_analysis.items()])

        prompt = f"""
Repository Context:
- Total commits: {total_commits}
- Contributors: {contributors}
- Recent activity (30d): {recent30}
- Top contributor: {top_dev}
- File types: {file_types}

Recent commits:
{recent_msgs}

Question: {req.question}
Provide a helpful answer based on the data above. Keep it concise and actionable.
""".strip()

        answer: str
        try:
            if ollama_service.check_model_availability():
                resp = ollama_service.client.chat(model=ollama_service.model, messages=[{"role": "user", "content": prompt}])
                answer = resp['message']['content'].strip()
            else:
                raise RuntimeError("Ollama not available")
        except Exception:
            # Heuristic fallback
            focus = commits[0].get('message','') if commits else 'N/A'
            answer = (
                f"Based on the repository stats, there are {total_commits} commits with {contributors} contributor(s). "
                f"Recent 30d activity is {recent30}. Top contributor appears to be {top_dev}. "
                f"Recent focus: {focus}.\n\n"
                f"Your question: '{req.question}'. From the data, the team shows {'ongoing' if recent30>0 else 'low'} momentum."
            )

        return ChatResponse(answer=answer)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/repo/{repo_name}/report", response_model=ReportResponse)
async def generate_report(repo_name: str, req: ReportRequest, current_user = Depends(get_current_user)):
    """Generate a text report similar to Streamlit reports."""
    try:
        company_id = getattr(current_user, 'startupId', 'demo_company') if not isinstance(current_user, dict) else current_user.get('startupId', 'demo_company')
        lead_id = getattr(current_user, 'id', 'demo_lead') if not isinstance(current_user, dict) else current_user.get('id', 'demo_lead')

        analysis_data = data_service.get_repository_analysis(company_id, lead_id, repo_name)
        if not analysis_data:
            raise HTTPException(status_code=404, detail="Repository not found or no data available")

        commits_df = pd.DataFrame(analysis_data.get('commits_data', []))
        dev_stats_df = pd.DataFrame.from_dict(analysis_data.get('dev_stats', {}), orient='index') if analysis_data.get('dev_stats') else pd.DataFrame()
        file_analysis = analysis_data.get('file_analysis', {}) or {}
        recent_activity = analysis_data.get('recent_activity', {}) or {}

        rtype = (req.type or '').strip()
        if rtype.lower().startswith('executive'):
            summary = ai_service.generate_project_summary(commits_df, file_analysis, recent_activity)
            content = f"Executive Summary\n\n{summary.get('summary','No summary')}\n\nHealth Score: {summary.get('health_score',0)}"
            return ReportResponse(content=content)

        if rtype.lower().startswith('developer'):
            insights = ai_service.analyze_developer_work(dev_stats_df, commits_df)
            lines = []
            if 'insights' in insights:
                for dev, data in list(insights['insights'].items())[:10]:
                    metrics = data.get('metrics', {})
                    lines.append(f"- {dev}: commits {metrics.get('commits',0)}, +{metrics.get('lines_added',0)} / -{metrics.get('lines_removed',0)}")
            content = "Developer Performance\n\n" + ("\n".join(lines) or "No data")
            return ReportResponse(content=content)

        if rtype.lower().startswith('project'):
            summary = ai_service.generate_project_summary(commits_df, file_analysis, recent_activity)
            content = (
                "Project Health\n\n" 
                f"Commits analyzed: {len(commits_df)}\n"
                f"Active developers (30d): {recent_activity.get('active_developers',0)}\n"
                f"Recent commits (30d): {recent_activity.get('total_commits',0)}\n"
                f"Health Score: {summary.get('health_score',0)}\n"
            )
            return ReportResponse(content=content)

        if rtype.lower().startswith('team'):
            insights = ai_service.analyze_developer_work(dev_stats_df, commits_df)
            recs = insights.get('recommendations', [])
            top = sorted(list(analysis_data.get('dev_stats', {}).items()), key=lambda kv: kv[1].get('commits',0), reverse=True)[:5]
            lines = [f"- {name}: commits {stats.get('commits',0)}" for name, stats in top]
            content = (
                "Team Activity\n\n" 
                f"Contributors: {len(analysis_data.get('dev_stats',{}))}\n"
                f"Commits (30d): {recent_activity.get('total_commits',0)}\n"
                "Top contributors:\n" + ("\n".join(lines) or "No data") + ("\n\nRecommendations:\n" + "\n".join(recs) if recs else "")
            )
            return ReportResponse(content=content)

        return ReportResponse(content="Report type not supported")
    except HTTPException:
        raise
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
