from __future__ import annotations

import hashlib
import json

import pytest

from cbc_api.analyze import (
    ALIASES,
    DISCLAIMER,
    ENGINE_VERSION,
    analyze_cbc_payload,
)



REQUIRED_TOP_LEVEL_KEYS = {
    "version", "profile", "meta", "summary",
    "labs", "flags", "derived",
    "signals", "combos", "recommendations",
    "disclaimer",
}

REQUIRED_META_KEYS = {
    "field_meta", "computed_abs", "normalized_diff", "missing_core", "context"
}

REQUIRED_SUMMARY_KEYS = {
    "headline", "signals_high", "signals_medium", "notes"
}

REQUIRED_RECOMMENDATIONS_KEYS = {"next_tests", "ask_doctor"}


class TestResponseEnvelope:

    def test_top_level_keys(self, healthy_male):
        r = analyze_cbc_payload(healthy_male)
        assert set(r.keys()) >= REQUIRED_TOP_LEVEL_KEYS, (
            f"Missing top-level keys: {REQUIRED_TOP_LEVEL_KEYS - set(r.keys())}"
        )

    def test_meta_keys(self, healthy_male):
        r = analyze_cbc_payload(healthy_male)
        assert set(r["meta"].keys()) >= REQUIRED_META_KEYS

    def test_summary_keys(self, healthy_male):
        r = analyze_cbc_payload(healthy_male)
        assert set(r["summary"].keys()) >= REQUIRED_SUMMARY_KEYS

    def test_recommendations_keys(self, iron_deficiency):
        r = analyze_cbc_payload(iron_deficiency)
        assert set(r["recommendations"].keys()) >= REQUIRED_RECOMMENDATIONS_KEYS

    def test_version_string(self, healthy_male):
        assert analyze_cbc_payload(healthy_male)["version"] == ENGINE_VERSION

    def test_disclaimer_present(self, healthy_male):
        r = analyze_cbc_payload(healthy_male)
        assert r["disclaimer"] == DISCLAIMER
        assert "медичною консультацією" in r["disclaimer"]



class TestProfileParsing:

    def test_age_coerced_to_float(self, healthy_male):
        r = analyze_cbc_payload(healthy_male)
        assert isinstance(r["profile"]["age"], float)
        assert r["profile"]["age"] == 35.0

    def test_string_age_coerced(self):
        r = analyze_cbc_payload({
            "sex": "male", "age": "42",
            "wbc": 7.0, "hgb": 14.0, "plt": 250,
        })
        assert r["profile"]["age"] == 42.0

    def test_invalid_age_becomes_none(self):
        r = analyze_cbc_payload({
            "sex": "male", "age": "old",
            "wbc": 7.0, "hgb": 14.0, "plt": 250,
        })
        assert r["profile"]["age"] is None



class TestAliasResolution:

    def test_nhanes_codes(self):
        r = analyze_cbc_payload({
            "RIAGENDR": "male", "RIDAGEYR": 45,
            "LBXWBCSI": 7.0, "LBXHGB": 14.0, "LBXPLTSI": 280,
            "LBXMCVSI": 88, "LBXRDW": 13.5,
        })
        meta = r["meta"]["field_meta"]
        assert "wbc" in meta
        assert meta["wbc"]["input_key"] == "LBXWBCSI"

    def test_ukrainian_esr(self):
        r = analyze_cbc_payload({
            "sex": "female", "age": 50,
            "wbc": 7.0, "hgb": 13.0, "plt": 250,
            "ШОЕ": 45,
        })
        assert any(s["id"] == "elevated_esr" for s in r["signals"])

    def test_aliases_table_completeness(self):
        for code in ("wbc", "hgb", "plt", "rbc", "mcv", "mch", "mchc",
                     "rdw", "mpv", "hct", "esr",
                     "neut_pct", "lymph_pct", "mono_pct", "eos_pct", "baso_pct",
                     "anc", "alc", "amc", "aec", "abc"):
            assert code in ALIASES, f"Missing aliases entry for '{code}'"
            assert len(ALIASES[code]) >= 1



class TestAbsCountDerivation:

    def test_abs_derived_from_pct(self, healthy_male):
        r = analyze_cbc_payload(healthy_male)
        assert set(r["meta"]["computed_abs"]) == {"anc", "alc", "amc", "aec", "abc"}

    def test_abs_not_derived_without_wbc(self):
        r = analyze_cbc_payload({
            "sex": "male", "age": 30,
            "hgb": 14.0, "plt": 250,
            "neut_pct": 60, "lymph_pct": 30,
        })
        assert r["meta"]["computed_abs"] == []

    def test_input_abs_overrides_derived(self):
        r = analyze_cbc_payload({
            "sex": "male", "age": 30,
            "wbc": 7.0, "hgb": 14.0, "plt": 250,
            "neut_pct": 60, "anc": 5.5,
        })
        assert "anc" not in r["meta"]["computed_abs"]



