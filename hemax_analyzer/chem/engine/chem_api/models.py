from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, model_validator



class RefRangeOverride(BaseModel):
    low: Optional[float] = Field(None, description="Lower bound (inclusive). Omit if not applicable.")
    high: Optional[float] = Field(None, description="Upper bound (inclusive). Omit if not applicable.")


class ClinicalContext(BaseModel):
    model_config = ConfigDict(extra="allow")

    has_diabetes: Optional[bool] = Field(
        None, description="Patient has diagnosed diabetes mellitus (any type).")
    has_hypertension: Optional[bool] = Field(
        None, description="Patient has diagnosed arterial hypertension.")
    has_ckd: Optional[bool] = Field(
        None, description="Patient has chronic kidney disease (any stage).")
    has_kidney_disease: Optional[bool] = Field(
        None, description="Legacy alias for has_ckd.")
    has_liver_disease: Optional[bool] = Field(
        None, description="Patient has known hepatitis / cirrhosis / NAFLD.")
    has_cardiovascular_disease: Optional[bool] = Field(
        None, description="Prior MI, stroke, established CAD, or PAD.")
    has_cardiac: Optional[bool] = Field(
        None, description="Legacy alias for has_cardiovascular_disease.")
    has_thyroid: Optional[bool] = Field(None, description="Thyroid disorder.")
    has_anemia_history: Optional[bool] = Field(None, description="Prior anemia.")
    has_autoimmune: Optional[bool] = Field(None, description="Autoimmune disease.")
    has_cancer_history: Optional[bool] = Field(None, description="Prior cancer.")
    recent_surgery: Optional[bool] = Field(None, description="Recent surgery.")

    on_statins: Optional[bool] = Field(
        None, description="Currently on statin therapy.")
    on_acei_arb: Optional[bool] = Field(
        None, description="Currently on ACE inhibitor or ARB.")
    on_diuretics: Optional[bool] = Field(
        None, description="Currently on any diuretic (loop, thiazide, K-sparing).")
    on_oral_diabetics: Optional[bool] = Field(
        None, description="Currently on oral diabetic medication.")
    on_insulin: Optional[bool] = Field(
        None, description="Currently on insulin therapy.")
    on_oral_anticoagulants: Optional[bool] = Field(
        None, description="Currently on warfarin / DOAC.")
    on_corticosteroids: Optional[bool] = Field(
        None, description="Currently on systemic corticosteroids.")

    takes_anticoagulants: Optional[bool] = Field(None, description="Legacy alias.")
    takes_corticosteroids: Optional[bool] = Field(None, description="Legacy alias.")
    takes_statins: Optional[bool] = Field(None, description="Legacy alias.")
    takes_metformin: Optional[bool] = Field(None, description="Legacy.")
    takes_insulin: Optional[bool] = Field(None, description="Legacy alias.")
    takes_ace_inhibitors: Optional[bool] = Field(None, description="Legacy alias.")
    takes_diuretics: Optional[bool] = Field(None, description="Legacy alias.")
    takes_beta_blockers: Optional[bool] = Field(None, description="Beta blocker.")
    takes_chemotherapy: Optional[bool] = Field(None, description="Active chemo.")
    takes_thyroid_meds: Optional[bool] = Field(None, description="Thyroid meds.")

    smoker: Optional[bool] = Field(None, description="Current smoker.")
    alcohol_regular: Optional[bool] = Field(None, description="Regular/heavy alcohol.")
    sedentary: Optional[bool] = Field(None, description="Sedentary lifestyle.")

    family_diabetes: Optional[bool] = Field(None, description="Family DM history.")
    family_cvd: Optional[bool] = Field(None, description="Family CVD history.")
    family_cancer: Optional[bool] = Field(None, description="Family cancer history.")

    pregnant: Optional[bool] = Field(
        None, description="Patient is currently pregnant — affects ALP, lipids, iron.")
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
            ("takes_anticoagulants",  "on_oral_anticoagulants"),
            ("takes_corticosteroids", "on_corticosteroids"),
            ("takes_statins",         "on_statins"),
            ("takes_insulin",         "on_insulin"),
            ("takes_ace_inhibitors",  "on_acei_arb"),
            ("takes_diuretics",       "on_diuretics"),
        ]:
            l, c = getattr(self, legacy), getattr(self, canonical)
            if l and not c:
                setattr(self, canonical, True)
            if c and not l:
                setattr(self, legacy, True)
        if self.takes_metformin and not self.on_oral_diabetics:
            self.on_oral_diabetics = True
        return self



