from __future__ import annotations


class TestModelLoading:

    def test_predictor_loads(self, predictor):
        assert predictor is not None
        assert predictor.model is not None

    def test_seven_targets(self, predictor):
        assert len(predictor.target_names) == 7

    def test_target_names_exact(self, predictor):
        assert set(predictor.target_names) == {
            "depression_moderate", "depression_severe",
            "sleep_deficiency", "daytime_dysfunction",
            "suicidal_ideation",
            "snore_high", "trouble_sleeping_high",
        }

    def test_v2_targets_present(self, predictor):
        assert "snore_high" in predictor.target_names
        assert "trouble_sleeping_high" in predictor.target_names

    def test_safety_critical_target_present(self, predictor):
        assert "suicidal_ideation" in predictor.target_names

    def test_57_features(self, predictor):
        assert len(predictor.feature_names) == 57

    def test_v2_features_present(self, predictor):
        v2_features = {
            "income_ratio", "edu_level",
            "metsyn_criteria_count", "fib4", "egfr_ckd_epi_2021",
            "iron_chem_ugdl", "non_hdl_mgdl", "globulin_gdl",
            "homa_ir", "arm_circ_cm", "sedentary_min_day",
        }
        missing = v2_features - set(predictor.feature_names)
        assert not missing, f"v2 features missing: {missing}"

    def test_feature_stats_present(self, predictor):
        for fname in predictor.feature_names:
            assert fname in predictor.feature_stats
            assert "mean" in predictor.feature_stats[fname]
            assert "std" in predictor.feature_stats[fname]

    def test_target_stats_present(self, predictor):
        for tname in predictor.target_names:
            assert tname in predictor.target_stats
            assert "prevalence" in predictor.target_stats[tname]

    def test_isotonic_loaded_for_all_targets(self, predictor):
        assert predictor.isotonic_params is not None
        for target in predictor.target_names:
            assert target in predictor.isotonic_params

    def test_isotonic_y_monotone(self, predictor):
        for target, params in predictor.isotonic_params.items():
            ys = params["y_thresholds"]
            for i in range(1, len(ys)):
                assert ys[i] >= ys[i-1] - 1e-9

    def test_model_in_eval_mode(self, predictor):
        assert not predictor.model.training

    def test_model_runs_on_cpu(self, predictor):
        assert predictor.device == "cpu"
