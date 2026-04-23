from __future__ import annotations

import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from engine.multimodal_inference import MultimodalDermaPredictor

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
log = logging.getLogger("derma_api")

_predictor: Optional[MultimodalDermaPredictor] = None


def get_predictor() -> MultimodalDermaPredictor:
    global _predictor
    if _predictor is None:
        model_dir = Path(os.environ.get(
            "DERMA_MODEL_DIR", "/app/model_out/multimodal/late_fusion"
        ))
        log.info(f"Loading DERMA multimodal model from {model_dir}")
        _predictor = MultimodalDermaPredictor(model_dir, device="cpu")
        log.info(f"DERMA predictor ready: {_predictor.model_name}")
    return _predictor


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        get_predictor()
        log.info("Startup complete — DERMA service ready")
    except Exception as e:
        log.error(f"Model load failed: {e}", exc_info=True)
    yield
    log.info("Shutdown")


app = FastAPI(
    title="HEMAX_DERMA API",
    description="Multimodal skin lesion classifier (image + patient metadata)",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)



class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "derma"
    model_loaded: bool


class InfoResponse(BaseModel):
    service: str = "derma"
    version: str = "2.0.0"
    model_architecture: str
    classes: list
    image_size: int
    meta_dim: int
    calibration_strategy: Optional[str] = None
    temperature: Optional[float] = None


class TopKItem(BaseModel):
    class_code: str
    class_name: str
    probability: float


class AnalyzeResponse(BaseModel):
    request_id: str
    top_class: str
    top_class_name: str
    confidence: float
    severity: str
    top_k: list
    all_probabilities: dict
    meta_used: dict
    processing_time_ms: float



@app.get("/derma/healthz", response_model=HealthResponse)
def healthz():
    try:
        loaded = _predictor is not None
        if not loaded:
            return HealthResponse(status="degraded", model_loaded=False)
        return HealthResponse(status="ok", model_loaded=True)
    except Exception:
        return HealthResponse(status="degraded", model_loaded=False)


@app.get("/derma/info", response_model=InfoResponse)
def info():
    p = get_predictor()
    return InfoResponse(
        model_architecture=p.model_name,
        classes=p.classes,
        image_size=p.image_size,
        meta_dim=p.meta_stats["meta_dim"],
        calibration_strategy=(p.calibration or {}).get("production_strategy"),
        temperature=(p.calibration or {}).get("temperature"),
    )


@app.post("/derma/analyze", response_model=AnalyzeResponse)
async def analyze(
    image: UploadFile = File(..., description="JPG/PNG dermoscopy image"),
    age: Optional[float] = Form(None, ge=0, le=120,
                                  description="Patient age in years"),
    sex: Optional[str] = Form(None, description="male/female/unknown"),
    localization: Optional[str] = Form(
        None, description="Anatomical site (back, face, scalp, ...)",
    ),
    top_k: int = Form(3, ge=1, le=7),
):
    request_id = str(uuid.uuid4())
    t0 = time.time()

    if image.content_type not in ("image/jpeg", "image/png", "image/jpg"):
        raise HTTPException(415, f"Unsupported content type: {image.content_type}. "
                                  "Send image/jpeg or image/png.")

    image_bytes = await image.read()
    if len(image_bytes) == 0:
        raise HTTPException(400, "Empty image upload")
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(413, "Image too large (max 10MB)")

    from engine.multimodal_inference import InvalidImageError

    try:
        predictor = get_predictor()
        result = predictor.predict(
            image_bytes=image_bytes,
            age=age,
            sex=sex,
            localization=localization,
            top_k=top_k,
        )
    except InvalidImageError as e:
        log.info(f"[{request_id}] Invalid image upload: {e}")
        raise HTTPException(400, f"Invalid image: {e}")
    except Exception as e:
        log.error(f"Prediction failed: {e}", exc_info=True)
        raise HTTPException(500, f"Inference error: {e}")

    elapsed_ms = (time.time() - t0) * 1000
    log.info(f"[{request_id}] {result['top_class']} "
             f"({result['confidence']:.2%}) in {elapsed_ms:.0f}ms")

    return AnalyzeResponse(
        request_id=request_id,
        top_class=result["top_class"],
        top_class_name=result["top_class_name"],
        confidence=result["confidence"],
        severity=result["severity"],
        top_k=result["top_k"],
        all_probabilities=result["all_probabilities"],
        meta_used=result["meta_used"],
        processing_time_ms=round(elapsed_ms, 1),
    )


@app.get("/")
def root():
    return {
        "service": "HEMAX_DERMA",
        "version": "2.0.0",
        "endpoints": {
            "health": "/derma/healthz",
            "info":   "/derma/info",
            "analyze": "/derma/analyze (POST multipart with image + optional metadata)",
            "docs":   "/docs",
        },
    }