class ChemAnalyzeRequest(BaseModel):

    sex: Optional[str] = Field(
        None,
        description="Patient sex: 'male' / 'female' (or 'm'/'f', 'M'/'F', NHANES 1/2). "
                    "Required for sex-specific reference ranges and eGFR.",
        examples=["female"],
    )
    age: Optional[Union[float, int, str]] = Field(
        None,
        description="Patient age in years. Required for eGFR (CKD-EPI 2021).",
        examples=[45],
    )

    labs: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Key-value pairs of lab results. Keys may be canonical codes, "
            "common aliases, or NHANES variable names. Values can be numbers "
            "or strings with units (e.g. '5.5 mmol/L', '92 mg/dL', '6.1%')."
        ),
        examples=[{
            "glucose": "92 mg/dL",
            "a1c": "5.2%",
            "creatinine": "0.8 mg/dL",
            "tchol": "180 mg/dL",
            "hdl": "58 mg/dL",
            "trigly": "90 mg/dL",
        }],
    )

    fasting_hours: Optional[float] = Field(
        None,
        ge=0,
        le=72,
        description="Hours fasted before blood draw. Affects glucose interpretation.",
        examples=[10.0],
    )
    fasting_8h: Optional[bool] = Field(
        None,
        description="Shorthand: True if fasted ≥ 8 h. Overridden by fasting_hours if both supplied.",
    )

    ref_ranges: Optional[Dict[str, RefRangeOverride]] = Field(
        None,
        description=(
            "Lab-specific reference ranges from the patient's actual lab report. "
            "Keyed by canonical lab code. Takes precedence over built-in defaults."
        ),
        examples=[{"glucose": {"low": 74, "high": 106}}],
    )

    context: Optional[ClinicalContext] = Field(
        None,
        description=(
            "Patient's clinical history and current medications. All fields "
            "optional. Used by the narrative layer to tailor messaging "
            "(known diabetic vs new diagnosis, on statins vs untreated, etc.)."
        ),
        examples=[{"has_diabetes": True, "on_oral_diabetics": True}],
    )

    @model_validator(mode="before")
    @classmethod
    def _flatten_top_level_labs(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        KNOWN_TOP_LEVEL = {
            "sex", "age", "labs", "fasting_hours", "fasting_8h",
            "ref_ranges", "context",
        }
        extra = {k: v for k, v in data.items() if k not in KNOWN_TOP_LEVEL}
        if extra and not data.get("labs"):
            data = dict(data)
            data["labs"] = extra
            for k in extra:
                del data[k]
        return data

    @model_validator(mode="after")
    def _validate_physiological_ranges(self):
        LIMITS = {
            "glucose":          (0.0,  2000.0, "mg/dL"),
            "creatinine":       (0.0,    50.0, "mg/dL"),
            "egfr":             (0.0,   200.0, "mL/min"),
            "alt":              (0.0, 50000.0, "U/L"),
            "ast":              (0.0, 50000.0, "U/L"),
            "ggt":              (0.0, 50000.0, "U/L"),
            "bilirubin_total":  (0.0,   100.0, "mg/dL"),
            "albumin":          (0.0,    10.0, "g/dL"),
            "total_protein":    (0.0,    20.0, "g/dL"),
            "tchol":            (0.0,  1500.0, "mg/dL"),
            "hdl":              (0.0,   300.0, "mg/dL"),
            "ldl":              (0.0,  1000.0, "mg/dL"),
            "trigly":           (0.0, 10000.0, "mg/dL"),
            "crp":              (0.0,  2000.0, "mg/L"),
            "sodium":           (80.0,  200.0, "mEq/L"),
            "potassium":        (1.0,    10.0, "mEq/L"),
            "calcium":          (4.0,    20.0, "mg/dL"),
            "uric_acid":        (0.0,    30.0, "mg/dL"),
            "iron":             (0.0,  1000.0, "µg/dL"),
            "ferritin":         (0.0, 50000.0, "ng/mL"),
            "vitd_25oh":        (0.0,   300.0, "ng/mL"),
        }
        errors = []
        labs = self.labs or {}
        for field, (lo, hi, unit) in LIMITS.items():
            val = labs.get(field)
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
        payload: Dict[str, Any] = {}

        if self.sex is not None:
            payload["sex"] = self.sex
        if self.age is not None:
            payload["age"] = self.age

        if self.fasting_hours is not None:
            payload["fasting_hours"] = self.fasting_hours
        if self.fasting_8h is not None:
            payload["fasting_8h"] = self.fasting_8h

        if self.ref_ranges:
            payload["ref_ranges"] = {
                k: {"low": v.low, "high": v.high}
                for k, v in self.ref_ranges.items()
            }

        if self.context is not None:
            payload["clinical_context"] = self.context.model_dump(exclude_none=True)

        payload.update(self.labs)
        return payload



class ProfileOut(BaseModel):
    sex: Optional[str]
    age: Optional[float]


class RefRangeOut(BaseModel):
    low: Optional[float]
    high: Optional[float]


class LabCardOut(BaseModel):
    code: str
    name: str
    value: float
    unit: str
    ref: RefRangeOut
    flag: Optional[str] = Field(None, description="'low' | 'high' | null")
    what: Optional[str] = None
    tips: List[str] = []
    source: str = Field(description="'input' | 'computed'")
    input_key: Optional[str] = None
    computed_from: Optional[List[str]] = None
    formula: Optional[str] = None
    unit_in: Optional[str] = None
    ref_source: str = Field(description="'default' | 'override'")


class SignalOut(BaseModel):
    id: str
    severity: str = Field(description="'high' | 'medium' | 'low'")
    title: str
    why: str
    next: List[str]
    evidence: Dict[str, Any]
    tags: List[str]


class ComboOut(BaseModel):
    id: str
    severity: str
    title: str
    why: str
    evidence: Dict[str, Any]
    next: List[str]
    tags: List[str]


class NextTestOut(BaseModel):
    test: str
    reason: str
    priority: int
    when: str


class AskDoctorOut(BaseModel):
    question: str
    why: str
    priority: int


class RecommendationsOut(BaseModel):
    next_tests: List[NextTestOut]
    ask_doctor: List[AskDoctorOut]


class SummaryOut(BaseModel):
    headline: str
    signals_high: int
    signals_medium: int
    notes: List[str]


class ContextOut(BaseModel):
    model_config = ConfigDict(extra="allow")

    fasting_hours: Optional[float] = None
    fasting_8h: Optional[bool] = None

    has_diabetes: Optional[bool] = None
    has_hypertension: Optional[bool] = None
    has_ckd: Optional[bool] = None
    has_liver_disease: Optional[bool] = None
    has_cardiovascular_disease: Optional[bool] = None
    on_statins: Optional[bool] = None
    on_acei_arb: Optional[bool] = None
    on_diuretics: Optional[bool] = None
    on_oral_diabetics: Optional[bool] = None
    on_insulin: Optional[bool] = None
    on_oral_anticoagulants: Optional[bool] = None
    pregnant: Optional[bool] = None


class MetaOut(BaseModel):
    computed: List[str]
    context: ContextOut
    missing_core: List[str]



class ChemAnalyzeResponse(BaseModel):

    version: str
    profile: ProfileOut
    meta: MetaOut
    summary: SummaryOut
    labs: List[LabCardOut]
    flags: Dict[str, Optional[str]]
    derived: Dict[str, Any]
    signals: List[SignalOut]
    combos: List[ComboOut]
    recommendations: RecommendationsOut
    disclaimer: str
    request_id: Optional[str] = None
    processing_time_ms: Optional[float] = None



class HealthResponse(BaseModel):
    status: str = "ok"
    module: str = "chem"
    system: str = "chem"


class InfoResponse(BaseModel):
    module: str = "chem"
    system: str = "chem"
    engine_version: str
    supported_labs: List[str]
    supported_aliases: Dict[str, List[str]]



class ErrorDetail(BaseModel):
    code: str
    message: str
    field: Optional[str] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
    request_id: Optional[str] = None



class ChemNarrativeRequest(ChemAnalyzeRequest):
    lang: Literal["uk", "en"] = Field(
        default="uk",
        description="Output language for the narrative. 'uk' = Ukrainian (default), 'en' = English."
    )


class NarrativeStoryOut(BaseModel):
    cluster_id: str = Field(..., description="Stable identifier of the cluster")
    tier: str = Field(..., description="critical | abnormal | info | minor | normal")
    icon: str = Field(..., description="Single emoji for the story card")
    title: str = Field(..., description="Plain-language headline")
    body: str = Field(..., description="Multi-paragraph markdown body")
    actions: List[str] = Field(default_factory=list, description="Ordered next steps")
    red_flags: List[str] = Field(default_factory=list, description="Symptoms warranting urgent care")
    severity: str = Field("low", description="low | medium | high — accent intensity")
    signals_used: List[str] = Field(default_factory=list,
                                    description="Engine signal IDs this story is based on")


class NarrativePatientOut(BaseModel):
    sex: Optional[str] = None
    age: Optional[float] = None
    age_bucket: Optional[str] = Field(None,
        description="child | teen | young_adult | adult | senior")


class ChemNarrativeResponse(BaseModel):
    summary: str = Field(..., description="One-line top-level framing")
    tone: Literal["normal", "attention_needed", "urgent", "incomplete"] = Field(
        ..., description="Drives UI colour scheme")
    lang: str = Field(..., description="Echo of request language")
    patient: NarrativePatientOut
    stories: List[NarrativeStoryOut] = Field(default_factory=list)
    request_id: Optional[str] = None
    processing_time_ms: Optional[float] = None
