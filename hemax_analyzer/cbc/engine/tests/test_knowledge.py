from __future__ import annotations

import pytest

from cbc_api.knowledge import ABS_REFS, LABS, RefRange



class TestRefRange:

    def test_frozen(self):
        rr = RefRange(low=1.0, high=2.0)
        with pytest.raises(Exception):
            rr.low = 99.0  # type: ignore[misc]

    def test_default_is_none(self):
        rr = RefRange()
        assert rr.low is None and rr.high is None

    def test_partial(self):
        rr = RefRange(low=1.0)
        assert rr.low == 1.0
        assert rr.high is None



EXPECTED_LAB_CODES = {
    "wbc", "neut_pct", "lymph_pct", "mono_pct", "eos_pct", "baso_pct",
    "rbc", "hgb", "hct", "mcv", "mch", "mchc", "rdw",
    "plt", "mpv", "esr",
}


class TestLABS:

    def test_all_expected_labs_present(self):
        assert EXPECTED_LAB_CODES <= set(LABS.keys()), (
            f"Missing lab definitions: {EXPECTED_LAB_CODES - set(LABS.keys())}"
        )

    def test_lab_count(self):
        assert len(LABS) == 16

    @pytest.mark.parametrize("code", sorted(EXPECTED_LAB_CODES))
    def test_lab_has_required_fields(self, code):
        lab = LABS[code]
        assert lab.code == code, "Code field must match dict key"
        assert lab.name_uk, "Ukrainian name must not be empty"
        assert lab.unit, "Unit must not be empty"
        assert lab.what, "`what` description must not be empty"
        assert isinstance(lab.low_means, list)
        assert isinstance(lab.high_means, list)
        assert isinstance(lab.tips, list)
        assert isinstance(lab.caveats, list)

    @pytest.mark.parametrize("code", sorted(EXPECTED_LAB_CODES))
    def test_lab_has_sane_ref_ranges(self, code):
        lab = LABS[code]
        assert lab.ref_female is not None or lab.ref_male is not None

    def test_sex_specific_hgb(self):
        hgb = LABS["hgb"]
        assert hgb.ref_female != hgb.ref_male
        assert (hgb.ref_male.low or 0) >= (hgb.ref_female.low or 0)

    def test_sex_specific_rbc(self):
        rbc = LABS["rbc"]
        assert rbc.ref_male != rbc.ref_female
        assert (rbc.ref_male.low or 0) >= (rbc.ref_female.low or 0)

    def test_esr_specific(self):
        esr = LABS["esr"]
        assert esr.ref_female.high is not None or esr.ref_male.high is not None



class TestABSRefs:

    def test_all_absolutes_present(self):
        expected = {"anc", "alc", "amc", "aec", "abc"}
        assert set(ABS_REFS.keys()) == expected

    @pytest.mark.parametrize("code", ["anc", "alc", "amc", "aec", "abc"])
    def test_abs_refs_have_bounds(self, code):
        rr = ABS_REFS[code]
        assert rr.low is not None
        assert rr.high is not None
        assert rr.low <= rr.high

    def test_anc_is_positive(self):
        assert ABS_REFS["anc"].low >= 0
