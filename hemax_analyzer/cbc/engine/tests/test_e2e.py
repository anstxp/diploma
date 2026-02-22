from __future__ import annotations

import pytest

from cbc_api.analyze import analyze_cbc_payload


def _ids(payload):
    return {s["id"] for s in analyze_cbc_payload(payload)["signals"]}



class TestIDA:

    payload = {
        "sex": "female", "age": 32,
        "wbc": 6.5, "hgb": 10.2, "plt": 380,
        "rbc": 4.5, "hct": 32, "mcv": 72, "mch": 23, "mchc": 30, "rdw": 17.5,
    }

    def test_diagnosis_signals_fire(self):
        ids = _ids(self.payload)
        assert "anemia_possible" in ids
        assert "microcytic_anemia_pattern" in ids
        assert "iron_deficiency_likely_pattern" in ids
        assert "high_rdw" in ids

    def test_recommends_ferritin(self):
        r = analyze_cbc_payload(self.payload)
        tests = [t["test"].lower() for t in r["recommendations"]["next_tests"]]
        assert any("феритин" in t for t in tests)



class TestB12Macrocytic:

    payload = {
        "sex": "female", "age": 70,
        "wbc": 5.0, "hgb": 9.0, "plt": 180,
        "rbc": 2.8, "hct": 28, "mcv": 115, "mch": 38, "mchc": 33, "rdw": 18,
    }

    def test_macrocytic_anemia_detected(self):
        ids = _ids(self.payload)
        assert "macrocytic_anemia_pattern" in ids

    def test_recommends_b12_folate(self):
        r = analyze_cbc_payload(self.payload)
        tests = [t["test"].lower() for t in r["recommendations"]["next_tests"]]
        assert any("b12" in t for t in tests)
        assert any("фолат" in t for t in tests)



class TestThalTrait:

    payload = {
        "sex": "female", "age": 28,
        "wbc": 6.5, "hgb": 11.5, "plt": 240,
        "rbc": 5.5, "hct": 35, "mcv": 65, "mch": 21, "mchc": 32, "rdw": 13.5,
    }

    def test_thal_trait_pattern(self):
        ids = _ids(self.payload)
        assert "thal_trait_like_pattern" in ids



class TestBacterialLike:

    payload = {
        "sex": "male", "age": 45,
        "wbc": 18.0, "hgb": 14.0, "plt": 280,
        "neut_pct": 85, "lymph_pct": 8, "mono_pct": 4, "eos_pct": 2, "baso_pct": 1,
    }

    def test_signals(self):
        ids = _ids(self.payload)
        assert "leukocytosis" in ids
        assert "neutrophilia" in ids
        assert "neutrophilic_leukocytosis" in ids
        assert "nlr_high" in ids

    def test_bacterial_combo_present(self):
        r = analyze_cbc_payload(self.payload)
        combo_ids = {c["id"] for c in r["combos"]}
        assert "bacterial_like_pattern" in combo_ids



class TestViralLymphocytosis:

    payload = {
        "sex": "male", "age": 19,
        "wbc": 12.0, "hgb": 15.0, "plt": 220,
        "neut_pct": 30, "lymph_pct": 60, "mono_pct": 6, "eos_pct": 3, "baso_pct": 1,
    }

    def test_signals(self):
        ids = _ids(self.payload)
        assert "lymphocytosis" in ids

    def test_viral_combo(self):
        r = analyze_cbc_payload(self.payload)
        combo_ids = {c["id"] for c in r["combos"]}
        assert "viral_like_pattern" in combo_ids



class TestSevereNeutropenia:

    payload = {
        "sex": "female", "age": 55,
        "wbc": 1.0, "hgb": 11.5, "plt": 180,
        "neut_pct": 20, "lymph_pct": 65, "mono_pct": 10, "eos_pct": 4, "baso_pct": 1,
    }

    def test_neutropenia_high_severity(self):
        r = analyze_cbc_payload(self.payload)
        neutro = next((s for s in r["signals"] if s["id"] == "neutropenia"), None)
        assert neutro is not None
        assert neutro["severity"] in ("high", "medium")



