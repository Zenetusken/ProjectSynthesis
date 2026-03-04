"""Async wrappers for PyGithub operations.

PyGithub is synchronous. All blocking calls are wrapped with
anyio.to_thread.run_sync() for use in async FastAPI endpoints.
"""

import base64
import logging
from typing import Optional

import anyio
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


async def _get_decrypted_token(session_id: str) -> str:
    """Retrieve and decrypt the GitHub token for a session."""
    from app.database import async_session
    from app.models.github import GitHubToken
    from app.routers.github_auth import _get_fernet
    from sqlalchemy import select

    async with async_session() as session:
        result = await session.execute(
            select(GitHubToken).where(GitHubToken.session_id == session_id)
        )
        token_record = result.scalar_one_or_none()
        if not token_record:
            raise ValueError(f"No GitHub token found for session {session_id}")

        fernet = _get_fernet()
        return fernet.decrypt(token_record.token_encrypted).decode()


async def get_repo_tree(
    session_id: str,
    full_name: str,
    branch: str,
) -> list[dict]:
    """Get the complete file tree for a repository.

    Returns list of {path, sha, size} dicts for blob entries.
    """
    token = await _get_decrypted_token(session_id)

    def _sync():
        from github import Github, Auth
        g = Github(auth=Auth.Token(token))
        repo = g.get_repo(full_name)
        b = repo.get_branch(branch)
        tree = repo.get_git_tree(b.commit.commit.tree.sha, recursive=True)
        return [
            {"path": e.path, "sha": e.sha, "size": e.size}
            for e in tree.tree
            if e.type == "blob"
        ]

    return await anyio.to_thread.run_sync(_sync)


async def get_file_content(
    session_id: str,
    full_name: str,
    sha: str,
) -> str:
    """Read a single file's content by its blob SHA.

    Returns the decoded text content.
    """
    token = await _get_decrypted_token(session_id)

    def _sync():
        from github import Github, Auth
        g = Github(auth=Auth.Token(token))
        repo = g.get_repo(full_name)
        blob = repo.get_git_blob(sha)
        if blob.encoding == "base64":
            return base64.b64decode(blob.content).decode("utf-8", errors="replace")
        return blob.content

    return await anyio.to_thread.run_sync(_sync)


async def validate_repo_access(
    token: str,
    full_name: str,
) -> dict:
    """Validate that a token has access to a repository.

    Returns repo metadata dict or raises ValueError.
    """
    def _sync():
        from github import Github, Auth
        g = Github(auth=Auth.Token(token))
        repo = g.get_repo(full_name)
        return {
            "full_name": repo.full_name,
            "default_branch": repo.default_branch,
            "language": repo.language,
            "private": repo.private,
        }

    return await anyio.to_thread.run_sync(_sync)
