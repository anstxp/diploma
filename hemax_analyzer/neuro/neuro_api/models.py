from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator



class NeuroAnalyzeRequest(BaseModel):

    sex: Optional[Union[str, int, float]] = Field(
        None, description="Sex: 'male'/'female'/'m'/'f' or NHANES code 1=M, 2=F")
    age: Optional[float] = Field(None, ge=0, le=120, description="Age in years")
    bmi: Optional[float] = Field(None, gt=10, lt=80, description="Body Mass Index")
    waist_cm: Optional[float] = Field(None, gt=20, lt=300)
    sbp: Optional[float] = Field(None, gt=50, lt=300, description="Systolic BP, mmHg")
    dbp: Optional[float] = Field(None, gt=30, lt=200, description="Diastolic BP, mmHg")
    pulse: Optional[float] = Field(None, gt=20, lt=250)

    labs: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Lab values relevant to mental health & sleep screening. "
                    "Key drivers: vit_d_total, ferritin, hba1c, hs_crp, rdw, "
                    "hb_gdl, tsh, b12.")

    sleep_hours_avg: Optional[float] = Field(
        None, ge=0, le=24,
        description="Average sleep duration per night (last 2 weeks)")
    sleep_latency_min: Optional[float] = Field(
        None, ge=0, le=300,
        description="Time to fall asleep (minutes)")
    night_awakenings: Optional[int] = Field(
        None, ge=0, le=20,
        description="Typical awakenings per night")
    early_morning_awakening: Optional[bool] = Field(
        None,
        description="Wakes up much earlier than intended")
    sleep_quality_subjective: Optional[int] = Field(
        None, ge=1, le=5,
        description="Subjective sleep quality (1=very poor, 5=excellent)")
    uses_sleep_meds: Optional[bool] = Field(
        None, description="Regularly uses sleep aids")
    naps_per_week: Optional[int] = Field(
        None, ge=0, le=21, description="Daytime naps per week")
    screen_time_before_bed_min: Optional[int] = Field(
        None, ge=0, le=480,
        description="Minutes of screen use in the hour before sleep")
    caffeine_servings_per_day: Optional[int] = Field(
        None, ge=0, le=20,
        description="Servings of coffee / tea / energy drinks per day")
    shift_work: Optional[bool] = Field(
        None, description="Works rotating or night shifts")
    snoring: Optional[bool] = Field(
        None, description="Snores regularly (self or partner)")
    witnessed_apnea: Optional[bool] = Field(
        None, description="Partner has observed breathing pauses during sleep")

    phq9_score: Optional[int] = Field(
        None, ge=0, le=27,
        description="PHQ-9 depression score (≥5 mild, ≥10 moderate, "
                    "≥15 moderately severe, ≥20 severe)")
    gad7_score: Optional[int] = Field(
        None, ge=0, le=21,
        description="GAD-7 anxiety score (≥5 mild, ≥10 moderate, ≥15 severe)")
    recent_life_stressors: Optional[bool] = Field(
        None, description="Major life event in the last 6 months")
    exercise_minutes_per_week: Optional[int] = Field(
        None, ge=0, le=2000,
        description="Moderate-or-greater intensity exercise per week")
    social_support_low: Optional[bool] = Field(
        None, description="Reports lacking close confidants")
    chronic_pain: Optional[bool] = Field(
        None, description="Chronic pain condition")

    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Clinical context flags: has_depression_history, "
                    "has_anxiety_history, has_bipolar, has_hypothyroidism, "
                    "has_diabetes, on_antidepressants, on_anxiolytics, "
                    "on_sleep_meds, on_thyroid_meds, alcohol_regular, "
                    "smoker, sedentary.")

    @model_validator(mode="before")
    @classmethod
    def _allow_top_level_labs(cls, data):
        if not isinstance(data, dict):
            return data
        structured = {
            "sex", "age", "bmi", "waist_cm", "sbp", "dbp", "pulse", "labs",
            "lang", "fasting_hours", "fasting_8h", "context",
            "sleep_hours_avg", "sleep_latency_min", "night_awakenings",
            "early_morning_awakening", "sleep_quality_subjective",
            "uses_sleep_meds", "naps_per_week", "screen_time_before_bed_min",
            "caffeine_servings_per_day", "shift_work", "snoring",
            "witnessed_apnea",
            "phq9_score", "gad7_score", "recent_life_stressors",
            "exercise_minutes_per_week", "social_support_low", "chronic_pain",
        }
        labs = dict(data.get("labs") or {})
        for k in list(data.keys()):
            if k not in structured and k.lower() not in structured:
                labs.setdefault(k, data.pop(k))
        if labs:
            data["labs"] = labs
        return data


class NeuroNarrativeRequest(NeuroAnalyzeRequest):
    lang: Literal["uk", "en"] = Field(
        default="uk", description="Output language for the narrative")


RiskAnalyzeRequest = NeuroAnalyzeRequest
RiskNarrativeRequest = NeuroNarrativeRequest



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
    odds_ratio_vs_baseline: float
    top_drivers: List[FeatureContributionOut] = Field(default_factory=list)


class RiskAnalyzeResponse(BaseModel):
    risks: List[TaskRiskOut]
    overall_tier: Literal["very_low", "low", "moderate", "high",
                          "very_high", "insufficient_data"]
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
