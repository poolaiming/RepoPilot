from __future__ import annotations

import json
import logging
from contextvars import ContextVar
from time import perf_counter
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


request_id: ContextVar[str] = ContextVar("request_id", default="-")
logger = logging.getLogger("uvicorn.error")


def record_event(event: str, **fields) -> None:
    # Only pass operational metadata; exception text and request bodies may contain secrets.
    logger.info(json.dumps({"event": event, "request_id": request_id.get(), **fields}))


def record_model(operation: str, mode: str, started: float, error_type: str | None = None) -> None:
    record_event("model", operation=operation, mode=mode, error_type=error_type,
                 duration_ms=round((perf_counter() - started) * 1000, 2))


class RequestTraceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = uuid4().hex
        trace_token = request_id.set(trace_id)
        started = perf_counter()
        status = 500
        error_type = None
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers["X-Request-ID"] = trace_id
            return response
        except Exception as exc:
            error_type = type(exc).__name__
            return JSONResponse({"detail": "Internal error. Use X-Request-ID to locate the request."},
                                status_code=500, headers={"X-Request-ID": trace_id})
        finally:
            route = request.scope.get("route")
            record_event("request", method=request.method,
                         route=getattr(route, "path", "unmatched"), status=status,
                         duration_ms=round((perf_counter() - started) * 1000, 2),
                         error_type=error_type)
            request_id.reset(trace_token)
