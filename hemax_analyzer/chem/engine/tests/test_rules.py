from __future__ import annotations

import pytest

from chem_api.chem.analyze import analyze_chem_payload


def _ids(payload: dict) -> set[str]:
    return {s["id"] for s in analyze_chem_payload(payload)["signals"]}


def _combo_ids(payload: dict) -> set[str]:
    return {c["id"] for c in analyze_chem_payload(payload)["combos"]}


def _get_signal(payload: dict, sig_id: str) -> dict | None:
    for s in analyze_chem_payload(payload)["signals"]:
        if s["id"] == sig_id:
            return s
    return None



class TestDataQualitySignals:

    def test_missing_core_chem_fires_on_empty(self):
        ids = _ids({"sex": "male", "age": 30})
        assert "missing_core_chem" in ids

    def test_missing_core_does_not_fire_when_panels_present(self):
        ids = _ids({
            "sex": "male", "age": 30,
            "glucose": 95, "a1c": 5.2,
            "creatinine": 1.0,
            "alt": 25, "ast": 22,
            "tchol": 180, "hdl": 55, "trigly": 100,
        })
        assert "missing_core_chem" not in ids



class TestGlucoseSignals:

    def test_glucose_diabetes_range(self):
        ids = _ids({"sex": "male", "age": 55, "glucose": 180})
        assert "glucose_diabetes_range" in ids

    def test_glucose_ifg_range(self):
        ids = _ids({"sex": "male", "age": 55, "glucose": 115})
        assert "glucose_ifg_range" in ids

    def test_a1c_diabetes_range(self):
        ids = _ids({"sex": "female", "age": 60, "a1c": 8.0})
        assert "a1c_diabetes_range" in ids

    def test_a1c_prediabetes_range(self):
        ids = _ids({"sex": "male", "age": 50, "a1c": 5.9})
        assert "a1c_prediabetes_range" in ids

    def test_hypoglycemia(self):
        ids = _ids({"sex": "male", "age": 40, "glucose": 60})
        assert "hypoglycemia" in ids

    def test_severe_hypoglycemia(self):
        ids = _ids({"sex": "male", "age": 40, "glucose": 35})
        assert "severe_hypoglycemia" in ids



class TestElectrolyteSignals:

    def test_hyperkalemia(self):
        ids = _ids({"sex": "female", "age": 60, "potassium": 6.2})
        assert "hyperkalemia" in ids

    def test_hyperkalemia_is_urgent_high_severity(self):
        sig = _get_signal({"sex": "female", "age": 60, "potassium": 6.6}, "hyperkalemia")
        assert sig is not None
        assert sig["severity"] in ("medium", "high")

    def test_hypokalemia(self):
        ids = _ids({"sex": "female", "age": 60, "potassium": 3.0})
        assert "hypokalemia" in ids

    def test_hyponatremia(self):
        ids = _ids({"sex": "female", "age": 60, "sodium": 128})
        assert "hyponatremia" in ids

    def test_hyponatremia_with_hyperglycemia_corrected_na(self):
        combos = _combo_ids({
            "sex": "female", "age": 60,
            "sodium": 128, "glucose": 280,
        })
        assert "hyponatremia_with_hyperglycemia_corrected_na" in combos

    def test_hypernatremia(self):
        ids = _ids({"sex": "female", "age": 70, "sodium": 152})
        assert "hypernatremia" in ids

    def test_bicarbonate_high(self):
        ids = _ids({"sex": "male", "age": 40, "bicarbonate": 32})
        assert "bicarbonate_high" in ids

    def test_bicarbonate_low(self):
        ids = _ids({"sex": "male", "age": 40, "bicarbonate": 18})
        assert "bicarbonate_low" in ids

    def test_chloride_high(self):
        ids = _ids({"sex": "male", "age": 40, "chloride": 112})
        assert "chloride_high" in ids

    def test_chloride_low(self):
        ids = _ids({"sex": "male", "age": 40, "chloride": 92})
        assert "chloride_low" in ids



