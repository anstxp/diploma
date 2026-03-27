from __future__ import annotations

import logging
import time
from typing import Any, Dict

from fastapi import APIRouter, Depends, status

from .dependencies import get_predictor, get_request_id
from .exceptions import AnalysisError, BadRequestError, ModelNotLoadedError
from .models import (
    HealthResponse, InfoResponse,
    RiskAnalyzeRequest, RiskAnalyzeResponse,
    RiskNarrativeRequest, RiskNarrativeResponse,
)

logger = logging.getLogger("risk.risk_api")

router = APIRouter(prefix="/risk", tags=["risk"])



@router.get("/healthz", response_model=HealthResponse, summary="Liveness probe")
async def healthz() -> HealthResponse:
    return HealthResponse(status="ok")



@router.get("/info", response_model=InfoResponse, summary="Model and dataset info")
async def info() -> InfoResponse:
    try:
        predictor = get_predictor()
    except Exception as exc:
        raise ModelNotLoadedError(str(exc))

    extras = predictor.extras
    n_train = int(extras.get("n_train", 0))
    n_val   = int(extras.get("n_val",   0))
    n_test  = int(extras.get("n_test",  0))

    if n_train == 0 or n_val == 0 or n_test == 0:
        history = extras.get("history")
        if isinstance(history, list) and history:
            last = history[-1] if isinstance(history[-1], dict) else {}
            n_train = n_train or int(last.get("n_train", 0))
            n_val   = n_val   or int(last.get("n_val",   0))
            n_test  = n_test  or int(last.get("n_test",  0))

    if n_test == 0:
        tm = extras.get("test_metrics")
        if isinstance(tm, dict):
            ns = [int(m.get("n", 0)) for m in tm.values() if isinstance(m, dict)]
            if ns:
                n_test = max(ns)

    return InfoResponse(
        model_version=str(extras.get("model_version", "1.0")),
        n_features=len(predictor.feature_names),
        n_targets=len(predictor.target_names),
        target_names=predictor.target_names,
        test_metrics=extras.get("test_metrics", {}),
        n_train=n_train,
        n_val=n_val,
        n_test=n_test,
    )



@router.post(
    "/analyze",
    response_model=RiskAnalyzeResponse,
    summary="Multi-task disease risk prediction",
    status_code=status.HTTP_200_OK,
)
async def analyze(
    request: RiskAnalyzeRequest,
    request_id: str = Depends(get_request_id),
) -> Dict[str, Any]:
    t0 = time.perf_counter()

    try:
        predictor = get_predictor()
    except Exception as exc:
        raise ModelNotLoadedError(str(exc))

    payload: Dict[str, Any] = dict(request.labs or {})
    if request.sex is not None:
        payload["sex"] = request.sex
    if request.age is not None:
        payload["age"] = request.age
    if request.bmi is not None:
        payload["bmi"] = request.bmi
    if request.waist_cm is not None:
        payload["waist_cm"] = request.waist_cm
    if request.sbp is not None:
        payload["sbp"] = request.sbp
    if request.dbp is not None:
        payload["dbp"] = request.dbp
    if request.pulse is not None:
        payload["pulse"] = request.pulse

    logger.info(f"[{request_id}] /risk/analyze keys={sorted(payload.keys())}")

    try:
        prediction = predictor.predict(payload)
    except Exception as exc:
        logger.exception("Risk prediction error")
        raise AnalysisError(f"Risk prediction error: {exc}") from exc

    risks_out = []
    for r in prediction.risks:

        risks_out.append({
            "target": r.target,
            "name_ua": r.name_ua,
            "name_en": r.name_en,
            "probability": round(r.probability, 4),
            "risk_tier": r.risk_tier,
            "population_prevalence": round(r.population_prevalence, 4),
            "risk_ratio_vs_baseline": round(r.risk_ratio_vs_baseline, 3),
            "odds_ratio_vs_baseline": round(r.odds_ratio_vs_baseline, 3),
            "top_drivers": [
                {
                    "feature": d.feature,
                    "value": d.value,
                    "z_score": round(d.z_score, 3),
                    "contribution": round(d.contribution, 3),
                    "direction": d.direction,
                }
                for d in (prediction.top_drivers.get(r.target) or [])
            ],
        })

    elapsed_ms = (time.perf_counter() - t0) * 1000
    return {
        "risks": risks_out,
        "overall_tier": prediction.overall_tier,
        "n_features_provided": prediction.n_features_provided,
        "n_features_total": prediction.n_features_total,
        "model_version": prediction.model_version,

        "dropped_keys": prediction.dropped_keys,
        "request_id": request_id,
        "processing_time_ms": round(elapsed_ms, 2),
    }



@router.post(
    "/analyze/narrative",
    summary="Multi-task risk → human-readable narrative report",
    status_code=status.HTTP_200_OK,
)
async def analyze_narrative(
    request: RiskNarrativeRequest,
    request_id: str = Depends(get_request_id),
) -> Dict[str, Any]:
    t0 = time.perf_counter()

    try:
        predictor = get_predictor()
    except Exception as exc:
        raise ModelNotLoadedError(str(exc))

    payload: Dict[str, Any] = dict(request.labs or {})
    for k in ("sex", "age", "bmi", "waist_cm", "sbp", "dbp", "pulse"):
        v = getattr(request, k, None)
        if v is not None:
            payload[k] = v

    if request.context is not None:
        payload["context"] = request.context

    lang = request.lang or "uk"
    logger.info(f"[{request_id}] /risk/analyze/narrative lang={lang}")

    try:
        prediction = predictor.predict(payload)
    except Exception as exc:
        raise AnalysisError(f"Risk prediction error: {exc}") from exc

    from .narrative import build_narrative
    report = build_narrative(prediction, lang=lang, payload=payload)

    elapsed_ms = (time.perf_counter() - t0) * 1000
    out = report.to_dict()
    out["request_id"] = request_id
    out["processing_time_ms"] = round(elapsed_ms, 2)
    return out
