from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from cbc_api.analyze import (
    ALIASES,
    DISCLAIMER,
    ENGINE_VERSION,
    analyze_cbc_payload,
)
from cbc_api.config import CBCConfig
from cbc_api.knowledge import ABS_REFS, LABS
from cbc_api.narrative.narrative_engine import load_clusters
from cbc_api.pediatric_refs import get_pediatric_ref
from cbc_api.spec import CBC_CORE, CBC_VARS, DIFF_ABS
from cbc_api.validation import PLAUSIBLE_RANGES, UNIT_CONFUSION_RULES



class TestR1_EngineVersionAndEnvelope:

    def test_engine_version_string(self):
        assert ENGINE_VERSION == "cbc_interpreter_prod_v1_0_max"

    def test_response_version_field(self):
        r = analyze_cbc_payload({"sex": "male", "age": 30, "wbc": 7.0})
        assert r["version"] == ENGINE_VERSION

    def test_response_top_level_envelope(self):
        r = analyze_cbc_payload({"sex": "male", "age": 30, "wbc": 7.0, "hgb": 14, "plt": 250})
        required = {
            "version", "profile", "meta", "summary",
            "labs", "flags", "derived",
            "signals", "combos", "recommendations",
            "disclaimer",
        }
        assert required <= set(r.keys())

    def test_disclaimer_is_present_and_non_empty(self):
        r = analyze_cbc_payload({"sex": "male", "age": 30})
        assert r["disclaimer"]
        assert "медичною консультацією" in r["disclaimer"], (
            "Disclaimer must clarify this is not a medical diagnosis"
        )

    def test_signals_field_is_list_of_dicts(self):
        r = analyze_cbc_payload({"sex": "female", "age": 30, "wbc": 6, "hgb": 9.5,
                                 "plt": 350, "mcv": 70, "rdw": 17})
        assert isinstance(r["signals"], list)
        for sig in r["signals"]:
            assert isinstance(sig, dict)
            assert "id" in sig and "severity" in sig

    def test_meta_contains_required_diagnostic_subfields(self):
        r = analyze_cbc_payload({"sex": "male", "age": 30, "wbc": 7.0, "hgb": 14, "plt": 250})
        m = r["meta"]
        assert "field_meta" in m
        assert "computed_abs" in m
        assert "normalized_diff" in m
        assert "missing_core" in m


EXPECTED_SIGNAL_IDS = {
    "missing_core_cbc",
    "leukocytosis", "leukopenia",
    "neutrophilia", "neutropenia",
    "neutrophilic_leukocytosis",
    "relative_neutrophilia",
    "lymphocytosis", "lymphopenia",
    "relative_lymphocytosis",
    "monocytosis",
    "eosinophilia",
    "basophilia",
    "anemia_possible", "high_hgb", "high_rdw",
    "microcytic_anemia_pattern", "macrocytic_anemia_pattern",
    "normocytic_anemia_pattern",
    "microcytosis_without_anemia", "macrocytosis_without_anemia",
    "iron_deficiency_likely_pattern",
    "thal_trait_like_pattern",
    "low_mchc_hypochromia", "high_mchc_note",
    "hemoconcentration_possible",
    "thrombocytopenia", "thrombocytosis",
    "low_plt_high_mpv", "low_plt_low_mpv",
    "plt_high_microcytosis_combo",
    "pancytopenia_pattern",
    "bicytopenia_wbc_hgb", "bicytopenia_wbc_plt", "bicytopenia_hgb_plt",
    "elevated_esr",
    "nlr_high",
    "anemia_with_diabetes",
    "leukocytosis_on_steroids",
    "thrombocytopenia_on_anticoagulants",
}