class TestRenalSignals:

    def test_creatinine_high(self):
        ids = _ids({"sex": "male", "age": 70, "creatinine": 2.3})
        assert "creatinine_high" in ids

    def test_egfr_low(self):
        ids = _ids({"sex": "male", "age": 70, "creatinine": 2.3})
        assert "egfr_low" in ids

    def test_kidney_function_reduced(self):
        combos = _combo_ids({"sex": "male", "age": 70, "creatinine": 2.3})
        assert "kidney_function_reduced" in combos



class TestLiverSignals:

    def test_transaminitis(self):
        ids = _ids({"sex": "male", "age": 40, "alt": 350, "ast": 220})
        assert "transaminitis" in ids

    def test_bilirubin_high(self):
        ids = _ids({"sex": "male", "age": 40, "bilirubin_total": 3.5})
        assert "bilirubin_high" in ids



class TestLipidSignals:

    def test_tchol_high(self):
        ids = _ids({"sex": "male", "age": 50, "tchol": 250})
        assert "tchol_high" in ids

    def test_low_hdl(self):
        ids = _ids({"sex": "male", "age": 50, "hdl": 30})
        assert "low_hdl" in ids

    def test_non_hdl_high(self):
        ids = _ids({"sex": "male", "age": 50, "tchol": 250, "hdl": 40})
        assert "non_hdl_high" in ids

    def test_hypertriglyceridemia(self):
        ids = _ids({"sex": "male", "age": 50, "trigly": 280})
        assert "hypertriglyceridemia" in ids

    def test_tg_very_high_pancreatitis_risk(self):
        combos = _combo_ids({"sex": "male", "age": 45, "trigly": 850})
        assert "tg_very_high_pancreatitis_risk" in combos

    def test_tg_hdl_ratio_high(self):
        ids = _ids({"sex": "male", "age": 50, "trigly": 280, "hdl": 35})
        assert "tg_hdl_ratio_high" in ids

    def test_atherogenic_dyslipidemia_pattern(self):
        ids = _ids({
            "sex": "male", "age": 50,
            "tchol": 230, "hdl": 32, "trigly": 280,
        })
        assert "atherogenic_dyslipidemia_pattern" in ids

    def test_fh_like_ldl_ge_190(self):
        combos = _combo_ids({"sex": "male", "age": 45, "ldl": 220})
        assert "fh_like_ldl_ge190" in combos

    def test_insulin_resistance_nafld_like(self):
        combos = _combo_ids({
            "sex": "male", "age": 45,
            "glucose": 118, "hdl": 35, "trigly": 260,
            "alt": 55, "ast": 42,
        })
        assert "insulin_resistance_nafld_like" in combos



class TestOtherSignals:

    def test_crp_high(self):
        ids = _ids({"sex": "male", "age": 40, "crp": 25})
        assert "crp_high" in ids

    def test_uric_acid_high(self):
        ids = _ids({"sex": "male", "age": 50, "uric_acid": 9.5})
        assert "uric_acid_high" in ids

    def test_iron_deficiency_likely(self):
        ids = _ids({
            "sex": "female", "age": 28,
            "ferritin": 9, "iron": 40, "tibc": 460,
        })
        assert "iron_deficiency_likely" in ids

    def test_ferritin_high_possible_inflammation(self):
        ids = _ids({"sex": "male", "age": 50, "ferritin": 600})
        assert "ferritin_high_possible_inflammation" in ids

    def test_high_tsat(self):
        ids = _ids({"sex": "male", "age": 50, "iron": 200, "tibc": 280})
        assert "high_tsat" in ids

    def test_low_tsat(self):
        ids = _ids({"sex": "female", "age": 30, "iron": 30, "tibc": 450})
        assert "low_tsat" in ids

    def test_vitd_deficiency(self):
        ids = _ids({"sex": "female", "age": 40, "vitd_25oh": 12})
        assert "vitd_deficiency" in ids

    def test_vitd_insufficiency(self):
        ids = _ids({"sex": "female", "age": 40, "vitd_25oh": 25})
        assert "vitd_insufficiency" in ids

    def test_vitd_high(self):
        ids = _ids({"sex": "female", "age": 40, "vitd_25oh": 120})
        assert "vitd_high" in ids
