
from __future__ import annotations

import sys
import time
import uuid
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Literal, Optional, Union

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("hemax.cbc")


try:
    from cbc_api import analyze_cbc_payload
    logger.info("cbc_api engine loaded successfully")
except ImportError as exc:
    logger.critical("Cannot import cbc_api: %s", exc)
    sys.exit(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("CBC API starting up…")
    yield
    logger.info("CBC API shutting down.")


app = FastAPI(
    title="Hemax CBC Analysis API",
    description=(
        "Educational CBC (Complete Blood Count) interpretation engine.\n\n"
        "**Not a medical device. Not a substitute for clinical judgement.**\n\n"
        "Accepts CBC values (with or without a differential), patient sex/age, "
        "and optional lab-specific reference overrides. Returns structured flags, "
        "pattern signals, combo interpretations, and next-step recommendations."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=512)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)



class LabValue(BaseModel):
    model_config = {"arbitrary_types_allowed": True}


LabField = Union[float, str, None]


class RefRangeOverride(BaseModel):
    low: Optional[float] = Field(None, description="Lower bound (inclusive). Omit to keep engine default.")
    high: Optional[float] = Field(None, description="Upper bound (inclusive). Omit to keep engine default.")


class SeverityBandOverride(BaseModel):
    mild: Optional[float] = None
    moderate: Optional[float] = None
    severe: Optional[float] = None


class SeverityThresholdsOverride(BaseModel):
    wbc_high: Optional[SeverityBandOverride] = None
    wbc_low: Optional[SeverityBandOverride] = None
    anc_high: Optional[SeverityBandOverride] = None
    anc_low: Optional[SeverityBandOverride] = None
    plt_high: Optional[SeverityBandOverride] = None
    plt_low: Optional[SeverityBandOverride] = None
    hgb_low_female: Optional[SeverityBandOverride] = None
    hgb_low_male: Optional[SeverityBandOverride] = None
    mcv_micro: Optional[float] = None
    mcv_macro: Optional[float] = None
    nlr_high_cutoff: Optional[float] = None


class EngineConfigOverride(BaseModel):
    severity_thresholds: Optional[SeverityThresholdsOverride] = None
    lab_order: Optional[List[str]] = Field(
        None,
        description="Override the display order of lab cards. Provide list of analyte codes.",
    )
    signal_priority: Optional[Dict[str, int]] = Field(
        None,
        description="Override priority scores for individual signal IDs.",
    )


class ClinicalContext(BaseModel):
    model_config = ConfigDict(extra="allow")

    has_diabetes: Optional[bool] = Field(None, description="Diagnosed diabetes mellitus (any type).")
    has_hypertension: Optional[bool] = Field(None, description="Diagnosed arterial hypertension.")
    has_ckd: Optional[bool] = Field(None, description="Chronic kidney disease (any stage).")
    has_kidney_disease: Optional[bool] = Field(None, description="Legacy alias for has_ckd.")
    has_liver_disease: Optional[bool] = Field(None, description="Hepatitis / cirrhosis / NAFLD.")
    has_cardiovascular_disease: Optional[bool] = Field(None, description="Prior MI, stroke, CAD, or PAD.")
    has_cardiac: Optional[bool] = Field(None, description="Legacy alias for has_cardiovascular_disease.")
    has_thyroid: Optional[bool] = Field(None, description="Thyroid disorder.")
    has_anemia_history: Optional[bool] = Field(None, description="Prior anemia diagnosis.")
    has_autoimmune: Optional[bool] = Field(None, description="Autoimmune disease (lupus, RA, etc.).")
    has_cancer_history: Optional[bool] = Field(None, description="Prior cancer diagnosis.")
    recent_surgery: Optional[bool] = Field(None, description="Recent surgical procedure.")

    on_statins: Optional[bool] = Field(None, description="Statin therapy.")
    on_acei_arb: Optional[bool] = Field(None, description="ACE inhibitor or ARB.")
    on_diuretics: Optional[bool] = Field(None, description="Loop / thiazide / K-sparing diuretic.")
    on_oral_diabetics: Optional[bool] = Field(None, description="Metformin / sulfonylureas / etc.")
    on_insulin: Optional[bool] = Field(None, description="Insulin therapy.")
    on_oral_anticoagulants: Optional[bool] = Field(None, description="Warfarin / DOAC / aspirin etc.")
    on_corticosteroids: Optional[bool] = Field(None, description="Systemic steroids (prednisone etc.).")

    takes_anticoagulants: Optional[bool] = Field(None, description="Legacy alias for on_oral_anticoagulants.")
    takes_corticosteroids: Optional[bool] = Field(None, description="Legacy alias for on_corticosteroids.")
    takes_statins: Optional[bool] = Field(None, description="Legacy alias for on_statins.")
    takes_metformin: Optional[bool] = Field(None, description="Component of on_oral_diabetics.")
    takes_insulin: Optional[bool] = Field(None, description="Legacy alias for on_insulin.")
    takes_ace_inhibitors: Optional[bool] = Field(None, description="Legacy alias for on_acei_arb.")
    takes_diuretics: Optional[bool] = Field(None, description="Legacy alias for on_diuretics.")
    takes_beta_blockers: Optional[bool] = Field(None, description="Beta blocker therapy.")
    takes_chemotherapy: Optional[bool] = Field(None, description="Active chemotherapy.")
    takes_thyroid_meds: Optional[bool] = Field(None, description="L-thyroxine / antithyroid.")

    smoker: Optional[bool] = Field(None, description="Current smoker.")
    alcohol_regular: Optional[bool] = Field(None, description="Regular or heavy alcohol use.")
    sedentary: Optional[bool] = Field(None, description="Sedentary lifestyle.")

    family_diabetes: Optional[bool] = Field(None, description="Family history of diabetes.")
    family_cvd: Optional[bool] = Field(None, description="Family history of CVD.")
    family_cancer: Optional[bool] = Field(None, description="Family history of cancer.")

    pregnant: Optional[bool] = Field(None, description="Currently pregnant.")
    is_pregnant: Optional[bool] = Field(None, description="Legacy alias for pregnant.")

    @model_validator(mode="after")
    def _unify_aliases(self):
        if self.has_kidney_disease and not self.has_ckd:
            self.has_ckd = True
        if self.has_ckd and not self.has_kidney_disease:
            self.has_kidney_disease = True
        if self.has_cardiac and not self.has_cardiovascular_disease:
            self.has_cardiovascular_disease = True
        if self.has_cardiovascular_disease and not self.has_cardiac:
            self.has_cardiac = True
        if self.is_pregnant and not self.pregnant:
            self.pregnant = True
        if self.pregnant and not self.is_pregnant:
            self.is_pregnant = True
        for legacy, canonical in [
            ("takes_anticoagulants",   "on_oral_anticoagulants"),
            ("takes_corticosteroids",  "on_corticosteroids"),
            ("takes_statins",          "on_statins"),
            ("takes_insulin",          "on_insulin"),
            ("takes_ace_inhibitors",   "on_acei_arb"),
            ("takes_diuretics",        "on_diuretics"),
        ]:
            l, c = getattr(self, legacy), getattr(self, canonical)
            if l and not c:
                setattr(self, canonical, True)
            if c and not l:
                setattr(self, legacy, True)
        if self.takes_metformin and not self.on_oral_diabetics:
            self.on_oral_diabetics = True
        return self


class CBCRequest(BaseModel):

    sex: Optional[str] = Field(
        None,
        description="Patient sex: 'male' / 'female' (or 'm'/'f'/'ч'/'ж').",
        examples=["female", "male"],
    )
    age: Optional[float] = Field(
        None,
        ge=0,
        le=130,
        description="Patient age in years.",
        examples=[34, 7, 65],
    )

    wbc: LabField = Field(None, description="WBC total (10³/µL). Also accepted as LBXWBCSI.")
    neut_pct: LabField = Field(None, description="Neutrophils % (0–100). Also: neutrophils_pct, LBXNEPCT.")
    lymph_pct: LabField = Field(None, description="Lymphocytes % (0–100). Also: lymphocytes_pct, LBXLYPCT.")
    mono_pct: LabField = Field(None, description="Monocytes % (0–100). Also: monocytes_pct, LBXMOPCT.")
    eos_pct: LabField = Field(None, description="Eosinophils % (0–100). Also: eosinophils_pct, LBXEOPCT.")
    baso_pct: LabField = Field(None, description="Basophils % (0–100). Also: basophils_pct, LBXBAPCT.")
    anc: LabField = Field(None, description="Absolute neutrophil count (10³/µL). Also: neutrophils_abs, LBDNENO.")
    alc: LabField = Field(None, description="Absolute lymphocyte count (10³/µL). Also: lymphocytes_abs, LBDLYMNO.")
    amc: LabField = Field(None, description="Absolute monocyte count (10³/µL). Also: monocytes_abs, LBDMONO.")
    aec: LabField = Field(None, description="Absolute eosinophil count (10³/µL). Also: eosinophils_abs, LBDEONO.")
    abc: LabField = Field(None, description="Absolute basophil count (10³/µL). Also: basophils_abs, LBDBANO.")

    rbc: LabField = Field(None, description="Red blood cells (10⁶/µL). Also: RBC, LBXRBCSI.")
    hgb: LabField = Field(None, description="Hemoglobin (g/dL). Also: hb, HGB, LBXHGB.")
    hct: LabField = Field(None, description="Hematocrit (%). Also: HCT, LBXHCT.")
    mcv: LabField = Field(None, description="Mean corpuscular volume (fL). Also: MCV, LBXMCVSI.")
    mch: LabField = Field(None, description="Mean corpuscular hemoglobin (pg). Also: MCH, LBXMCHSI.")
    mchc: LabField = Field(None, description="Mean corpuscular Hb concentration (g/dL). Also: MCHC, LBXMC.")
    rdw: LabField = Field(None, description="Red cell distribution width (%). Also: RDW, LBXRDW.")

    platelets: LabField = Field(None, description="Platelet count alias. Normalised to 'plt'.")
    plt: LabField = Field(None, description="Platelet count (10³/µL). Also: PLT, LBXPLTSI.")
    mpv: LabField = Field(None, description="Mean platelet volume (fL). Also: MPV, LBXMPSI.")

    esr: LabField = Field(
        None,
        description="Erythrocyte sedimentation rate, mm/hour. Adult upper limit: 20 (ШОЕ in Ukrainian labs).",
        examples=[8, 32]
    )

    LBXWBCSI: LabField = Field(None, description="NHANES alias for WBC.")
    LBXNEPCT: LabField = Field(None, description="NHANES alias for Neutrophils %.")
    LBXLYPCT: LabField = Field(None, description="NHANES alias for Lymphocytes %.")
    LBXMOPCT: LabField = Field(None, description="NHANES alias for Monocytes %.")
    LBXEOPCT: LabField = Field(None, description="NHANES alias for Eosinophils %.")
    LBXBAPCT: LabField = Field(None, description="NHANES alias for Basophils %.")
    LBDNENO: LabField = Field(None, description="NHANES alias for ANC.")
    LBDLYMNO: LabField = Field(None, description="NHANES alias for ALC.")
    LBDMONO: LabField = Field(None, description="NHANES alias for AMC.")
    LBDEONO: LabField = Field(None, description="NHANES alias for AEC.")
    LBDBANO: LabField = Field(None, description="NHANES alias for ABC.")
    LBXRBCSI: LabField = Field(None, description="NHANES alias for RBC.")
    LBXHGB: LabField = Field(None, description="NHANES alias for Hemoglobin.")
    LBXHCT: LabField = Field(None, description="NHANES alias for Hematocrit.")
    LBXMCVSI: LabField = Field(None, description="NHANES alias for MCV.")
    LBXMCHSI: LabField = Field(None, description="NHANES alias for MCH.")
    LBXMC: LabField = Field(None, description="NHANES alias for MCHC.")
    LBXRDW: LabField = Field(None, description="NHANES alias for RDW.")
    LBXPLTSI: LabField = Field(None, description="NHANES alias for Platelets.")
    LBXMPSI: LabField = Field(None, description="NHANES alias for MPV.")
    RIAGENDR: Optional[Any] = Field(None, description="NHANES alias for sex (1=male, 2=female).")
    RIDAGEYR: Optional[float] = Field(None, description="NHANES alias for age.")

    ref_ranges: Optional[Dict[str, RefRangeOverride]] = Field(
        None,
        description=(
            "Override built-in reference ranges with your lab's values. "
            "Keys are analyte codes (e.g. `hgb`, `wbc`). "
            "Values in standard units (g/dL for hgb, 10³/µL for wbc, etc.)."
        ),
        examples=[{"hgb": {"low": 11.5, "high": 16.0}, "wbc": {"low": 3.8, "high": 10.5}}],
    )
    config: Optional[EngineConfigOverride] = Field(
        None,
        description="Fine-tune engine severity thresholds, lab display order, or signal priorities.",
    )

    context: Optional[ClinicalContext] = Field(
        default=None,
        description=(
            "Clinical context flags from patient profile. Used to adapt "
            "narrative tone (known diabetic → glycemic control wording, "
            "on anticoagulants → bleeding-risk warnings, etc.). "
            "Both legacy `takes_X` and canonical `on_X` keys are accepted."
        ),
        examples=[{"has_diabetes": True, "on_oral_anticoagulants": True}],
    )

    @field_validator("sex", mode="before")
    @classmethod
    def _normalise_sex(cls, v):
        if v is None:
            return v
        sv = str(v).strip().lower()
        if sv in {"1", "m", "male", "man", "ч", "чоловік"}:
            return "male"
        if sv in {"2", "f", "female", "woman", "ж", "жінка"}:
            return "female"
        return v

    @model_validator(mode="after")
    def _resolve_platelets_alias(self):
        if self.plt is None and self.platelets is not None:
            self.plt = self.platelets
        return self

    @model_validator(mode="after")
    def _validate_physiological_ranges(self):
        LIMITS = {
            "wbc":      (0.0,  1_000_000.0,  "counts"),
            "hgb":      (0.0,  300.0,        "g/dL or g/L"),
            "hct":      (0.0,  100.0,        "% or fraction"),
            "rbc":      (0.0,  10_000_000.0, "counts"),
            "plt":      (0.0,  5_000_000.0,  "counts"),
            "mcv":      (30.0, 180.0,        "fL"),
            "mch":      (5.0,  60.0,         "pg"),
            "mchc":     (15.0, 400.0,        "g/dL or g/L"),
            "rdw":      (5.0,  50.0,         "%"),
            "mpv":      (2.0,  20.0,         "fL"),
            "neut_pct": (0.0,  100.0,        "%"),
            "lymph_pct":(0.0,  100.0,        "%"),
            "mono_pct": (0.0,  100.0,        "%"),
            "eos_pct":  (0.0,  100.0,        "%"),
            "baso_pct": (0.0,  100.0,        "%"),
            "anc":      (0.0,  1_000_000.0,  "counts"),
            "alc":      (0.0,  1_000_000.0,  "counts"),
        }
        errors = []
        for field, (lo, hi, unit) in LIMITS.items():
            val = getattr(self, field, None)
            if val is None:
                continue
            try:
                v = float(val)
            except (TypeError, ValueError):
                continue
            if v < lo or v > hi:
                errors.append(
                    f"{field}={v} поза фізіологічними межами ({lo}–{hi} {unit})"
                )
        if errors:
            raise ValueError("Неможливі значення: " + "; ".join(errors))
        return self


    def to_engine_payload(self) -> Dict[str, Any]:
        d = self.model_dump(exclude_none=True)
        d.pop("platelets", None)
        if "ref_ranges" in d and d["ref_ranges"] is not None:
            d["ref_ranges"] = {k: v for k, v in d["ref_ranges"].items()}
        if "config" in d and d["config"] is not None:
            raw_cfg = d["config"]
            if "severity_thresholds" in raw_cfg and raw_cfg["severity_thresholds"] is not None:
                raw_cfg["severity_thresholds"] = {
                    k: v for k, v in raw_cfg["severity_thresholds"].items() if v is not None
                }
            d["config"] = raw_cfg
        return d



class CBCResponse(BaseModel):
    request_id: str
    processing_time_ms: float
    version: str
    profile: Dict[str, Any]
    meta: Dict[str, Any]
    summary: Dict[str, Any]
    labs: List[Dict[str, Any]]
    flags: Dict[str, Any]
    derived: Dict[str, Any]
    signals: List[Dict[str, Any]]
    combos: List[Dict[str, Any]]
    recommendations: Dict[str, Any]
    disclaimer: str


class BatchCBCRequest(BaseModel):
    records: List[Dict[str, Any]] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Array of CBC payloads. Each item may include an optional 'id' for correlation.",
    )


