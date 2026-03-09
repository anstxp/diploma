from __future__ import annotations

import pytest

from chem_api.chem.parse import Parsed, parse_number_and_unit


class TestParseNumberAndUnit:

    def test_int_input(self):
        p = parse_number_and_unit(42)
        assert p.value == 42.0
        assert p.unit is None
        assert p.raw == 42

    def test_float_input(self):
        p = parse_number_and_unit(3.14)
        assert p.value == 3.14
        assert p.unit is None

    def test_none_input(self):
        p = parse_number_and_unit(None)
        assert p.value is None
        assert p.unit is None

    def test_pure_numeric_string(self):
        p = parse_number_and_unit("42")
        assert p.value == 42.0
        assert p.unit is None

    def test_embedded_unit(self):
        p = parse_number_and_unit("180 mg/dL")
        assert p.value == 180.0
        assert p.unit and "mg/dL" in p.unit

    def test_micro_symbol_normalized(self):
        p = parse_number_and_unit("95 μg/dL")
        assert p.value == 95.0
        assert "µ" in (p.unit or "")

    def test_umol_normalized(self):
        p = parse_number_and_unit("88 umol/L")
        assert p.value == 88.0
        assert "µmol" in (p.unit or "")

    def test_per_normalized_to_slash(self):
        p = parse_number_and_unit("180 mg per dL")
        assert "/" in (p.unit or "")

    def test_negative_value(self):
        p = parse_number_and_unit("-1.5")
        assert p.value == -1.5

    def test_garbage_string(self):
        p = parse_number_and_unit("not a number")
        assert p.value is None
        assert p.unit is None

    def test_empty_string(self):
        p = parse_number_and_unit("")
        assert p.value is None

    def test_whitespace_only(self):
        p = parse_number_and_unit("   ")
        assert p.value is None
