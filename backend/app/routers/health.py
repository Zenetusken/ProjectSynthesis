import asyncio
import logging

from fastapi import APIRouter

from app.config import settings
from app.database import check_db_connection

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])

# Will be set by main.py lifespan
_provider = None

_MCP_PROBE_TIMEOUT = 2.0  # seconds


def set_provider(provider):
    global _provider
    _provider = provider


async def _probe_mcp() -> bool:
    """Return True if the standalone MCP server is accepting TCP connections.

    Uses a lightweight TCP connect rather than a full MCP initialize handshake
    to avoid creating sessions on every 15-second health poll.
    """
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(settings.MCP_HOST, settings.MCP_PORT),
            timeout=_MCP_PROBE_TIMEOUT,
        )
        writer.close()
        await writer.wait_closed()
        return True
    except Exception:
        return False


@router.get("/api/health")
async def health_check():
    """Health check endpoint returning system status."""
    db_ok, mcp_ok = await asyncio.gather(
        check_db_connection(),
        _probe_mcp(),
    )

    github_oauth_enabled = bool(
        settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET
    )

    provider_name = _provider.name if _provider else "none"
    overall = "ok" if db_ok else "degraded"

    mcp_url = f"http://{settings.MCP_HOST}:{settings.MCP_PORT}/mcp"
    return {
        "status": overall,
        "provider": provider_name,
        "github_oauth_enabled": github_oauth_enabled,
        "db_connected": db_ok,
        "mcp_connected": mcp_ok,
        "mcp_url": mcp_url,
        "version": "2.0.0",
    }
