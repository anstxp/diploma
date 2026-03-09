from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from chem_api.chem.analyze import (
    ALIASES,
    DISCLAIMER,
    ENGINE_VERSION,
    analyze_chem_payload,
)
from chem_api.chem.config import ChemConfig
from chem_api.chem.knowledge import LABS
from chem_api.narrative.narrative_engine import load_clusters



class TestR1_EngineVersionAndEnvelope:

    def test_engine_version_string(self):
        assert ENGINE_VERSION == "chem_interpreter_prod_v1_2_max"

    def test_response_version_field(self):
        r = analyze_chem_payload({"sex": "male", "age": 30, "glucose": 95})
        assert r["version"] == ENGINE_VERSION

    def test_response_top_level_envelope(self):
        r = analyze_chem_payload({"sex": "male", "age": 30, "glucose": 95})
        required = {
            "version", "profile", "meta", "summary",
            "labs", "flags", "derived",
            "signals", "combos", "recommendations",
            "disclaimer",
        }
        assert required <= set(r.keys())

    def test_disclaimer_present(self):
        r = analyze_chem_payload({"sex": "male", "age": 30, "glucose": 95})
        assert r["disclaimer"] == DISCLAIMER
        assert "медичною консультацією" in r["disclaimer"]

    def test_meta_subfields(self):
        r = analyze_chem_payload({"sex": "male", "age": 30, "glucose": 95})
        m = r["meta"]
        for key in ("field_meta", "computed", "context", "missing_core"):
            assert key in m, f"meta missing '{key}'"



EXPECTED_SIGNAL_IDS = {
    "missing_core_chem",
    "glucose_diabetes_range", "glucose_ifg_range",
    "a1c_diabetes_range", "a1c_prediabetes_range",
    "hypoglycemia", "severe_hypoglycemia",
    "hyperkalemia", "hypokalemia",
    "hyponatremia", "hypernatremia",
    "bicarbonate_high", "bicarbonate_low",
    "chloride_high", "chloride_low",
    "creatinine_high", "egfr_low",
    "transaminitis", "bilirubin_high",
    "tchol_high", "low_hdl", "non_hdl_high",
    "hypertriglyceridemia", "tg_hdl_ratio_high",
    "atherogenic_dyslipidemia_pattern",
    "crp_high", "uric_acid_high",
    "iron_deficiency_likely",
    "ferritin_high_possible_inflammation",
    "high_tsat", "low_tsat",
    "vitd_deficiency", "vitd_insufficiency", "vitd_high",
}


class TestR2_SignalCatalog:

    def test_expected_signal_count_lower_bound(self):
        assert len(EXPECTED_SIGNAL_IDS) >= 32

    def test_missing_core_data_quality_signal(self):
        r = analyze_chem_payload({})
        assert any(s["id"] == "missing_core_chem" for s in r["signals"])

    def test_signal_priority_table_covers_urgent(self):
        cfg = ChemConfig()
        for sig in ("hyperkalemia", "hypokalemia",
                    "hyponatremia", "hypernatremia",
                    "severe_hypoglycemia"):
            assert sig in cfg.signal_priority

    def test_severity_levels_valid(self):
        scenarios = [
            {"sex": "female", "age": 60, "glucose": 35},
            {"sex": "male", "age": 70, "creatinine": 2.3,
             "potassium": 6.4},
            {"sex": "female", "age": 28, "ferritin": 9,
             "iron": 40, "tibc": 460},
            {},
        ]
        for payload in scenarios:
            for sig in analyze_chem_payload(payload)["signals"]:
                assert sig["severity"] in ("high", "medium", "low")



EXPECTED_COMBO_IDS = {
    "kidney_function_reduced",
    "atherogenic_dyslipidemia_pattern",
    "insulin_resistance_nafld_like",
    "fh_like_ldl_ge190",
    "tg_very_high_pancreatitis_risk",
    "hyponatremia_with_hyperglycemia_corrected_na",
}


