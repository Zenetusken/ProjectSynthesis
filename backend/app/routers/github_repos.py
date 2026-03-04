import uuid
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from cryptography.fernet import Fernet

from app.database import get_session
from app.config import settings
from app.models.github import GitHubToken, LinkedRepo
from app.schemas.github import LinkRepoRequest, RepoInfo, LinkedRepoResponse
from app.routers.github_auth import _get_fernet

logger = logging.getLogger(__name__)
router = APIRouter(tags=["github-repos"])

# Simple in-memory cache for repo lists
_repo_cache: dict[str, tuple[float, list]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes


async def _get_github_token(request: Request, session: AsyncSession) -> str:
    """Retrieve and decrypt the GitHub token for the current session."""
    session_id = request.session.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated with GitHub")

    result = await session.execute(
        select(GitHubToken).where(GitHubToken.session_id == session_id)
    )
    token_record = result.scalar_one_or_none()
    if not token_record:
        raise HTTPException(status_code=401, detail="No GitHub token found. Connect GitHub first.")

    fernet = _get_fernet()
    return fernet.decrypt(token_record.token_encrypted).decode()


@router.get("/api/github/repos")
async def list_repos(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """List repositories accessible with the user's GitHub token."""
    import time

    token = await _get_github_token(request, session)

    # Check cache
    cache_key = request.session.get("session_id", "")
    if cache_key in _repo_cache:
        cached_time, cached_repos = _repo_cache[cache_key]
        if time.time() - cached_time < CACHE_TTL_SECONDS:
            return cached_repos

    # Fetch from GitHub
    repos = []
    page = 1
    async with httpx.AsyncClient() as client:
        while True:
            resp = await client.get(
                "https://api.github.com/user/repos",
                params={
                    "per_page": 100,
                    "page": page,
                    "sort": "updated",
                    "direction": "desc",
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
            )
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=resp.status_code,
                    detail="Failed to fetch repos from GitHub",
                )

            data = resp.json()
            if not data:
                break

            for repo in data:
                repos.append({
                    "full_name": repo["full_name"],
                    "name": repo["name"],
                    "private": repo.get("private", False),
                    "default_branch": repo.get("default_branch", "main"),
                    "description": repo.get("description"),
                    "language": repo.get("language"),
                    "size_kb": repo.get("size", 0),
                })

            # Only fetch up to 5 pages (500 repos max)
            if page >= 5 or len(data) < 100:
                break
            page += 1

    # Update cache
    import time as time_mod
    _repo_cache[cache_key] = (time_mod.time(), repos)

    return repos


@router.post("/api/github/repos/link")
async def link_repo(
    body: LinkRepoRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Link a GitHub repository for codebase-aware optimization."""
    token = await _get_github_token(request, session)
    session_id = request.session.get("session_id", "")

    # Validate repo access
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api.github.com/repos/{body.full_name}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Repository not found or not accessible")
        repo_data = resp.json()

    branch = body.branch or repo_data.get("default_branch", "main")

    # Remove any existing linked repo for this session
    await session.execute(
        delete(LinkedRepo).where(LinkedRepo.session_id == session_id)
    )

    linked = LinkedRepo(
        session_id=session_id,
        full_name=body.full_name,
        branch=branch,
        default_branch=repo_data.get("default_branch"),
        language=repo_data.get("language"),
    )
    session.add(linked)
    await session.commit()

    return {
        "id": linked.id,
        "full_name": linked.full_name,
        "branch": linked.branch,
        "default_branch": linked.default_branch,
        "language": linked.language,
    }


@router.get("/api/github/repos/linked")
async def get_linked_repo(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Get the currently linked repository for this session."""
    session_id = request.session.get("session_id")
    if not session_id:
        return None

    result = await session.execute(
        select(LinkedRepo).where(LinkedRepo.session_id == session_id)
    )
    linked = result.scalar_one_or_none()
    if not linked:
        return None

    return {
        "id": linked.id,
        "full_name": linked.full_name,
        "branch": linked.branch,
        "default_branch": linked.default_branch,
        "language": linked.language,
        "linked_at": linked.linked_at.isoformat() if linked.linked_at else None,
    }


@router.delete("/api/github/repos/unlink")
async def unlink_repo(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Unlink the currently linked repository."""
    session_id = request.session.get("session_id")
    if not session_id:
        return {"unlinked": False, "reason": "No session"}

    result = await session.execute(
        delete(LinkedRepo).where(LinkedRepo.session_id == session_id)
    )
    await session.commit()

    return {"unlinked": True}
