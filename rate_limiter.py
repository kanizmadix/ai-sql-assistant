"""
Simple in-memory token-bucket rate limiter implemented as Starlette
middleware. Per-IP buckets, refilling at a configurable rate.
"""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from config import settings


class _Bucket:
    __slots__ = ("tokens", "updated")

    def __init__(self, tokens: float) -> None:
        self.tokens = tokens
        self.updated = time.monotonic()


class TokenBucketRateLimiter(BaseHTTPMiddleware):
    """Per-IP token bucket. Default: 60 tokens, 1/sec refill."""

    EXEMPT_PATHS = {"/health", "/", "/static", "/favicon.ico"}

    def __init__(self, app, capacity: int | None = None, refill_per_sec: float | None = None):
        super().__init__(app)
        self.capacity = capacity or settings.RATE_LIMIT_CAPACITY
        self.refill = refill_per_sec or settings.RATE_LIMIT_REFILL_PER_SEC
        self._buckets: dict[str, _Bucket] = defaultdict(lambda: _Bucket(self.capacity))
        self._lock = Lock()

    def _take(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            bucket = self._buckets[key]
            elapsed = now - bucket.updated
            bucket.tokens = min(self.capacity, bucket.tokens + elapsed * self.refill)
            bucket.updated = now
            if bucket.tokens >= 1.0:
                bucket.tokens -= 1.0
                return True
            return False

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in self.EXEMPT_PATHS:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = client_ip

        if not self._take(key):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limited",
                    "message": "Too many requests; slow down.",
                },
            )
        return await call_next(request)
