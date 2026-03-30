from __future__ import annotations

import numpy as np
import pytest


class TestIsotonicApplication:

    def test_apply_isotonic_passes_through_when_no_params(self, predictor):
        original = predictor.isotonic_params
        try:
            predictor.isotonic_params = None
            assert predictor._apply_isotonic("told_chd", 0.5) == 0.5
        finally:
            predictor.isotonic_params = original

    def test_apply_isotonic_for_unknown_target(self, predictor):
        assert predictor._apply_isotonic("nonexistent_target", 0.5) == 0.5

    def test_apply_isotonic_returns_float_in_0_1(self, predictor):
        for target in predictor.target_names:
            for raw in (0.01, 0.1, 0.3, 0.5, 0.7, 0.9, 0.99):
                cal = predictor._apply_isotonic(target, raw)
                assert 0.0 <= cal <= 1.0

    def test_apply_isotonic_is_monotone(self, predictor):
        for target in predictor.target_names:
            raws = [0.05, 0.10, 0.25, 0.40, 0.60, 0.80, 0.95]
            cals = [predictor._apply_isotonic(target, r) for r in raws]
            for i in range(1, len(cals)):
                assert cals[i] >= cals[i-1] - 1e-9, (
                    f"{target}: not monotone — {cals[i-1]:.4f} → {cals[i]:.4f}"
                )

    def test_clipping_below_min(self, predictor):
        for target, params in predictor.isotonic_params.items():
            x_min = params.get("x_min", params["x_thresholds"][0])
            cal_below = predictor._apply_isotonic(target, x_min / 2)
            cal_at = predictor._apply_isotonic(target, x_min)
            assert abs(cal_below - cal_at) < 1e-6

    def test_clipping_above_max(self, predictor):
        for target, params in predictor.isotonic_params.items():
            x_max = params.get("x_max", params["x_thresholds"][-1])
            if x_max < 0.99:
                cal_above = predictor._apply_isotonic(target, min(0.999, x_max + 0.05))
                cal_at = predictor._apply_isotonic(target, x_max)
                assert abs(cal_above - cal_at) < 1e-6


class TestRareEventCalibration:

    @pytest.mark.parametrize("target", ["told_chd", "told_chf", "told_stroke"])
    def test_calibration_reduces_rare_event_inflation(self, predictor, target):
        raw = 0.5
        cal = predictor._apply_isotonic(target, raw)
        assert cal <= raw


class TestCalibrationIntegration:

    def test_predict_uses_calibrated_probs(self, predictor, healthy_male):
        result = predictor.predict(healthy_male)
        for r in result.risks:
            assert 0.0 <= r.probability <= 1.0
