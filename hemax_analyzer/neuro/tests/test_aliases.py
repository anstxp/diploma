from __future__ import annotations

import pytest

from neuro_api.neuro.inference import ALIASES


class TestAliasesTable:

    def test_essential_cbc(self):
        for short, canonical in (
            ("wbc",  "wbc"),
            ("hgb",  "hb_gdl"),
            ("hb",   "hb_gdl"),
            ("plt",  "plt"),
            ("rbc",  "rbc"),
        ):
            assert ALIASES.get(short) == canonical

    def test_essential_chem(self):
        for short, canonical in (
            ("glucose",    "glucose_fasting"),
            ("a1c",        "hba1c_pct"),
            ("creatinine", "creatinine_mgdl"),
            ("tchol",      "tchol_mgdl"),
            ("hdl",        "hdl_mgdl"),
            ("crp",        "hs_crp"),
        ):
            assert ALIASES.get(short) == canonical

    def test_demographics(self):
        for short, canonical in (
            ("age",   "age_years"),
            ("sex",   "sex"),
            ("bmi",   "bmi"),
            ("sbp",   "sbp"),
            ("dbp",   "dbp"),
        ):
            assert ALIASES.get(short) == canonical

    def test_v2_ses_features(self):
        assert ALIASES.get("income_ratio") == "income_ratio"
        assert ALIASES.get("pir") == "income_ratio"
        assert ALIASES.get("poverty_income_ratio") == "income_ratio"
        assert ALIASES.get("education") == "edu_level"

    def test_v2_composite_features(self):
        assert ALIASES.get("metsyn_count") == "metsyn_criteria_count"
        assert ALIASES.get("fib_4") == "fib4"
        assert ALIASES.get("non_hdl") == "non_hdl_mgdl"

    def test_v2_homa_ir(self):
        assert "homa_ir" in ALIASES or any(
            v == "homa_ir" for v in ALIASES.values()
        )

    def test_v2_iron_chem(self):
        assert ALIASES.get("serum_iron") == "iron_chem_ugdl"
        assert ALIASES.get("iron") == "iron_chem_ugdl"

    def test_alias_count_lower_bound(self):
        assert len(ALIASES) >= 60

    def test_no_two_step_chains(self):
        for short, canonical in ALIASES.items():
            if canonical in ALIASES:
                assert ALIASES[canonical] == canonical, (
                    f"{short} → {canonical} → {ALIASES[canonical]} is a chain"
                )