class TestDiffPercentNormalization:

    def test_fraction_input_scaled(self):
        r = analyze_cbc_payload({
            "sex": "male", "age": 30,
            "wbc": 7.0, "hgb": 14.0, "plt": 250,
            "neut_pct": 0.60, "lymph_pct": 0.30, "mono_pct": 0.07,
            "eos_pct": 0.02, "baso_pct": 0.01,
        })
        assert r["meta"]["normalized_diff"]["rule"] == "fractions_to_percent"
        assert "neut_pct" in r["meta"]["normalized_diff"]["scaled_codes"]

    def test_percent_input_not_scaled(self):
        r = analyze_cbc_payload({
            "sex": "male", "age": 30,
            "wbc": 7.0, "hgb": 14.0, "plt": 250,
            "neut_pct": 60, "lymph_pct": 30, "mono_pct": 7,
            "eos_pct": 2, "baso_pct": 1,
        })
        assert r["meta"]["normalized_diff"]["rule"] == "none"



class TestRefRangesOverride:

    def test_custom_hgb_ref_changes_flag(self):
        base = {
            "sex": "female", "age": 30,
            "wbc": 7.0, "hgb": 11.5, "plt": 250,
        }
        ids_default = {s["id"] for s in analyze_cbc_payload(base)["signals"]}
        assert "anemia_possible" in ids_default

        override = {**base, "ref_ranges": {"hgb": {"low": 10.0, "high": 15.5}}}
        ids_override = {s["id"] for s in analyze_cbc_payload(override)["signals"]}
        assert "anemia_possible" not in ids_override

    def test_ref_alias_works(self):
        for key in ("ref_ranges", "ref"):
            payload = {
                "sex": "male", "age": 30, "wbc": 7.0, "hgb": 14.5, "plt": 250,
                key: {"hgb": {"low": 16.0, "high": 20.0}},
            }
            ids = {s["id"] for s in analyze_cbc_payload(payload)["signals"]}
            assert "anemia_possible" in ids



class TestConfigOverride:

    def test_severity_threshold_override_changes_severity(self):
        base = {"sex": "male", "age": 30, "wbc": 16.0, "hgb": 14, "plt": 250}
        r_default = analyze_cbc_payload(base)
        leuko = next((s for s in r_default["signals"] if s["id"] == "leukocytosis"), None)
        assert leuko is not None
        assert leuko["severity"] == "medium"

        override = {
            **base,
            "config": {
                "severity_thresholds": {
                    "wbc_high": {"mild": 11.0, "moderate": 13.0, "severe": 15.0}
                }
            },
        }
        r_over = analyze_cbc_payload(override)
        leuko_over = next((s for s in r_over["signals"] if s["id"] == "leukocytosis"), None)
        assert leuko_over is not None
        assert leuko_over["severity"] == "high"



class TestSorting:

    def test_labs_sorted_by_lab_order(self, healthy_male):
        r = analyze_cbc_payload(healthy_male)
        codes = [c["code"] for c in r["labs"]]
        assert codes[0] == "wbc"

    def test_signals_sorted_by_severity_first(self, pancytopenia):
        r = analyze_cbc_payload(pancytopenia)
        if len(r["signals"]) >= 2:
            severities = [s["severity"] for s in r["signals"]]
            sev_rank = {"high": 3, "medium": 2, "low": 1}
            ranks = [sev_rank.get(sev, 0) for sev in severities]
            assert ranks == sorted(ranks, reverse=True)



class TestDeterminism:

    def test_same_input_same_output(self, iron_deficiency):
        hashes = set()
        for _ in range(100):
            r = analyze_cbc_payload(iron_deficiency)
            h = hashlib.sha256(
                json.dumps(r, sort_keys=True, default=str, ensure_ascii=False).encode()
            ).hexdigest()
            hashes.add(h)
        assert len(hashes) == 1, (
            f"Engine is non-deterministic — got {len(hashes)} unique outputs"
        )

    def test_determinism_across_all_fixtures(self, all_patient_names, request):
        payload = request.getfixturevalue(all_patient_names)
        r1 = analyze_cbc_payload(payload)
        r2 = analyze_cbc_payload(payload)
        h1 = hashlib.sha256(json.dumps(r1, sort_keys=True, default=str).encode()).hexdigest()
        h2 = hashlib.sha256(json.dumps(r2, sort_keys=True, default=str).encode()).hexdigest()
        assert h1 == h2



class TestEdgeCases:

    def test_empty_payload(self):
        r = analyze_cbc_payload({})
        assert r["version"] == ENGINE_VERSION
        assert "missing_core_cbc" in {s["id"] for s in r["signals"]}

    def test_only_age(self):
        r = analyze_cbc_payload({"age": 30})
        assert r["profile"]["age"] == 30.0

    def test_string_value_with_embedded_unit(self):
        r = analyze_cbc_payload({
            "sex": "male", "age": 30,
            "wbc": "6.5 10^3/uL", "hgb": "14.5 g/dL", "plt": 250,
        })
        assert r["meta"]["field_meta"]["wbc"]["unit_in"] is not None

    def test_signals_have_required_fields(self, iron_deficiency):
        r = analyze_cbc_payload(iron_deficiency)
        for sig in r["signals"]:
            assert "id" in sig
            assert "severity" in sig
            assert sig["severity"] in ("high", "medium", "low")
            assert "title" in sig

    def test_labs_have_required_fields(self, healthy_male):
        r = analyze_cbc_payload(healthy_male)
        for lab in r["labs"]:
            assert "code" in lab
            assert "value" in lab or "flag" in lab
