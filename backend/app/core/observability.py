import logging
import random
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings

logger = logging.getLogger("app.observability")


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Lightweight request timing for production latency tracking."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"

        # Reduce log I/O pressure in production:
        # always log slow requests, sample fast requests, and skip health endpoint.
        if (
            settings.REQUEST_TIMING_LOG_ENABLED
            and request.url.path != "/health"
            and (
                elapsed_ms >= settings.REQUEST_TIMING_LOG_MIN_MS
                or random.random() <= settings.REQUEST_TIMING_LOG_SAMPLE_RATE
            )
        ):
            logger.info(
                "request_timing method=%s path=%s status=%s duration_ms=%.2f",
                request.method,
                request.url.path,
                response.status_code,
                elapsed_ms,
            )
        return response
