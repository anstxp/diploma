from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from neuro_api.narrative.narrative_engine import load_clusters
from neuro_api.neuro.inference import (
    ALIASES,
    TIER_ORDER,
    _classify_risk_tier,
    _aggregate_overall_tier,
    _RARE_EVENT_TASKS,
)



class TestR1_ModelArchitecture:

    def test_seven_targets(self, predictor):
        assert len(predictor.target_names) == 7

    def test_target_names_exact(self, predictor):
        assert set(predictor.target_names) == {
            "depression_moderate", "depression_severe",
            "sleep_deficiency", "daytime_dysfunction",
            "suicidal_ideation",
            "snore_high", "trouble_sleeping_high",
        }

    def test_suicidal_ideation_present(self, predictor):
        assert "suicidal_ideation" in predictor.target_names

    def test_v2_task_heads_present(self, predictor):
        assert "snore_high" in predictor.target_names
        assert "trouble_sleeping_high" in predictor.target_names

    def test_57_features(self, predictor):
        assert len(predictor.feature_names) == 57

    def test_v2_features_present(self, predictor):
        v2 = {"income_ratio", "edu_level", "metsyn_criteria_count",
              "fib4", "egfr_ckd_epi_2021", "iron_chem_ugdl",
              "non_hdl_mgdl", "globulin_gdl", "homa_ir",
              "arm_circ_cm", "sedentary_min_day"}
        missing = v2 - set(predictor.feature_names)
        assert not missing

    def test_all_features_have_stats(self, predictor):
        for f in predictor.feature_names:
            assert "mean" in predictor.feature_stats[f]
            assert "std" in predictor.feature_stats[f]

    def test_all_targets_have_prevalence(self, predictor):
        for t in predictor.target_names:
            assert "prevalence" in predictor.target_stats[t]



class TestR2_ResponseEnvelope:

    def test_has_risks_array(self, predictor, metabolic_at_risk):
        result = predictor.predict(metabolic_at_risk)
        assert hasattr(result, "risks")
        assert len(result.risks) == 7

    def test_has_overall_tier(self, predictor, metabolic_at_risk):
        result = predictor.predict(metabolic_at_risk)
        assert hasattr(result, "overall_tier")

    def test_has_feature_counts(self, predictor, metabolic_at_risk):
        result = predictor.predict(metabolic_at_risk)
        assert result.n_features_total == 57

    def test_has_top_drivers(self, predictor, metabolic_at_risk):
        result = predictor.predict(metabolic_at_risk)
        for t in predictor.target_names:
            assert t in result.top_drivers

    def test_has_model_version(self, predictor, metabolic_at_risk):
        result = predictor.predict(metabolic_at_risk)
        assert isinstance(result.model_version, str)
        assert len(result.model_version) > 0

    def test_each_risk_has_required_fields(self, predictor, metabolic_at_risk):
        result = predictor.predict(metabolic_at_risk)
        for r in result.risks:
            assert hasattr(r, "target")
            assert hasattr(r, "name_ua")
            assert hasattr(r, "name_en")
            assert hasattr(r, "probability")
            assert hasattr(r, "risk_tier")
            assert hasattr(r, "population_prevalence")
            assert hasattr(r, "probability_ratio_vs_baseline")
            assert hasattr(r, "odds_ratio_vs_baseline")



class TestR3_TierClassification:

    def test_five_tiers(self):
        assert TIER_ORDER == ("very_low", "low", "moderate", "high", "very_high")

    def test_rare_event_tasks_include_safety_critical(self):
        assert "suicidal_ideation" in _RARE_EVENT_TASKS
        assert "depression_severe" in _RARE_EVENT_TASKS

    def test_rare_event_thresholds_for_suicidal(self):
        for prob, expected in (
            (0.50, "very_high"),
            (0.25, "high"),
            (0.15, "moderate"),
            (0.07, "low"),
            (0.02, "very_low"),
        ):
            assert _classify_risk_tier(prob, 0.04, "suicidal_ideation") == expected

    def test_common_condition_absolute(self):
        assert _classify_risk_tier(0.90, 0.15, "depression_moderate") == "very_high"



class TestR4_AggregationRule:

    def test_insufficient_below_min_coverage(self):
        from neuro_api.neuro.inference import TaskRiskResult
        risks = [TaskRiskResult("d", "", "", 0.5, "very_high", 0.04, 12.0)] * 7
        result = _aggregate_overall_tier(risks, feature_coverage=0.10)
        assert result == "insufficient_data"

    def test_single_very_high_overall_moderate(self):
        from neuro_api.neuro.inference import TaskRiskResult
        risks = [
            TaskRiskResult("suicidal_ideation", "", "", 0.50, "very_high", 0.04, 12.5),
            TaskRiskResult("b", "", "", 0.1, "low", 0.05, 2.0),
            TaskRiskResult("c", "", "", 0.1, "low", 0.05, 2.0),
            TaskRiskResult("d", "", "", 0.1, "low", 0.05, 2.0),
            TaskRiskResult("e", "", "", 0.1, "low", 0.05, 2.0),
            TaskRiskResult("f", "", "", 0.1, "low", 0.05, 2.0),
            TaskRiskResult("g", "", "", 0.1, "low", 0.05, 2.0),
        ]
        result = _aggregate_overall_tier(risks, feature_coverage=0.8)
        assert result == "moderate"

    def test_two_very_high_overall_very_high(self):
        from neuro_api.neuro.inference import TaskRiskResult
        risks = [TaskRiskResult(f"t{i}", "", "", 0.5, "very_high", 0.05, 10.0)
                 for i in range(2)] + \
                [TaskRiskResult(f"t{i}", "", "", 0.1, "low", 0.05, 2.0)
                 for i in range(5)]
        result = _aggregate_overall_tier(risks, feature_coverage=0.8)
        assert result == "very_high"