class TestITP:

    payload = {
        "sex": "female", "age": 30,
        "wbc": 7.0, "hgb": 14.0, "plt": 18,
    }

    def test_severe_thrombocytopenia(self):
        r = analyze_cbc_payload(self.payload)
        thr = next((s for s in r["signals"] if s["id"] == "thrombocytopenia"), None)
        assert thr is not None
        assert thr["severity"] == "high"



class TestPancytopenia:

    payload = {
        "sex": "male", "age": 60,
        "wbc": 2.0, "hgb": 7.5, "plt": 35,
        "rbc": 2.5, "hct": 22, "mcv": 105, "mch": 33, "mchc": 32, "rdw": 16.5,
    }

    def test_pancytopenia_pattern(self):
        ids = _ids(self.payload)
        assert "pancytopenia_pattern" in ids

    def test_overall_high_severity(self):
        r = analyze_cbc_payload(self.payload)
        assert r["summary"]["signals_high"] >= 1



class TestPolycythemia:

    payload = {
        "sex": "male", "age": 55,
        "wbc": 11.0, "hgb": 19.5, "plt": 480,
        "rbc": 6.3, "hct": 58, "mcv": 88,
    }

    def test_high_hgb(self):
        ids = _ids(self.payload)
        assert "high_hgb" in ids

    def test_thrombocytosis(self):
        ids = _ids(self.payload)
        assert "thrombocytosis" in ids



class TestCLLLike:

    payload = {
        "sex": "male", "age": 72,
        "wbc": 35.0, "hgb": 12.5, "plt": 220,
        "neut_pct": 15, "lymph_pct": 78, "mono_pct": 5, "eos_pct": 1, "baso_pct": 1,
    }

    def test_signals(self):
        ids = _ids(self.payload)
        assert "leukocytosis" in ids
        assert "lymphocytosis" in ids



class TestEosinophilia:

    payload = {
        "sex": "male", "age": 35,
        "wbc": 10.5, "hgb": 14.5, "plt": 260,
        "neut_pct": 50, "lymph_pct": 22, "mono_pct": 5, "eos_pct": 20, "baso_pct": 3,
    }

    def test_eosinophilia(self):
        ids = _ids(self.payload)
        assert "eosinophilia" in ids



class TestReactiveThrombocytosis:

    payload = {
        "sex": "female", "age": 45,
        "wbc": 9.5, "hgb": 12.0, "plt": 650,
        "rbc": 4.2, "hct": 36, "mcv": 86, "mch": 28, "mchc": 33, "rdw": 14.0,
    }

    def test_thrombocytosis(self):
        ids = _ids(self.payload)
        assert "thrombocytosis" in ids



class TestSteroidLeukocytosis:

    payload = {
        "sex": "female", "age": 60,
        "wbc": 14.0, "hgb": 13.5, "plt": 290,
        "neut_pct": 78, "lymph_pct": 14, "mono_pct": 5, "eos_pct": 2, "baso_pct": 1,
        "context": {"on_corticosteroids": True},
    }

    def test_context_aware_signal(self):
        ids = _ids(self.payload)
        assert "leukocytosis_on_steroids" in ids



class TestAllNormal:

    payload = {
        "sex": "male", "age": 35,
        "wbc": 6.5, "hgb": 15.0, "plt": 250,
        "neut_pct": 60, "lymph_pct": 30, "mono_pct": 7, "eos_pct": 2, "baso_pct": 1,
        "rbc": 5.0, "hct": 45, "mcv": 88, "mch": 29, "mchc": 33,
        "rdw": 13.0, "mpv": 9.5,
    }

    def test_zero_clinical_signals(self):
        r = analyze_cbc_payload(self.payload)
        assert r["summary"]["signals_high"] == 0
        assert r["summary"]["signals_medium"] == 0
        ids = {s["id"] for s in r["signals"]}
        assert "missing_core_cbc" not in ids

    def test_headline_says_normal(self):
        r = analyze_cbc_payload(self.payload)
        assert "не виявлено" in r["summary"]["headline"].lower() or \
               "норм" in r["summary"]["headline"].lower()
