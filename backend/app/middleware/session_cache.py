"""Session cache middleware — mirrors Starlette session data to Redis.

Keeps Starlette's cookie-based SessionMiddleware as the source of truth,
but writes a copy to Redis for server-side visibility (admin tools,
multi-worker session lookup, server-side invalidation).

The middleware is a no-op when Redis is unavailable. Redis is resolved
lazily from ``app.state.redis`` on each request, avoiding the chicken-and-egg
problem of middleware registration happening before lifespan startup.
"""

from __future__ import annotations

import json
import logging

from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)

_SESSION_TTL_SECONDS = 7 * 86400  # 7 days, matches SessionMiddleware max_age


class SessionCacheMiddleware:
    """ASGI middleware that mirrors session data to Redis after each response."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Process the request normally
        await self.app(scope, receive, send)

        # Lazily resolve Redis from app.state (populated during lifespan)
        app = scope.get("app")
        if app is None:
            return
        redis_svc = getattr(app.state, "redis", None)
        if redis_svc is None or not redis_svc.is_available or redis_svc.client is None:
            return

        # Access session data from scope (set by SessionMiddleware)
        session = scope.get("session")
        if not session:
            return

        session_id = session.get("session_id")
        if not session_id:
            return

        try:
            key = f"synthesis:session:{session_id}"
            await redis_svc.client.set(
                key,
                json.dumps(session, default=str),
                ex=_SESSION_TTL_SECONDS,
            )
        except Exception as e:
            # Never fail the response due to session caching
            logger.debug("Session cache write failed for %s: %s", session_id, e)
