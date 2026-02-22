from __future__ import annotations

import pytest

from cbc_api.analyze import analyze_cbc_payload
from cbc_api.rules import _flag, _sev_high, _sev_low, _sex_norm
from cbc_api.config import CBCConfig, SeverityBand
from cbc_api.knowledge import RefRange



class TestFlagHelper:

    def test_below_low_returns_low(self):
        rr = RefRange(low=4.0, high=11.0)
        assert _flag(3.0, rr) == "low"

    def test_above_high_returns_high(self):
        rr = RefRange(low=4.0, high=11.0)
        assert _flag(12.0, rr) == "high"

    def test_in_range_returns_normal(self):
        rr = RefRange(low=4.0, high=11.0)
        assert _flag(7.0, rr) == "normal"

    def test_at_boundary_low_is_normal(self):
        rr = RefRange(low=4.0, high=11.0)
        assert _flag(4.0, rr) == "normal"

    def test_at_boundary_high_is_normal(self):
        rr = RefRange(low=4.0, high=11.0)
        assert _flag(11.0, rr) == "normal"

    def test_none_value(self):
        rr = RefRange(low=4.0, high=11.0)
        assert _flag(None, rr) is None

    def test_no_bounds(self):
        rr = RefRange()
        assert _flag(7.0, rr) == "normal"


class TestSeverityHelpers:

    def test_sev_high_classifies(self):
        band = SeverityBand(mild=11.0, moderate=15.0, severe=25.0)
        assert _sev_high(12.0, band) == "low"
        assert _sev_high(17.0, band) == "medium"
        assert _sev_high(30.0, band) == "high"
        assert _sev_high(10.0, band) is None
        assert _sev_high(None, band) is None

    def test_sev_low_classifies(self):
        band = SeverityBand(mild=3.5, moderate=2.0, severe=1.0)
        assert _sev_low(1.5, band) == "medium"
        assert _sev_low(0.8, band) == "high"
        assert _sev_low(3.0, band) == "low"
        assert _sev_low(None, band) is None


class TestSexNorm:

    @pytest.mark.parametrize("inp,expected", [
        ("male", "male"), ("MALE", "male"), ("m", "male"), ("M", "male"),
        ("ч", "male"), ("чоловік", "male"),
        ("female", "female"), ("FEMALE", "female"), ("f", "female"),
        ("F", "female"), ("ж", "female"), ("жінка", "female"),
        (None, None), ("", None), ("unknown", None),
    ])
    def test_sex_norm_variants(self, inp, expected):
        assert _sex_norm(inp) == expected

    def test_sex_norm_numeric_nhanes_returns_none(self):
        assert _sex_norm(1) is None
        assert _sex_norm(2) is None
        assert _sex_norm("1") is None



def _signal_ids(payload: dict) -> set[str]:
    result = analyze_cbc_payload(payload)
    return {s["id"] for s in result["signals"]}


def _get_signal(payload: dict, sig_id: str) -> dict | None:
    for s in analyze_cbc_payload(payload)["signals"]:
        if s["id"] == sig_id:
            return s
    return None


class TestDataQualitySignals:

    def test_missing_core_cbc_fires_on_empty(self):
        ids = _signal_ids({"sex": "male", "age": 30})
        assert "missing_core_cbc" in ids

    def test_missing_core_does_not_fire_when_core_present(self):
        ids = _signal_ids({
            "sex": "male", "age": 30,
            "wbc": 7.0, "hgb": 14.0, "plt": 250,
        })
        assert "missing_core_cbc" not in ids


class TestWhiteCellSignals:

    def test_leukocytosis(self):
        ids = _signal_ids({"sex": "male", "age": 40, "wbc": 12.5, "hgb": 14, "plt": 250})
        assert "leukocytosis" in ids

    def test_leukopenia(self):
        ids = _signal_ids({"sex": "male", "age": 40, "wbc": 2.5, "hgb": 14, "plt": 250})
        assert "leukopenia" in ids

    def test_neutrophilic_leukocytosis(self, bacterial):
        ids = _signal_ids(bacterial)
        assert "neutrophilic_leukocytosis" in ids

    def test_neutrophilia(self, bacterial):
        ids = _signal_ids(bacterial)
        assert "neutrophilia" in ids

    def test_neutropenia(self, severe_neutropenia):
        ids = _signal_ids(severe_neutropenia)
        assert "neutropenia" in ids

    def test_neutropenia_is_high_severity(self, severe_neutropenia):
        sig = _get_signal(severe_neutropenia, "neutropenia")
        assert sig is not None
        assert sig["severity"] == "high"

    def test_lymphocytosis(self, viral_lymphocytosis):
        ids = _signal_ids(viral_lymphocytosis)
        assert "lymphocytosis" in ids

    def test_lymphopenia(self):
        ids = _signal_ids({
            "sex": "male", "age": 40, "wbc": 6.0, "hgb": 14, "plt": 250,
            "neut_pct": 88, "lymph_pct": 8, "mono_pct": 3, "eos_pct": 1, "baso_pct": 0,
        })
        assert "lymphopenia" in ids

    def test_eosinophilia(self, eosinophilia_pt):
        ids = _signal_ids(eosinophilia_pt)
        assert "eosinophilia" in ids

    def test_monocytosis(self):
        ids = _signal_ids({
            "sex": "male", "age": 35, "wbc": 8.0, "hgb": 14, "plt": 250,
            "neut_pct": 50, "lymph_pct": 28, "mono_pct": 15, "eos_pct": 5, "baso_pct": 2,
        })
        assert "monocytosis" in ids

    def test_basophilia(self):
        ids = _signal_ids({
            "sex": "male", "age": 35, "wbc": 8.0, "hgb": 14, "plt": 250,
            "neut_pct": 50, "lymph_pct": 28, "mono_pct": 8, "eos_pct": 6, "baso_pct": 8,
        })
        assert "basophilia" in ids