class BatchCBCResponseItem(BaseModel):
    id: Optional[str] = None
    index: int
    ok: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BatchCBCResponse(BaseModel):
    request_id: str
    processing_time_ms: float
    total: int
    succeeded: int
    failed: int
    results: List[BatchCBCResponseItem]



def _run_engine(payload: Dict[str, Any], lang: str = "uk") -> Dict[str, Any]:
    try:
        from cbc_api.validation import validate_payload
        vres = validate_payload(payload)
    except Exception as exc:
        logger.exception("Validation layer error")
        vres = None

    if vres is not None:
        if vres.has_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "validation_failed",
                    "message": ("Не вдалося перевірити дані — див. список помилок."
                                if lang == "uk"
                                else "Input validation failed — see errors list."),
                    **vres.to_dict(lang=lang),
                },
            )
        payload = vres.normalised

    try:
        result = analyze_cbc_payload(payload)
    except Exception as exc:
        logger.exception("Engine error for payload keys=%s", list(payload.keys()))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"CBC engine error: {exc}",
        ) from exc

    if vres is not None and vres.warnings:
        result["validation"] = vres.to_dict(lang=lang)
    return result



@app.middleware("http")
async def _request_id_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = req_id
    request.state.start_time = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - request.state.start_time) * 1000
    response.headers["X-Request-ID"] = req_id
    response.headers["X-Processing-Time-Ms"] = f"{elapsed_ms:.2f}"
    return response