class TestR2_SignalCatalog:

    def test_expected_signal_count(self):
        assert len(EXPECTED_SIGNAL_IDS) == 40

    def test_data_quality_signal_present(self):
        r = analyze_cbc_payload({})
        assert any(s["id"] == "missing_core_cbc" for s in r["signals"])

    def test_signal_priority_table_covers_main_signals(self):
        cfg = CBCConfig()
        for sig in ("pancytopenia_pattern", "neutropenia", "thrombocytopenia",
                    "anemia_possible", "leukocytosis", "missing_core_cbc"):
            assert sig in cfg.signal_priority

    def test_severity_levels_are_limited(self):
        valid = {"high", "medium", "low"}
        scenarios = [
            {"sex": "female", "age": 30, "wbc": 6, "hgb": 9.5, "plt": 350,
             "mcv": 70, "rdw": 17},
            {"sex": "male", "age": 60, "wbc": 2.5, "hgb": 9, "plt": 60},
            {"sex": "male", "age": 40, "wbc": 15, "hgb": 14, "plt": 250,
             "neut_pct": 85, "lymph_pct": 10, "mono_pct": 3, "eos_pct": 1,
             "baso_pct": 1},
            {},
        ]
        for payload in scenarios:
            for sig in analyze_cbc_payload(payload)["signals"]:
                assert sig["severity"] in valid

    def test_urgent_signals_are_high_severity(self):
        r = analyze_cbc_payload({"sex": "male", "age": 50, "wbc": 2.0, "hgb": 8.0, "plt": 40,
                                  "rbc": 2.8})
        pancyt = next((s for s in r["signals"] if s["id"] == "pancytopenia_pattern"), None)
        assert pancyt and pancyt["severity"] == "high"



_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "cbc_api" / "narrative" / "templates"


class TestR3_NarrativeCoverage:

    def test_31_clusters(self):
        assert len(load_clusters()) == 31

    def test_bilingual_template_files(self):
        cluster_ids = {c["id"] for c in load_clusters()}
        for cid in cluster_ids:
            assert (_TEMPLATES_DIR / f"{cid}.uk.md").exists(), (
                f"Cluster '{cid}' missing UK template"
            )
            assert (_TEMPLATES_DIR / f"{cid}.en.md").exists(), (
                f"Cluster '{cid}' missing EN template"
            )

    def test_62_template_files_total(self):
        assert len(list(_TEMPLATES_DIR.glob("*.uk.md"))) == 31
        assert len(list(_TEMPLATES_DIR.glob("*.en.md"))) == 31



class TestR4_ReferenceRanges:

    def test_16_adult_labs(self):
        assert len(LABS) == 16

    def test_hgb_is_sex_specific(self):
        hgb = LABS["hgb"]
        assert hgb.ref_male != hgb.ref_female
        assert (hgb.ref_male.low or 0) > (hgb.ref_female.low or 0)

    def test_5_absolute_diff_refs(self):
        assert set(ABS_REFS.keys()) == {"anc", "alc", "amc", "aec", "abc"}

    def test_pediatric_covers_newborn_through_adolescent(self):
        for age in (0.05, 0.5, 1, 5, 10):
            rr = get_pediatric_ref("hgb", age, None)
            assert rr is not None, f"No pediatric Hb ref for age {age} (sex=None)"
            assert rr.low and rr.high
        for age in (12, 15, 17):
            for sex in ("male", "female"):
                rr = get_pediatric_ref("hgb", age, sex)
                assert rr is not None, f"No pediatric Hb ref for age {age}, sex={sex}"
                assert rr.low and rr.high



