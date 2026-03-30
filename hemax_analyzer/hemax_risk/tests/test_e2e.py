from __future__ import annotations

import pytest



class TestHealthyYoung:

    def test_predicts_without_error(self, predictor, low_risk_young):
        result = predictor.predict(low_risk_young)
        assert result is not None

    def test_probabilities_all_in_range(self, predictor, low_risk_young):
        result = predictor.predict(low_risk_young)
        for r in result.risks:
            assert 0.0 <= r.probability <= 1.0



class TestDiabeticUncontrolled:

    def test_diabetes_probability_elevated(self, predictor, diabetic_patient):
        result = predictor.predict(diabetic_patient)
        diabetes = next(r for r in result.risks if r.target == "told_diabetes")
        assert diabetes.probability > diabetes.population_prevalence

    def test_diabetes_tier_at_least_moderate(self, predictor, diabetic_patient):
        result = predictor.predict(diabetic_patient)
        diabetes = next(r for r in result.risks if r.target == "told_diabetes")
        assert diabetes.risk_tier in ("moderate", "high", "very_high")



class TestHypertensive:

    def test_htn_probability_elevated(self, predictor, hypertensive_patient):
        result = predictor.predict(hypertensive_patient)
        htn = next(r for r in result.risks if r.target == "told_htn")
        assert htn.probability > htn.population_prevalence

    def test_htn_tier_at_least_moderate(self, predictor, hypertensive_patient):
        result = predictor.predict(hypertensive_patient)
        htn = next(r for r in result.risks if r.target == "told_htn")
        assert htn.risk_tier in ("moderate", "high", "very_high")



class TestMetabolicSyndrome:

    def test_multiple_risks_elevated(self, predictor, metabolic_syndrome_patient):
        result = predictor.predict(metabolic_syndrome_patient)
        elevated = sum(
            1 for r in result.risks
            if r.target in ("told_htn", "told_diabetes", "told_high_chol")
            and r.probability > r.population_prevalence
        )
        assert elevated >= 2



class TestCVDHighRisk:

    def test_overall_tier_elevated(self, predictor, cvd_high_risk_patient):
        result = predictor.predict(cvd_high_risk_patient)
        assert result.overall_tier not in ("very_low", "insufficient_data")

    def test_at_least_one_cvd_risk_elevated(self, predictor, cvd_high_risk_patient):
        result = predictor.predict(cvd_high_risk_patient)
        cvd_risks = [
            r for r in result.risks
            if r.target in ("told_chd", "told_chf", "told_stroke")
        ]
        elevated = [r for r in cvd_risks if r.probability > r.population_prevalence]
        assert len(elevated) >= 1



class TestEmptyPayload:

    def test_insufficient_data(self, predictor, empty_payload):
        result = predictor.predict(empty_payload)
        assert result.overall_tier == "insufficient_data"

    def test_n_features_provided_zero_or_low(self, predictor, empty_payload):
        result = predictor.predict(empty_payload)
        assert result.n_features_provided < 12



class TestSparsePayload:

    def test_only_sex_age_insufficient(self, predictor):
        result = predictor.predict({"sex": 1, "age": 50})
        assert result.overall_tier == "insufficient_data"

    def test_predicts_without_crash_on_partial(self, predictor):
        result = predictor.predict({"sex": 1, "age": 50, "glucose": 120})
        assert result is not None



class TestSIUnits:

    def test_glucose_mmol_handled(self, predictor):
        result_mmol = predictor.predict({
            "sex": 1, "age": 55, "bmi": 28,
            "glucose": "8.8 mmol/L",
            "sbp": 130, "tchol": 200, "hdl": 45,
        })
        result_mgdl = predictor.predict({
            "sex": 1, "age": 55, "bmi": 28,
            "glucose": 158,
            "sbp": 130, "tchol": 200, "hdl": 45,
        })
        d_mmol = next(r for r in result_mmol.risks if r.target == "told_diabetes")
        d_mgdl = next(r for r in result_mgdl.risks if r.target == "told_diabetes")
        assert abs(d_mmol.probability - d_mgdl.probability) < 0.10



class TestSexSpecificPredictions:

    def test_male_vs_female_differ(self, predictor):
        male = predictor.predict({
            "sex": 1, "age": 60, "sbp": 145, "tchol": 220, "hdl": 40,
        })
        female = predictor.predict({
            "sex": 2, "age": 60, "sbp": 145, "tchol": 220, "hdl": 40,
        })
        male_probs = {r.target: r.probability for r in male.risks}
        female_probs = {r.target: r.probability for r in female.risks}
        differences = [abs(male_probs[t] - female_probs[t]) for t in male_probs]
        assert max(differences) > 0.01



class TestAgeSensitivity:

    def test_older_patient_higher_cvd_risk(self, predictor):
        young = predictor.predict({
            "sex": 1, "age": 30, "sbp": 130, "tchol": 200, "hdl": 50,
            "glucose": 95, "bmi": 25, "creatinine": 1.0,
        })
        old = predictor.predict({
            "sex": 1, "age": 70, "sbp": 130, "tchol": 200, "hdl": 50,
            "glucose": 95, "bmi": 25, "creatinine": 1.0,
        })
        avg_young = sum(r.probability for r in young.risks) / 6
        avg_old = sum(r.probability for r in old.risks) / 6
        assert avg_old > avg_young



class TestDeterminismAcrossScenarios:

    def test_determinism_on_all_fixtures(self, predictor, all_patient_names, request):
        payload = request.getfixturevalue(all_patient_names)
        r1 = predictor.predict(payload)
        r2 = predictor.predict(payload)
        assert r1.overall_tier == r2.overall_tier
        for a, b in zip(r1.risks, r2.risks):
            assert a.probability == b.probability



class TestTopDrivers:

    def test_glucose_appears_in_diabetes_drivers(self, predictor, diabetic_patient):
        result = predictor.predict(diabetic_patient)
        diabetes_drivers = result.top_drivers["told_diabetes"]
        driver_features = {d.feature for d in diabetes_drivers}
        assert any("glucose" in f or "hba1c" in f for f in driver_features)
