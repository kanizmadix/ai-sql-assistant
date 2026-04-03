"""
Domain exceptions and the FastAPI handlers that translate them into
clean JSON error responses.
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base class for application-level errors."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str = "") -> None:
        super().__init__(message or self.__class__.__name__)
        self.message = message or self.__class__.__name__


class UnsafeQuery(AppError):
    status_code = 400
    code = "unsafe_query"


class QueryFailed(AppError):
    status_code = 400
    code = "query_failed"


class DatabaseNotFound(AppError):
    status_code = 404
    code = "database_not_found"


class ExportError(AppError):
    status_code = 400
    code = "export_error"


class RateLimited(AppError):
    status_code = 429
    code = "rate_limited"


def install_handlers(app) -> None:
    """Register exception handlers on a FastAPI app."""

    @app.exception_handler(AppError)
    async def _app_error(_request: Request, exc: AppError):  # type: ignore[unused-ignore]
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.code, "message": exc.message},
        )

    @app.exception_handler(Exception)
    async def _unexpected(_request: Request, exc: Exception):  # type: ignore[unused-ignore]
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "message": str(exc)},
        )
