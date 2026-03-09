from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .exceptions import register_exception_handlers
from .middleware import RequestIDMiddleware, TimingMiddleware
from .router import router, public_router

logger = logging.getLogger("chem.chem_api")


logging.basicConfig(
    level=os.getenv("HEMAX_LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)



def create_app(
    *,
    title: str = "Hemax · Clinical Chemistry API",
    description: str = (
        "Biochemistry interpretation module for the **Hemax** health platform.\n\n"
        "Accepts raw lab panels and returns structured clinical signals, "
        "derived values, pattern-based alerts, and next-step recommendations.\n\n"
        "All interpretations are **educational** — not a substitute for clinical judgement."
    ),
    version: str = "1.0.0",
    root_path: str = "",
    cors_origins: list[str] | None = None,
    docs_url: str | None = "/docs",
    redoc_url: str | None = "/redoc",
) -> FastAPI:
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        root_path=root_path,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_tags=[
            {
                "name": "Clinical Chemistry",
                "description": "Biochemistry panel analysis, lab catalogue, and module health.",
            }
        ],
    )

    origins = cors_origins
    if origins is None:
        env_origins = os.getenv("HEMAX_CORS_ORIGINS", "*")
        origins = [o.strip() for o in env_origins.split(",") if o.strip()] or ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time-Ms"],
    )

    app.add_middleware(TimingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    register_exception_handlers(app)

    app.include_router(router)
    app.include_router(public_router)

    @app.on_event("startup")
    async def _startup() -> None:
        logger.info("Hemax Chem API starting up (version=%s)", version)

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        logger.info("Hemax Chem API shutting down")

    return app



app = create_app()
