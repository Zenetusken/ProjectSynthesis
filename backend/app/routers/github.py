"""GitHub integration endpoints.

Handles OAuth authentication, personal access token storage,
repository listing, file tree browsing, and file content reading.
"""

import logging
import secrets
import uuid
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.schemas.github import PATRequest, RepoInfo, GitHubUserInfo
from app.services.github_service import (
    encrypt_token,
    decrypt_token,
    store_token,
    get_token_for_session,
    get_token_info,
    delete_token,
    validate_pat,
    get_user_repos,
    get_repo_tree,
    read_file_content,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["github"])

# GitHub OAuth endpoints
GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"

# In-memory CSRF state store (per-session, short-lived)
_oauth_states: dict[str, str] = {}


def _get_session_id(request: Request) -> str:
    """Extract or create a session ID from cookies.

    Args:
        request: The incoming FastAPI request.

    Returns:
        A session ID string.
    """
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id


# ───────────────────────────────────────────────────────────────────────
# OAuth flow
# ───────────────────────────────────────────────────────────────────────

@router.get("/api/github/auth/url")
async def get_oauth_url(request: Request):
    """Get the GitHub OAuth authorization URL.

    Generates a CSRF state token and returns the URL the frontend
    should redirect to for GitHub authentication.

    Returns 400 if GitHub OAuth is not configured.
    """
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=400,
            detail="GitHub OAuth is not configured. Set GITHUB_CLIENT_ID and "
                   "GITHUB_CLIENT_SECRET in your .env file, or use a PAT instead.",
        )

    session_id = _get_session_id(request)
    state = secrets.token_urlsafe(32)
    _oauth_states[session_id] = state

    auth_url = (
        f"{GITHUB_AUTHORIZE_URL}"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&scope=repo"
        f"&state={state}"
        f"&allow_signup=false"
    )

    return {"url": auth_url, "state": state}


@router.get("/api/github/auth/callback")
async def oauth_callback(
    code: str,
    state: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Handle the GitHub OAuth callback.

    Exchanges the authorization code for an access token, validates
    the CSRF state, fetches user info, and stores the encrypted token.

    Redirects to the frontend root on success.
    """
    session_id = _get_session_id(request)

    # Verify CSRF state
    expected_state = _oauth_states.pop(session_id, None)
    if not expected_state or state != expected_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state (CSRF check failed)")

    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured")

    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GITHUB_TOKEN_URL,
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )

    if token_response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to exchange OAuth code for token")

    token_data = token_response.json()
    access_token = token_data.get("access_token")
    if not access_token:
        error = token_data.get("error_description", token_data.get("error", "Unknown error"))
        raise HTTPException(status_code=400, detail=f"GitHub OAuth error: {error}")

    scopes = token_data.get("scope", "")

    # Fetch user info
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            GITHUB_USER_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )

    if user_response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch GitHub user info")

    user_data = user_response.json()
    github_user_id = user_data["id"]
    github_login = user_data["login"]

    # Store encrypted token
    await store_token(
        session,
        session_id=session_id,
        github_user_id=github_user_id,
        github_login=github_login,
        token=access_token,
        token_type="oauth",
        scopes=scopes,
    )

    # Redirect to frontend with session cookie
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        max_age=86400 * 30,  # 30 days
    )
    return response


# ───────────────────────────────────────────────────────────────────────
# Personal Access Token (PAT)
# ───────────────────────────────────────────────────────────────────────

@router.post("/api/github/pat")
async def store_pat(
    body: PATRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Store a GitHub Personal Access Token.

    Validates the token by calling the GitHub /user endpoint,
    then encrypts and stores it.

    Returns user info on success, 401 if the token is invalid.
    """
    # Validate the PAT
    user_info = await validate_pat(body.token)
    if not user_info:
        raise HTTPException(
            status_code=401,
            detail="Invalid GitHub token. Ensure your PAT has the required permissions.",
        )

    session_id = _get_session_id(request)

    await store_token(
        session,
        session_id=session_id,
        github_user_id=user_info["id"],
        github_login=user_info["login"],
        token=body.token,
        token_type="pat",
    )

    response_data = GitHubUserInfo(
        connected=True,
        login=user_info["login"],
        avatar_url=user_info.get("avatar_url"),
        github_user_id=user_info["id"],
        token_type="pat",
    )

    from fastapi.responses import JSONResponse

    resp = JSONResponse(content=response_data.model_dump())
    resp.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        max_age=86400 * 30,
    )
    return resp


# ───────────────────────────────────────────────────────────────────────
# Repository browsing
# ───────────────────────────────────────────────────────────────────────

@router.get("/api/github/repos")
async def list_repos(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """List repositories accessible by the authenticated user.

    Requires a valid GitHub token stored for the current session.
    Returns 401 if not authenticated.
    """
    session_id = _get_session_id(request)
    token = await get_token_for_session(session, session_id)
    if not token:
        raise HTTPException(status_code=401, detail="GitHub not connected")

    repos = await get_user_repos(token)
    return {"repos": repos}


@router.get("/api/github/repos/{owner}/{repo}/tree")
async def get_repo_tree_endpoint(
    owner: str,
    repo: str,
    branch: str = Query("main"),
    request: Request = None,
    session: AsyncSession = Depends(get_session),
):
    """Get the file tree of a repository.

    Returns a list of files with paths, SHA hashes, and sizes.
    Binary files, node_modules, and other excluded paths are filtered out.

    Args:
        owner: Repository owner (GitHub username or org).
        repo: Repository name.
        branch: Branch name (default: main).
    """
    session_id = _get_session_id(request)
    token = await get_token_for_session(session, session_id)
    if not token:
        raise HTTPException(status_code=401, detail="GitHub not connected")

    full_name = f"{owner}/{repo}"
    tree = await get_repo_tree(token, full_name, branch)
    return {"tree": tree, "full_name": full_name, "branch": branch}


@router.get("/api/github/repos/{owner}/{repo}/files/{path:path}")
async def read_file(
    owner: str,
    repo: str,
    path: str,
    branch: str = Query("main"),
    request: Request = None,
    session: AsyncSession = Depends(get_session),
):
    """Read a file from a repository.

    Fetches the file tree to find the blob SHA, then reads the content.

    Args:
        owner: Repository owner.
        repo: Repository name.
        path: File path within the repository.
        branch: Branch name (default: main).
    """
    session_id = _get_session_id(request)
    token = await get_token_for_session(session, session_id)
    if not token:
        raise HTTPException(status_code=401, detail="GitHub not connected")

    full_name = f"{owner}/{repo}"

    # Get tree to find the SHA for this path
    tree = await get_repo_tree(token, full_name, branch)
    file_entry = next((e for e in tree if e["path"] == path), None)
    if not file_entry:
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    content = await read_file_content(token, full_name, file_entry["sha"])
    if content is None:
        raise HTTPException(status_code=500, detail="Failed to read file content")

    return {
        "path": path,
        "content": content,
        "size_bytes": file_entry.get("size_bytes", 0),
        "sha": file_entry["sha"],
    }


# ───────────────────────────────────────────────────────────────────────
# Auth management
# ───────────────────────────────────────────────────────────────────────

@router.delete("/api/github/auth")
async def disconnect_github(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Disconnect GitHub by removing the stored token.

    Clears the encrypted token from the database for the current session.
    """
    session_id = _get_session_id(request)
    deleted = await delete_token(session, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="No GitHub connection found")

    return {"disconnected": True}
