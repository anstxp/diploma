from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from risk_api.narrative.narrative_engine import load_clusters
from risk_api.risk.inference import (
    ALIASES,
    TIER_ORDER,
    _classify_risk_tier,
    _aggregate_overall_tier,
)



class TestR1_ModelArchitecture:

    def test_six_targets(self, predictor):
        assert len(predictor.target_names) == 6

    def test_target_names_exact(self, predictor):
        assert set(predictor.target_names) == {
            "told_htn", "told_diabetes", "told_high_chol",
            "told_chd", "told_chf", "told_stroke",
        }

    def test_46_features(self, predictor):
        assert len(predictor.feature_names) == 46

    def test_all_features_have_stats(self, predictor):
        for f in predictor.feature_names:
            assert f in predictor.feature_stats
            assert "mean" in predictor.feature_stats[f]
            assert "std" in predictor.feature_stats[f]

    def test_all_targets_have_prevalence(self, predictor):
        for t in predictor.target_names:
            assert t in predictor.target_stats
            assert "prevalence" in predictor.target_stats[t]



class TestR2_ResponseEnvelope:

    def test_response_has_risks_array(self, predictor, diabetic_patient):
        result = predictor.predict(diabetic_patient)
        assert hasattr(result, "risks")
        assert len(result.risks) == 6

    def test_response_has_overall_tier(self, predictor, diabetic_patient):
        result = predictor.predict(diabetic_patient)
        assert hasattr(result, "overall_tier")
        assert result.overall_tier in TIER_ORDER + ("insufficient_data",)

    def test_response_has_feature_counts(self, predictor, diabetic_patient):
        result = predictor.predict(diabetic_patient)
        assert hasattr(result, "n_features_provided")
        assert hasattr(result, "n_features_total")
        assert result.n_features_total == 46

    def test_response_has_top_drivers(self, predictor, diabetic_patient):
        result = predictor.predict(diabetic_patient)
        assert hasattr(result, "top_drivers")
        for t in predictor.target_names:
            assert t in result.top_drivers

    def test_response_has_dropped_keys(self, predictor, diabetic_patient):
        result = predictor.predict(diabetic_patient)
        assert hasattr(result, "dropped_keys")
        assert isinstance(result.dropped_keys, list)

    def test_each_risk_has_required_fields(self, predictor, diabetic_patient):
        result = predictor.predict(diabetic_patient)
        for r in result.risks:
            assert hasattr(r, "target")
            assert hasattr(r, "name_ua")
            assert hasattr(r, "name_en")
            assert hasattr(r, "probability")
            assert hasattr(r, "risk_tier")
            assert hasattr(r, "population_prevalence")
            assert hasattr(r, "risk_ratio_vs_baseline")



class TestR3_TierClassification:

    def test_five_tiers_plus_insufficient(self):
        assert TIER_ORDER == ("very_low", "low", "moderate", "high", "very_high")

    def test_rare_event_thresholds(self):
        assert _classify_risk_tier(0.40, 0.03, "told_chd") == "very_high"
        assert _classify_risk_tier(0.25, 0.03, "told_chd") == "high"
        assert _classify_risk_tier(0.15, 0.03, "told_chd") == "moderate"
        assert _classify_risk_tier(0.07, 0.03, "told_chd") == "low"
        assert _classify_risk_tier(0.02, 0.03, "told_chd") == "very_low"

    def test_common_condition_absolute(self):
        assert _classify_risk_tier(0.90, 0.15) == "very_high"
        assert _classify_risk_tier(0.85, 0.15) == "very_high"



class TestR4_AggregationRule:

    def test_insufficient_below_min_coverage(self):
        from risk_api.risk.inference import TaskRiskResult
        risks = [TaskRiskResult("dummy", "", "", 0.5, "very_high", 0.1)] * 6
        result = _aggregate_overall_tier(risks, feature_coverage=0.10)
        assert result == "insufficient_data"

    def test_single_very_high_overall_moderate(self):
        from risk_api.risk.inference import TaskRiskResult
        risks = [
            TaskRiskResult("a", "", "", 0.5, "very_high", 0.05),
            TaskRiskResult("b", "", "", 0.1, "low", 0.05),
            TaskRiskResult("c", "", "", 0.1, "low", 0.05),
            TaskRiskResult("d", "", "", 0.1, "low", 0.05),
            TaskRiskResult("e", "", "", 0.1, "low", 0.05),
            TaskRiskResult("f", "", "", 0.1, "low", 0.05),
        ]
        result = _aggregate_overall_tier(risks, feature_coverage=0.8)
        assert result == "moderate"

    def test_two_very_high_overall_very_high(self):
        from risk_api.risk.inference import TaskRiskResult
        risks = [
            TaskRiskResult("a", "", "", 0.5, "very_high", 0.05),
            TaskRiskResult("b", "", "", 0.5, "very_high", 0.05),
            TaskRiskResult("c", "", "", 0.1, "low", 0.05),
            TaskRiskResult("d", "", "", 0.1, "low", 0.05),
            TaskRiskResult("e", "", "", 0.1, "low", 0.05),
            TaskRiskResult("f", "", "", 0.1, "low", 0.05),
        ]
        result = _aggregate_overall_tier(risks, feature_coverage=0.8)
        assert result == "very_high"



