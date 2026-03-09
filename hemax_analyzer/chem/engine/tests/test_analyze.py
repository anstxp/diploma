from __future__ import annotations

import hashlib
import json

import pytest

from chem_api.chem.analyze import (
    ALIASES,
    DISCLAIMER,
    ENGINE_VERSION,
    analyze_chem_payload,
)



REQUIRED_TOP_LEVEL_KEYS = {
    "version", "profile", "meta", "summary",
    "labs", "flags", "derived",
    "signals", "combos", "recommendations",
    "disclaimer",
}

REQUIRED_META_KEYS = {"field_meta", "computed", "context", "missing_core"}

REQUIRED_SUMMARY_KEYS = {
    "headline", "signals_high", "signals_medium", "notes"
}


class TestResponseEnvelope:

    def test_top_level_keys(self, healthy_male):
        r = analyze_chem_payload(healthy_male)
        assert REQUIRED_TOP_LEVEL_KEYS <= set(r.keys())

    def test_meta_keys(self, healthy_male):
        r = analyze_chem_payload(healthy_male)
        assert REQUIRED_META_KEYS <= set(r["meta"].keys())

    def test_summary_keys(self, healthy_male):
        r = analyze_chem_payload(healthy_male)
        assert REQUIRED_SUMMARY_KEYS <= set(r["summary"].keys())

    def test_version_string(self, healthy_male):
        assert analyze_chem_payload(healthy_male)["version"] == ENGINE_VERSION

    def test_disclaimer_present(self, healthy_male):
        r = analyze_chem_payload(healthy_male)
        assert r["disclaimer"] == DISCLAIMER
        assert "медичною консультацією" in r["disclaimer"]



class TestProfileParsing:

    def test_age_coerced_to_float(self, healthy_male):
        r = analyze_chem_payload(healthy_male)
        assert isinstance(r["profile"]["age"], float)
        assert r["profile"]["age"] == 35.0

    def test_string_age_coerced(self):
        r = analyze_chem_payload({"sex": "male", "age": "42", "glucose": 95})
        assert r["profile"]["age"] == 42.0

    def test_invalid_age_becomes_none(self):
        r = analyze_chem_payload({"sex": "male", "age": "old", "glucose": 95})
        assert r["profile"]["age"] is None

    def test_sex_normalized_male(self):
        r = analyze_chem_payload({"sex": "M", "age": 30, "glucose": 95})
        assert r["profile"]["sex"] == "male"

    def test_sex_normalized_female(self):
        r = analyze_chem_payload({"sex": "F", "age": 30, "glucose": 95})
        assert r["profile"]["sex"] == "female"

    def test_sex_normalized_ukrainian(self):
        r = analyze_chem_payload({"sex": "жінка", "age": 30, "glucose": 95})
        assert r["profile"]["sex"] == "female"



class TestAliasResolution:

    def test_nhanes_glucose(self):
        r = analyze_chem_payload({"sex": "male", "age": 30, "LBXGLU": 95})
        assert r["meta"]["field_meta"]["glucose"]["input_key"] == "LBXGLU"

    def test_nhanes_lipid(self):
        r = analyze_chem_payload({
            "sex": "male", "age": 30,
            "LBXTC": 180, "LBXHDD": 50,
        })
        assert r["meta"]["field_meta"]["tchol"]["input_key"] == "LBXTC"

    def test_a1c_alias(self):
        for alias in ("a1c", "hba1c", "LBXGH"):
            r = analyze_chem_payload({"sex": "male", "age": 30, alias: 5.5})
            assert r["meta"]["field_meta"]["a1c"]["input_key"] == alias

    def test_creatinine_alias(self):
        r = analyze_chem_payload({"sex": "male", "age": 30, "scr": 1.0})
        assert r["meta"]["field_meta"]["creatinine"]["input_key"] == "scr"

    def test_aliases_table_completeness(self):
        for code in ("glucose", "a1c", "creatinine", "alt", "ast", "tchol",
                     "hdl", "sodium", "potassium", "calcium",
                     "iron", "ferritin", "vitd_25oh"):
            assert code in ALIASES
            assert len(ALIASES[code]) >= 1



class TestEmbeddedUnits:

    def test_glucose_with_mgdl(self):
        r = analyze_chem_payload({
            "sex": "male", "age": 30,
            "glucose": "92 mg/dL",
            "creatinine": "1.0 mg/dL",
        })
        meta = r["meta"]["field_meta"]
        assert meta["glucose"]["unit_in"] is not None

    def test_glucose_mmol_converted(self):
        r = analyze_chem_payload({
            "sex": "male", "age": 30,
            "glucose": "5.0 mmol/L",
        })
        lab = next(l for l in r["labs"] if l["code"] == "glucose")
        assert 89 < lab["value"] < 92



