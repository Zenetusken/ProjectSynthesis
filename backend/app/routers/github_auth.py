import logging
import uuid
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from itsdangerous import BadSignature, SignatureExpired, TimestampSigner
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.models.github import GitHubToken
from app.schemas.github import GitHubUserInfo, PATRequest
from app.services.github_service import _get_fernet, decrypt_token

logger = logging.getLogger(__name__)
router = APIRouter(tags=["github-auth"])

# CSRF state is time-bound: expires after 10 minutes (per spec)
_CSRF_MAX_AGE = 600

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


def _csrf_signer() -> TimestampSigner:
    """Return a TimestampSigner keyed on the app SECRET_KEY."""
    return TimestampSigner(settings.SECRET_KEY)


def _get_session_id(request: Request) -> str:
    """Get or create a session ID from cookies."""
    session = request.session
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return session["session_id"]


@router.get("/auth/github/login")
async def github_login(request: Request):
    """Initiate GitHub OAuth flow. Redirects to GitHub."""
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=400,
            detail="GitHub OAuth not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET.",
        )

    # Generate time-bound CSRF state via TimestampSigner
    raw_token = uuid.uuid4().hex
    state = _csrf_signer().sign(raw_token).decode()
    request.session["oauth_state"] = state

    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "scope": "repo",
        "state": state,
        "allow_signup": "false",
    }
    redirect_url = f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}"
    return RedirectResponse(url=redirect_url)


@router.get("/auth/github/callback")
async def github_callback(
    request: Request,
    code: str = "",
    state: str = "",
    session: AsyncSession = Depends(get_session),
):
    """Handle GitHub OAuth callback."""
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state parameter")

    # Verify CSRF state — exact match + signature + expiry check.
    # Always consume (pop) the stored state so it cannot be replayed.
    stored_state = request.session.pop("oauth_state", None)
    if not stored_state or state != stored_state:
        raise HTTPException(status_code=400, detail="State mismatch (CSRF protection)")
    try:
        _csrf_signer().unsign(state, max_age=_CSRF_MAX_AGE)
    except SignatureExpired:
        raise HTTPException(
            status_code=400,
            detail="OAuth state expired — please restart the login flow",
        )
    except BadSignature:
        raise HTTPException(
            status_code=400,
            detail="Invalid OAuth state signature (CSRF protection)",
        )

    # Exchange code for token
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GITHUB_TOKEN_URL,
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        token_data = token_resp.json()

    access_token = token_data.get("access_token")
    if not access_token:
        error = token_data.get("error_description", "Failed to get access token")
        raise HTTPException(status_code=400, detail=error)

    scopes = token_data.get("scope", "")

    # Fetch user info
    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            GITHUB_USER_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )
        if user_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch GitHub user info")
        user_data = user_resp.json()

    # Encrypt and store token
    fernet = _get_fernet()
    encrypted_token = fernet.encrypt(access_token.encode())

    session_id = _get_session_id(request)
    github_user_id = user_data["id"]
    github_login = user_data["login"]

    # Remove any existing token for this session
    await session.execute(
        delete(GitHubToken).where(GitHubToken.session_id == session_id)
    )

    new_token = GitHubToken(
        session_id=session_id,
        github_user_id=github_user_id,
        github_login=github_login,
        token_encrypted=encrypted_token,
        token_type="oauth",
        scopes=scopes,
    )
    session.add(new_token)
    await session.commit()

    # Store user info in session
    request.session["github_user_id"] = github_user_id
    request.session["github_login"] = github_login

    # Redirect to frontend
    return RedirectResponse(url="/")


@router.get("/auth/github/me")
async def github_me(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Get current GitHub auth status."""
    session_id = request.session.get("session_id")
    if not session_id:
        return GitHubUserInfo(connected=False).model_dump()

    result = await session.execute(
        select(GitHubToken).where(GitHubToken.session_id == session_id)
    )
    token_record = result.scalar_one_or_none()
    if not token_record:
        return GitHubUserInfo(connected=False).model_dump()

    # Optionally fetch fresh avatar URL
    avatar_url = None
    try:
        decrypted = decrypt_token(bytes(token_record.token_encrypted))
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                GITHUB_USER_URL,
                headers={
                    "Authorization": f"Bearer {decrypted}",
                    "Accept": "application/json",
                },
            )
            if resp.status_code == 200:
                avatar_url = resp.json().get("avatar_url")
    except Exception:
        pass

    return {
        "connected": True,
        "login": token_record.github_login,
        "avatar_url": avatar_url,
        "github_user_id": token_record.github_user_id,
        "token_type": token_record.token_type,
    }


@router.delete("/auth/github/logout")
async def github_logout(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Revoke and delete stored GitHub token."""
    session_id = request.session.get("session_id")
    if session_id:
        await session.execute(
            delete(GitHubToken).where(GitHubToken.session_id == session_id)
        )
        await session.commit()
        from app.routers.github_repos import evict_repo_cache
        evict_repo_cache(session_id)

    # Clear session GitHub data
    request.session.pop("github_user_id", None)
    request.session.pop("github_login", None)

    return {"disconnected": True}


@router.post("/auth/github/pat")
async def submit_pat(
    body: PATRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Submit a Personal Access Token for GitHub authentication."""
    # Validate the token by calling GitHub API
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            GITHUB_USER_URL,
            headers={
                "Authorization": f"Bearer {body.token}",
                "Accept": "application/json",
            },
        )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=401,
                detail="Invalid GitHub token. Ensure it has 'Contents: Read' permission.",
            )
        user_data = resp.json()

    # Encrypt and store
    fernet = _get_fernet()
    encrypted_token = fernet.encrypt(body.token.encode())

    session_id = _get_session_id(request)
    github_user_id = user_data["id"]
    github_login = user_data["login"]

    # Remove existing token
    await session.execute(
        delete(GitHubToken).where(GitHubToken.session_id == session_id)
    )

    new_token = GitHubToken(
        session_id=session_id,
        github_user_id=github_user_id,
        github_login=github_login,
        token_encrypted=encrypted_token,
        token_type="pat",
    )
    session.add(new_token)
    await session.commit()

    # Store in session
    request.session["github_user_id"] = github_user_id
    request.session["github_login"] = github_login

    return GitHubUserInfo(
        connected=True,
        login=github_login,
        avatar_url=user_data.get("avatar_url"),
        github_user_id=github_user_id,
        token_type="pat",
    ).model_dump()
