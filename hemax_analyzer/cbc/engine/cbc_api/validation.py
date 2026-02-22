from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional



PLAUSIBLE_RANGES: dict[str, tuple[float, float, str]] = {
    "wbc":       (0.1,   500.0, "×10⁹/L"),
    "anc":       (0.01,  400.0, "×10⁹/L"),
    "alc":       (0.01,  400.0, "×10⁹/L"),
    "amc":       (0.0,    50.0, "×10⁹/L"),
    "aec":       (0.0,    50.0, "×10⁹/L"),
    "abc":       (0.0,    10.0, "×10⁹/L"),
    "neut_pct":  (0.0,   100.0, "%"),
    "lymph_pct": (0.0,   100.0, "%"),
    "mono_pct":  (0.0,    50.0, "%"),
    "eos_pct":   (0.0,    70.0, "%"),
    "baso_pct":  (0.0,    30.0, "%"),
    "rbc":       (0.5,     8.5, "×10¹²/L"),
    "hgb":       (2.0,    24.0, "g/dL"),
    "hct":       (8.0,    75.0, "%"),
    "mcv":       (40.0,  160.0, "fL"),
    "mch":       (10.0,   50.0, "pg"),
    "mchc":      (20.0,   40.0, "g/dL"),
    "rdw":       (8.0,    40.0, "%"),
    "plt":       (1.0,  3000.0, "×10⁹/L"),
    "mpv":       (4.0,    20.0, "fL"),
}



UNIT_CONFUSION_RULES: dict[str, list[dict]] = {
    "hgb": [
        {
            "min": 40.0, "max": 240.0,
            "factor": 0.1,
            "original_unit": "g/L",
            "target_unit": "g/dL",
        },
    ],
    "mchc": [
        {
            "min": 200.0, "max": 400.0,
            "factor": 0.1,
            "original_unit": "g/L",
            "target_unit": "g/dL",
        },
    ],
    "hct": [
        {
            "min": 0.08, "max": 0.75,
            "factor": 100.0,
            "original_unit": "fraction",
            "target_unit": "%",
        },
    ],
    "plt": [
        {
            "min": 1000.0, "max": 3_000_000.0,
            "factor": 0.001,
            "original_unit": "/µL",
            "target_unit": "×10⁹/L",
        },
    ],
    "wbc": [
        {
            "min": 500.0, "max": 500_000.0,
            "factor": 0.001,
            "original_unit": "/µL",
            "target_unit": "×10⁹/L",
        },
    ],
    "rbc": [
        {
            "min": 500_000.0, "max": 8_500_000.0,
            "factor": 0.000001,
            "original_unit": "/µL",
            "target_unit": "×10¹²/L",
        },
    ],
}


PCT_FIELDS = ("neut_pct", "lymph_pct", "mono_pct", "eos_pct", "baso_pct")



@dataclass
class FieldIssue:
    field: str
    level: str
    code: str
    message_uk: str
    message_en: str
    original_value: Any = None
    corrected_value: Any = None


