from __future__ import annotations

from pathlib import Path

import pytest


class TestModelLoading:

    def test_predictor_loads(self, predictor):
        assert predictor is not None
        assert predictor.model is not None

    def test_targets_count(self, predictor):
        assert len(predictor.target_names) == 6

    def test_target_names(self, predictor):
        assert set(predictor.target_names) == {
            "told_htn", "told_diabetes", "told_high_chol",
            "told_chd", "told_chf", "told_stroke",
        }

    def test_feature_count(self, predictor):
        assert len(predictor.feature_names) == 46

    def test_feature_stats_present(self, predictor):
        for fname in predictor.feature_names:
            assert fname in predictor.feature_stats
            stats = predictor.feature_stats[fname]
            assert "mean" in stats
            assert "std" in stats

    def test_target_stats_present(self, predictor):
        for tname in predictor.target_names:
            assert tname in predictor.target_stats
            assert "prevalence" in predictor.target_stats[tname]

    def test_means_array_shape(self, predictor):
        n = len(predictor.feature_names)
        assert predictor.means.shape == (n,)
        assert predictor.stds.shape == (n,)

    def test_isotonic_params_loaded(self, predictor):
        assert predictor.isotonic_params is not None
        for target in predictor.target_names:
            assert target in predictor.isotonic_params, (
                f"Isotonic params missing for {target}"
            )

    def test_isotonic_params_structure(self, predictor):
        for target, params in predictor.isotonic_params.items():
            assert "x_thresholds" in params
            assert "y_thresholds" in params
            assert len(params["x_thresholds"]) == len(params["y_thresholds"])

    def test_isotonic_y_is_monotone(self, predictor):
        for target, params in predictor.isotonic_params.items():
            ys = params["y_thresholds"]
            for i in range(1, len(ys)):
                assert ys[i] >= ys[i-1] - 1e-9, (
                    f"{target}: y not monotone at index {i}"
                )


class TestModelArchitecture:

    def test_model_in_eval_mode(self, predictor):
        assert not predictor.model.training

    def test_model_runs_on_cpu(self, predictor):
        assert predictor.device == "cpu"

    def test_model_version_accessible(self, predictor):
        version = predictor.extras.get("model_version", "unknown")
        assert version is None or isinstance(version, str)
