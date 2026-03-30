from __future__ import annotations

import hashlib
import json

import pytest

from risk_api.risk.inference import (
    FeatureContribution,
    RiskPrediction,
    TaskRiskResult,
    TIER_ORDER,
)



class TestOutputShape:

    def test_returns_risk_prediction(self, predictor, healthy_male):
        result = predictor.predict(healthy_male)
        assert isinstance(result, RiskPrediction)

    def test_six_risks(self, predictor, healthy_male):
        result = predictor.predict(healthy_male)
        assert len(result.risks) == 6

    def test_each_risk_is_task_result(self, predictor, healthy_male):
        result = predictor.predict(healthy_male)
        for r in result.risks:
            assert isinstance(r, TaskRiskResult)

    def test_probabilities_in_0_1(self, predictor, healthy_male):
        result = predictor.predict(healthy_male)
        for r in result.risks:
            assert 0.0 <= r.probability <= 1.0

    def test_tiers_valid(self, predictor, healthy_male):
        result = predictor.predict(healthy_male)
        for r in result.risks:
            assert r.risk_tier in TIER_ORDER

    def test_overall_tier_valid(self, predictor, healthy_male):
        result = predictor.predict(healthy_male)
        assert result.overall_tier in TIER_ORDER + ("insufficient_data",)

    def test_n_features_provided_le_total(self, predictor, healthy_male):
        result = predictor.predict(healthy_male)
        assert 0 <= result.n_features_provided <= result.n_features_total
        assert result.n_features_total == 46

    def test_top_drivers_per_task(self, predictor, healthy_male):
        result = predictor.predict(healthy_male)
        for target in predictor.target_names:
            assert target in result.top_drivers
            drivers = result.top_drivers[target]
            assert isinstance(drivers, list)
            assert len(drivers) <= 5
            for d in drivers:
                assert isinstance(d, FeatureContribution)

    def test_model_version_string(self, predictor, healthy_male):
        result = predictor.predict(healthy_male)
        assert isinstance(result.model_version, str)
        assert len(result.model_version) > 0

    def test_dropped_keys_empty_for_clean_input(self, predictor, healthy_male):
        result = predictor.predict(healthy_male)
        assert result.dropped_keys == []



class TestRiskRatioFields:

    def test_risk_ratio_matches_odds_ratio(self, predictor, healthy_male):
        result = predictor.predict(healthy_male)
        for r in result.risks:
            assert r.risk_ratio_vs_baseline == r.odds_ratio_vs_baseline

    def test_risk_ratio_is_prob_over_baseline(self, predictor, diabetic_patient):
        result = predictor.predict(diabetic_patient)
        for r in result.risks:
            expected = r.probability / max(r.population_prevalence, 0.01)
            assert abs(r.risk_ratio_vs_baseline - expected) < 1e-3



class TestDeterminism:

    def test_100_runs_same_hash(self, predictor, diabetic_patient):
        hashes = set()
        for _ in range(100):
            r = predictor.predict(diabetic_patient)
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
        male = predictor.predict({"sex": 1, "age": 60, "sbp": 140})
        female = predictor.predict({"sex": 2, "age": 60, "sbp": 140})
        male_probs = [r.probability for r in male.risks]
        female_probs = [r.probability for r in female.risks]
        assert male_probs != female_probs

    def test_nhanes_1_is_male(self, predictor):
        r1 = predictor.predict({"sex": 1, "age": 50, "sbp": 130})
        r2 = predictor.predict({"sex": "male", "age": 50, "sbp": 130})
        for a, b in zip(r1.risks, r2.risks):
            assert abs(a.probability - b.probability) < 0.05

    def test_nhanes_2_is_female(self, predictor):
        r1 = predictor.predict({"sex": 2, "age": 50, "sbp": 130})
        r2 = predictor.predict({"sex": "female", "age": 50, "sbp": 130})
        for a, b in zip(r1.risks, r2.risks):
            assert abs(a.probability - b.probability) < 0.05

    def test_normalized_zero_is_male(self, predictor):
        result = predictor.predict({"sex": 0, "age": 50, "sbp": 130})
        assert result is not None

    def test_ambiguous_sex_treated_as_missing(self, predictor):
        result = predictor.predict({"sex": "robot", "age": 50})
        assert result is not None



class TestDroppedKeys:

    def test_garbage_lab_value_dropped(self, predictor):
        result = predictor.predict({
            "sex": 1, "age": 50,
            "glucose": "totally garbage value",
        })
        assert "glucose" in result.dropped_keys

    def test_unknown_field_silently_ignored(self, predictor):
        result = predictor.predict({
            "sex": 1, "age": 50,
            "glucose": 95,
            "completely_made_up_field": 99,
        })
        assert "completely_made_up_field" not in result.dropped_keys



class TestInsufficientData:

    def test_empty_payload_insufficient(self, predictor, empty_payload):
        result = predictor.predict(empty_payload)
        assert result.overall_tier == "insufficient_data"

    def test_sparse_payload_insufficient(self, predictor):
        result = predictor.predict({"sex": 1, "age": 50})
        assert result.overall_tier == "insufficient_data"

    def test_full_payload_not_insufficient(self, predictor, healthy_male):
        result = predictor.predict(healthy_male)
        assert result.overall_tier != "insufficient_data"



class TestTopDrivers:

    def test_drivers_per_task(self, predictor, healthy_male):
        result = predictor.predict(healthy_male)
        for target in predictor.target_names:
            drivers = result.top_drivers[target]
            assert 1 <= len(drivers) <= 5

    def test_driver_direction_valid(self, predictor, diabetic_patient):
        result = predictor.predict(diabetic_patient)
        for target in predictor.target_names:
            for d in result.top_drivers[target]:
                assert d.direction in ("raises", "lowers", "neutral")

    def test_top_k_respected(self, predictor, healthy_male):
        result = predictor.predict(healthy_male, top_k_drivers=3)
        for target in predictor.target_names:
            assert len(result.top_drivers[target]) <= 3



class TestEmbeddedUnits:

    def test_glucose_mmol_parsed(self, predictor):
        result = predictor.predict({
            "sex": 1, "age": 50,
            "glucose": "8.8 mmol/L",
            "sbp": 140, "hgb": 14.5, "creatinine": 1.0,
            "tchol": 200, "hdl": 45, "bmi": 28,
        })
        assert "glucose" not in result.dropped_keys

    def test_creatinine_umol_parsed(self, predictor):
        result = predictor.predict({
            "sex": 1, "age": 50,
            "creatinine": "88 µmol/L",
            "sbp": 140, "glucose": 95,
            "tchol": 200, "hdl": 45, "bmi": 28,
        })
        assert "creatinine" not in result.dropped_keys
