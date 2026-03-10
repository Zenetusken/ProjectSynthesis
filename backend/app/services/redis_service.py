"""Shared Redis singleton with connection pooling, health check, and graceful degradation.

When Redis is unavailable, all consumers fall back to in-memory alternatives.
The app never crashes due to a missing Redis instance.
"""

import logging
import time
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from redis.asyncio import ConnectionPool as _RedisPool
    from redis.asyncio import Redis as _RedisClient

logger = logging.getLogger(__name__)

_RECONNECT_COOLDOWN = 30  # seconds between reconnection attempts

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None  # type: ignore[assignment]


class RedisService:
    """Async Redis client wrapper with graceful degradation.

    Usage::

        svc = RedisService(host="localhost", port=6379, db=0, password="")
        connected = await svc.connect()
        if svc.is_available:
            await svc.client.set("key", "value")
        await svc.close()
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str = "",
    ) -> None:
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._pool: Optional["_RedisPool"] = None
        self._client: Optional["_RedisClient"] = None
        self._available = False
        self._last_reconnect_attempt: float = 0.0

    async def connect(self) -> bool:
        """Attempt to connect to Redis. Returns True if successful.

        Catches ConnectionError/TimeoutError and sets is_available = False
        instead of crashing the application.
        """
        if aioredis is None:
            logger.critical(
                "Redis unavailable — 'redis' package not installed. "
                "Install with: pip install redis>=5.0"
            )
            self._available = False
            return False

        try:
            self._pool = aioredis.ConnectionPool(
                host=self._host,
                port=self._port,
                db=self._db,
                password=self._password or None,
                decode_responses=True,
                max_connections=20,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            self._client = aioredis.Redis(connection_pool=self._pool)
            # Verify connection with a PING
            await self._client.ping()
            self._available = True
            logger.info("Redis connected at %s:%s (db=%s)", self._host, self._port, self._db)
            return True
        except (ConnectionError, TimeoutError, OSError) as e:
            logger.critical(
                "Redis unavailable at %s:%s — %s. "
                "Falling back to in-memory rate limiting and caching.",
                self._host, self._port, e,
            )
            self._available = False
            self._client = None
            self._pool = None
            return False
        except Exception as e:
            logger.critical("Redis connection failed unexpectedly: %s", e)
            self._available = False
            self._client = None
            self._pool = None
            return False

    async def close(self) -> None:
        """Close the Redis connection pool."""
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception:
                pass
            self._client = None
        if self._pool is not None:
            try:
                await self._pool.disconnect()
            except Exception:
                pass
            self._pool = None
        self._available = False

    async def health_check(self) -> bool:
        """Return True if Redis responds to PING.

        When Redis was previously marked unavailable, attempts reconnection
        with a cooldown to avoid connection storms.
        """
        if self._available:
            if self._client is None:
                self._available = False
                return False
            try:
                return await self._client.ping()
            except Exception:
                self._available = False
                return False

        # Redis marked unavailable — attempt reconnection with cooldown
        now = time.time()
        if now - self._last_reconnect_attempt < _RECONNECT_COOLDOWN:
            return False
        self._last_reconnect_attempt = now

        # If pool/client still exist, try a simple ping first
        if self._client is not None:
            try:
                await self._client.ping()
                self._available = True
                logger.info("Redis reconnected at %s:%s", self._host, self._port)
                return True
            except Exception:
                return False

        # Client was torn down — attempt full reconnect
        return await self.connect()

    @property
    def is_available(self) -> bool:
        """Whether Redis is currently connected and responsive."""
        return self._available

    @property
    def is_ready(self) -> bool:
        """Whether Redis is available and the client is accessible.

        Convenience guard combining ``is_available`` and a non-None ``client``
        so callers don't need to repeat the double-check pattern.
        """
        return self._available and self._client is not None

    @property
    def client(self) -> Optional["_RedisClient"]:
        """The underlying redis.asyncio.Redis client, or None if unavailable."""
        return self._client if self._available else None

    @property
    def uri(self) -> str:
        """Build a redis:// URI from connection parameters (for libraries that need it)."""
        if self._password:
            return f"redis://:{self._password}@{self._host}:{self._port}/{self._db}"
        return f"redis://{self._host}:{self._port}/{self._db}"
