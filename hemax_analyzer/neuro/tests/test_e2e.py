from __future__ import annotations

import pytest



class TestHealthyYoungAdult:

    def test_predicts_without_error(self, predictor, healthy_young_adult):
        result = predictor.predict(healthy_young_adult)
        assert result is not None

    def test_probabilities_all_in_range(self, predictor, healthy_young_adult):
        result = predictor.predict(healthy_young_adult)
        for r in result.risks:
            assert 0.0 <= r.probability <= 1.0



class TestLowRiskYoung:

    def test_overall_tier_not_severe(self, predictor, low_risk_young_active):
        result = predictor.predict(low_risk_young_active)
        assert result.overall_tier in (
            "very_low", "low", "moderate", "insufficient_data"
        )



class TestMetabolicAtRisk:

    def test_at_least_one_mental_health_risk_elevated(self, predictor, metabolic_at_risk):
        result = predictor.predict(metabolic_at_risk)
        elevated = [r for r in result.risks if r.probability > r.population_prevalence]
        assert len(elevated) >= 1



class TestLowSESHighInflammation:

    def test_predicts_without_error(self, predictor, low_ses_high_inflammation):
        result = predictor.predict(low_ses_high_inflammation)
        assert result is not None

    def test_depression_or_sleep_elevated(self, predictor, low_ses_high_inflammation):
        result = predictor.predict(low_ses_high_inflammation)
        mental_health = [r for r in result.risks
                         if r.target in ("depression_moderate", "sleep_deficiency",
                                         "daytime_dysfunction")]
        elevated = [r for r in mental_health if r.probability > r.population_prevalence]
        assert len(elevated) >= 1



class TestChronicDiseaseBurden:

    def test_overall_tier_above_very_low(self, predictor, chronic_disease_burden):
        result = predictor.predict(chronic_disease_burden)
        assert result.overall_tier not in ("very_low",)



class TestElderlyAtRisk:

    def test_predicts_without_error(self, predictor, elderly_at_risk):
        result = predictor.predict(elderly_at_risk)
        assert result is not None

    def test_sleep_risks_present(self, predictor, elderly_at_risk):
        result = predictor.predict(elderly_at_risk)
        sleep_targets = ("sleep_deficiency", "trouble_sleeping_high",
                         "daytime_dysfunction")
        sleep_risks = [r for r in result.risks if r.target in sleep_targets]
        assert len(sleep_risks) == 3



class TestEmptyPayload:

    def test_insufficient_data(self, predictor, empty_payload):
        result = predictor.predict(empty_payload)
        assert result.overall_tier == "insufficient_data"


class TestSparsePayload:

    def test_only_sex_age_insufficient(self, predictor):
        result = predictor.predict({"sex": 1, "age": 50})
        assert result.overall_tier == "insufficient_data"

    def test_predicts_without_crash_on_partial(self, predictor):
        result = predictor.predict({"sex": 1, "age": 50, "glucose": 120, "crp": 5})
        assert result is not None



class TestSIUnits:

    def test_glucose_mmol_handled(self, predictor):
        result_mmol = predictor.predict({
            "sex": 1, "age": 50, "bmi": 28,
            "glucose": "8.8 mmol/L",
            "sbp": 130, "tchol": 200, "hdl": 45, "crp": 3,
        })
        result_mgdl = predictor.predict({
            "sex": 1, "age": 50, "bmi": 28,
            "glucose": 158,
            "sbp": 130, "tchol": 200, "hdl": 45, "crp": 3,
        })
        m_pred_str = sorted([r.target for r in result_mmol.risks])
        d_pred_str = sorted([r.target for r in result_mgdl.risks])
        assert m_pred_str == d_pred_str



class TestSexSpecificPredictions:

    def test_male_vs_female_differ(self, predictor):
        male = predictor.predict({
            "sex": 1, "age": 45, "bmi": 28, "sbp": 130,
            "glucose": 100, "tchol": 200, "hdl": 45, "crp": 2,
        })
        female = predictor.predict({
            "sex": 2, "age": 45, "bmi": 28, "sbp": 130,
            "glucose": 100, "tchol": 200, "hdl": 45, "crp": 2,
        })
        male_probs = {r.target: r.probability for r in male.risks}
        female_probs = {r.target: r.probability for r in female.risks}
        differences = [abs(male_probs[t] - female_probs[t]) for t in male_probs]
        assert max(differences) > 0.01



class TestDeterminismAcrossScenarios:

    def test_determinism_on_all_fixtures(self, predictor, all_patient_names, request):
        payload = request.getfixturevalue(all_patient_names)
        r1 = predictor.predict(payload)
        r2 = predictor.predict(payload)
        assert r1.overall_tier == r2.overall_tier
        for a, b in zip(r1.risks, r2.risks):
            assert a.probability == b.probability



class TestSafetySuicidalIdeation:

    def test_suicidal_target_always_in_response(self, predictor, healthy_young_adult):
        result = predictor.predict(healthy_young_adult)
        suicidal = next(r for r in result.risks if r.target == "suicidal_ideation")
        assert suicidal is not None
        assert 0.0 <= suicidal.probability <= 1.0

    def test_suicidal_uses_absolute_thresholds(self, predictor, healthy_young_adult):
        result = predictor.predict(healthy_young_adult)
        suicidal = next(r for r in result.risks if r.target == "suicidal_ideation")
        assert suicidal.risk_tier not in ("high", "very_high"), (
            f"Healthy patient flagged as {suicidal.risk_tier} for suicidal ideation"
        )

    def test_safety_critical_calibrated(self, predictor):
        assert predictor.isotonic_params is not None
        assert "suicidal_ideation" in predictor.isotonic_params



class TestTopDrivers:

    def test_drivers_present_for_safety_critical(self, predictor, metabolic_at_risk):
        result = predictor.predict(metabolic_at_risk)
        assert "suicidal_ideation" in result.top_drivers
        assert len(result.top_drivers["suicidal_ideation"]) >= 1

    def test_drivers_for_all_seven_targets(self, predictor, metabolic_at_risk):
        result = predictor.predict(metabolic_at_risk)
        for target in predictor.target_names:
            assert target in result.top_drivers
            assert len(result.top_drivers[target]) >= 1
