from __future__ import annotations

import pytest

from chem_api.chem.knowledge import LABS
from chem_api.chem.spec import LabDef, RefRange


EXPECTED_LAB_CODES = {
    "glucose", "a1c",
    "creatinine", "urea", "bun", "egfr",
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


class TestLabsCatalog:

    def test_all_expected_labs_present(self):
        missing = EXPECTED_LAB_CODES - set(LABS.keys())
        assert not missing, f"Missing lab defs: {missing}"

    def test_lab_count(self):
        assert len(LABS) >= 34

    @pytest.mark.parametrize("code", sorted(EXPECTED_LAB_CODES))
    def test_lab_has_required_fields(self, code):
        lab = LABS[code]
        assert isinstance(lab, LabDef)
        assert lab.code == code
        assert lab.name, f"{code} has empty name"
        assert lab.unit, f"{code} has empty unit"

    @pytest.mark.parametrize("code", sorted(EXPECTED_LAB_CODES))
    def test_lab_has_some_ref_range(self, code):
        lab = LABS[code]
        has_any = (lab.ref_any.low is not None or lab.ref_any.high is not None)
        has_m = (lab.ref_male.low is not None or lab.ref_male.high is not None)
        has_f = (lab.ref_female.low is not None or lab.ref_female.high is not None)
        assert has_any or has_m or has_f, f"{code} has no reference range"

    def test_ref_for_male(self):
        lab = LABS["hdl"]
        rr = lab.ref_for("male")
        assert isinstance(rr, RefRange)

    def test_ref_for_female(self):
        lab = LABS["hdl"]
        rr = lab.ref_for("female")
        assert isinstance(rr, RefRange)

    def test_ref_for_unknown_sex_falls_back(self):
        lab = LABS["glucose"]
        rr = lab.ref_for(None)
        assert isinstance(rr, RefRange)

    def test_creatinine_is_sex_specific(self):
        lab = LABS["creatinine"]
        male = lab.ref_for("male")
        female = lab.ref_for("female")
        if (male.high is not None) and (female.high is not None):
            assert male.high != female.high or male.low != female.low

    def test_hdl_is_sex_specific(self):
        lab = LABS["hdl"]
        male = lab.ref_for("male")
        female = lab.ref_for("female")
        if (male.low is not None) and (female.low is not None):
            assert female.low >= male.low

    def test_potassium_range_realistic(self):
        rr = LABS["potassium"].ref_for(None)
        if rr.low is not None and rr.high is not None:
            assert 2.0 <= rr.low <= 4.0
            assert 4.5 <= rr.high <= 6.5

    def test_glucose_range_realistic(self):
        rr = LABS["glucose"].ref_for(None)
        if rr.low is not None and rr.high is not None:
            assert 50 <= rr.low <= 80
            assert 95 <= rr.high <= 130