@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", "unknown")
    logger.exception("Unhandled exception [%s]", req_id)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred.",
            "request_id": req_id,
        },
    )



@app.get(
    "/",
    tags=["Meta"],
    summary="API root — health check + version",
    response_description="Basic health and version info.",
)
async def root():
    return {
        "service": "Hemax CBC Analysis API",
        "version": "1.0.0",
        "status": "ok",
        "endpoints": {
            "analyze": "POST /analyze",
            "batch":   "POST /analyze/batch",
            "fields":  "GET  /fields",
            "health":  "GET  /health",
            "docs":    "GET  /docs",
        },
        "disclaimer": (
            "Educational tool only. Not a medical device. "
            "Not a substitute for clinical assessment by a qualified professional."
        ),
    }


@app.get(
    "/health",
    tags=["Meta"],
    summary="Health check",
)
async def health():
    return {"status": "ok", "engine": "cbc_api"}


@app.get(
    "/fields",
    tags=["Meta"],
    summary="Accepted input field names and their units",
    description=(
        "Returns a reference of every analyte code, its unit, "
        "and the full list of accepted field aliases (including NHANES names)."
    ),
)
async def fields():
    return {
        "analytes": {
            "wbc":      {"unit": "10³/µL", "aliases": ["wbc","WBC","LBXWBCSI"]},
            "neut_pct": {"unit": "%",       "aliases": ["neut_pct","neutrophils_pct","NEUT%","LBXNEPCT"]},
            "lymph_pct":{"unit": "%",       "aliases": ["lymph_pct","lymphocytes_pct","LYMPH%","LBXLYPCT"]},
            "mono_pct": {"unit": "%",       "aliases": ["mono_pct","monocytes_pct","LBXMOPCT"]},
            "eos_pct":  {"unit": "%",       "aliases": ["eos_pct","eosinophils_pct","LBXEOPCT"]},
            "baso_pct": {"unit": "%",       "aliases": ["baso_pct","basophils_pct","LBXBAPCT"]},
            "anc":      {"unit": "10³/µL", "aliases": ["anc","neutrophils_abs","LBDNENO"], "note": "Auto-computed from WBC × neut_pct if omitted."},
            "alc":      {"unit": "10³/µL", "aliases": ["alc","lymphocytes_abs","LBDLYMNO"], "note": "Auto-computed from WBC × lymph_pct if omitted."},
            "amc":      {"unit": "10³/µL", "aliases": ["amc","monocytes_abs","LBDMONO"], "note": "Auto-computed if omitted."},
            "aec":      {"unit": "10³/µL", "aliases": ["aec","eosinophils_abs","LBDEONO"], "note": "Auto-computed if omitted."},
            "abc":      {"unit": "10³/µL", "aliases": ["abc","basophils_abs","LBDBANO"], "note": "Auto-computed if omitted."},
            "rbc":      {"unit": "10⁶/µL", "aliases": ["rbc","RBC","LBXRBCSI"]},
            "hgb":      {"unit": "g/dL",   "aliases": ["hgb","hb","HGB","LBXHGB"]},
            "hct":      {"unit": "%",       "aliases": ["hct","HCT","LBXHCT"]},
            "mcv":      {"unit": "fL",      "aliases": ["mcv","MCV","LBXMCVSI"]},
            "mch":      {"unit": "pg",      "aliases": ["mch","MCH","LBXMCHSI"]},
            "mchc":     {"unit": "g/dL",   "aliases": ["mchc","MCHC","LBXMC"]},
            "rdw":      {"unit": "%",       "aliases": ["rdw","RDW","LBXRDW"]},
            "plt":      {"unit": "10³/µL", "aliases": ["plt","platelets","PLT","LBXPLTSI"]},
            "mpv":      {"unit": "fL",      "aliases": ["mpv","MPV","LBXMPSI"]},
        },
        "demographics": {
            "sex": {
                "accepted": ["male","female","m","f","M","F","ч","ж","1","2"],
                "nhanes": "RIAGENDR (1=male, 2=female)",
            },
            "age": {
                "unit": "years",
                "nhanes": "RIDAGEYR",
                "note": "Used for paediatric reference ranges (< 18 years).",
            },
        },
        "unit_formats": {
            "description": "Values can be bare numbers or strings with embedded units.",
            "examples": [
                "7.8",
                "7.8 10^3/µL",
                "7800 /µL",
                "7.8 x10^9/L",
            ],
            "note": "When units are embedded, the engine auto-converts to standard units.",
        },
    }


