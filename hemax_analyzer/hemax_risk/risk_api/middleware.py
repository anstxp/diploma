from __future__ import annotations

import logging
import time
import uuid
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("risk.risk_api")


class RequestContextMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id

        t0 = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            elapsed = (time.perf_counter() - t0) * 1000
            logger.exception(
                f"[{request_id}] {request.method} {request.url.path} -> 500 in {elapsed:.1f}ms"
            )
            raise

        elapsed = (time.perf_counter() - t0) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = f"{elapsed:.1f}"
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"-> {response.status_code} in {elapsed:.1f}ms"
        )
        return response