class TestFastingContext:

    def test_fasting_hours_recorded(self):
        r = analyze_chem_payload({
            "sex": "male", "age": 30, "glucose": 95,
            "fasting_hours": 12,
        })
        assert r["meta"]["context"]["fasting_hours"] == 12.0
        assert r["meta"]["context"]["fasting_8h"] is True

    def test_fasting_8h_derived_from_hours(self):
        r = analyze_chem_payload({
            "sex": "male", "age": 30, "glucose": 95,
            "fasting_hours": 6,
        })
        assert r["meta"]["context"]["fasting_8h"] is False

    def test_fasting_8h_explicit_true(self):
        r = analyze_chem_payload({
            "sex": "male", "age": 30, "glucose": 95,
            "fasting_8h": True,
        })
        assert r["meta"]["context"]["fasting_8h"] is True

    def test_fasting_8h_string_yes(self):
        r = analyze_chem_payload({
            "sex": "male", "age": 30, "glucose": 95,
            "fasting_8h": "yes",
        })
        assert r["meta"]["context"]["fasting_8h"] is True

    def test_fasting_8h_ukrainian(self):
        r = analyze_chem_payload({
            "sex": "male", "age": 30, "glucose": 95,
            "fasting_8h": "так",
        })
        assert r["meta"]["context"]["fasting_8h"] is True



class TestClinicalContext:

    def test_bool_flags_preserved(self):
        r = analyze_chem_payload({
            "sex": "male", "age": 50, "glucose": 95,
            "clinical_context": {
                "has_diabetes": True,
                "on_statins": False,
            },
        })
        ctx = r["meta"]["context"]["clinical"]
        assert ctx["has_diabetes"] is True
        assert ctx["on_statins"] is False

    def test_non_bool_values_filtered(self):
        r = analyze_chem_payload({
            "sex": "male", "age": 50, "glucose": 95,
            "clinical_context": {"weird": "maybe"},
        })
        assert "weird" not in r["meta"]["context"]["clinical"]

    def test_invalid_clinical_context_skipped(self):
        r = analyze_chem_payload({
            "sex": "male", "age": 50, "glucose": 95,
            "clinical_context": "not a dict",
        })
        assert r["meta"]["context"]["clinical"] == {}



class TestRefRangesOverride:

    def test_override_changes_flag(self):
        base = {"sex": "male", "age": 30, "glucose": 95}
        normal = analyze_chem_payload(base)
        glu_lab = next(l for l in normal["labs"] if l["code"] == "glucose")
        assert glu_lab["flag"] is None or glu_lab["flag"] == "normal" or glu_lab["flag"] != "high"

        override = {**base, "ref_ranges": {"glucose": {"low": 60, "high": 90}}}
        ov_r = analyze_chem_payload(override)
        glu_lab = next(l for l in ov_r["labs"] if l["code"] == "glucose")
        assert glu_lab["flag"] == "high"

    def test_override_marked_in_ref_source(self):
        r = analyze_chem_payload({
            "sex": "male", "age": 30, "glucose": 95,
            "ref_ranges": {"glucose": {"low": 60, "high": 90}},
        })
        glu_lab = next(l for l in r["labs"] if l["code"] == "glucose")
        assert glu_lab["ref_source"] == "override"



class TestNegativeValueRejection:

    def test_negative_glucose_rejected(self):
        r = analyze_chem_payload({"sex": "male", "age": 30, "glucose": -5})
        assert not any(l["code"] == "glucose" for l in r["labs"])



class TestDeterminism:

    def test_100_runs_same_hash(self, metabolic_syndrome):
        hashes = set()
        for _ in range(100):
            r = analyze_chem_payload(metabolic_syndrome)
            h = hashlib.sha256(
                json.dumps(r, sort_keys=True, default=str, ensure_ascii=False).encode()
            ).hexdigest()
            hashes.add(h)
        assert len(hashes) == 1

    def test_determinism_across_all_fixtures(self, all_patient_names, request):
        payload = request.getfixturevalue(all_patient_names)
        r1 = analyze_chem_payload(payload)
        r2 = analyze_chem_payload(payload)
        h1 = hashlib.sha256(json.dumps(r1, sort_keys=True, default=str).encode()).hexdigest()
        h2 = hashlib.sha256(json.dumps(r2, sort_keys=True, default=str).encode()).hexdigest()
        assert h1 == h2



class TestEdgeCases:

    def test_empty_payload(self):
        r = analyze_chem_payload({})
        assert r["version"] == ENGINE_VERSION
        assert "missing_core_chem" in {s["id"] for s in r["signals"]}

    def test_only_age(self):
        r = analyze_chem_payload({"age": 30})
        assert r["profile"]["age"] == 30.0

    def test_signals_have_required_fields(self, iron_deficiency):
        r = analyze_chem_payload(iron_deficiency)
        for sig in r["signals"]:
            assert "id" in sig
            assert "severity" in sig
            assert sig["severity"] in ("high", "medium", "low")

    def test_labs_have_required_fields(self, healthy_male):
        r = analyze_chem_payload(healthy_male)
        for lab in r["labs"]:
            assert "code" in lab
            assert "value" in lab
            assert "unit" in lab
            assert "flag" in lab

    def test_lab_cards_sorted_by_lab_order(self, healthy_male):
        r = analyze_chem_payload(healthy_male)
        codes = [l["code"] for l in r["labs"]]
        if "glucose" in codes and "sodium" in codes:
            assert codes.index("glucose") < codes.index("sodium")