@app.post(
    "/analyze",
    tags=["Analysis"],
    summary="Analyse a single CBC result",
    response_description="Structured interpretation with flags, signals, combos, and recommendations.",
    status_code=200,
)
async def analyze(request: Request, body: CBCRequest) -> Dict[str, Any]:
    req_id: str = request.state.request_id
    t0 = request.state.start_time

    payload = body.to_engine_payload()
    logger.info("[%s] /analyze keys=%s sex=%s age=%s", req_id, sorted(payload.keys()), payload.get("sex"), payload.get("age"))

    result = _run_engine(payload)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    result["request_id"] = req_id
    result["processing_time_ms"] = round(elapsed_ms, 2)
    return result


@app.post(
    "/analyze/batch",
    tags=["Analysis"],
    summary="Analyse multiple CBC records in one request",
    response_description="Array of per-record results, including any per-record errors.",
    status_code=200,
)
async def analyze_batch(request: Request, body: BatchCBCRequest) -> BatchCBCResponse:
    req_id: str = request.state.request_id
    t0 = request.state.start_time

    logger.info("[%s] /analyze/batch records=%d", req_id, len(body.records))

    results: List[BatchCBCResponseItem] = []
    succeeded = 0
    failed = 0

    for idx, raw_record in enumerate(body.records):
        record_id = str(raw_record.get("id", "")) or None
        try:
            result = _run_engine(raw_record)
            results.append(BatchCBCResponseItem(
                id=record_id,
                index=idx,
                ok=True,
                result=result,
            ))
            succeeded += 1
        except HTTPException as exc:
            detail = exc.detail
            if isinstance(detail, dict):
                err_msg = detail.get("message") or str(detail)
            else:
                err_msg = str(detail)
            logger.info("[%s] batch record %d validation/engine error: %s",
                        req_id, idx, err_msg)
            results.append(BatchCBCResponseItem(
                id=record_id,
                index=idx,
                ok=False,
                error=err_msg,
            ))
            failed += 1
        except Exception as exc:
            logger.warning("[%s] batch record %d error: %s", req_id, idx, exc)
            results.append(BatchCBCResponseItem(
                id=record_id,
                index=idx,
                ok=False,
                error=str(exc),
            ))
            failed += 1

    elapsed_ms = (time.perf_counter() - t0) * 1000
    return BatchCBCResponse(
        request_id=req_id,
        processing_time_ms=round(elapsed_ms, 2),
        total=len(body.records),
        succeeded=succeeded,
        failed=failed,
        results=results,
    )



