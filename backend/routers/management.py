"""
Management Router
Exposes endpoints to analyze repositories and retrieve cached analyses
for the Team Lead Management dashboard.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Any, Dict, Optional

from services.management_service import management_service


router = APIRouter(prefix="/api/management", tags=["management"])


class AnalyzeRepoRequest(BaseModel):
    repo_url: HttpUrl
    max_commits: Optional[int] = 100


@router.post("/analyze-repo")
async def analyze_repo(payload: AnalyzeRepoRequest) -> Dict[str, Any]:
    result = management_service.analyze_repository(
        repo_url=str(payload.repo_url), max_commits=payload.max_commits or 100
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Analysis failed"))
    return result


@router.get("/cached")
async def list_cached() -> Dict[str, Any]:
    return management_service.list_cached()


class AnalyzeLocalRequest(BaseModel):
    local_path: str
    max_commits: Optional[int] = 100


@router.post("/analyze-local")
async def analyze_local(payload: AnalyzeLocalRequest) -> Dict[str, Any]:
    result = management_service.analyze_local(
        local_path=payload.local_path, max_commits=payload.max_commits or 100
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Analysis failed"))
    return result


class AskRequest(BaseModel):
    question: str
    repo_name: Optional[str] = None
    local_path: Optional[str] = None
    max_commits: Optional[int] = 100


@router.post("/ask")
async def ask_repo(payload: AskRequest) -> Dict[str, Any]:
    result = management_service.ask(
        question=payload.question,
        repo_name=payload.repo_name,
        local_path=payload.local_path,
        max_commits=payload.max_commits or 100,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Q&A failed"))
    return result

# ---- Alias endpoints to match the provided prompt spec ----
@router.post("/analyze")
async def analyze_root(payload: AnalyzeRepoRequest) -> Dict[str, Any]:
    return await analyze_repo(payload)


@router.get("/commits")
async def get_commits_root(repo_name: str, limit: int | None = None) -> Dict[str, Any]:
    return management_service.get_commits(repo_name, limit)


@router.get("/developers")
async def get_developers_root(repo_name: str) -> Dict[str, Any]:
    return management_service.get_developers(repo_name)


@router.get("/commits/by-developer")
async def get_commits_by_developer_root(repo_name: str, author: str, limit: int | None = None) -> Dict[str, Any]:
    return management_service.get_commits_by_author(repo_name, author, limit)


class ChatAliasRequest(BaseModel):
    repo_name: Optional[str] = None
    question: str


@router.post("/chat")
async def chat_root(payload: ChatAliasRequest) -> Dict[str, Any]:
    return management_service.ask(question=payload.question, repo_name=payload.repo_name)


class ReportAliasRequest(BaseModel):
    repo_name: str
    report_type: str


@router.post("/generate-report")
async def report_root(payload: ReportAliasRequest) -> Dict[str, Any]:
    return management_service.generate_report(repo_name=payload.repo_name, report_type=payload.report_type)


