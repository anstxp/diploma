from __future__ import annotations

import hashlib
import json

import pytest

from neuro_api.neuro.inference import (
    FeatureContribution,
    RiskPrediction,
    TaskRiskResult,
    TIER_ORDER,
)



class TestOutputShape:

    def test_returns_risk_prediction(self, predictor, healthy_young_adult):
        result = predictor.predict(healthy_young_adult)
        assert isinstance(result, RiskPrediction)

    def test_seven_risks(self, predictor, healthy_young_adult):
        result = predictor.predict(healthy_young_adult)
        assert len(result.risks) == 7

    def test_each_risk_is_task_result(self, predictor, healthy_young_adult):
        result = predictor.predict(healthy_young_adult)
        for r in result.risks:
            assert isinstance(r, TaskRiskResult)

    def test_probabilities_in_0_1(self, predictor, healthy_young_adult):
        result = predictor.predict(healthy_young_adult)
        for r in result.risks:
            assert 0.0 <= r.probability <= 1.0

    def test_tiers_valid(self, predictor, healthy_young_adult):
        result = predictor.predict(healthy_young_adult)
        for r in result.risks:
            assert r.risk_tier in TIER_ORDER

    def test_overall_tier_valid(self, predictor, healthy_young_adult):
        result = predictor.predict(healthy_young_adult)
        assert result.overall_tier in TIER_ORDER + ("insufficient_data",)

    def test_n_features_total_57(self, predictor, healthy_young_adult):
        result = predictor.predict(healthy_young_adult)
        assert result.n_features_total == 57

    def test_n_features_provided_le_total(self, predictor, healthy_young_adult):
        result = predictor.predict(healthy_young_adult)
        assert 0 <= result.n_features_provided <= 57

    def test_top_drivers_for_each_target(self, predictor, healthy_young_adult):
        result = predictor.predict(healthy_young_adult)
        for target in predictor.target_names:
            assert target in result.top_drivers
            drivers = result.top_drivers[target]
            assert isinstance(drivers, list)
            for d in drivers:
                assert isinstance(d, FeatureContribution)

    def test_model_version_set(self, predictor, healthy_young_adult):
        result = predictor.predict(healthy_young_adult)
        assert isinstance(result.model_version, str)
        assert len(result.model_version) > 0



class TestProbabilityRatio:

    def test_ratio_matches_baseline(self, predictor, metabolic_at_risk):
        result = predictor.predict(metabolic_at_risk)
        for r in result.risks:
            expected = r.probability / max(r.population_prevalence, 0.01)
            assert abs(r.probability_ratio_vs_baseline - expected) < 1e-3

    def test_odds_ratio_is_alias_for_probability_ratio(self, predictor, metabolic_at_risk):
        result = predictor.predict(metabolic_at_risk)
        for r in result.risks:
            assert r.odds_ratio_vs_baseline == r.probability_ratio_vs_baseline



class TestDeterminism:

    def test_100_runs_same_hash(self, predictor, metabolic_at_risk):
        hashes = set()
        for _ in range(100):
            r = predictor.predict(metabolic_at_risk)
            blob = json.dumps({
                "tier": r.overall_tier,
                "risks": [(x.target, round(x.probability, 8)) for x in r.risks],
            }, sort_keys=True)
            hashes.add(hashlib.sha256(blob.encode()).hexdigest())
        assert len(hashes) == 1

    def test_determinism_across_fixtures(self, predictor, all_patient_names, request):
        payload = request.getfixturevalue(all_patient_names)
        r1 = predictor.predict(payload)
        r2 = predictor.predict(payload)
        for a, b in zip(r1.risks, r2.risks):
            assert a.probability == b.probability
            assert a.risk_tier == b.risk_tier



class TestSexNormalization:

    def test_male_vs_female_produce_different_predictions(self, predictor):
        male = predictor.predict({"sex": 1, "age": 45, "bmi": 26, "sbp": 130})
        female = predictor.predict({"sex": 2, "age": 45, "bmi": 26, "sbp": 130})
        male_probs = [r.probability for r in male.risks]
        female_probs = [r.probability for r in female.risks]
        assert male_probs != female_probs

    def test_nhanes_codes_normalized(self, predictor):
        r1 = predictor.predict({"sex": 1, "age": 45, "bmi": 26})
        r2 = predictor.predict({"sex": "male", "age": 45, "bmi": 26})
        for a, b in zip(r1.risks, r2.risks):
            assert abs(a.probability - b.probability) < 0.05

    def test_female_string(self, predictor):
        result = predictor.predict({"sex": "female", "age": 45, "bmi": 26})
        assert result is not None



class TestDroppedKeys:

    def test_garbage_lab_value_dropped(self, predictor):
        result = predictor.predict({
            "sex": 1, "age": 50,
            "glucose": "totally garbage",
            "sbp": 140, "bmi": 28, "hgb": 14.5, "tchol": 200,
        })
        assert result is not None



class TestInsufficientData:

    def test_empty_payload_insufficient(self, predictor, empty_payload):
        result = predictor.predict(empty_payload)
        assert result.overall_tier == "insufficient_data"

    def test_sparse_payload_insufficient(self, predictor):
        result = predictor.predict({"sex": 1, "age": 50})
        assert result.overall_tier == "insufficient_data"

    def test_full_payload_not_insufficient(self, predictor, healthy_young_adult):
        result = predictor.predict(healthy_young_adult)
        assert result.overall_tier != "insufficient_data"



class TestEmbeddedUnits:

    def test_glucose_mmol_parsed(self, predictor):
        result = predictor.predict({
            "sex": 1, "age": 50,
            "glucose": "8.8 mmol/L",
            "sbp": 140, "hgb": 14.5,
            "tchol": 200, "hdl": 45, "bmi": 28,
        })
        assert result.n_features_provided > 5



class TestTopDrivers:

    def test_drivers_per_task(self, predictor, healthy_young_adult):
        result = predictor.predict(healthy_young_adult)
        for target in predictor.target_names:
            drivers = result.top_drivers[target]
            assert 1 <= len(drivers) <= 5

    def test_driver_direction_valid(self, predictor, metabolic_at_risk):
        result = predictor.predict(metabolic_at_risk)
        for target in predictor.target_names:
            for d in result.top_drivers[target]:
                assert d.direction in ("raises", "lowers", "neutral")

    def test_top_k_respected(self, predictor, healthy_young_adult):
        result = predictor.predict(healthy_young_adult, top_k_drivers=3)
        for target in predictor.target_names:
            assert len(result.top_drivers[target]) <= 3
