from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("chem.chem_api")



class ChemAPIError(Exception):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, field: str | None = None):
        self.message = message
        self.field = field
        super().__init__(message)


class BadRequestError(ChemAPIError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "BAD_REQUEST"


class ValidationError(ChemAPIError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    code = "VALIDATION_ERROR"


class AnalysisError(ChemAPIError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "ANALYSIS_ERROR"



def _error_body(code: str, message: str, field: str | None, request_id: str | None) -> dict[str, Any]:
    body: dict[str, Any] = {
        "error": {"code": code, "message": message},
    }
    if field is not None:
        body["error"]["field"] = field
    if request_id:
        body["request_id"] = request_id
    return body


def _get_request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)



def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(ChemAPIError)
    async def chem_api_error_handler(request: Request, exc: ChemAPIError) -> JSONResponse:
        logger.warning("ChemAPIError [%s]: %s", exc.code, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.code, exc.message, exc.field, _get_request_id(request)),
        )

    @app.exception_handler(RequestValidationError)
    async def pydantic_validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = exc.errors()
        first = errors[0] if errors else {}
        field_loc = " → ".join(str(p) for p in first.get("loc", []) if p != "body")
        message = first.get("msg", "Validation error")
        logger.warning("Validation error on %s: %s", request.url.path, errors)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body(
                "VALIDATION_ERROR",
                message,
                field_loc or None,
                _get_request_id(request),
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s", request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body(
                "INTERNAL_ERROR",
                "An unexpected error occurred. Please try again or contact support.",
                None,
                _get_request_id(request),
            ),
        )
