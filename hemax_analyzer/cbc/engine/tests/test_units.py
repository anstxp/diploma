from __future__ import annotations

import math

import pytest

from cbc_api.units import (
    parse_value_unit,
    smart_round,
    to_fl,
    to_gdl_hb,
    to_gdl_mchc,
    to_kul,
    to_mul,
    to_pct,
    to_pg,
)



class TestParseValueUnit:

    def test_int_returns_float_no_unit(self):
        v, u = parse_value_unit(42)
        assert v == 42.0
        assert u is None

    def test_float_returns_unchanged(self):
        v, u = parse_value_unit(3.14)
        assert v == 3.14
        assert u is None

    def test_none_input(self):
        assert parse_value_unit(None) == (None, None)

    def test_empty_string(self):
        assert parse_value_unit("") == (None, None)

    def test_whitespace_only(self):
        assert parse_value_unit("   ") == (None, None)

    def test_nan_input(self):
        v, u = parse_value_unit(float("nan"))
        assert v is None
        assert u is None

    def test_pure_numeric_string(self):
        v, u = parse_value_unit("12.5")
        assert v == 12.5
        assert u is None

    def test_negative_numeric(self):
        v, u = parse_value_unit("-3.2")
        assert v == -3.2

    def test_embedded_unit_kul(self):
        v, u = parse_value_unit("6.5 10^3/uL")
        assert v == 6.5
        assert u is not None and "10^3" in u

    def test_embedded_unit_gdl(self):
        v, u = parse_value_unit("14.5 g/dL")
        assert v == 14.5
        assert u == "g/dL"

    def test_garbage_string(self):
        v, u = parse_value_unit("not a number")
        assert v is None

    def test_string_with_x_multiplier(self):
        v, u = parse_value_unit("520 x10^3/µL")
        assert v == 520.0
        assert u is not None



class TestToKul:

    @pytest.mark.parametrize("unit", [
        None, "10^3/uL", "10^3/µL", "k/uL", "K/µL", "x10^3/uL"
    ])
    def test_already_kul(self, unit):
        assert to_kul(6.5, unit) == 6.5

    def test_10e9_per_L_numerically_equal(self):
        assert to_kul(6.5, "10^9/L") == 6.5

    def test_per_uL_divides_by_1000(self):
        assert to_kul(6500.0, "/µL") == 6.5

    def test_per_L_divides_by_1e9(self):
        assert to_kul(6.5e9, "/L") == pytest.approx(6.5)

    def test_unknown_unit_keeps_value(self):
        assert to_kul(7.0, "weird-unit") == 7.0



class TestToMul:

    @pytest.mark.parametrize("unit", [None, "10^6/uL", "10^6/µL", "M/uL"])
    def test_already_mul(self, unit):
        assert to_mul(5.0, unit) == 5.0

    def test_10e12_per_L_numerically_equal(self):
        assert to_mul(5.0, "10^12/L") == 5.0

    def test_per_uL_divides_by_1e6(self):
        assert to_mul(4_500_000.0, "/µL") == 4.5

    def test_per_L_divides_by_1e12(self):
        assert to_mul(4.5e12, "/L") == pytest.approx(4.5)



class TestToGdlHb:

    def test_already_gdl(self):
        assert to_gdl_hb(14.5, "g/dL") == 14.5

    def test_g_per_L_divides_by_10(self):
        assert to_gdl_hb(145.0, "g/L") == 14.5

    def test_no_unit_assumes_gdl(self):
        assert to_gdl_hb(14.5, None) == 14.5

    def test_alias_gdl(self):
        assert to_gdl_hb(14.5, "gdL") == 14.5



class TestSimpleConverters:

    def test_to_pct_passthrough(self):
        assert to_pct(42.0, "%") == 42.0
        assert to_pct(42.0, None) == 42.0

    def test_to_fl_passthrough(self):
        assert to_fl(88.0, "fL") == 88.0

    def test_to_pg_passthrough(self):
        assert to_pg(29.0, "pg") == 29.0

    def test_to_gdl_mchc_passthrough(self):
        assert to_gdl_mchc(33.0, "g/dL") == 33.0

    def test_to_gdl_mchc_g_per_L(self):
        assert to_gdl_mchc(330.0, "g/L") == 33.0



class TestSmartRound:

    def test_none_passthrough(self):
        assert smart_round(None) is None

    def test_default_digits_3(self):
        assert smart_round(3.14159) == 3.142

    def test_explicit_digits(self):
        assert smart_round(3.14159, 1) == 3.1
        assert smart_round(3.14159, 0) == 3.0

    def test_handles_int(self):
        assert smart_round(5, 2) == 5.0

    def test_handles_invalid(self):
        assert smart_round("nope") is None



@pytest.mark.parametrize("val", [1.0, 6.5, 12.3, 250.0])
def test_to_kul_default_round_trip(val):
    out = to_kul(val, None)
    assert out == val
    assert not math.isnan(out)
