from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

WEIGHTS_PATH = _ROOT / "neuro_api" / "weights" / "model.pt"
ISOTONIC_PATH = _ROOT / "neuro_api" / "weights" / "isotonic_params.json"



@pytest.fixture(scope="session")
def predictor():
    from neuro_api.neuro.inference import RiskPredictor
    return RiskPredictor(WEIGHTS_PATH, isotonic_path=ISOTONIC_PATH)



@pytest.fixture
def healthy_young_adult() -> dict:
    return {
        "sex": 1, "age": 28,
        "bmi": 23, "sbp": 118, "dbp": 76, "pulse": 68,
        "wbc": 6.5, "hgb": 15.0, "plt": 250, "mcv": 88,
        "neut_pct": 55, "lymph_pct": 32, "mono_pct": 8,
        "glucose": 90, "a1c": 5.2,
        "creatinine": 1.0, "alt": 22, "ast": 20,
        "tchol": 170, "hdl": 55, "trigly": 90,
        "sodium": 140, "potassium": 4.2,
        "crp": 1.0, "vitd_25oh": 32,
        "income_ratio": 3.0, "edu_level": 5,
    }


@pytest.fixture
def healthy_middle_aged() -> dict:
    return {
        "sex": 2, "age": 45,
        "bmi": 24, "sbp": 122, "dbp": 78,
        "wbc": 6.0, "hgb": 13.5, "plt": 240,
        "glucose": 92, "a1c": 5.3,
        "tchol": 180, "hdl": 60, "trigly": 100,
        "vitd_25oh": 30, "crp": 1.5,
        "income_ratio": 2.5, "edu_level": 4,
    }


@pytest.fixture
def metabolic_at_risk() -> dict:
    return {
        "sex": 1, "age": 50, "bmi": 32, "waist": 108,
        "sbp": 145, "dbp": 90,
        "glucose": 115, "a1c": 6.0,
        "tchol": 220, "hdl": 38, "trigly": 240,
        "alt": 48, "ast": 38,
        "crp": 5.0,
        "metsyn_criteria_count": 4, "homa_ir": 4.2,
        "income_ratio": 1.5, "edu_level": 3,
    }


@pytest.fixture
def low_ses_high_inflammation() -> dict:
    return {
        "sex": 2, "age": 38,
        "bmi": 29, "sbp": 132,
        "glucose": 95, "a1c": 5.5,
        "crp": 12.0,
        "wbc": 9.5, "hgb": 12.0, "plt": 280,
        "vitd_25oh": 14,
        "income_ratio": 0.8,
        "edu_level": 2,
        "sedentary_min_day": 600,
    }


@pytest.fixture
def chronic_disease_burden() -> dict:
    return {
        "sex": 1, "age": 65,
        "bmi": 31, "sbp": 155, "dbp": 95,
        "glucose": 165, "a1c": 8.2,
        "creatinine": 1.6, "egfr_ckd_epi_2021": 48,
        "tchol": 230, "hdl": 36, "trigly": 220,
        "alt": 55, "ast": 48, "fib4": 2.1,
        "crp": 8.5,
    }


@pytest.fixture
def elderly_at_risk() -> dict:
    return {
        "sex": 2, "age": 75,
        "bmi": 26, "sbp": 142,
        "glucose": 102, "a1c": 5.8,
        "creatinine": 1.1, "egfr_ckd_epi_2021": 58,
        "tchol": 200, "hdl": 50,
        "vitd_25oh": 18,
        "edu_level": 3, "income_ratio": 1.2,
    }


@pytest.fixture
def low_risk_young_active() -> dict:
    return {
        "sex": 1, "age": 26,
        "bmi": 22, "sbp": 110, "dbp": 70,
        "glucose": 85, "a1c": 5.0,
        "tchol": 160, "hdl": 65,
        "vitd_25oh": 38, "crp": 0.8,
        "sedentary_min_day": 240,
        "income_ratio": 4.0, "edu_level": 5,
    }


@pytest.fixture
def incomplete_payload() -> dict:
    return {"sex": 1, "age": 50}


@pytest.fixture
def empty_payload() -> dict:
    return {}



SAMPLE_PATIENTS = (
    "healthy_young_adult", "healthy_middle_aged",
    "metabolic_at_risk", "low_ses_high_inflammation",
    "chronic_disease_burden", "elderly_at_risk",
    "low_risk_young_active", "incomplete_payload",
)


@pytest.fixture(params=SAMPLE_PATIENTS)
def all_patient_names(request):
    return request.param
