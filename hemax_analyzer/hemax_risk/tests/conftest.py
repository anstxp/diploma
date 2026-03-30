from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

WEIGHTS_PATH = _ROOT / "risk_api" / "weights" / "model.pt"
ISOTONIC_PATH = _ROOT / "risk_api" / "weights" / "isotonic_params.json"



@pytest.fixture(scope="session")
def predictor():
    from risk_api.risk.inference import RiskPredictor
    return RiskPredictor(WEIGHTS_PATH, isotonic_path=ISOTONIC_PATH)



@pytest.fixture
def healthy_male() -> dict:
    return {
        "sex": 1, "age": 30,
        "bmi": 23, "sbp": 118, "dbp": 76, "pulse": 68,
        "glucose": 90, "a1c": 5.2,
        "creatinine": 1.0,
        "alt": 22, "ast": 20,
        "tchol": 170, "hdl": 55, "trigly": 90,
        "sodium": 140, "potassium": 4.2,
        "hgb": 15.0, "wbc": 6.5, "plt": 250,
    }


@pytest.fixture
def healthy_female() -> dict:
    return {
        "sex": 2, "age": 28,
        "bmi": 22, "sbp": 115, "dbp": 74,
        "glucose": 88, "a1c": 5.1,
        "creatinine": 0.8,
        "tchol": 170, "hdl": 62, "trigly": 80,
        "hgb": 13.5, "wbc": 6.0, "plt": 230,
    }


@pytest.fixture
def diabetic_patient() -> dict:
    return {
        "sex": 2, "age": 58,
        "bmi": 32, "sbp": 145, "dbp": 90,
        "glucose": 180, "a1c": 8.5,
        "creatinine": 1.1,
        "tchol": 220, "hdl": 38, "trigly": 280,
        "alt": 45, "ast": 38,
    }


@pytest.fixture
def hypertensive_patient() -> dict:
    return {
        "sex": 1, "age": 62,
        "bmi": 28, "sbp": 158, "dbp": 96,
        "glucose": 100, "a1c": 5.7,
        "creatinine": 1.1,
        "tchol": 215, "hdl": 42, "trigly": 165,
    }


@pytest.fixture
def metabolic_syndrome_patient() -> dict:
    return {
        "sex": 1, "age": 55,
        "bmi": 33, "waist": 110,
        "sbp": 152, "dbp": 92,
        "glucose": 118, "a1c": 6.1,
        "tchol": 235, "hdl": 36, "trigly": 270,
        "alt": 55, "ast": 42,
    }


@pytest.fixture
def cvd_high_risk_patient() -> dict:
    return {
        "sex": 1, "age": 70,
        "bmi": 30, "sbp": 160, "dbp": 95,
        "glucose": 140, "a1c": 7.2,
        "creatinine": 1.3,
        "tchol": 250, "hdl": 32, "ldl": 175, "trigly": 220,
        "hgb": 13.5, "alt": 30, "ast": 28,
    }


@pytest.fixture
def low_risk_young() -> dict:
    return {
        "sex": 2, "age": 25,
        "bmi": 21, "sbp": 108, "dbp": 70,
        "glucose": 82, "a1c": 5.0,
    }


@pytest.fixture
def incomplete_payload() -> dict:
    return {"sex": 1, "age": 50}


@pytest.fixture
def empty_payload() -> dict:
    return {}



SAMPLE_PATIENTS = (
    "healthy_male", "healthy_female",
    "diabetic_patient", "hypertensive_patient",
    "metabolic_syndrome_patient", "cvd_high_risk_patient",
    "low_risk_young", "incomplete_payload",
)


@pytest.fixture(params=SAMPLE_PATIENTS)
def all_patient_names(request):
    return request.param
