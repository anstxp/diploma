from __future__ import annotations

import pytest

from chem_api.chem.units import (
    parse_value_unit,
    to_gdl,
    to_mgdl_bilirubin,
    to_mgdl_bun,
    to_mgdl_calcium,
    to_mgdl_chol,
    to_mgdl_creatinine,
    to_mgdl_glucose,
    to_mgdl_magnesium,
    to_mgdl_phosphate,
    to_mgdl_trig,
    to_mgdl_uric,
    to_mgdl_urea,
    to_mgl_crp,
    to_mmolL,
    to_pct,
    to_ugdl_iron,
)



class TestParseValueUnit:

    def test_int(self):
        assert parse_value_unit(42) == (42.0, None)

    def test_float(self):
        assert parse_value_unit(3.14) == (3.14, None)

    def test_none(self):
        assert parse_value_unit(None) == (None, None)

    def test_empty_string(self):
        v, u = parse_value_unit("")
        assert v is None

    def test_numeric_string(self):
        v, u = parse_value_unit("12.5")
        assert v == 12.5
        assert u is None

    def test_embedded_unit(self):
        v, u = parse_value_unit("180 mg/dL")
        assert v == 180.0
        assert u and "mg/dl" in u.lower()

    def test_embedded_unit_mmol(self):
        v, u = parse_value_unit("5.5 mmol/L")
        assert v == 5.5
        assert u and "mmol" in u.lower()

    def test_comma_decimal_separator(self):
        v, u = parse_value_unit("5,5 mmol/L")
        assert v == 5.5

    def test_percent_unit(self):
        v, u = parse_value_unit("6.1%")
        assert v == 6.1
        assert u == "%"

    def test_garbage_string(self):
        v, u = parse_value_unit("foo bar")
        assert v is None



class TestToMgdlGlucose:

    def test_mgdl_passthrough(self):
        assert to_mgdl_glucose(90, "mg/dL") == 90.0
        assert to_mgdl_glucose(90, None) == 90.0

    def test_mmol_to_mgdl(self):
        result = to_mgdl_glucose(5.0, "mmol/L")
        assert 89 < result < 92

    def test_extreme_value(self):
        result = to_mgdl_glucose(14.0, "mmol/L")
        assert 250 < result < 256



class TestToMgdlChol:

    def test_mgdl_passthrough(self):
        assert to_mgdl_chol(180, "mg/dL") == 180.0

    def test_mmol_to_mgdl(self):
        result = to_mgdl_chol(4.66, "mmol/L")
        assert 178 < result < 182



class TestToMgdlTrig:

    def test_mgdl_passthrough(self):
        assert to_mgdl_trig(150, "mg/dL") == 150.0

    def test_mmol_to_mgdl(self):
        result = to_mgdl_trig(1.7, "mmol/L")
        assert 148 < result < 152



class TestToMgdlCreatinine:

    def test_mgdl_passthrough(self):
        assert to_mgdl_creatinine(1.0, "mg/dL") == 1.0

    def test_umol_to_mgdl(self):
        result = to_mgdl_creatinine(88.4, "µmol/L")
        assert 0.98 < result < 1.02


class TestToMgdlUrea:

    def test_mgdl_passthrough(self):
        assert to_mgdl_urea(40, "mg/dL") == 40.0

    def test_mmol_to_mgdl_urea_molecule(self):
        result = to_mgdl_urea(7.0, "mmol/L")
        assert 41 < result < 43


class TestToMgdlBun:

    def test_mgdl_passthrough(self):
        assert to_mgdl_bun(20, "mg/dL") == 20.0

    def test_mmol_to_mgdl_bun(self):
        result = to_mgdl_bun(7.0, "mmol/L")
        assert 18 < result < 21



class TestToMgdlBilirubin:

    def test_mgdl_passthrough(self):
        assert to_mgdl_bilirubin(1.0, "mg/dL") == 1.0

    def test_umol_to_mgdl(self):
        result = to_mgdl_bilirubin(17.1, "µmol/L")
        assert 0.99 < result < 1.01



class TestToMgdlUric:

    def test_mgdl_passthrough(self):
        assert to_mgdl_uric(5.5, "mg/dL") == 5.5

    def test_umol_to_mgdl(self):
        result = to_mgdl_uric(327.0, "µmol/L")
        assert 5.3 < result < 5.7

    def test_unknown_unit_passthrough(self):
        assert to_mgdl_uric(0.32, "mmol/L") == 0.32



class TestToGdl:

    def test_gdl_passthrough(self):
        assert to_gdl(4.4, "g/dL") == 4.4

    def test_gl_to_gdl(self):
        assert to_gdl(44, "g/L") == 4.4



class TestToMglCrp:

    def test_mgl_passthrough(self):
        assert to_mgl_crp(1.2, "mg/L") == 1.2

    def test_mgdl_to_mgl(self):
        result = to_mgl_crp(0.12, "mg/dL")
        assert 1.1 < result < 1.3



class TestToMmolL:

    def test_mmol_passthrough(self):
        assert to_mmolL(140, "mmol/L") == 140.0
        assert to_mmolL(140, None) == 140.0

    def test_meq_l_passthrough(self):
        assert to_mmolL(140, "mEq/L") == 140.0



class TestMineralConverters:

    def test_calcium_mgdl_passthrough(self):
        assert to_mgdl_calcium(9.4, "mg/dL") == 9.4

    def test_calcium_mmol_to_mgdl(self):
        result = to_mgdl_calcium(2.35, "mmol/L")
        assert 9.3 < result < 9.5

    def test_magnesium_mgdl_passthrough(self):
        assert to_mgdl_magnesium(2.0, "mg/dL") == 2.0

    def test_phosphate_mgdl_passthrough(self):
        assert to_mgdl_phosphate(3.4, "mg/dL") == 3.4



class TestToUgdlIron:

    def test_ugdl_passthrough(self):
        assert to_ugdl_iron(95, "µg/dL") == 95.0
        assert to_ugdl_iron(95, "ug/dL") == 95.0

    def test_umol_to_ugdl(self):
        result = to_ugdl_iron(17.0, "µmol/L")
        assert 92 < result < 100



class TestToPct:

    def test_pct_passthrough(self):
        assert to_pct(30.0, "%") == 30.0
        assert to_pct(30.0, None) == 30.0