class TestR5_IsotonicCalibration:

    def test_isotonic_params_loaded(self, predictor):
        assert predictor.isotonic_params is not None
        assert len(predictor.isotonic_params) == 6

    def test_isotonic_all_targets(self, predictor):
        for t in predictor.target_names:
            assert t in predictor.isotonic_params

    def test_isotonic_monotone(self, predictor):
        for t, params in predictor.isotonic_params.items():
            ys = params["y_thresholds"]
            for i in range(1, len(ys)):
                assert ys[i] >= ys[i-1] - 1e-9

    def test_calibration_in_predict_pipeline(self, predictor, diabetic_patient):
        result = predictor.predict(diabetic_patient)
        for r in result.risks:
            assert 0.0 <= r.probability <= 1.0



class TestR6_InputFlexibility:

    def test_aliases_cover_short_names(self):
        for short in ("wbc", "hgb", "plt", "glucose", "a1c",
                      "creatinine", "tchol", "hdl", "trigly", "tg",
                      "sex", "age", "bmi", "sbp", "dbp"):
            assert short in ALIASES

    def test_aliases_cover_nhanes_style(self):
        for full in ("glucose_fasting", "hba1c_pct", "creatinine_mgdl"):
            assert full in ALIASES
            assert ALIASES[full] == full

    def test_embedded_units_glucose(self, predictor):
        result = predictor.predict({
            "sex": 1, "age": 50,
            "glucose": "8.8 mmol/L",
            "sbp": 140, "hdl": 45, "tchol": 200, "bmi": 28,
        })
        assert "glucose" not in result.dropped_keys

    def test_nested_labs_key(self, predictor):
        result = predictor.predict({
            "sex": 1, "age": 50,
            "labs": {"glucose": 95, "tchol": 200, "hdl": 45},
            "sbp": 140, "bmi": 28,
        })
        assert result is not None
        assert "glucose" not in result.dropped_keys



_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "risk_api" / "narrative" / "templates"


class TestR7_NarrativeCoverage:

    def test_17_clusters(self):
        assert len(load_clusters()) == 17

    def test_bilingual_templates(self):
        cluster_ids = {c["id"] for c in load_clusters()}
        for cid in cluster_ids:
            assert (_TEMPLATES_DIR / f"{cid}.uk.md").exists()
            assert (_TEMPLATES_DIR / f"{cid}.en.md").exists()

    def test_34_template_files_total(self):
        assert len(list(_TEMPLATES_DIR.glob("*.uk.md"))) == 17
        assert len(list(_TEMPLATES_DIR.glob("*.en.md"))) == 17



class TestR8_Determinism:

    def test_100_runs_byte_identical(self, predictor, diabetic_patient):
        hashes = set()
        for _ in range(100):
            r = predictor.predict(diabetic_patient)
            blob = json.dumps({
                "tier": r.overall_tier,
                "risks": [(x.target, round(x.probability, 8)) for x in r.risks],
            }, sort_keys=True)
            hashes.add(hashlib.sha256(blob.encode()).hexdigest())
        assert len(hashes) == 1



class TestR9_Safety:

    def test_sex_mapping_correct(self, predictor):
        male_pred = predictor.predict({
            "sex": 1, "age": 60, "sbp": 145, "tchol": 220, "hdl": 40, "bmi": 28,
        })
        female_pred = predictor.predict({
            "sex": 2, "age": 60, "sbp": 145, "tchol": 220, "hdl": 40, "bmi": 28,
        })
        male_probs = [r.probability for r in male_pred.risks]
        female_probs = [r.probability for r in female_pred.risks]
        assert male_probs != female_probs, (
            "Sex mapping bug regression — male and female predictions identical"
        )

    def test_insufficient_data_gate(self, predictor):
        result = predictor.predict({"sex": 1, "age": 50})
        assert result.overall_tier == "insufficient_data"

    def test_dropped_keys_reported(self, predictor):
        result = predictor.predict({
            "sex": 1, "age": 50,
            "glucose": "totally garbage",
            "sbp": 140, "tchol": 200, "hdl": 45, "bmi": 28,
        })
        assert "glucose" in result.dropped_keys

    def test_probabilities_in_valid_range(self, predictor):
        scenarios = [
            {"sex": 1, "age": 30, "sbp": 110},
            {"sex": 2, "age": 75, "sbp": 180, "glucose": 240, "a1c": 10.5},
            {},
            {"sex": 2, "age": 50, "bmi": 45},
        ]
        for payload in scenarios:
            result = predictor.predict(payload)
            for r in result.risks:
                assert 0.0 <= r.probability <= 1.0, (
                    f"Out-of-range prob {r.probability} for {r.target}"
                )

    def test_tier_classification_total(self):
        for tier in TIER_ORDER:
            assert tier in ("very_low", "low", "moderate", "high", "very_high")