try:
    from cbc_api.narrative import build_narrative
    _HAS_NARRATIVE = True
    logger.info("cbc_api.narrative loaded (Phase 4 narrative layer active)")
except Exception as exc:                      # pragma: no cover
    _HAS_NARRATIVE = False
    logger.warning("narrative layer unavailable: %s", exc)


class NarrativeRequest(CBCRequest):
    lang: Literal["uk", "en"] = Field(
        default="uk",
        description="Language for the human-readable narrative. 'uk' = Ukrainian, 'en' = English."
    )


@app.post(
    "/analyze/narrative",
    tags=["Analysis"],
    summary="Analyse a CBC and return a human-readable narrative",
    response_description=(
        "A structured narrative report, designed for display to end-users who "
        "do not have medical training. Contains 1-N story cards, each with a "
        "plain-language title, body, list of next steps, and red-flag symptoms."
    ),
    status_code=200,
)
async def analyze_narrative(request: Request, body: NarrativeRequest) -> Dict[str, Any]:
    if not _HAS_NARRATIVE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Narrative layer is not available in this deployment.",
        )

    req_id: str = request.state.request_id
    t0 = request.state.start_time

    payload = body.to_engine_payload()
    lang = body.lang
    logger.info("[%s] /analyze/narrative keys=%s sex=%s age=%s lang=%s",
                req_id, sorted(payload.keys()), payload.get("sex"),
                payload.get("age"), lang)

    raw = _run_engine(payload, lang=lang)
    report = build_narrative(raw, lang=lang)

    elapsed_ms = (time.perf_counter() - t0) * 1000
    out = report.to_dict()
    if "validation" in raw:
        out["validation"] = raw["validation"]
    out["request_id"] = req_id
    out["processing_time_ms"] = round(elapsed_ms, 2)
    return out