class TestR5_InputFlexibility:

    def test_nhanes_codes_recognised(self):
        r = analyze_cbc_payload({
            "RIAGENDR": "male", "RIDAGEYR": 35,
            "LBXWBCSI": 6.5, "LBXHGB": 14.0, "LBXPLTSI": 250,
            "LBXMCVSI": 88,
        })
        meta = r["meta"]["field_meta"]
        assert meta["wbc"]["input_key"] == "LBXWBCSI"
        assert meta["hgb"]["input_key"] == "LBXHGB"

    def test_ukrainian_esr_alias(self):
        r = analyze_cbc_payload({
            "sex": "female", "age": 40,
            "wbc": 7, "hgb": 13, "plt": 250,
            "ШОЕ": 45,
        })
        assert any(s["id"] == "elevated_esr" for s in r["signals"])

    def test_embedded_unit_strings(self):
        r = analyze_cbc_payload({
            "sex": "male", "age": 30,
            "wbc": "6.5 10^3/uL",
            "hgb": "14.5 g/dL",
            "plt": "250 10^3/uL",
        })
        assert r["meta"]["missing_core"] == []

    def test_fraction_input_is_normalised(self):
        r = analyze_cbc_payload({
            "sex": "male", "age": 30,
            "wbc": 7.0, "hgb": 14.0, "plt": 250,
            "neut_pct": 0.60, "lymph_pct": 0.30, "mono_pct": 0.07,
            "eos_pct": 0.02, "baso_pct": 0.01,
        })
        assert r["meta"]["normalized_diff"]["rule"] == "fractions_to_percent"

    def test_aliases_table_covers_spec_core(self):
        for nhanes_code in CBC_CORE:
            found = False
            for canonical, alias_list in ALIASES.items():
                if nhanes_code in alias_list:
                    found = True
                    break
            assert found, f"NHANES code {nhanes_code} has no alias mapping"



class TestR6_Determinism:

    def test_100_runs_byte_identical(self):
        payload = {
            "sex": "female", "age": 35,
            "wbc": 6.0, "hgb": 11.0, "plt": 300,
            "rbc": 4.0, "mcv": 80, "mch": 27, "mchc": 33, "rdw": 14.5,
            "neut_pct": 55, "lymph_pct": 33, "mono_pct": 8, "eos_pct": 3, "baso_pct": 1,
        }
        hashes = set()
        for _ in range(100):
            r = analyze_cbc_payload(payload)
            blob = json.dumps(r, sort_keys=True, default=str, ensure_ascii=False)
            hashes.add(hashlib.sha256(blob.encode()).hexdigest())
        assert len(hashes) == 1



class TestR7_Safety:

    def test_missing_core_is_low_priority(self):
        cfg = CBCConfig()
        assert cfg.signal_priority["missing_core_cbc"] < 0

    def test_empty_payload_warns_not_silent(self):
        r = analyze_cbc_payload({})
        assert any(s["id"] == "missing_core_cbc" for s in r["signals"])
        assert "неповний" in r["summary"]["headline"].lower() or \
               "відсутні" in r["summary"]["headline"].lower()

    def test_pancytopenia_severity_propagates(self):
        r = analyze_cbc_payload({
            "sex": "male", "age": 50,
            "wbc": 2.0, "hgb": 8.0, "plt": 40, "rbc": 2.8,
        })
        assert r["summary"]["signals_high"] >= 1



class TestR8_EmpiricalConfig:

    def test_empirical_config_file_exists_in_outputs(self):
        path = Path(__file__).resolve().parent.parent.parent / "outputs" / "engine_config.json"
        assert path.exists(), f"missing {path}"
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        assert isinstance(cfg, dict)

    def test_empirical_refs_file_exists_in_outputs(self):
        path = Path(__file__).resolve().parent.parent.parent / "outputs" / "empirical_refs.json"
        assert path.exists()
        with open(path, "r", encoding="utf-8") as f:
            refs = json.load(f)
        assert isinstance(refs, dict)



class TestR9_ValidationContract:

    def test_plausibility_ranges_cover_all_core_labs(self):
        for lab in ("wbc", "hgb", "plt", "rbc", "hct", "mcv", "mch", "mchc", "rdw"):
            assert lab in PLAUSIBLE_RANGES

    def test_unit_confusion_covers_common_cases(self):
        for case in ("hgb", "plt", "wbc", "rbc", "hct"):
            assert case in UNIT_CONFUSION_RULES

    def test_validate_payload_returns_structured_result(self):
        from cbc_api.validation import validate_payload, ValidationResult
        r = validate_payload({"hgb": 14.0})
        assert isinstance(r, ValidationResult)
        assert isinstance(r.errors, list)
        assert isinstance(r.warnings, list)
        assert isinstance(r.normalised, dict)