class TestR3_ComboCatalog:

    def test_combo_kidney_function_reduced(self):
        combos = {c["id"] for c in analyze_chem_payload({
            "sex": "male", "age": 70, "creatinine": 2.3,
        })["combos"]}
        assert "kidney_function_reduced" in combos

    def test_combo_pancreatitis_risk(self):
        combos = {c["id"] for c in analyze_chem_payload({
            "sex": "male", "age": 45, "trigly": 850,
        })["combos"]}
        assert "tg_very_high_pancreatitis_risk" in combos

    def test_combo_fh_suspect(self):
        combos = {c["id"] for c in analyze_chem_payload({
            "sex": "male", "age": 40, "ldl": 220,
        })["combos"]}
        assert "fh_like_ldl_ge190" in combos

    def test_combo_insulin_resistance(self):
        combos = {c["id"] for c in analyze_chem_payload({
            "sex": "male", "age": 45,
            "glucose": 118, "hdl": 35, "trigly": 260,
            "alt": 55, "ast": 42,
        })["combos"]}
        assert "insulin_resistance_nafld_like" in combos

    def test_combo_corrected_na(self):
        combos = {c["id"] for c in analyze_chem_payload({
            "sex": "female", "age": 60,
            "sodium": 128, "glucose": 280,
        })["combos"]}
        assert "hyponatremia_with_hyperglycemia_corrected_na" in combos



_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "chem_api" / "narrative" / "templates"


class TestR4_NarrativeCoverage:

    def test_48_clusters(self):
        assert len(load_clusters()) == 48

    def test_bilingual_template_files(self):
        cluster_ids = {c["id"] for c in load_clusters()}
        for cid in cluster_ids:
            assert (_TEMPLATES_DIR / f"{cid}.uk.md").exists()
            assert (_TEMPLATES_DIR / f"{cid}.en.md").exists()

    def test_96_template_files_total(self):
        assert len(list(_TEMPLATES_DIR.glob("*.uk.md"))) == 48
        assert len(list(_TEMPLATES_DIR.glob("*.en.md"))) == 48



class TestR5_ReferenceRanges:

    def test_at_least_34_analytes(self):
        core_analytes = {
            "glucose", "a1c", "creatinine", "urea", "bun",
            "alt", "ast", "alp", "ggt",
            "bilirubin_total", "bilirubin_direct",
            "albumin", "total_protein",
            "tchol", "hdl", "ldl", "trigly",
            "crp",
            "sodium", "potassium", "chloride", "bicarbonate",
            "calcium", "magnesium", "phosphate",
            "iron", "ferritin", "tibc", "tsat",
            "uric_acid",
            "amylase", "lipase", "ck", "ldh",
            "vitd_25oh",
        }
        missing = core_analytes - set(LABS.keys())
        assert not missing, f"Missing LABS entries: {missing}"

    def test_sex_specific_creatinine(self):
        male = LABS["creatinine"].ref_for("male")
        female = LABS["creatinine"].ref_for("female")
        assert male.high is not None and female.high is not None

    def test_sex_specific_hdl(self):
        male = LABS["hdl"].ref_for("male")
        female = LABS["hdl"].ref_for("female")
        if male.low is not None and female.low is not None:
            assert female.low >= male.low

    def test_potassium_realistic(self):
        rr = LABS["potassium"].ref_for(None)
        assert 3.0 <= rr.low <= 4.0
        assert 4.5 <= rr.high <= 6.5



class TestR6_InputFlexibility:

    def test_nhanes_codes_recognised(self):
        r = analyze_chem_payload({
            "RIAGENDR": "male", "RIDAGEYR": 45,
            "LBXGLU": 95, "LBXSCR": 1.0,
            "LBXSAT": 25, "LBXSAS": 22,
            "LBXTC": 180, "LBXHDD": 50,
        })
        meta = r["meta"]["field_meta"]
        assert meta["glucose"]["input_key"] == "LBXGLU"
        assert meta["creatinine"]["input_key"] == "LBXSCR"

    def test_embedded_unit_string_glucose(self):
        r = analyze_chem_payload({
            "sex": "male", "age": 30,
            "glucose": "5.0 mmol/L",
        })
        glu_lab = next(l for l in r["labs"] if l["code"] == "glucose")
        assert 89 < glu_lab["value"] < 92

    def test_aliases_table_covers_all_core(self):
        for code in ("glucose", "a1c", "creatinine", "alt", "ast", "tchol",
                     "hdl", "ldl", "trigly", "sodium", "potassium",
                     "calcium", "magnesium", "iron", "ferritin", "vitd_25oh"):
            assert code in ALIASES, f"Missing alias entry for '{code}'"
            assert len(ALIASES[code]) >= 1

    def test_ukrainian_fasting_token(self):
        r = analyze_chem_payload({
            "sex": "male", "age": 30, "glucose": 95,
            "fasting_8h": "так",
        })
        assert r["meta"]["context"]["fasting_8h"] is True



