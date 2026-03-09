from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ENGINE_DIR = Path(__file__).resolve().parent.parent
if str(_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(_ENGINE_DIR))



@pytest.fixture
def healthy_male() -> dict:
    return {
        "sex": "male", "age": 35,
        "glucose": 90, "a1c": 5.2,
        "creatinine": 1.0, "urea": 28,
        "alt": 25, "ast": 22, "alp": 75, "ggt": 18,
        "bilirubin_total": 0.7, "bilirubin_direct": 0.2,
        "albumin": 4.4, "total_protein": 7.2,
        "tchol": 180, "hdl": 50, "ldl": 110, "trigly": 100,
        "crp": 1.2,
        "sodium": 140, "potassium": 4.2, "chloride": 102, "bicarbonate": 25,
        "calcium": 9.4, "magnesium": 2.0, "phosphate": 3.4,
        "iron": 95, "ferritin": 120, "tibc": 320, "tsat": 30,
        "uric_acid": 5.5,
        "vitd_25oh": 32,
    }


@pytest.fixture
def healthy_female() -> dict:
    return {
        "sex": "female", "age": 32,
        "glucose": 92, "a1c": 5.2,
        "creatinine": 0.8, "urea": 28,
        "alt": 18, "ast": 20, "alp": 75, "ggt": 14,
        "bilirubin_total": 0.6, "bilirubin_direct": 0.1,
        "albumin": 4.4, "total_protein": 7.2,
        "tchol": 180, "hdl": 58, "trigly": 90,
        "crp": 1.2,
        "sodium": 140, "potassium": 4.2, "chloride": 102, "bicarbonate": 25,
        "calcium": 9.4, "magnesium": 2.0, "phosphate": 3.4,
        "iron": 95, "ferritin": 40, "tibc": 320,
        "uric_acid": 4.8,
        "vitd_25oh": 32,
    }


@pytest.fixture
def diabetes() -> dict:
    return {
        "sex": "female", "age": 58,
        "glucose": 180, "a1c": 8.5,
        "creatinine": 1.1,
        "fasting_8h": True,
    }


@pytest.fixture
def prediabetes() -> dict:
    return {
        "sex": "male", "age": 50,
        "glucose": 115, "a1c": 5.9,
        "fasting_hours": 12,
    }


@pytest.fixture
def metabolic_syndrome() -> dict:
    return {
        "sex": "male", "age": 45,
        "glucose": 118, "a1c": 6.1,
        "tchol": 240, "hdl": 35, "trigly": 260,
        "alt": 55, "ast": 42,
        "creatinine": 1.1,
        "crp": 6.5,
    }


@pytest.fixture
def atherogenic_dyslipidemia() -> dict:
    return {
        "sex": "male", "age": 50,
        "tchol": 230, "hdl": 32, "trigly": 280, "ldl": 142,
    }


@pytest.fixture
def severe_hypertriglyceridemia() -> dict:
    return {
        "sex": "male", "age": 45,
        "tchol": 380, "hdl": 25, "trigly": 850,
    }


@pytest.fixture
def kidney_disease() -> dict:
    return {
        "sex": "male", "age": 70,
        "creatinine": 2.3, "urea": 80,
        "potassium": 5.4,
        "sodium": 138,
    }


@pytest.fixture
def acute_hyperkalemia() -> dict:
    return {
        "sex": "female", "age": 60,
        "sodium": 128, "potassium": 6.2,
        "creatinine": 2.3, "glucose": 260,
    }


@pytest.fixture
def hepatocellular_injury() -> dict:
    return {
        "sex": "male", "age": 38,
        "alt": 350, "ast": 220, "alp": 85, "ggt": 70,
        "bilirubin_total": 1.8, "bilirubin_direct": 0.6,
    }


@pytest.fixture
def cholestatic_pattern() -> dict:
    return {
        "sex": "female", "age": 55,
        "alt": 60, "ast": 50, "alp": 380, "ggt": 280,
        "bilirubin_total": 3.5, "bilirubin_direct": 2.2,
    }


@pytest.fixture
def iron_deficiency() -> dict:
    return {
        "sex": "female", "age": 28,
        "ferritin": 9, "iron": 40, "tibc": 460,
    }


@pytest.fixture
def hyperuricemia() -> dict:
    return {
        "sex": "male", "age": 50,
        "uric_acid": 9.5,
    }


@pytest.fixture
def vitd_deficiency() -> dict:
    return {
        "sex": "female", "age": 40,
        "vitd_25oh": 12,
    }


@pytest.fixture
def incomplete_panel() -> dict:
    return {"sex": "male", "age": 30}



SAMPLE_PATIENTS = (
    "healthy_male", "healthy_female",
    "diabetes", "prediabetes",
    "metabolic_syndrome", "atherogenic_dyslipidemia",
    "severe_hypertriglyceridemia",
    "kidney_disease", "acute_hyperkalemia",
    "hepatocellular_injury", "cholestatic_pattern",
    "iron_deficiency",
    "hyperuricemia", "vitd_deficiency",
    "incomplete_panel",
)


@pytest.fixture(params=SAMPLE_PATIENTS)
def all_patient_names(request):
    return request.param
