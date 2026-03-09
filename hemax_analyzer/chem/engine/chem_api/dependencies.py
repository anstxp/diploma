from __future__ import annotations

import os
import logging

from fastapi import Depends, Header, HTTPException, Request, status

logger = logging.getLogger("chem.chem_api")

_AUTH_ENABLED = os.getenv("HEMAX_CHEM_AUTH_ENABLED", "false").lower() in ("1", "true", "yes")
_API_KEYS: set[str] = {
    k.strip()
    for k in os.getenv("HEMAX_CHEM_API_KEYS", "").split(",")
    if k.strip()
}


async def get_api_key(x_api_key: str | None = Header(default=None)) -> str | None:
    if not _AUTH_ENABLED:
        return None
    if not x_api_key or x_api_key not in _API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Valid X-API-Key header is required."},
        )
    return x_api_key


async def get_request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)
