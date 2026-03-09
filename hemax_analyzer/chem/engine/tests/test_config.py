from __future__ import annotations

import pytest

from chem_api.chem.config import ChemConfig, SeverityBand


class TestSeverityBand:

    def test_frozen(self):
        b = SeverityBand(mild=1.0, moderate=2.0, severe=3.0)
        with pytest.raises(Exception):
            b.mild = 99.0  # type: ignore[misc]

    def test_creation(self):
        b = SeverityBand(mild=110, moderate=126, severe=250)
        assert b.mild == 110
        assert b.moderate == 126
        assert b.severe == 250


class TestChemConfig:

    def test_glucose_thresholds(self):
        cfg = ChemConfig()
        assert cfg.glucose_high.mild == 110
        assert cfg.glucose_high.moderate == 126
        assert cfg.glucose_high.severe == 250

    def test_glucose_low_thresholds(self):
        cfg = ChemConfig()
        assert cfg.glucose_low.mild == 70
        assert cfg.glucose_low.moderate == 54
        assert cfg.glucose_low.severe == 40

    def test_potassium_thresholds(self):
        cfg = ChemConfig()
        assert cfg.potassium_high.mild == 5.5
        assert cfg.potassium_high.severe == 6.5

    def test_sodium_thresholds(self):
        cfg = ChemConfig()
        assert cfg.sodium_low.severe == 120
        assert cfg.sodium_high.severe == 160

    def test_trigly_thresholds(self):
        cfg = ChemConfig()
        assert cfg.trigly_high.mild == 150
        assert cfg.trigly_high.severe == 500

    def test_lab_order_is_tuple(self):
        cfg = ChemConfig()
        assert isinstance(cfg.lab_order, tuple)
        assert cfg.lab_order[0] == "glucose"
        assert "vitd_25oh" in cfg.lab_order

    def test_lab_order_includes_derived(self):
        cfg = ChemConfig()
        for derived in ("egfr", "anion_gap", "non_hdl",
                        "tc_hdl_ratio", "calcium_corrected"):
            assert derived in cfg.lab_order, f"{derived} missing from lab_order"

    def test_signal_priority_table(self):
        cfg = ChemConfig()
        for urgent in ("hyperkalemia", "hypokalemia",
                       "hyponatremia", "hypernatremia",
                       "severe_hypoglycemia"):
            assert cfg.signal_priority.get(urgent, 0) >= 110, (
                f"{urgent} should be high-priority"
            )

    def test_signal_priority_returns_default_for_unknown(self):
        cfg = ChemConfig()
        assert cfg.signal_priority.get("nonexistent_signal_id", 0) == 0
