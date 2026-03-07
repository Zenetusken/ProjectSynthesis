"""Async wrappers for PyGithub operations.

PyGithub is synchronous. All blocking calls are wrapped with
anyio.to_thread.run_sync() for use in async FastAPI endpoints.
"""

import logging

import anyio

logger = logging.getLogger(__name__)


async def _get_decrypted_token(session_id: str) -> str:
    """Retrieve and decrypt the GitHub token for a session.

    Uses github_service.decrypt_token to avoid importing from the router layer.
    """
    from sqlalchemy import select

    from app.database import async_session
    from app.models.github import GitHubToken
    from app.services.github_service import decrypt_token

    async with async_session() as session:
        result = await session.execute(
            select(GitHubToken).where(GitHubToken.session_id == session_id)
        )
        token_record = result.scalar_one_or_none()
        if not token_record:
            raise ValueError(f"No GitHub token found for session {session_id}")

        return decrypt_token(bytes(token_record.token_encrypted))


async def validate_repo_access(
    token: str,
    full_name: str,
) -> dict:
    """Validate that a token has access to a repository.

    Returns repo metadata dict or raises ValueError.
    """
    def _sync():
        from github import Auth, Github
        g = Github(auth=Auth.Token(token))
        repo = g.get_repo(full_name)
        return {
            "full_name": repo.full_name,
            "default_branch": repo.default_branch,
            "language": repo.language,
            "private": repo.private,
        }

    return await anyio.to_thread.run_sync(_sync)
