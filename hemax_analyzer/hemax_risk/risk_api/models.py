from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator



class RiskAnalyzeRequest(BaseModel):
    sex: Optional[Union[str, int, float]] = Field(
        None,
        description="Sex: 'male'/'female'/'m'/'f' or NHANES code 1=M, 2=F"
    )
    age: Optional[float] = Field(
        None, ge=0, le=120,
        description="Age in years"
    )
    bmi: Optional[float] = Field(None, gt=10, lt=80, description="Body Mass Index")
    waist_cm: Optional[float] = Field(None, gt=20, lt=300)
    sbp: Optional[float] = Field(None, gt=50, lt=300, description="Systolic BP, mmHg")
    dbp: Optional[float] = Field(None, gt=30, lt=200, description="Diastolic BP, mmHg")
    pulse: Optional[float] = Field(None, gt=20, lt=250)

    labs: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Lab values keyed by canonical name or alias (hgb/hemoglobin, "
                    "glucose/glucose_fasting, hba1c/a1c, etc.)"
    )

    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Clinical context: {'clinical': {has_diabetes: bool, "
                    "on_statins: bool, on_acei_arb: bool, takes_metformin: bool, "
                    "has_cardiovascular_disease: bool, smoker: bool, ...}}. "
                    "Adjusts narrative tone for known-patient scenarios."
    )

    @model_validator(mode="before")
    @classmethod
    def _allow_top_level_labs(cls, data):
        if not isinstance(data, dict):
            return data
        structured = {"sex", "age", "bmi", "waist_cm", "sbp", "dbp", "pulse",
                      "labs", "lang", "fasting_hours", "fasting_8h", "context"}
        labs = dict(data.get("labs") or {})
        for k in list(data.keys()):
            if k not in structured and k.lower() not in structured:
                labs.setdefault(k, data.pop(k))
        if labs:
            data["labs"] = labs
        return data


class RiskNarrativeRequest(RiskAnalyzeRequest):
    lang: Literal["uk", "en"] = Field(
        default="uk",
        description="Output language for the narrative"
    )



class FeatureContributionOut(BaseModel):
    feature: str
    value: Optional[float]
    z_score: float
    contribution: float
    direction: Literal["raises", "lowers", "neutral"]


class TaskRiskOut(BaseModel):
    target: str
    name_ua: str
    name_en: str
    probability: float = Field(..., ge=0, le=1)
    risk_tier: Literal["very_low", "low", "moderate", "high", "very_high", "uncertain"]
    population_prevalence: float = Field(..., ge=0, le=1)
    risk_ratio_vs_baseline: float = Field(
        default=1.0,
        description=(
            "Risk ratio: predicted probability divided by the population "
            "prevalence for this condition (e.g. 2.5 means the model "
            "assigns 2.5× the population-baseline probability)."
        ),
    )

    odds_ratio_vs_baseline: float = Field(
        default=1.0,
        description=(
            "DEPRECATED alias for risk_ratio_vs_baseline. The value is the "
            "same; the field is misnamed (it's a risk ratio, not an odds "
            "ratio) but kept for API backward compatibility."
        ),
    )
    top_drivers: List[FeatureContributionOut] = Field(default_factory=list)


class RiskAnalyzeResponse(BaseModel):
    risks: List[TaskRiskOut]
    overall_tier: Literal["very_low", "low", "moderate", "high", "very_high", "insufficient_data"]
    n_features_provided: int
    n_features_total: int
    model_version: str
    request_id: Optional[str] = None
    processing_time_ms: Optional[float] = None



class NarrativeStoryOut(BaseModel):
    cluster_id: str
    tier: Literal["critical", "abnormal", "info", "minor", "normal"]
    icon: str
    title: str
    body: str
    actions: List[str] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)
    severity: Literal["low", "medium", "high"] = "low"
    risks_used: List[str] = Field(default_factory=list)


class NarrativePatientOut(BaseModel):
    sex: Optional[str] = None
    age: Optional[float] = None
    age_bucket: Optional[str] = None


class RiskNarrativeResponse(BaseModel):
    summary: str
    tone: Literal["normal", "attention_needed", "urgent", "neutral"]
    lang: str
    patient: NarrativePatientOut
    overall_tier: str
    stories: List[NarrativeStoryOut] = Field(default_factory=list)
    risks: List[TaskRiskOut] = Field(default_factory=list)
    request_id: Optional[str] = None
    processing_time_ms: Optional[float] = None



class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"] = "ok"


class InfoResponse(BaseModel):
    model_version: str
    n_features: int
    n_targets: int
    target_names: List[str]
    test_metrics: Dict[str, Dict[str, Any]]
    n_train: int
    n_val: int
    n_test: int
