from __future__ import annotations

import pytest

from chem_api.chem.analyze import analyze_chem_payload


def _ids(payload):
    return {s["id"] for s in analyze_chem_payload(payload)["signals"]}


def _combos(payload):
    return {c["id"] for c in analyze_chem_payload(payload)["combos"]}



class TestEstablishedT2D:

    payload = {
        "sex": "female", "age": 58,
        "glucose": 180, "a1c": 8.5,
        "creatinine": 1.1,
        "fasting_8h": True,
    }

    def test_diabetes_signals(self):
        ids = _ids(self.payload)
        assert "glucose_diabetes_range" in ids
        assert "a1c_diabetes_range" in ids



class TestPrediabetes:

    payload = {
        "sex": "male", "age": 50,
        "glucose": 115, "a1c": 5.9,
        "fasting_hours": 12,
    }

    def test_ifg_and_a1c_pre(self):
        ids = _ids(self.payload)
        assert "glucose_ifg_range" in ids
        assert "a1c_prediabetes_range" in ids



class TestMetabolicSyndrome:

    payload = {
        "sex": "male", "age": 45,
        "glucose": 118, "a1c": 6.1,
        "tchol": 240, "hdl": 35, "trigly": 260,
        "alt": 55, "ast": 42,
        "creatinine": 1.1,
        "crp": 6.5,
    }

    def test_insulin_resistance_combo(self):
        combos = _combos(self.payload)
        assert "insulin_resistance_nafld_like" in combos



class TestSevereHypertriglyceridemia:

    payload = {"sex": "male", "age": 45, "trigly": 850}

    def test_combo_fires(self):
        combos = _combos(self.payload)
        assert "tg_very_high_pancreatitis_risk" in combos



class TestFHSuspect:

    payload = {
        "sex": "male", "age": 38,
        "tchol": 320, "hdl": 45, "ldl": 220, "trigly": 130,
    }

    def test_fh_combo(self):
        combos = _combos(self.payload)
        assert "fh_like_ldl_ge190" in combos



class TestAtherogenicDyslipidemia:

    payload = {
        "sex": "male", "age": 50,
        "tchol": 230, "hdl": 32, "trigly": 280,
    }

    def test_pattern(self):
        ids = _ids(self.payload)
        assert "atherogenic_dyslipidemia_pattern" in ids



class TestCKD:

    payload = {
        "sex": "male", "age": 70,
        "creatinine": 2.3, "urea": 80,
        "potassium": 5.4,
    }

    def test_egfr_low(self):
        ids = _ids(self.payload)
        assert "egfr_low" in ids
        assert "creatinine_high" in ids

    def test_combo_kidney(self):
        combos = _combos(self.payload)
        assert "kidney_function_reduced" in combos



class TestUrgentElectrolytes:

    payload = {
        "sex": "female", "age": 60,
        "sodium": 128, "potassium": 6.2,
        "creatinine": 2.3, "glucose": 260,
    }

    def test_urgent_signals(self):
        ids = _ids(self.payload)
        assert "hyperkalemia" in ids
        assert "hyponatremia" in ids
        assert "creatinine_high" in ids



class TestHepatocellularInjury:

    payload = {
        "sex": "male", "age": 38,
        "alt": 350, "ast": 220, "alp": 85, "ggt": 70,
        "bilirubin_total": 1.8, "bilirubin_direct": 0.6,
    }

    def test_transaminitis(self):
        ids = _ids(self.payload)
        assert "transaminitis" in ids



class TestCholestaticPattern:

    payload = {
        "sex": "female", "age": 55,
        "alt": 60, "ast": 50, "alp": 380, "ggt": 280,
        "bilirubin_total": 3.5, "bilirubin_direct": 2.2,
    }

    def test_bilirubin_high(self):
        ids = _ids(self.payload)
        assert "bilirubin_high" in ids



class TestIronDeficiency:

    payload = {
        "sex": "female", "age": 28,
        "ferritin": 9, "iron": 40, "tibc": 460,
    }

    def test_iron_deficiency(self):
        ids = _ids(self.payload)
        assert "iron_deficiency_likely" in ids



class TestHyperuricemia:

    payload = {"sex": "male", "age": 50, "uric_acid": 9.5}

    def test_uric_acid_high(self):
        ids = _ids(self.payload)
        assert "uric_acid_high" in ids



class TestVitDDeficiency:

    payload = {"sex": "female", "age": 40, "vitd_25oh": 12}

    def test_vitd_deficiency(self):
        ids = _ids(self.payload)
        assert "vitd_deficiency" in ids



class TestVitDInsufficiency:

    payload = {"sex": "female", "age": 40, "vitd_25oh": 25}

    def test_vitd_insufficiency(self):
        ids = _ids(self.payload)
        assert "vitd_insufficiency" in ids



class TestSevereHypoglycemia:

    payload = {"sex": "female", "age": 70, "glucose": 35}

    def test_severe_hypoglycemia(self):
        ids = _ids(self.payload)
        assert "severe_hypoglycemia" in ids



class TestAcuteInflammation:

    payload = {
        "sex": "male", "age": 50,
        "crp": 50, "ferritin": 600,
        "alt": 30, "ast": 28,
    }

    def test_crp_high(self):
        ids = _ids(self.payload)
        assert "crp_high" in ids



class TestPseudohyponatremia:

    payload = {
        "sex": "female", "age": 65,
        "sodium": 128, "glucose": 380,
    }

    def test_corrected_na_combo(self):
        combos = _combos(self.payload)
        assert "hyponatremia_with_hyperglycemia_corrected_na" in combos



class TestIronOverload:

    payload = {
        "sex": "male", "age": 50,
        "iron": 220, "tibc": 280, "ferritin": 800,
    }

    def test_high_tsat(self):
        ids = _ids(self.payload)
        assert "high_tsat" in ids



class TestHypochloremia:

    payload = {
        "sex": "female", "age": 60,
        "sodium": 140, "chloride": 92, "potassium": 3.3,
    }

    def test_chloride_low(self):
        ids = _ids(self.payload)
        assert "chloride_low" in ids



class TestMildHyponatremia:

    payload = {"sex": "female", "age": 70, "sodium": 132}

    def test_hyponatremia(self):
        ids = _ids(self.payload)
        assert "hyponatremia" in ids



class TestAllNormal:

    payload = {
        "sex": "male", "age": 35,
        "glucose": 90, "a1c": 5.2,
        "creatinine": 1.0, "alt": 25, "ast": 22,
        "tchol": 170, "hdl": 65, "trigly": 90,
        "sodium": 140, "potassium": 4.2, "chloride": 102, "bicarbonate": 25,
        "calcium": 9.4, "vitd_25oh": 32,
    }

    def test_zero_clinical_signals(self):
        r = analyze_chem_payload(self.payload)
        non_quality = [s for s in r["signals"]
                       if "quality" not in (s.get("tags") or [])]
        clinical = [s for s in non_quality if s["id"] != "missing_core_chem"]
        assert len(clinical) == 0, (
            f"Expected zero clinical signals on normal panel, got: "
            f"{[s['id'] for s in clinical]}"
        )

    def test_headline_says_no_findings(self):
        r = analyze_chem_payload(self.payload)
        h = r["summary"]["headline"]
        assert ("Значних відхилень" in h or
                "Недостатньо даних" in h)