class TestPlateletSignals:

    def test_thrombocytopenia(self, severe_thrombocytopenia):
        ids = _signal_ids(severe_thrombocytopenia)
        assert "thrombocytopenia" in ids

    def test_thrombocytopenia_high_severity(self, severe_thrombocytopenia):
        sig = _get_signal(severe_thrombocytopenia, "thrombocytopenia")
        assert sig is not None
        assert sig["severity"] == "high"

    def test_thrombocytosis(self, reactive_thrombocytosis):
        ids = _signal_ids(reactive_thrombocytosis)
        assert "thrombocytosis" in ids


class TestRedCellSignals:

    def test_anemia_possible(self, iron_deficiency):
        ids = _signal_ids(iron_deficiency)
        assert "anemia_possible" in ids

    def test_microcytic_anemia_pattern(self, iron_deficiency):
        ids = _signal_ids(iron_deficiency)
        assert "microcytic_anemia_pattern" in ids

    def test_macrocytic_anemia_pattern(self, b12_macrocytic):
        ids = _signal_ids(b12_macrocytic)
        assert "macrocytic_anemia_pattern" in ids

    def test_normocytic_anemia_pattern(self):
        ids = _signal_ids({
            "sex": "female", "age": 35,
            "wbc": 6.0, "hgb": 10.0, "plt": 250,
            "rbc": 4.0, "hct": 32, "mcv": 88, "mch": 29, "mchc": 33, "rdw": 13.5,
        })
        assert "normocytic_anemia_pattern" in ids

    def test_high_hgb(self, polycythemia):
        ids = _signal_ids(polycythemia)
        assert "high_hgb" in ids

    def test_high_rdw(self, iron_deficiency):
        ids = _signal_ids(iron_deficiency)
        assert "high_rdw" in ids

    def test_iron_deficiency_likely_pattern(self, iron_deficiency):
        ids = _signal_ids(iron_deficiency)
        assert "iron_deficiency_likely_pattern" in ids

    def test_microcytosis_without_anemia(self):
        ids = _signal_ids({
            "sex": "male", "age": 35,
            "wbc": 7.0, "hgb": 14.5, "plt": 280,
            "mcv": 75, "rdw": 13.0,
        })
        assert "microcytosis_without_anemia" in ids

    def test_macrocytosis_without_anemia(self):
        ids = _signal_ids({
            "sex": "male", "age": 35,
            "wbc": 6.5, "hgb": 15.0, "plt": 240,
            "mcv": 105, "rdw": 14.0,
        })
        assert "macrocytosis_without_anemia" in ids

    def test_thalassemia_trait_pattern(self, thalassemia_trait):
        ids = _signal_ids(thalassemia_trait)
        assert "thal_trait_like_pattern" in ids


class TestCombinationSignals:

    def test_plt_high_microcytosis_combo(self):
        ids = _signal_ids({
            "sex": "female", "age": 40,
            "wbc": 7.0, "hgb": 11.5, "plt": 500,
            "mcv": 75, "rdw": 15.0,
        })
        assert "plt_high_microcytosis_combo" in ids

    def test_pancytopenia_pattern(self, pancytopenia):
        ids = _signal_ids(pancytopenia)
        assert "pancytopenia_pattern" in ids

    def test_pancytopenia_high_severity(self, pancytopenia):
        sig = _get_signal(pancytopenia, "pancytopenia_pattern")
        assert sig is not None
        assert sig["severity"] == "high"


class TestSupportiveSignals:

    def test_elevated_esr(self, high_esr):
        ids = _signal_ids(high_esr)
        assert "elevated_esr" in ids

    def test_nlr_high(self, bacterial):
        ids = _signal_ids(bacterial)
        assert "nlr_high" in ids

    def test_low_mchc_hypochromia(self, iron_deficiency):
        ids = _signal_ids(iron_deficiency)
        assert "low_mchc_hypochromia" in ids



class TestContextAwareSignals:

    def test_anemia_with_diabetes_when_diabetes_context(self):
        ids = _signal_ids({
            "sex": "female", "age": 60,
            "wbc": 7.0, "hgb": 10.0, "plt": 250,
            "rbc": 4.0, "hct": 32, "mcv": 90, "mch": 29, "mchc": 33, "rdw": 13.5,
            "context": {"has_diabetes": True},
        })
        assert "anemia_with_diabetes" in ids

    def test_leukocytosis_on_steroids_variant(self):
        ids = _signal_ids({
            "sex": "male", "age": 50,
            "wbc": 14.0, "hgb": 14, "plt": 280,
            "neut_pct": 80, "lymph_pct": 14, "mono_pct": 3, "eos_pct": 2, "baso_pct": 1,
            "context": {"on_corticosteroids": True},
        })
        assert "leukocytosis_on_steroids" in ids

    def test_thrombocytopenia_on_anticoagulants_variant(self):
        ids = _signal_ids({
            "sex": "male", "age": 65,
            "wbc": 6.0, "hgb": 13.0, "plt": 80,
            "context": {"on_oral_anticoagulants": True},
        })
        assert "thrombocytopenia_on_anticoagulants" in ids

    def test_thrombocytopenia_on_anticoagulants_is_high_severity(self):
        sig = _get_signal(
            {
                "sex": "male", "age": 65,
                "wbc": 6.0, "hgb": 13.0, "plt": 80,
                "context": {"on_oral_anticoagulants": True},
            },
            "thrombocytopenia_on_anticoagulants",
        )
        assert sig is not None
        assert sig["severity"] == "high"
