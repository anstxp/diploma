from __future__ import annotations

import pytest

from cbc_api.config import CBCConfig, SeverityBand, _parse_severity_band, load_config



class TestSeverityBand:

    def test_frozen(self):
        band = SeverityBand(mild=10.0, moderate=20.0, severe=30.0)
        with pytest.raises(Exception):
            band.mild = 99.0  # type: ignore[misc]

    def test_creation(self):
        b = SeverityBand(mild=1.0, moderate=2.0, severe=3.0)
        assert b.mild == 1.0 and b.moderate == 2.0 and b.severe == 3.0



class TestCBCConfigDefaults:

    def test_default_thresholds_present(self):
        cfg = CBCConfig()
        assert cfg.wbc_high.mild == 11.1
        assert cfg.wbc_low.severe == 1.0
        assert cfg.plt_low.mild == 150.0
        assert cfg.plt_high.severe == 1000.0
        assert cfg.esr_high.mild == 20.0
        assert cfg.hgb_low_female.mild == 12.0
        assert cfg.hgb_low_male.mild == 13.0

    def test_mcv_cutoffs(self):
        cfg = CBCConfig()
        assert cfg.mcv_micro == 80.0
        assert cfg.mcv_macro == 100.0

    def test_lab_order_is_tuple(self):
        cfg = CBCConfig()
        assert isinstance(cfg.lab_order, tuple)
        assert cfg.lab_order[0] == "wbc"
        assert "plt" in cfg.lab_order

    def test_signal_priority_contains_known_signals(self):
        cfg = CBCConfig()
        for sig in ("pancytopenia_pattern", "neutropenia", "thrombocytopenia",
                    "anemia_possible", "leukocytosis", "missing_core_cbc"):
            assert sig in cfg.signal_priority

    def test_pancytopenia_is_highest_priority(self):
        cfg = CBCConfig()
        pri = cfg.signal_priority
        assert pri["pancytopenia_pattern"] >= max(
            pri.get("anemia_possible", 0),
            pri.get("leukocytosis", 0),
            pri.get("thrombocytosis", 0),
        )

    def test_missing_core_lowest_priority(self):
        cfg = CBCConfig()
        assert cfg.signal_priority["missing_core_cbc"] < 0



class TestParseSeverityBand:

    def test_returns_default_on_non_dict(self):
        default = SeverityBand(1.0, 2.0, 3.0)
        for bad in (None, "string", 42, [1, 2, 3]):
            assert _parse_severity_band(bad, default) == default

    def test_partial_override_keeps_defaults(self):
        default = SeverityBand(1.0, 2.0, 3.0)
        out = _parse_severity_band({"mild": 10.0}, default)
        assert out.mild == 10.0
        assert out.moderate == 2.0
        assert out.severe == 3.0

    def test_full_override(self):
        default = SeverityBand(1.0, 2.0, 3.0)
        out = _parse_severity_band(
            {"mild": 10.0, "moderate": 20.0, "severe": 30.0}, default
        )
        assert out == SeverityBand(10.0, 20.0, 30.0)

    def test_coerces_string_numbers(self):
        default = SeverityBand(1.0, 2.0, 3.0)
        out = _parse_severity_band({"mild": "10.5"}, default)
        assert out.mild == 10.5

    def test_invalid_value_falls_back(self):
        default = SeverityBand(1.0, 2.0, 3.0)
        out = _parse_severity_band({"mild": "not a number"}, default)
        assert out.mild == 1.0



class TestLoadConfig:

    def test_empty_payload_returns_defaults(self):
        cfg = load_config({})
        assert cfg.wbc_high.mild == CBCConfig().wbc_high.mild

    def test_none_returns_defaults(self):
        cfg = load_config(None)
        assert isinstance(cfg, CBCConfig)

    def test_override_severity_threshold(self):
        cfg = load_config({
            "config": {
                "severity_thresholds": {
                    "wbc_high": {"mild": 12.0, "moderate": 16.0, "severe": 30.0},
                },
            }
        })
        assert cfg.wbc_high.mild == 12.0
        assert cfg.wbc_high.moderate == 16.0
        assert cfg.wbc_high.severe == 30.0

    def test_override_mcv_cutoff(self):
        cfg = load_config({
            "config": {"severity_thresholds": {"mcv_micro": 75.0}}
        })
        assert cfg.mcv_micro == 75.0

    def test_override_lab_order(self):
        new_order = ["hgb", "wbc", "plt"]
        cfg = load_config({"config": {"lab_order": new_order}})
        assert cfg.lab_order == tuple(new_order)

    def test_lab_order_with_non_strings_is_ignored(self):
        cfg = load_config({"config": {"lab_order": ["hgb", 42, "plt"]}})
        assert cfg.lab_order == CBCConfig().lab_order

    def test_override_signal_priority(self):
        cfg = load_config({"config": {"signal_priority": {"custom_signal": 1234}}})
        assert cfg.signal_priority.get("custom_signal") == 1234
        assert "pancytopenia_pattern" in cfg.signal_priority

    def test_signal_priority_with_non_numeric_value_skipped(self):
        cfg = load_config({"config": {"signal_priority": {"weird": "abc"}}})
        assert "weird" not in cfg.signal_priority

    def test_no_config_key(self):
        cfg = load_config({"sex": "male", "wbc": 6.0})
        assert cfg.wbc_high.mild == CBCConfig().wbc_high.mild
