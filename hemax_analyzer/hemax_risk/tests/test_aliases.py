from __future__ import annotations

import pytest

from risk_api.risk.inference import ALIASES


class TestAliasesTable:

    def test_contains_essential_cbc(self):
        for short, canonical in (
            ("wbc",  "wbc"),
            ("hgb",  "hb_gdl"),
            ("hb",   "hb_gdl"),
            ("plt",  "plt"),
            ("rbc",  "rbc"),
            ("mcv",  "mcv"),
        ):
            assert ALIASES.get(short) == canonical, (
                f"{short!r} should map to {canonical!r}"
            )

    def test_contains_essential_chem(self):
        for short, canonical in (
            ("glucose",    "glucose_fasting"),
            ("a1c",        "hba1c_pct"),
            ("hba1c",      "hba1c_pct"),
            ("creatinine", "creatinine_mgdl"),
            ("tchol",      "tchol_mgdl"),
            ("hdl",        "hdl_mgdl"),
            ("trigly",     "trigly_mgdl"),
            ("tg",         "trigly_mgdl"),
            ("crp",        "hs_crp"),
        ):
            assert ALIASES.get(short) == canonical, (
                f"{short!r} should map to {canonical!r}"
            )

    def test_contains_demographics(self):
        for short, canonical in (
            ("age",   "age_years"),
            ("sex",   "sex"),
            ("bmi",   "bmi"),
            ("waist", "waist_cm"),
            ("sbp",   "sbp"),
            ("dbp",   "dbp"),
            ("pulse", "pulse"),
        ):
            assert ALIASES.get(short) == canonical

    def test_alias_count_bounds(self):
        assert len(ALIASES) >= 50

    def test_no_self_loops_in_chain(self):
        for short, canonical in ALIASES.items():
            if canonical in ALIASES:
                assert ALIASES[canonical] == canonical, (
                    f"{short} → {canonical} → {ALIASES[canonical]} is a chain"
                )

    def test_hba1c_variants(self):
        for variant in ("a1c", "hba1c", "hba1c_pct"):
            assert ALIASES[variant] == "hba1c_pct"

    def test_triglyceride_short_alias(self):
        assert ALIASES["tg"] == "trigly_mgdl"

    def test_hgb_variants(self):
        for variant in ("hgb", "hb", "hemoglobin"):
            assert ALIASES[variant] == "hb_gdl"
