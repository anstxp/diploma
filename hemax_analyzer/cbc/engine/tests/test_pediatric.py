from __future__ import annotations

import pytest

from cbc_api.knowledge import RefRange
from cbc_api.pediatric_refs import (
    PED_BANDS,
    RBC_INDICES_BY_YEAR,
    get_ped_band,
    get_pediatric_abs_ref,
    get_pediatric_ref,
)



class TestPedBands:

    def test_bands_present(self):
        assert len(PED_BANDS) > 0

    def test_first_band_starts_at_0(self):
        first = PED_BANDS[0]
        assert first.age_min == 0.0

    def test_bands_cover_0_to_18_continuously(self):
        coverage = sorted(PED_BANDS, key=lambda b: b.age_min)
        for age in (0.0, 1.0, 5.0, 10.0, 15.0):
            assert any(b.matches(age, "male") or b.matches(age, "female")
                       for b in PED_BANDS), f"No band covers age {age}"



class TestGetPedBand:

    def test_newborn_returns_band(self):
        b = get_ped_band(0.05, None)
        assert b is not None
        assert "hgb" in b.labs

    def test_10_year_old(self):
        b = get_ped_band(10.0, "male")
        assert b is not None

    def test_18_year_old_returns_none(self):
        assert get_ped_band(18.0, "male") is None

    def test_25_year_old_returns_none(self):
        assert get_ped_band(25.0, "female") is None

    def test_negative_age_returns_none(self):
        assert get_ped_band(-1.0, None) is None

    def test_none_age_returns_none(self):
        assert get_ped_band(None, "male") is None



class TestGetPediatricRef:

    def test_newborn_hgb_is_high(self):
        rr = get_pediatric_ref("hgb", 0.05, None)
        assert rr is not None
        assert rr.low and rr.low >= 13.0

    def test_10_year_old_hgb(self):
        rr = get_pediatric_ref("hgb", 10.0, None)
        assert rr is not None
        assert rr.low is not None and rr.high is not None

    def test_unknown_code_returns_none(self):
        rr = get_pediatric_ref("magicunknown_lab", 5.0, None)
        assert rr is None

    def test_adult_age_returns_none(self):
        rr = get_pediatric_ref("hgb", 30.0, "male")
        assert rr is None

    @pytest.mark.parametrize("year", list(RBC_INDICES_BY_YEAR.keys()))
    def test_year_specific_mcv_indices_for_children(self, year):
        rr = get_pediatric_ref("mcv", float(year), None)
        assert rr is not None
        assert rr.low is not None and rr.high is not None



class TestGetPediatricAbsRef:

    def test_newborn_anc(self):
        rr = get_pediatric_abs_ref("anc", 0.05, None)
        assert rr is not None
        assert rr.low is not None

    def test_unknown_code(self):
        rr = get_pediatric_abs_ref("xyz", 5.0, None)
        assert rr is None

    def test_adult_returns_none(self):
        rr = get_pediatric_abs_ref("anc", 25.0, "male")
        assert rr is None
