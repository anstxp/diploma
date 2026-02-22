from __future__ import annotations

import os
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
        "wbc": 6.5, "hgb": 15.0, "plt": 250,
        "neut_pct": 60, "lymph_pct": 30, "mono_pct": 7,
        "eos_pct": 2, "baso_pct": 1,
        "rbc": 5.0, "hct": 45, "mcv": 88, "mch": 29, "mchc": 33,
        "rdw": 13.0, "mpv": 9.5,
    }


@pytest.fixture
def healthy_female() -> dict:
    return {
        "sex": "female", "age": 28,
        "wbc": 6.0, "hgb": 13.5, "plt": 230,
        "neut_pct": 58, "lymph_pct": 32, "mono_pct": 6,
        "eos_pct": 3, "baso_pct": 1,
        "rbc": 4.5, "hct": 40, "mcv": 85, "mch": 28, "mchc": 33,
        "rdw": 13.5, "mpv": 9.0,
    }


@pytest.fixture
def iron_deficiency() -> dict:
    return {
        "sex": "female", "age": 30,
        "wbc": 6.0, "hgb": 9.5, "plt": 350,
        "neut_pct": 55, "lymph_pct": 33, "mono_pct": 8, "eos_pct": 3, "baso_pct": 1,
        "rbc": 4.5, "hct": 30, "mcv": 70, "mch": 24, "mchc": 31, "rdw": 17.0, "mpv": 9.0,
    }


@pytest.fixture
def b12_macrocytic() -> dict:
    return {
        "sex": "female", "age": 65,
        "wbc": 5.0, "hgb": 9.0, "plt": 200,
        "rbc": 3.0, "hct": 28, "mcv": 112, "mch": 38, "mchc": 33, "rdw": 16.5,
    }


@pytest.fixture
def bacterial() -> dict:
    return {
        "sex": "male", "age": 40,
        "wbc": 15.0, "hgb": 14.0, "plt": 280,
        "neut_pct": 85, "lymph_pct": 10, "mono_pct": 3, "eos_pct": 1, "baso_pct": 1,
        "rbc": 4.8, "hct": 43, "mcv": 89, "mch": 30, "mchc": 33, "rdw": 13.5, "mpv": 9.5,
    }


@pytest.fixture
def viral_lymphocytosis() -> dict:
    return {
        "sex": "male", "age": 22,
        "wbc": 11.5, "hgb": 15.0, "plt": 240,
        "neut_pct": 35, "lymph_pct": 55, "mono_pct": 6, "eos_pct": 3, "baso_pct": 1,
        "rbc": 5.0, "hct": 44, "mcv": 88, "mch": 30, "mchc": 33, "rdw": 13.0,
    }


@pytest.fixture
def severe_neutropenia() -> dict:
    return {
        "sex": "female", "age": 60,
        "wbc": 1.2, "hgb": 12.0, "plt": 180,
        "neut_pct": 35, "lymph_pct": 50, "mono_pct": 10, "eos_pct": 4, "baso_pct": 1,
    }


@pytest.fixture
def severe_thrombocytopenia() -> dict:
    return {
        "sex": "male", "age": 45,
        "wbc": 7.0, "hgb": 14.0, "plt": 25,
    }


@pytest.fixture
def pancytopenia() -> dict:
    return {
        "sex": "male", "age": 55,
        "wbc": 2.5, "hgb": 9.0, "plt": 60,
        "rbc": 3.0, "hct": 27, "mcv": 90, "mch": 30, "mchc": 33, "rdw": 14.0,
    }


@pytest.fixture
def polycythemia() -> dict:
    return {
        "sex": "male", "age": 55,
        "wbc": 8.5, "hgb": 19.5, "plt": 400,
        "rbc": 6.2, "hct": 60, "mcv": 90, "mch": 30, "mchc": 33, "rdw": 13.5,
    }


@pytest.fixture
def thalassemia_trait() -> dict:
    return {
        "sex": "female", "age": 28,
        "wbc": 6.5, "hgb": 11.5, "plt": 240,
        "rbc": 5.4, "hct": 36, "mcv": 65, "mch": 21, "mchc": 32, "rdw": 13.5,
    }


@pytest.fixture
def eosinophilia_pt() -> dict:
    return {
        "sex": "male", "age": 40,
        "wbc": 9.0, "hgb": 14.5, "plt": 250,
        "neut_pct": 50, "lymph_pct": 25, "mono_pct": 6, "eos_pct": 18, "baso_pct": 1,
    }


@pytest.fixture
def reactive_thrombocytosis() -> dict:
    return {
        "sex": "female", "age": 35,
        "wbc": 8.5, "hgb": 13.0, "plt": 580,
        "rbc": 4.5, "hct": 39, "mcv": 87, "mch": 29, "mchc": 33, "rdw": 14.0, "mpv": 9.5,
    }


@pytest.fixture
def high_esr() -> dict:
    return {
        "sex": "female", "age": 50,
        "wbc": 7.0, "hgb": 13.0, "plt": 250,
        "esr": 65,
    }


@pytest.fixture
def incomplete_panel() -> dict:
    return {"sex": "male", "age": 30}



SAMPLE_PATIENTS = (
    "healthy_male", "healthy_female",
    "iron_deficiency", "b12_macrocytic",
    "bacterial", "viral_lymphocytosis",
    "severe_neutropenia", "severe_thrombocytopenia", "pancytopenia",
    "polycythemia", "thalassemia_trait",
    "eosinophilia_pt", "reactive_thrombocytosis",
    "high_esr", "incomplete_panel",
)


@pytest.fixture(params=SAMPLE_PATIENTS)
def all_patient_names(request):
    return request.param
