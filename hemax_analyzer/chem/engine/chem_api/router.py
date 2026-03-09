from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from .dependencies import get_api_key, get_request_id
from .exceptions import AnalysisError, BadRequestError
from .models import (
    ChemAnalyzeRequest,
    ChemAnalyzeResponse,
    ChemNarrativeRequest,
    ChemNarrativeResponse,
    HealthResponse,
    InfoResponse,
    LabCardOut,
    RefRangeOut,
)

from .chem.analyze import analyze_chem_payload, ALIASES
from .chem.knowledge import LABS

logger = logging.getLogger("chem.chem_api")

router = APIRouter(
    prefix="/chem",
    tags=["Clinical Chemistry"],
    dependencies=[Depends(get_api_key)],
)

public_router = APIRouter(
    prefix="/chem",
    tags=["Clinical Chemistry"],
)



@router.post(
    "/analyze",
    response_model=ChemAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze biochemistry panel",
    description=(
        "Accepts a structured lab payload and returns a full clinical chemistry "
        "interpretation: per-lab cards with flags, pattern-based signals (glycaemia, "
        "lipids, kidney, liver, electrolytes, iron, vitamins), combo patterns, "
        "recommendations, and derived values (eGFR, LDL, anion gap, …).\n\n"
        "Lab values may include units as strings (`'5.5 mmol/L'`) or be bare numbers "
        "(assumed to be in the canonical unit for that analyte). "
        "Both SI and conventional units are accepted."
    ),
    responses={
        200: {"description": "Analysis completed successfully."},
        400: {"description": "Payload structurally invalid or empty."},
        422: {"description": "Pydantic validation error."},
        500: {"description": "Internal analysis error."},
    },
)
async def analyze(
    body: ChemAnalyzeRequest,
    request_id: Optional[str] = Depends(get_request_id),
) -> ChemAnalyzeResponse:
    import time as _time
    t0 = _time.perf_counter()
    payload = body.to_engine_payload()

    if not payload:
        raise BadRequestError("Request body must contain at least one lab value.")

    try:
        result = analyze_chem_payload(payload)
    except Exception as exc:
        logger.exception("Analysis engine error (request_id=%s)", request_id)
        raise AnalysisError(f"Analysis failed: {exc}") from exc

    elapsed_ms = round((_time.perf_counter() - t0) * 1000, 2)
    if isinstance(result, dict):
        result["request_id"] = request_id
        result["processing_time_ms"] = elapsed_ms
    return result  # type: ignore[return-value]



@router.get(
    "/labs",
    summary="List all supported lab codes",
    description="Returns every lab code the engine recognises, with its name, unit, "
                "reference ranges, and group.",
    status_code=status.HTTP_200_OK,
)
async def list_labs() -> Dict[str, Any]:
    items = []
    for code, lab in LABS.items():
        rr_any = lab.ref_any
        rr_male = lab.ref_male
        rr_female = lab.ref_female
        items.append({
            "code": code,
            "name": lab.name,
            "unit": lab.unit,
            "group": lab.group,
            "what": lab.what,
            "tips": list(lab.tips),
            "ref": {
                "any": {"low": rr_any.low, "high": rr_any.high},
                "male": {"low": rr_male.low, "high": rr_male.high},
                "female": {"low": rr_female.low, "high": rr_female.high},
            },
            "aliases": ALIASES.get(code, [code]),
        })
    return {"count": len(items), "labs": items}



@router.get(
    "/labs/{code}",
    summary="Get detail for a single lab code",
    status_code=status.HTTP_200_OK,
)
async def get_lab(code: str) -> Dict[str, Any]:
    code = code.lower().strip()
    if code not in LABS:
        resolved = next(
            (canon for canon, aliases in ALIASES.items() if code in [a.lower() for a in aliases]),
            None,
        )
        if resolved is None or resolved not in LABS:
            raise BadRequestError(f"Unknown lab code: '{code}'. Use GET /chem/labs for the full list.")
        code = resolved

    lab = LABS[code]
    rr_any = lab.ref_any
    rr_male = lab.ref_male
    rr_female = lab.ref_female

    return {
        "code": code,
        "name": lab.name,
        "unit": lab.unit,
        "group": lab.group,
        "what": lab.what,
        "tips": list(lab.tips),
        "ref": {
            "any": {"low": rr_any.low, "high": rr_any.high},
            "male": {"low": rr_male.low, "high": rr_male.high},
            "female": {"low": rr_female.low, "high": rr_female.high},
        },
        "aliases": ALIASES.get(code, [code]),
    }



@public_router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness probe",
    description="Returns 200 OK when the module is running. Use for load-balancer health checks.",
    status_code=status.HTTP_200_OK,
)
async def health() -> HealthResponse:
    return HealthResponse()



@router.get(
    "/info",
    response_model=InfoResponse,
    summary="Module metadata",
    description="Returns engine version, list of supported lab codes, and all recognised aliases.",
    status_code=status.HTTP_200_OK,
)
async def info() -> InfoResponse:
    from .chem.analyze import analyze_chem_payload as _eng
    dummy = analyze_chem_payload({})
    engine_version: str = dummy.get("version", "unknown")

    return InfoResponse(
        engine_version=engine_version,
        supported_labs=list(LABS.keys()),
        supported_aliases=ALIASES,
    )



import time
import uuid

try:
    from .narrative import build_narrative
    _HAS_NARRATIVE = True
    logger.info("chem narrative layer loaded (Phase 4)")
except Exception as exc:                                 # pragma: no cover
    _HAS_NARRATIVE = False
    logger.warning("chem narrative layer unavailable: %s", exc)


@router.post(
    "/analyze/narrative",
    summary="Analyze chemistry panel and return human-readable narrative",
    response_description=(
        "Structured narrative report designed for end-users without medical "
        "training. Returns 1-N story cards, each with title, body, actions, "
        "and red flags, in Ukrainian or English."
    ),
    status_code=status.HTTP_200_OK,
)
async def analyze_narrative(
    request: ChemNarrativeRequest,
    request_id: str = Depends(get_request_id),
) -> Dict[str, Any]:
    if not _HAS_NARRATIVE:
        raise BadRequestError("Narrative layer is not available in this deployment.")

    t0 = time.perf_counter()

    payload: Dict[str, Any] = dict(request.labs or {})
    if request.sex is not None:
        payload["sex"] = request.sex
    if request.age is not None:
        payload["age"] = request.age
    if request.fasting_hours is not None:
        payload["fasting_hours"] = request.fasting_hours
    if request.fasting_8h is not None:
        payload["fasting_8h"] = request.fasting_8h
    if request.ref_ranges is not None:
        payload["ref_ranges"] = {
            k: (v.model_dump() if hasattr(v, "model_dump") else v)
            for k, v in request.ref_ranges.items()
        }
    if request.context is not None:
        payload["clinical_context"] = request.context.model_dump(exclude_none=True)

    lang = request.lang or "uk"

    logger.info("[%s] /chem/analyze/narrative keys=%s sex=%s age=%s lang=%s clinical=%s",
                request_id, sorted(payload.keys()),
                payload.get("sex"), payload.get("age"), lang,
                payload.get("clinical_context"))

    try:
        raw = analyze_chem_payload(payload)
    except Exception as exc:
        logger.exception("CHEM engine error")
        raise AnalysisError(f"CHEM engine error: {exc}") from exc

    report = build_narrative(raw, lang=lang)

    elapsed_ms = (time.perf_counter() - t0) * 1000
    out = report.to_dict()
    out["request_id"] = request_id
    out["processing_time_ms"] = round(elapsed_ms, 2)
    return out
