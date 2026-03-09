from __future__ import annotations

import pytest

from chem_api.chem.analyze import analyze_chem_payload


def _lab(result: dict, code: str) -> dict | None:
    for l in result["labs"]:
        if l["code"] == code:
            return l
    return None


def _derived_value(result: dict, code: str) -> float | None:
    lab = _lab(result, code)
    return lab["value"] if lab else None



class TestEGFR:

    def test_egfr_input_preserved(self):
        r = analyze_chem_payload({"sex": "male", "age": 60, "egfr": 75})
        lab = _lab(r, "egfr")
        assert lab is not None
        assert lab["value"] == 75
        assert lab["source"] == "input"

    def test_egfr_input_string_with_unit(self):
        r = analyze_chem_payload({
            "sex": "male", "age": 60,
            "egfr": "38 mL/min/1.73m²",
        })
        lab = _lab(r, "egfr")
        assert lab is not None
        assert lab["value"] == 38

    def test_egfr_computed_from_creatinine(self):
        r = analyze_chem_payload({
            "sex": "male", "age": 50,
            "creatinine": 1.0,
        })
        lab = _lab(r, "egfr")
        assert lab is not None
        assert lab["source"] == "computed"
        assert 85 < lab["value"] < 105

    def test_egfr_low_in_ckd(self):
        r = analyze_chem_payload({
            "sex": "male", "age": 70,
            "creatinine": 2.3,
        })
        lab = _lab(r, "egfr")
        assert lab is not None
        assert 20 < lab["value"] < 40

    def test_egfr_female_factor(self):
        male = analyze_chem_payload({"sex": "male", "age": 50, "creatinine": 1.0})
        female = analyze_chem_payload({"sex": "female", "age": 50, "creatinine": 1.0})
        assert _derived_value(male, "egfr") > 50
        assert _derived_value(female, "egfr") > 50

    def test_egfr_not_computed_without_age(self):
        r = analyze_chem_payload({"sex": "male", "creatinine": 1.0})
        assert _lab(r, "egfr") is None

    def test_egfr_not_computed_without_sex(self):
        r = analyze_chem_payload({"age": 50, "creatinine": 1.0})
        assert _lab(r, "egfr") is None



class TestLipidDerived:

    def test_non_hdl_computed(self):
        r = analyze_chem_payload({"tchol": 200, "hdl": 50})
        assert _derived_value(r, "non_hdl") == 150

    def test_non_hdl_skipped_when_inputs_missing(self):
        r = analyze_chem_payload({"tchol": 200})
        assert _lab(r, "non_hdl") is None

    def test_friedewald_ldl_computed(self):
        r = analyze_chem_payload({"tchol": 200, "hdl": 50, "trigly": 150})
        assert _derived_value(r, "ldl") == 120

    def test_friedewald_skipped_high_tg(self):
        r = analyze_chem_payload({"tchol": 200, "hdl": 50, "trigly": 500})
        ldl_lab = _lab(r, "ldl")
        assert ldl_lab is None

    def test_ldl_input_not_overwritten(self):
        r = analyze_chem_payload({
            "tchol": 200, "hdl": 50, "trigly": 100,
            "ldl": 130,
        })
        assert _derived_value(r, "ldl") == 130

    def test_tc_hdl_ratio(self):
        r = analyze_chem_payload({"tchol": 200, "hdl": 50})
        assert _derived_value(r, "tc_hdl_ratio") == 4.0

    def test_tg_hdl_ratio(self):
        r = analyze_chem_payload({"trigly": 150, "hdl": 50})
        assert _derived_value(r, "tg_hdl_ratio") == 3.0

    def test_ratios_skipped_when_hdl_zero(self):
        r = analyze_chem_payload({"tchol": 200, "hdl": 0})
        assert _lab(r, "tc_hdl_ratio") is None



class TestAstAltRatio:

    def test_ast_alt_ratio(self):
        r = analyze_chem_payload({"ast": 40, "alt": 20})
        assert _derived_value(r, "ast_alt_ratio") == 2.0

    def test_skipped_when_alt_zero(self):
        r = analyze_chem_payload({"ast": 40, "alt": 0})
        assert _lab(r, "ast_alt_ratio") is None



class TestAnionGap:

    def test_anion_gap_normal(self):
        r = analyze_chem_payload({
            "sodium": 140, "chloride": 102, "bicarbonate": 25,
        })
        assert _derived_value(r, "anion_gap") == 13

    def test_anion_gap_skipped_partial(self):
        r = analyze_chem_payload({"sodium": 140, "chloride": 102})
        assert _lab(r, "anion_gap") is None



class TestCorrectedCalcium:

    def test_correction_for_low_albumin(self):
        r = analyze_chem_payload({"calcium": 8.5, "albumin": 3.0})
        assert _derived_value(r, "calcium_corrected") == 9.3

    def test_no_correction_normal_albumin(self):
        r = analyze_chem_payload({"calcium": 9.4, "albumin": 4.0})
        assert _derived_value(r, "calcium_corrected") == 9.4



class TestGlobulin:

    def test_globulin_computed(self):
        r = analyze_chem_payload({"total_protein": 7.2, "albumin": 4.4})
        assert _derived_value(r, "globulin") == pytest.approx(2.8)

    def test_ag_ratio_computed(self):
        r = analyze_chem_payload({"total_protein": 7.2, "albumin": 4.4})
        ratio = _derived_value(r, "ag_ratio")
        assert 1.5 < ratio < 1.65



class TestTSAT:

    def test_tsat_computed_from_iron_tibc(self):
        r = analyze_chem_payload({"iron": 100, "tibc": 400})
        assert _derived_value(r, "tsat") == 25

    def test_tsat_input_not_overwritten(self):
        r = analyze_chem_payload({"iron": 100, "tibc": 400, "tsat": 35})
        assert _derived_value(r, "tsat") == 35

    def test_tsat_skipped_when_tibc_zero(self):
        r = analyze_chem_payload({"iron": 100, "tibc": 0})
        assert _lab(r, "tsat") is None
