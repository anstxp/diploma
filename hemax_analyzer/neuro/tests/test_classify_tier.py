from __future__ import annotations

import pytest

from neuro_api.neuro.inference import (
    TIER_ORDER, TIER_RANK,
    _classify_risk_tier,
    _max_tier,
    _RARE_EVENT_TASKS,
)


class TestTierOrder:

    def test_tier_order_constant(self):
        assert TIER_ORDER == ("very_low", "low", "moderate", "high", "very_high")

    def test_tier_rank_strictly_increasing(self):
        ranks = [TIER_RANK[t] for t in TIER_ORDER]
        assert ranks == sorted(ranks)
        assert len(set(ranks)) == len(ranks)


class TestRareEventTasksDefinition:

    def test_suicidal_ideation_is_rare(self):
        assert "suicidal_ideation" in _RARE_EVENT_TASKS

    def test_depression_severe_is_rare(self):
        assert "depression_severe" in _RARE_EVENT_TASKS

    def test_common_tasks_not_rare(self):
        for common in ("depression_moderate", "sleep_deficiency",
                       "daytime_dysfunction", "snore_high",
                       "trouble_sleeping_high"):
            assert common not in _RARE_EVENT_TASKS



class TestRareEventClassification:

    @pytest.mark.parametrize("target", ["depression_severe", "suicidal_ideation"])
    def test_above_very_high_threshold(self, target):
        assert _classify_risk_tier(0.50, baseline=0.04, target=target) == "very_high"

    @pytest.mark.parametrize("target", ["depression_severe", "suicidal_ideation"])
    def test_at_very_high_threshold(self, target):
        assert _classify_risk_tier(0.40, baseline=0.04, target=target) == "very_high"

    @pytest.mark.parametrize("target", ["depression_severe", "suicidal_ideation"])
    def test_high_band(self, target):
        assert _classify_risk_tier(0.25, baseline=0.04, target=target) == "high"
        assert _classify_risk_tier(0.39, baseline=0.04, target=target) == "high"

    @pytest.mark.parametrize("target", ["depression_severe", "suicidal_ideation"])
    def test_moderate_band(self, target):
        assert _classify_risk_tier(0.15, baseline=0.04, target=target) == "moderate"

    @pytest.mark.parametrize("target", ["depression_severe", "suicidal_ideation"])
    def test_low_band(self, target):
        assert _classify_risk_tier(0.07, baseline=0.04, target=target) == "low"

    @pytest.mark.parametrize("target", ["depression_severe", "suicidal_ideation"])
    def test_very_low_band(self, target):
        assert _classify_risk_tier(0.02, baseline=0.04, target=target) == "very_low"

    def test_boundary_exact(self):
        assert _classify_risk_tier(0.40, 0.04, "suicidal_ideation") == "very_high"
        assert _classify_risk_tier(0.399999, 0.04, "suicidal_ideation") == "high"

    def test_baseline_ignored_for_rare(self):
        for baseline in (0.001, 0.05, 0.20):
            assert _classify_risk_tier(0.25, baseline,
                                       "suicidal_ideation") == "high"



class TestCommonConditionClassification:

    def test_very_high_at_85(self):
        assert _classify_risk_tier(0.90, baseline=0.10,
                                   target="depression_moderate") == "very_high"

    def test_high_at_65_above(self):
        assert _classify_risk_tier(0.70, baseline=0.10,
                                   target="depression_moderate") == "high"

    def test_low_prob_low_ratio(self):
        result = _classify_risk_tier(0.03, baseline=0.10,
                                     target="depression_moderate")
        assert result in ("very_low", "low")

    def test_ratio_based_high(self):
        assert _classify_risk_tier(0.30, baseline=0.10,
                                   target="sleep_deficiency") == "high"

    def test_zero_baseline_safe(self):
        result = _classify_risk_tier(0.10, baseline=0.0,
                                     target="depression_moderate")
        assert result in TIER_ORDER



class TestMaxTier:

    def test_picks_highest(self):
        assert _max_tier(["low", "moderate", "very_low"]) == "moderate"

    def test_picks_very_high(self):
        assert _max_tier(["low", "very_high"]) == "very_high"

    def test_empty_returns_low(self):
        assert _max_tier([]) == "low"

    def test_unknown_tier_safe(self):
        result = _max_tier(["low", "unknown_xyz"])
        assert result in ("low", "unknown_xyz")