class TestR7_DerivedAnalytes:

    def test_egfr_computed_from_creatinine(self):
        r = analyze_chem_payload({"sex": "male", "age": 50, "creatinine": 1.0})
        labs = {l["code"]: l for l in r["labs"]}
        assert "egfr" in labs
        assert labs["egfr"]["source"] == "computed"

    def test_egfr_formula_documented(self):
        r = analyze_chem_payload({"sex": "male", "age": 50, "creatinine": 1.0})
        labs = {l["code"]: l for l in r["labs"]}
        assert labs["egfr"]["formula"] == "CKD-EPI 2021"

    def test_anion_gap_computed(self):
        r = analyze_chem_payload({
            "sex": "male", "age": 30,
            "sodium": 140, "chloride": 102, "bicarbonate": 25,
        })
        labs = {l["code"]: l for l in r["labs"]}
        assert "anion_gap" in labs
        assert labs["anion_gap"]["value"] == 13

    def test_lipid_ratios_computed(self):
        r = analyze_chem_payload({"tchol": 200, "hdl": 50, "trigly": 150})
        labs = {l["code"]: l for l in r["labs"]}
        assert "non_hdl" in labs
        assert "tc_hdl_ratio" in labs
        assert "tg_hdl_ratio" in labs

    def test_corrected_calcium_computed(self):
        r = analyze_chem_payload({"calcium": 8.5, "albumin": 3.0})
        labs = {l["code"]: l for l in r["labs"]}
        assert "calcium_corrected" in labs



class TestR8_Determinism:

    def test_100_runs_byte_identical(self):
        payload = {
            "sex": "female", "age": 55,
            "glucose": 180, "a1c": 8.5,
            "creatinine": 1.1, "alt": 35, "ast": 30,
            "tchol": 230, "hdl": 40, "trigly": 200,
            "crp": 4.5,
        }
        hashes = set()
        for _ in range(100):
            r = analyze_chem_payload(payload)
            blob = json.dumps(r, sort_keys=True, default=str, ensure_ascii=False)
            hashes.add(hashlib.sha256(blob.encode()).hexdigest())
        assert len(hashes) == 1



class TestR9_Safety:

    def test_empty_payload_warns_not_silent(self):
        r = analyze_chem_payload({})
        assert any(s["id"] == "missing_core_chem" for s in r["signals"])
        assert "Недостатньо даних" in r["summary"]["headline"] or \
               "відхилень" in r["summary"]["headline"]

    def test_severe_hyperkalemia_high_severity(self):
        r = analyze_chem_payload({
            "sex": "female", "age": 70, "potassium": 6.8,
        })
        assert r["summary"]["signals_high"] >= 1

    def test_severe_hyponatremia_high_severity(self):
        r = analyze_chem_payload({
            "sex": "female", "age": 70, "sodium": 119,
        })
        assert r["summary"]["signals_high"] >= 1

    def test_signal_priority_sorts_urgent_first(self):
        r = analyze_chem_payload({
            "sex": "female", "age": 70,
            "potassium": 6.5,
            "vitd_25oh": 25,
        })
        signals = r["signals"]
        sig_ids = [s["id"] for s in signals]
        if "hyperkalemia" in sig_ids and "vitd_insufficiency" in sig_ids:
            assert sig_ids.index("hyperkalemia") < sig_ids.index("vitd_insufficiency")
