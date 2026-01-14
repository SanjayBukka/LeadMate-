from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd  # type: ignore

from management.repo_analyzer import RepoAnalyzer
from management.ai_insights import AIInsights
from management.data_manager import DataManager
from management.ollama_client import OllamaClient
from management.config import APP_CONFIG


class ManagementService:
    def __init__(self) -> None:
        self.data_manager = DataManager()
        self.ai_insights = AIInsights()
        self.ollama = OllamaClient()

    def analyze_repository(self, repo_url: str, max_commits: int = 100) -> Dict[str, Any]:
        """
        Clone or open the repo and return analysis artifacts.

        Returns a JSON-serializable dict with:
        - repo_name
        - commits (list of dicts)
        - developer_stats (list of dicts)
        - file_analysis (dict)
        - recent_activity (dict)
        - summaries (optional AI summaries)
        """
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        repo_path = Path(APP_CONFIG.repos_dir) / repo_name  # type: ignore[attr-defined]

        analyzer = RepoAnalyzer(str(repo_path))
        if not analyzer.clone_or_open_repo(repo_url):
            return {
                "success": False,
                "message": "Failed to clone or open repository. Check the URL and connectivity.",
            }

        commits_df: pd.DataFrame = analyzer.get_commits_data(max_commits)
        dev_stats: pd.DataFrame = analyzer.get_developer_stats()
        file_analysis: Dict[str, int] = analyzer.get_file_analysis()
        recent_activity: Dict[str, Any] = analyzer.get_recent_activity()

        # Cache results to CSVs via DataManager (optional but helpful)
        self.data_manager.save_analysis_data(repo_name, commits_df, dev_stats, file_analysis)

        # Optional AI-generated summaries (will gracefully degrade if Ollama not available)
        summaries: Dict[str, Any] = {}
        try:
            proj_summary = self.ai_insights.generate_project_summary(
                commits_df, file_analysis, recent_activity
            )
            summaries["project_summary"] = proj_summary
        except Exception:
            summaries["project_summary"] = None

        # Convert DataFrames to JSON-serializable structures
        commits_json = (
            commits_df.assign(date=lambda d: d["date"].astype(str)).to_dict(orient="records")
            if not commits_df.empty
            else []
        )
        dev_stats_json = dev_stats.reset_index().assign(
            first_commit=lambda d: d["first_commit"].astype(str),
            last_commit=lambda d: d["last_commit"].astype(str),
        ).to_dict(orient="records") if not dev_stats.empty else []

        return {
            "success": True,
            "repo_name": repo_name,
            "commits": commits_json,
            "developer_stats": dev_stats_json,
            "file_analysis": file_analysis,
            "recent_activity": recent_activity,
            "summaries": summaries,
        }

    def list_cached(self) -> Dict[str, Any]:
        """List cached repository analyses."""
        repos = self.data_manager.get_cached_repos()
        return {"success": True, "cached": repos}

    def analyze_local(self, local_path: str, max_commits: int = 100) -> Dict[str, Any]:
        """Analyze an already-cloned local repository path without network cloning."""
        path = Path(local_path).resolve()
        if not path.exists():
            return {"success": False, "message": f"Local path not found: {path}"}

        repo_name = path.name
        analyzer = RepoAnalyzer(str(path))
        # Validate repo root
        if not (path / ".git").exists():
            return {"success": False, "message": f"Path is not a Git repository: {path}"}
        # Ensure the local repository is opened so commits can be read
        try:
            analyzer.clone_or_open_repo("")
        except Exception as e:
            return {"success": False, "message": f"Failed to open repository: {e}"}

        try:
            commits_df: pd.DataFrame = analyzer.get_commits_data(max_commits)
            dev_stats: pd.DataFrame = analyzer.get_developer_stats()
            file_analysis: Dict[str, int] = analyzer.get_file_analysis()
            recent_activity: Dict[str, Any] = analyzer.get_recent_activity()
        except Exception as e:
            return {"success": False, "message": f"Git analysis error: {e}"}

        self.data_manager.save_analysis_data(repo_name, commits_df, dev_stats, file_analysis)

        commits_json = (
            commits_df.assign(date=lambda d: d["date"].astype(str)).to_dict(orient="records")
            if not commits_df.empty
            else []
        )
        dev_stats_json = dev_stats.reset_index().assign(
            first_commit=lambda d: d["first_commit"].astype(str),
            last_commit=lambda d: d["last_commit"].astype(str),
        ).to_dict(orient="records") if not dev_stats.empty else []

        return {
            "success": True,
            "repo_name": repo_name,
            "commits": commits_json,
            "developer_stats": dev_stats_json,
            "file_analysis": file_analysis,
            "recent_activity": recent_activity,
        }

    def ask(self, question: str, repo_name: Optional[str] = None, local_path: Optional[str] = None,
            max_commits: int = 100) -> Dict[str, Any]:
        """
        Answer a question about a repository using recent commits and stats as context.
        Prefers cached data by repo_name; if local_path is provided, analyzes path ad-hoc.
        """
        commits_df: pd.DataFrame = pd.DataFrame()
        dev_stats: pd.DataFrame = pd.DataFrame()
        recent_activity: Dict[str, Any] = {}

        if repo_name:
            c, d, _ = self.data_manager.load_analysis_data(repo_name)
            commits_df, dev_stats = c, d
            # Construct recent activity from commits if missing
            if not commits_df.empty:
                cutoff = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=30)
                rc = commits_df[commits_df['date'] > cutoff] if 'date' in commits_df.columns else commits_df
                recent_activity = {
                    'total_commits': len(rc),
                    'active_developers': rc['author'].nunique() if 'author' in rc.columns else 0,
                    'lines_added': int(rc['insertions'].sum()) if 'insertions' in rc.columns else 0,
                    'lines_removed': int(rc['deletions'].sum()) if 'deletions' in rc.columns else 0,
                    'most_active_dev': rc['author'].mode().iloc[0] if ('author' in rc.columns and not rc.empty) else 'None',
                }
        elif local_path:
            # Ad-hoc analysis of local path
            result = self.analyze_local(local_path, max_commits=max_commits)
            if not result.get("success"):
                return result
            # Reconstruct DFs from JSON for context summarization
            commits_df = pd.DataFrame(result.get("commits", []))
            dev_stats = pd.DataFrame(result.get("developer_stats", []))
            recent_activity = result.get("recent_activity", {})
        else:
            return {"success": False, "message": "Provide either repo_name (cached) or local_path."}

        # Build context
        top_commit_rows = commits_df.head(5)[[c for c in ["author", "date", "message"] if c in commits_df.columns]] if not commits_df.empty else pd.DataFrame()
        top_dev = dev_stats.iloc[0] if not dev_stats.empty else None

        context_lines = [
            f"Total commits: {len(commits_df)}",
            f"Contributors: {commits_df['author'].nunique() if ('author' in commits_df.columns and not commits_df.empty) else 0}",
            f"Recent (30d) commits: {recent_activity.get('total_commits', 0)}",
            f"Most active: {recent_activity.get('most_active_dev', 'Unknown')}",
        ]
        if top_dev is not None and 'commits' in top_dev.index:
            context_lines.append(f"Top contributor: {top_dev.name} ({int(top_dev['commits'])} commits)")

        if not top_commit_rows.empty:
            context_lines.append("Recent commits:")
            context_lines.append(top_commit_rows.to_string(index=False))

        prompt = (
            "You are an engineering assistant. Use the repository context to answer the user's question.\n\n"
            + "Repository Context:\n"
            + "\n".join(context_lines)
            + f"\n\nQuestion: {question}\n"
            + "Answer concisely and, when helpful, cite authors/dates/changes from the context."
        )

        answer = self.ollama.generate(prompt, task_type="balanced")
        return {"success": True, "answer": answer or "Unable to generate an answer at this time."}

    # ---- Convenience getters for cached data ----
    def get_commits(self, repo_name: str, limit: Optional[int] = None) -> Dict[str, Any]:
        commits_df, _, _ = self.data_manager.load_analysis_data(repo_name)
        if commits_df.empty:
            return {"success": True, "repo_name": repo_name, "commits": []}
        df = commits_df.sort_values("date", ascending=False)
        if limit:
            df = df.head(int(limit))
        commits_json = df.assign(date=lambda d: d["date"].astype(str)).to_dict(orient="records")
        return {"success": True, "repo_name": repo_name, "commits": commits_json}

    def get_developers(self, repo_name: str) -> Dict[str, Any]:
        _, dev_stats, _ = self.data_manager.load_analysis_data(repo_name)
        if dev_stats.empty:
            return {"success": True, "repo_name": repo_name, "developers": []}
        ds = dev_stats.sort_values("commits", ascending=False).reset_index().assign(
            first_commit=lambda d: d["first_commit"].astype(str),
            last_commit=lambda d: d["last_commit"].astype(str),
        )
        return {"success": True, "repo_name": repo_name, "developers": ds.to_dict(orient="records")}

    def get_commits_by_author(self, repo_name: str, author: str, limit: Optional[int] = None) -> Dict[str, Any]:
        commits_df, _, _ = self.data_manager.load_analysis_data(repo_name)
        if commits_df.empty or 'author' not in commits_df.columns:
            return {"success": True, "repo_name": repo_name, "author": author, "commits": []}
        df = commits_df[commits_df['author'] == author].sort_values('date', ascending=False)
        if limit:
            df = df.head(int(limit))
        commits_json = df.assign(date=lambda d: d['date'].astype(str)).to_dict(orient='records')
        return {"success": True, "repo_name": repo_name, "author": author, "commits": commits_json}

    # ---- Report generation ----
    def generate_report(self, repo_name: str, report_type: str = "executive") -> Dict[str, Any]:
        commits_df, dev_stats, file_analysis = self.data_manager.load_analysis_data(repo_name)
        if commits_df.empty and dev_stats.empty:
            return {"success": False, "message": "No cached data for repo. Analyze first."}

        recent_activity: Dict[str, Any] = {}
        if not commits_df.empty:
            cutoff = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=30)
            rc = commits_df[commits_df['date'] > cutoff] if 'date' in commits_df.columns else commits_df
            recent_activity = {
                'total_commits': len(rc),
                'active_developers': rc['author'].nunique() if 'author' in rc.columns else 0,
                'lines_added': int(rc['insertions'].sum()) if 'insertions' in rc.columns else 0,
                'lines_removed': int(rc['deletions'].sum()) if 'deletions' in rc.columns else 0,
                'most_active_dev': rc['author'].mode().iloc[0] if ('author' in rc.columns and not rc.empty) else 'None',
            }

        if report_type.lower() in ("executive", "summary"):
            text = self.ai_insights.generate_project_summary(commits_df, file_analysis, recent_activity)
            return {"success": True, "type": "executive", "content": text}

        if report_type.lower() in ("developer", "developer_performance"):
            insights = self.ai_insights.analyze_developer_work(dev_stats, commits_df)
            return {"success": True, "type": "developer_performance", "content": insights}

        if report_type.lower() in ("project_health", "health"):
            # Build prompt similar to streamlit_app and call ollama directly
            total_commits = len(commits_df)
            active_devs = recent_activity.get('active_developers', 0)
            commits_per_day = (recent_activity.get('total_commits', 0) / 30.0) if recent_activity else 0.0
            added = recent_activity.get('lines_added', 0)
            removed = recent_activity.get('lines_removed', 0)
            extensions = ", ".join(file_analysis.keys()) if file_analysis else ""
            prompt = (
                "Assess the health of this software project:\n\n"
                f"Metrics:\n- Total commits analyzed: {total_commits}\n"
                f"- Active developers (30d): {active_devs}\n"
                f"- Average commits per day: {commits_per_day:.1f}\n"
                f"- Recent lines added: {added}\n"
                f"- Recent lines removed: {removed}\n\n"
                f"File types: {extensions}\n\n"
                "Provide a project health assessment with:\n"
                "1. Overall health score (1-10)\n2. Key strengths\n3. Areas of concern\n4. Recommendations\n"
            )
            content = self.ollama.generate(prompt, task_type="detailed")
            return {"success": True, "type": "project_health", "content": content}

        return {"success": False, "message": f"Unknown report_type: {report_type}"}


management_service = ManagementService()


