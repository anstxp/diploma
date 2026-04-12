from __future__ import annotations

import pytest

from neuro_api.neuro.units import normalize_lab_to_us_units, parse_lab_value


class TestParseLabValue:

    def test_int(self):
        assert parse_lab_value(42) == 42.0

    def test_float(self):
        assert parse_lab_value(3.14) == 3.14

    def test_none(self):
        assert parse_lab_value(None) is None

    def test_bool_rejected(self):
        assert parse_lab_value(True) is None
        assert parse_lab_value(False) is None

    def test_pure_numeric_string(self):
        assert parse_lab_value("13.5") == 13.5

    def test_numeric_with_unit(self):
        assert parse_lab_value("8.8 mmol/L") == 8.8

    def test_comma_decimal_separator(self):
        assert parse_lab_value("5,5%") == 5.5

    def test_garbage_string(self):
        assert parse_lab_value("hello world") is None

    def test_empty_string(self):
        assert parse_lab_value("") is None


class TestGlucoseConversion:

    def test_mgdl_passthrough(self):
        assert normalize_lab_to_us_units(90, "glucose") == 90.0

    def test_mmol_to_mgdl_explicit(self):
        result = normalize_lab_to_us_units("5.0 mmol/L", "glucose")
        assert 89.0 < result < 91.0

    def test_heuristic_string_low_values_treated_as_mmol(self):
        result = normalize_lab_to_us_units("5.0", "glucose")
        assert 89.0 < result < 91.0


class TestCholesterolConversion:

    def test_mgdl_passthrough(self):
        assert normalize_lab_to_us_units(200, "tchol") == 200.0

    def test_mmol_to_mgdl(self):
        result = normalize_lab_to_us_units("5.0 mmol/L", "tchol")
        assert 192.0 < result < 195.0

    def test_hdl_same_factor(self):
        result = normalize_lab_to_us_units("1.5 mmol/L", "hdl")
        assert 57.0 < result < 59.0


class TestCreatinineConversion:

    def test_mgdl_passthrough(self):
        assert normalize_lab_to_us_units(1.0, "creatinine") == 1.0

    def test_umol_to_mgdl(self):
        result = normalize_lab_to_us_units("88 µmol/L", "creatinine")
        assert 0.99 < result < 1.01


class TestUreaVsBun:

    def test_urea_factor(self):
        result = normalize_lab_to_us_units("7 mmol/L", "urea")
        assert 41.0 < result < 43.0

    def test_bun_factor(self):
        result = normalize_lab_to_us_units("7 mmol/L", "bun")
        assert 18.0 < result < 21.0


class TestHemoglobinConversion:

    def test_gdl_passthrough(self):
        assert normalize_lab_to_us_units(14.5, "hgb") == 14.5

    def test_gl_to_gdl(self):
        result = normalize_lab_to_us_units("145 g/L", "hgb")
        assert result == 14.5


class TestHbA1cConversion:

    def test_no_conversion(self):
        assert normalize_lab_to_us_units(6.5, "hba1c") == 6.5


class TestCRPConversion:

    def test_mgl_passthrough(self):
        assert normalize_lab_to_us_units(5.0, "crp") == 5.0


class TestElectrolytes:

    @pytest.mark.parametrize("name", ["sodium", "potassium", "chloride", "bicarbonate"])
    def test_mmol_passthrough(self, name):
        assert normalize_lab_to_us_units(140, name) == 140.0


class TestEdgeCases:

    def test_none_input(self):
        assert normalize_lab_to_us_units(None, "glucose") is None

    def test_bool_input(self):
        assert normalize_lab_to_us_units(True, "glucose") is None

    def test_garbage_string(self):
        assert normalize_lab_to_us_units("not a number", "glucose") is None

    def test_unknown_lab_passes_through(self):
        assert normalize_lab_to_us_units(42, "unknown_xyz") == 42.0
