from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from .dependencies import get_predictor
from .exceptions import RiskAPIError
from .middleware import RequestContextMiddleware
from .router import router as risk_router

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("risk.risk_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        get_predictor()
        logger.info("Risk model warmed up at startup")
    except Exception as exc:
        logger.error(f"Failed to load risk model at startup: {exc}")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="HEMAX_RISK API",
        version="1.0.0",
        description=(
            "Multi-task neural network for 6 disease risks "
            "(hypertension, diabetes, high cholesterol, CHD, CHF, stroke). "
            "Trained on NHANES 1999-2023 (~42k records, mean test AUC = 0.852)."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(RequestContextMiddleware)

    @app.exception_handler(RiskAPIError)
    async def risk_api_error_handler(request: Request, exc: RiskAPIError):
        rid = getattr(request.state, "request_id", None)
        logger.warning(f"[{rid}] {request.url.path} -> {exc.status_code}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
                "request_id": rid,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        rid = getattr(request.state, "request_id", None)
        logger.warning(f"[{rid}] Validation error on {request.url.path}: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation failed",
                "details": exc.errors(),
                "request_id": rid,
            },
        )

    app.include_router(risk_router)

    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "service": "HEMAX_RISK",
            "version": app.version,
            "docs": "/docs",
            "health": "/risk/healthz",
            "info": "/risk/info",
        }

    return app


app = create_app()
