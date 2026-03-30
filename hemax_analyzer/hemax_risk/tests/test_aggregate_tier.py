from __future__ import annotations

import pytest

from risk_api.risk.inference import (
    TaskRiskResult,
    _aggregate_overall_tier,
)


def _mk(tier: str) -> TaskRiskResult:
    return TaskRiskResult(
        target="dummy", name_ua="", name_en="",
        probability=0.1, risk_tier=tier,
        population_prevalence=0.1,
    )



class TestInsufficientDataGate:

    def test_below_25_pct_coverage(self):
        risks = [_mk("very_high")] * 6
        result = _aggregate_overall_tier(risks, feature_coverage=0.10)
        assert result == "insufficient_data"

    def test_exact_threshold_passes(self):
        risks = [_mk("very_low")] * 6
        result = _aggregate_overall_tier(risks, feature_coverage=0.25)
        assert result != "insufficient_data"

    def test_high_coverage(self):
        risks = [_mk("low")] * 6
        result = _aggregate_overall_tier(risks, feature_coverage=0.90)
        assert result != "insufficient_data"



class TestEscalationRules:

    def test_two_very_high_overall_very_high(self):
        risks = [_mk("very_high"), _mk("very_high"),
                 _mk("low"), _mk("low"), _mk("low"), _mk("low")]
        assert _aggregate_overall_tier(risks, 0.9) == "very_high"

    def test_one_very_high_plus_one_high_overall_high(self):
        risks = [_mk("very_high"), _mk("high"),
                 _mk("low"), _mk("low"), _mk("low"), _mk("low")]
        assert _aggregate_overall_tier(risks, 0.9) == "high"

    def test_two_high_overall_high(self):
        risks = [_mk("high"), _mk("high"),
                 _mk("low"), _mk("low"), _mk("low"), _mk("low")]
        assert _aggregate_overall_tier(risks, 0.9) == "high"

    def test_single_very_high_alone_overall_moderate(self):
        risks = [_mk("very_high"),
                 _mk("low"), _mk("low"), _mk("low"), _mk("low"), _mk("low")]
        assert _aggregate_overall_tier(risks, 0.9) == "moderate"



class TestNonEscalatingCases:

    def test_one_high_overall_moderate(self):
        risks = [_mk("high"),
                 _mk("low"), _mk("low"), _mk("low"), _mk("low"), _mk("low")]
        assert _aggregate_overall_tier(risks, 0.9) == "moderate"

    def test_two_moderate_overall_moderate(self):
        risks = [_mk("moderate"), _mk("moderate"),
                 _mk("low"), _mk("low"), _mk("low"), _mk("low")]
        assert _aggregate_overall_tier(risks, 0.9) == "moderate"

    def test_one_moderate_overall_low(self):
        risks = [_mk("moderate"),
                 _mk("very_low"), _mk("very_low"), _mk("very_low"),
                 _mk("very_low"), _mk("very_low")]
        assert _aggregate_overall_tier(risks, 0.9) == "low"

    def test_all_very_low_overall_very_low(self):
        risks = [_mk("very_low")] * 6
        assert _aggregate_overall_tier(risks, 0.9) == "very_low"

    def test_all_low_overall_very_low(self):
        risks = [_mk("low")] * 6
        assert _aggregate_overall_tier(risks, 0.9) == "very_low"



class TestEdgeCases:

    def test_empty_risks_list(self):
        result = _aggregate_overall_tier([], feature_coverage=0.5)
        assert result == "very_low"

    def test_zero_coverage(self):
        result = _aggregate_overall_tier([], feature_coverage=0.0)
        assert result == "insufficient_data"
