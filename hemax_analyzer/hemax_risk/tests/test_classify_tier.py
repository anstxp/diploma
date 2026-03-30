from __future__ import annotations

import pytest

from risk_api.risk.inference import (
    TIER_ORDER, TIER_RANK,
    _classify_risk_tier,
    _max_tier,
)



class TestTierOrder:

    def test_tier_order_constant(self):
        assert TIER_ORDER == ("very_low", "low", "moderate", "high", "very_high")

    def test_tier_rank_strictly_increasing(self):
        ranks = [TIER_RANK[t] for t in TIER_ORDER]
        assert ranks == sorted(ranks)
        assert len(set(ranks)) == len(ranks)



class TestRareEventClassification:

    @pytest.mark.parametrize("target", ["told_chd", "told_chf", "told_stroke"])
    def test_above_very_high_threshold(self, target):
        assert _classify_risk_tier(0.50, baseline=0.03, target=target) == "very_high"

    @pytest.mark.parametrize("target", ["told_chd", "told_chf", "told_stroke"])
    def test_high_band(self, target):
        assert _classify_risk_tier(0.25, baseline=0.03, target=target) == "high"
        assert _classify_risk_tier(0.39, baseline=0.03, target=target) == "high"

    @pytest.mark.parametrize("target", ["told_chd", "told_chf", "told_stroke"])
    def test_moderate_band(self, target):
        assert _classify_risk_tier(0.15, baseline=0.03, target=target) == "moderate"

    @pytest.mark.parametrize("target", ["told_chd", "told_chf", "told_stroke"])
    def test_low_band(self, target):
        assert _classify_risk_tier(0.07, baseline=0.03, target=target) == "low"

    @pytest.mark.parametrize("target", ["told_chd", "told_chf", "told_stroke"])
    def test_very_low_band(self, target):
        assert _classify_risk_tier(0.02, baseline=0.03, target=target) == "very_low"

    def test_exact_threshold_boundary(self):
        assert _classify_risk_tier(0.40, 0.03, "told_chd") == "very_high"
        assert _classify_risk_tier(0.39999, 0.03, "told_chd") == "high"

    def test_rare_threshold_ignores_baseline(self):
        for baseline in (0.001, 0.05, 0.10):
            assert _classify_risk_tier(0.25, baseline, "told_chd") == "high"



class TestCommonConditionClassification:

    def test_very_high_at_absolute_threshold(self):
        assert _classify_risk_tier(0.90, baseline=0.20) == "very_high"
        assert _classify_risk_tier(0.85, baseline=0.20) == "very_high"

    def test_high_at_absolute_threshold(self):
        assert _classify_risk_tier(0.70, baseline=0.20) == "high"

    def test_low_prob_with_low_ratio_returns_low(self):
        result = _classify_risk_tier(0.03, baseline=0.05)
        assert result in ("very_low", "low")

    def test_very_low_when_prob_well_below_baseline(self):
        assert _classify_risk_tier(0.04, baseline=0.10) == "very_low"

    def test_ratio_based_moderate(self):
        assert _classify_risk_tier(0.30, baseline=0.10) == "high"

    def test_ratio_based_very_high(self):
        assert _classify_risk_tier(0.55, baseline=0.10) == "very_high"

    def test_zero_baseline_safe(self):
        result = _classify_risk_tier(0.10, baseline=0.0)
        assert result in TIER_ORDER



class TestMaxTier:

    def test_picks_highest(self):
        assert _max_tier(["low", "moderate", "very_low"]) == "moderate"

    def test_picks_very_high(self):
        assert _max_tier(["low", "very_high", "moderate"]) == "very_high"

    def test_empty_returns_low(self):
        assert _max_tier([]) == "low"

    def test_single_element(self):
        assert _max_tier(["high"]) == "high"

    def test_unknown_tier_safe(self):
        result = _max_tier(["low", "unknown_xyz"])
        assert result in ("low", "unknown_xyz")