class TestR5_IsotonicCalibration:

    def test_isotonic_loaded(self, predictor):
        assert predictor.isotonic_params is not None
        assert len(predictor.isotonic_params) == 7

    def test_isotonic_all_targets(self, predictor):
        for t in predictor.target_names:
            assert t in predictor.isotonic_params, (
                f"Missing isotonic params for {t}"
            )

    def test_isotonic_safety_critical_calibrated(self, predictor):
        assert "suicidal_ideation" in predictor.isotonic_params

    def test_isotonic_monotone(self, predictor):
        for t, params in predictor.isotonic_params.items():
            ys = params["y_thresholds"]
            for i in range(1, len(ys)):
                assert ys[i] >= ys[i-1] - 1e-9

    def test_calibration_applied_in_predict(self, predictor, metabolic_at_risk):
        result = predictor.predict(metabolic_at_risk)
        for r in result.risks:
            assert 0.0 <= r.probability <= 1.0



class TestR6_InputFlexibility:

    def test_aliases_cover_short_names(self):
        for short in ("wbc", "hgb", "plt", "glucose", "a1c", "creatinine",
                      "tchol", "hdl", "trigly", "sex", "age", "bmi"):
            assert short in ALIASES

    def test_aliases_cover_v2_ses(self):
        assert ALIASES.get("pir") == "income_ratio"
        assert ALIASES.get("education") == "edu_level"
        assert ALIASES.get("metsyn_count") == "metsyn_criteria_count"

    def test_embedded_units_glucose(self, predictor):
        result = predictor.predict({
            "sex": 1, "age": 50, "bmi": 28,
            "glucose": "8.8 mmol/L",
            "sbp": 140, "hdl": 45, "tchol": 200, "crp": 2,
        })
        assert result is not None
        assert result.n_features_provided > 5



_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "neuro_api" / "narrative" / "templates"


class TestR7_NarrativeCoverage:

    def test_13_clusters(self):
        assert len(load_clusters()) == 13

    def test_bilingual_templates(self):
        cluster_ids = {c["id"] for c in load_clusters()}
        for cid in cluster_ids:
            assert (_TEMPLATES_DIR / f"{cid}.uk.md").exists()
            assert (_TEMPLATES_DIR / f"{cid}.en.md").exists()

    def test_26_template_files_total(self):
        assert len(list(_TEMPLATES_DIR.glob("*.uk.md"))) == 13
        assert len(list(_TEMPLATES_DIR.glob("*.en.md"))) == 13



class TestR8_Determinism:

    def test_100_runs_byte_identical(self, predictor, metabolic_at_risk):
        hashes = set()
        for _ in range(100):
            r = predictor.predict(metabolic_at_risk)
            blob = json.dumps({
                "tier": r.overall_tier,
                "risks": [(x.target, round(x.probability, 8)) for x in r.risks],
            }, sort_keys=True)
            hashes.add(hashlib.sha256(blob.encode()).hexdigest())
        assert len(hashes) == 1



class TestR9_Safety:

    def test_sex_mapping_correct(self, predictor):
        male = predictor.predict({
            "sex": 1, "age": 45, "bmi": 28, "sbp": 130,
            "glucose": 100, "tchol": 200, "hdl": 45, "crp": 2,
        })
        female = predictor.predict({
            "sex": 2, "age": 45, "bmi": 28, "sbp": 130,
            "glucose": 100, "tchol": 200, "hdl": 45, "crp": 2,
        })
        male_probs = [r.probability for r in male.risks]
        female_probs = [r.probability for r in female.risks]
        assert male_probs != female_probs

    def test_insufficient_data_gate(self, predictor):
        result = predictor.predict({"sex": 1, "age": 50})
        assert result.overall_tier == "insufficient_data"

    def test_garbage_lab_value_no_exception(self, predictor):
        result = predictor.predict({
            "sex": 1, "age": 50,
            "glucose": "totally garbage",
            "sbp": 140, "tchol": 200, "hdl": 45, "bmi": 28, "crp": 2,
        })
        assert result is not None

    def test_suicidal_target_always_reported(self, predictor):
        for payload in [
            {"sex": 1, "age": 30, "bmi": 22, "sbp": 110, "glucose": 90, "crp": 1},
            {"sex": 2, "age": 75, "bmi": 28, "sbp": 145, "glucose": 110, "crp": 4},
            {},
        ]:
            result = predictor.predict(payload)
            targets = {r.target for r in result.risks}
            assert "suicidal_ideation" in targets

    def test_probabilities_in_valid_range_stress(self, predictor):
        scenarios = [
            {"sex": 1, "age": 30, "bmi": 22},
            {"sex": 2, "age": 75, "bmi": 38, "glucose": 250, "a1c": 10.0,
             "sbp": 180, "crp": 25, "vitd_25oh": 8, "income_ratio": 0.5},
            {},
            {"sex": 2, "age": 50, "bmi": 45, "homa_ir": 8.0,
             "metsyn_criteria_count": 5},
        ]
        for payload in scenarios:
            result = predictor.predict(payload)
            for r in result.risks:
                assert 0.0 <= r.probability <= 1.0, (
                    f"Out-of-range prob {r.probability} for {r.target}"
                )