@dataclass
class ValidationResult:
    normalised: dict
    errors: list[FieldIssue] = field(default_factory=list)
    warnings: list[FieldIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def to_dict(self, lang: str = "uk") -> dict:
        def dump(items):
            return [
                {
                    "field": i.field,
                    "code": i.code,
                    "message": i.message_uk if lang == "uk" else i.message_en,
                    "original_value": i.original_value,
                    "corrected_value": i.corrected_value,
                }
                for i in items
            ]
        return {
            "errors":   dump(self.errors),
            "warnings": dump(self.warnings),
        }



def _as_number(v: Any) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        if isinstance(v, float) and (v != v):
            return None
        return float(v)
    s = str(v).strip()
    if not s:
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _check_unit_confusion(field: str, val: float) -> Optional[dict]:
    for rule in UNIT_CONFUSION_RULES.get(field, []):
        if rule["min"] <= val <= rule["max"]:
            return rule
    return None


def _check_fraction_pct(field: str, val: float) -> bool:
    FRACTION_PRONE_FIELDS = ("neut_pct", "lymph_pct", "mono_pct")
    return field in FRACTION_PRONE_FIELDS and 0.0 < val < 1.0



def _all_pct_fields_are_fractions(payload: dict) -> bool:
    _CHECK = ("neut_pct", "lymph_pct", "mono_pct")
    supplied = [payload.get(f) for f in _CHECK if payload.get(f) is not None]
    if len(supplied) < 2:
        return False
    values = [_as_number(v) for v in supplied]
    if any(v is None for v in values):
        return False
    return all(0.0 < v < 1.0 for v in values)


def validate_payload(payload: dict) -> ValidationResult:
    out_payload = dict(payload)
    errors: list[FieldIssue] = []
    warnings: list[FieldIssue] = []

    skip_fraction_check = _all_pct_fields_are_fractions(payload)

    for fld, (lo, hi, unit) in PLAUSIBLE_RANGES.items():
        raw = payload.get(fld)
        if raw is None:
            continue

        if isinstance(raw, float) and raw != raw:
            out_payload.pop(fld, None)
            warnings.append(FieldIssue(
                field=fld, level="warning", code="nan_dropped",
                message_uk=f"Значення поля '{fld}' — NaN, проігноровано.",
                message_en=f"Value of field '{fld}' is NaN; ignoring.",
                original_value=raw,
            ))
            continue

        v = _as_number(raw)
        if v is None:
            if isinstance(raw, str):
                try:
                    from .units import parse_value_unit  # type: ignore
                    vv, _ = parse_value_unit(raw)
                    if vv is None:
                        errors.append(FieldIssue(
                            field=fld, level="error", code="not_numeric",
                            message_uk=f"Поле '{fld}' має бути числом, отримано: {raw!r}",
                            message_en=f"Field '{fld}' must be a number; got: {raw!r}",
                            original_value=raw,
                        ))
                        continue
                except Exception:
                    errors.append(FieldIssue(
                        field=fld, level="error", code="not_numeric",
                        message_uk=f"Поле '{fld}' має бути числом, отримано: {raw!r}",
                        message_en=f"Field '{fld}' must be a number; got: {raw!r}",
                        original_value=raw,
                    ))
                    continue
            else:
                errors.append(FieldIssue(
                    field=fld, level="error", code="not_numeric",
                    message_uk=f"Поле '{fld}' має бути числом.",
                    message_en=f"Field '{fld}' must be a number.",
                    original_value=raw,
                ))
                continue
            continue

        if not skip_fraction_check and _check_fraction_pct(fld, v):
            corrected = round(v * 100.0, 2)
            out_payload[fld] = corrected
            warnings.append(FieldIssue(
                field=fld, level="warning", code="fraction_as_percent",
                message_uk=(f"Значення {fld}={v} виглядає як частка (0-1). "
                            f"Припускаю, що ви мали на увазі {corrected}%. "
                            f"Перевірте формат у вихідному аналізі."),
                message_en=(f"Value {fld}={v} looks like a fraction (0-1). "
                            f"Assuming you meant {corrected}%. Please verify the source format."),
                original_value=v,
                corrected_value=corrected,
            ))
            v = corrected
        rule = _check_unit_confusion(fld, v)
        if rule is not None:
            corrected = round(v * rule["factor"], 3)
            out_payload[fld] = corrected
            warnings.append(FieldIssue(
                field=fld, level="warning", code="unit_autoconverted",
                message_uk=(f"Значення {fld}={v} схоже на одиниці '{rule['original_unit']}' "
                            f"(типові для українських лабораторій). Автоматично конвертовано "
                            f"у '{rule['target_unit']}': {corrected:g}."),
                message_en=(f"Value {fld}={v} looks like '{rule['original_unit']}' units. "
                            f"Auto-converted to '{rule['target_unit']}': {corrected:g}."),
                original_value=v,
                corrected_value=corrected,
            ))
            v = corrected
            if not (lo <= v <= hi):
                errors.append(FieldIssue(
                    field=fld, level="error", code="out_of_plausible_range",
                    message_uk=(f"Навіть після автоконвертації значення {fld}={v:g} {unit} "
                                f"виходить за фізіологічні межі ({lo:g}–{hi:g} {unit})."),
                    message_en=(f"Even after auto-conversion, {fld}={v:g} {unit} is outside "
                                f"physiological bounds ({lo:g}–{hi:g} {unit})."),
                    original_value=raw, corrected_value=v,
                ))
                continue

        elif not (lo <= v <= hi):
            errors.append(FieldIssue(
                field=fld, level="error", code="out_of_plausible_range",
                message_uk=(f"Значення {fld}={v:g} виходить за фізіологічні межі "
                            f"({lo:g}–{hi:g} {unit}). Перевірте одиниці вимірювання "
                            f"або правильність введення."),
                message_en=(f"Value {fld}={v:g} is outside physiological bounds "
                            f"({lo:g}–{hi:g} {unit}). Please check units and data entry."),
                original_value=raw,
            ))
            continue

    if payload.get("sex") is None and any(
        payload.get(k) is not None for k in ("hgb", "hct", "rbc")
    ):
        warnings.append(FieldIssue(
            field="sex", level="warning", code="sex_missing",
            message_uk=("Не вказано стать. Без неї референтні межі для гемоглобіну, "
                        "гематокриту та еритроцитів будуть менш точними."),
            message_en=("Sex is not provided. Reference ranges for haemoglobin, "
                        "haematocrit and RBC will be less accurate without it."),
        ))

    core = ("hgb", "wbc", "plt", "hct", "rbc")
    if not any(_as_number(payload.get(k)) is not None for k in core):
        if not any(payload.get(k) is not None for k in core):
            warnings.append(FieldIssue(
                field="payload", level="warning", code="no_core_values",
                message_uk=("Жоден з ключових показників (Hb, WBC, PLT, Hct, RBC) "
                            "не надано. Інтерпретація буде обмежена."),
                message_en=("None of the core values (Hb, WBC, PLT, Hct, RBC) were "
                            "provided. Interpretation will be limited."),
            ))

    return ValidationResult(
        normalised=out_payload,
        errors=errors,
        warnings=warnings,
    )
