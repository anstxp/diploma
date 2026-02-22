from __future__ import annotations

import pytest

from cbc_api.validation import (
    PCT_FIELDS,
    PLAUSIBLE_RANGES,
    UNIT_CONFUSION_RULES,
    FieldIssue,
    ValidationResult,
    validate_payload,
)



class TestStaticTables:

    def test_plausible_ranges_present(self):
        for code in ("wbc", "hgb", "plt", "mcv", "rdw", "rbc", "hct"):
            assert code in PLAUSIBLE_RANGES

    def test_plausible_ranges_are_ordered(self):
        for code, (lo, hi, unit) in PLAUSIBLE_RANGES.items():
            assert lo <= hi, f"{code}: lo {lo} > hi {hi}"
            assert isinstance(unit, str) and unit

    def test_unit_confusion_rules_cover_common_pitfalls(self):
        for code in ("hgb", "hct", "plt", "wbc", "rbc"):
            assert code in UNIT_CONFUSION_RULES, (
                f"{code} should have unit-confusion auto-detection"
            )

    def test_pct_fields_are_diff_codes(self):
        assert set(PCT_FIELDS) == {
            "neut_pct", "lymph_pct", "mono_pct", "eos_pct", "baso_pct"
        }



class TestFieldIssueAndValidationResult:

    def test_field_issue_creation(self):
        issue = FieldIssue(
            field="hgb", level="warning", code="unit_autoconverted",
            message_uk="UK msg", message_en="EN msg",
            original_value=145.0, corrected_value=14.5,
        )
        assert issue.field == "hgb"
        assert issue.level == "warning"
        assert issue.original_value == 145.0
        assert issue.corrected_value == 14.5

    def test_validation_result_no_errors_warnings(self):
        r = ValidationResult(normalised={"hgb": 14.5})
        assert r.normalised == {"hgb": 14.5}
        assert r.errors == []
        assert r.warnings == []
        assert r.has_errors is False

    def test_has_errors_true(self):
        bad = FieldIssue(field="x", level="error", code="bad",
                         message_uk="", message_en="")
        r = ValidationResult(normalised={}, errors=[bad])
        assert r.has_errors is True

    def test_to_dict_returns_localised_messages(self):
        bad = FieldIssue(field="hgb", level="error", code="oor",
                         message_uk="ук", message_en="en")
        r = ValidationResult(normalised={}, errors=[bad])
        out_uk = r.to_dict(lang="uk")
        out_en = r.to_dict(lang="en")
        assert out_uk["errors"][0]["message"] == "ук"
        assert out_en["errors"][0]["message"] == "en"



class TestValidatePayloadHappy:

    def test_normal_payload_no_warnings(self):
        r = validate_payload({
            "sex": "male", "age": 35,
            "hgb": 15.0, "wbc": 6.5, "plt": 250,
            "mcv": 88, "rdw": 13.5,
        })
        assert not r.has_errors
        assert r.warnings == []
        assert r.normalised["hgb"] == 15.0



class TestUnitConfusion:

    def test_hgb_g_per_L_autoconverted(self):
        r = validate_payload({"hgb": 145.0, "sex": "male"})
        assert not r.has_errors
        assert any(w.code == "unit_autoconverted" for w in r.warnings)
        assert r.normalised["hgb"] == pytest.approx(14.5)

    def test_hct_fraction_autoconverted(self):
        r = validate_payload({"hct": 0.42, "sex": "female"})
        assert not r.has_errors
        assert r.normalised["hct"] == pytest.approx(42.0)

    def test_plt_raw_count_autoconverted(self):
        r = validate_payload({"plt": 250_000.0, "sex": "male"})
        assert not r.has_errors
        assert r.normalised["plt"] == pytest.approx(250.0)

    def test_wbc_raw_count_autoconverted(self):
        r = validate_payload({"wbc": 6500.0, "sex": "male"})
        assert not r.has_errors
        assert r.normalised["wbc"] == pytest.approx(6.5)



class TestFractionAsPercent:

    def test_single_neut_pct_as_fraction_corrected(self):
        r = validate_payload({"sex": "male", "neut_pct": 0.65})
        assert not r.has_errors
        assert r.normalised["neut_pct"] == 65.0
        assert any(w.code == "fraction_as_percent" for w in r.warnings)

    def test_eos_below_1_not_auto_scaled(self):
        r = validate_payload({"sex": "male", "eos_pct": 0.5})
        assert not r.has_errors
        assert r.normalised["eos_pct"] == 0.5

    def test_baso_below_1_not_auto_scaled(self):
        r = validate_payload({"sex": "male", "baso_pct": 0.3})
        assert not r.has_errors
        assert r.normalised["baso_pct"] == 0.3



class TestPlausibilityErrors:

    def test_negative_hgb_error(self):
        r = validate_payload({"hgb": -5.0, "sex": "male"})
        assert r.has_errors
        assert any(e.field == "hgb" for e in r.errors)

    def test_extreme_wbc_error(self):
        r = validate_payload({"wbc": 1000.0, "sex": "male"})
        normalised_wbc = r.normalised.get("wbc")
        assert normalised_wbc is None or normalised_wbc < 100

    def test_non_numeric_value(self):
        r = validate_payload({"hgb": "not a number"})
        assert r.has_errors

    def test_nan_value_treated_as_missing(self):
        import math
        r = validate_payload({"hgb": float("nan")})
        out = r.normalised.get("hgb")
        if out is not None:
            assert not (isinstance(out, float) and out != out)



class TestRequiredFieldWarnings:

    def test_missing_sex_with_hgb_warns(self):
        r = validate_payload({"hgb": 14.0, "wbc": 7.0})
        assert not r.has_errors
        assert any(w.code == "sex_missing" for w in r.warnings)

    def test_missing_sex_with_no_red_labs_no_warning(self):
        r = validate_payload({"wbc": 7.0})
        assert not r.has_errors
        assert not any(w.code == "sex_missing" for w in r.warnings)

    def test_empty_payload_warns_no_core(self):
        r = validate_payload({"sex": "male"})
        assert not r.has_errors
        assert any(w.code == "no_core_values" for w in r.warnings)
