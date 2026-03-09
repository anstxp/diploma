from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from .config import ChemConfig
from .knowledge import LABS
from .rules import analyze_patterns
from .spec import RefRange
from .units import (
    parse_value_unit,
    to_gdl,
    to_mgdl_bilirubin,
    to_mgdl_bun,
    to_mgdl_calcium,
    to_mgdl_chol,
    to_mgdl_creatinine,
    to_mgdl_glucose,
    to_mgdl_magnesium,
    to_mgdl_phosphate,
    to_mgdl_trig,
    to_mgdl_uric,
    to_mgdl_urea,
    to_mgl_crp,
    to_mmolL,
    to_pct,
    to_ugdl_iron,
)



ENGINE_VERSION = "chem_interpreter_prod_v1_2_max"

DISCLAIMER = (
    "Освітня інтерпретація. Не є медичною консультацією. При симптомах "
    "або різко відхилених значеннях зверніться до лікаря/невідкладної допомоги."
)

_RESPONSE_NOTES: Tuple[str, ...] = (
    "Це освітня інтерпретація, не діагноз.",
    "Точні референси залежать від лабораторії. За можливості передайте "
    "ref_ranges з бланку.",
    "Окремі показники (глюкоза, ліпіди) важливо інтерпретувати з урахуванням "
    "натще/ненатще.",
)

_SEVERITY_RANK: Dict[str, int] = {"high": 3, "medium": 2, "low": 1}

_DERIVED_CODES: frozenset[str] = frozenset({
    "non_hdl", "tc_hdl_ratio", "tg_hdl_ratio", "ast_alt_ratio",
    "anion_gap", "globulin", "ag_ratio", "calcium_corrected",
})

_DERIVED_NAMES: Dict[str, str] = {
    "egfr":              "eGFR (CKD-EPI 2021)",
    "non_hdl":           "Non-HDL холестерин",
    "tc_hdl_ratio":      "TC/HDL (коеф.)",
    "tg_hdl_ratio":      "TG/HDL (коеф.)",
    "ast_alt_ratio":     "AST/ALT (коеф.)",
    "anion_gap":         "Аніонна щілина",
    "globulin":          "Глобуліни (обчислено)",
    "ag_ratio":          "A/G ratio (обчислено)",
    "calcium_corrected": "Кальцій скоригований (обчислено)",
}

_TRUE_TOKENS = frozenset({"1", "true", "yes", "y", "так", "да"})
_FALSE_TOKENS = frozenset({"0", "false", "no", "n", "ні", "нет"})



ALIASES: Dict[str, List[str]] = {
    "sex": ["sex", "gender", "RIAGENDR", "riagendr"],
    "age": ["age", "RIDAGEYR", "ridageyr"],

    "glucose": ["glucose", "glu", "LBXGLU", "lbxglu", "glucose_mgdl"],
    "a1c":     ["a1c", "hba1c", "hbA1c", "LBXGH", "lbxgh", "a1c_pct"],

    "creatinine": ["creatinine", "scr", "LBXSCR", "lbxscr", "creatinine_mgdl"],
    "urea":       ["urea", "urea_mgdl", "urea_mgdL", "urea_mg/dl"],
    "bun":        ["bun", "BUN", "bun_mgdl", "LBXSCBUN", "lbxs cbun"],

    "alt": ["alt", "ALT", "lbxsat", "LBXSAT", "SGPT"],
    "ast": ["ast", "AST", "lbxsas", "LBXSAS", "SGOT"],
    "alp": ["alp", "ALP", "alk_phos", "alkaline_phosphatase"],
    "ggt": ["ggt", "GGT", "gamma_gt"],

    "bilirubin_total":  ["bilirubin_total", "bilirubin", "tbil", "LBXSTB", "lbxstb"],
    "bilirubin_direct": ["bilirubin_direct", "dbil", "direct_bilirubin"],

    "albumin":       ["albumin", "alb", "LBDSAL", "lbdsal"],
    "total_protein": ["total_protein", "protein_total", "tp", "LBXSTP", "lbxstp"],

    "tchol":  ["tchol", "total_cholesterol", "cholesterol_total",
               "cholesterol", "LBXTC", "lbxtc"],
    "hdl":    ["hdl", "LBXHDD", "lbxhdd", "LBXHDL", "lbxhdl"],
    "ldl":    ["ldl", "LBDLDL", "lbdldl", "ldl_calc"],
    "trigly": ["trigly", "triglycerides", "LBXTR", "lbxtr"],

    "crp": ["crp", "hscrp", "LBXCRP", "lbxcrp"],

    "sodium":      ["sodium", "na", "LBXSNA", "lbxsna"],
    "potassium":   ["potassium", "k", "LBXSKSI", "lbxsk"],
    "chloride":    ["chloride", "cl"],
    "bicarbonate": ["bicarbonate", "co2", "tco2", "hco3"],

    "calcium":   ["calcium", "ca"],
    "magnesium": ["magnesium", "mg"],
    "phosphate": ["phosphate", "phos", "phosphorus", "p"],

    "iron":     ["iron", "fe"],
    "ferritin": ["ferritin", "fer"],
    "tibc":     ["tibc", "TIBC"],
    "tsat":     ["tsat", "transferrin_saturation", "sat"],

    "uric_acid": ["uric_acid", "uric", "ua"],

    "amylase": ["amylase", "amy"],
    "lipase":  ["lipase", "lip"],
    "ck":      ["ck", "cpk", "creatine_kinase"],
    "ldh":     ["ldh", "lactate_dehydrogenase"],

    "vitd_25oh": ["vitd", "vitamin_d", "25ohd", "vitd_25oh"],

    "egfr":          ["egfr", "gfr", "egfr_ckd", "estimated_gfr"],
    "fasting_hours": ["fasting_hours", "fastingHours", "fasting",
                      "hours_fasting", "fasting_h"],
    "fasting_8h":    ["fasting_8h", "fasting8h", "fasting_ok_8h",
                      "fasting_ok", "fasting>=8h"],
}



@dataclass(frozen=True)
class _LabSpec:
    code: str
    converter: Callable[[float, Optional[str]], float]
    canonical_unit: str


def _no_op(v: float, u: Optional[str]) -> float:
    return float(v)


_CORE_LABS: Tuple[_LabSpec, ...] = (
    _LabSpec("glucose",          to_mgdl_glucose,    "mg/dL"),
    _LabSpec("a1c",              _no_op,             "%"),
    _LabSpec("creatinine",       to_mgdl_creatinine, "mg/dL"),
    _LabSpec("urea",             to_mgdl_urea,       "mg/dL"),
    _LabSpec("bun",              to_mgdl_bun,        "mg/dL"),
    _LabSpec("alt",              _no_op,             "U/L"),
    _LabSpec("ast",              _no_op,             "U/L"),
    _LabSpec("alp",              _no_op,             "U/L"),
    _LabSpec("ggt",              _no_op,             "U/L"),
    _LabSpec("bilirubin_total",  to_mgdl_bilirubin,  "mg/dL"),
    _LabSpec("bilirubin_direct", to_mgdl_bilirubin,  "mg/dL"),
    _LabSpec("albumin",          to_gdl,             "g/dL"),
    _LabSpec("total_protein",    to_gdl,             "g/dL"),
    _LabSpec("tchol",            to_mgdl_chol,       "mg/dL"),
    _LabSpec("hdl",              to_mgdl_chol,       "mg/dL"),
    _LabSpec("ldl",              to_mgdl_chol,       "mg/dL"),
    _LabSpec("trigly",           to_mgdl_trig,       "mg/dL"),
    _LabSpec("crp",              to_mgl_crp,         "mg/L"),
    _LabSpec("sodium",           to_mmolL,           "mmol/L"),
    _LabSpec("potassium",        to_mmolL,           "mmol/L"),
    _LabSpec("chloride",         to_mmolL,           "mmol/L"),
    _LabSpec("bicarbonate",      to_mmolL,           "mmol/L"),
    _LabSpec("calcium",          to_mgdl_calcium,    "mg/dL"),
    _LabSpec("magnesium",        to_mgdl_magnesium,  "mg/dL"),
    _LabSpec("phosphate",        to_mgdl_phosphate,  "mg/dL"),
    _LabSpec("iron",             to_ugdl_iron,       "µg/dL"),
    _LabSpec("ferritin",         _no_op,             "ng/mL"),
    _LabSpec("tibc",             to_ugdl_iron,       "µg/dL"),
    _LabSpec("tsat",             to_pct,             "%"),
    _LabSpec("uric_acid",        to_mgdl_uric,       "mg/dL"),
    _LabSpec("amylase",          _no_op,             "U/L"),
    _LabSpec("lipase",           _no_op,             "U/L"),
    _LabSpec("ck",               _no_op,             "U/L"),
    _LabSpec("ldh",              _no_op,             "U/L"),
    _LabSpec("vitd_25oh",        _no_op,             "ng/mL"),
)



def _get_first_with_key(
    payload: Dict[str, Any],
    keys: List[str],
) -> Tuple[Any, Optional[str]]:
    for k in keys:
        if k in payload and payload[k] is not None:
            return payload[k], k
    return None, None


def _sex_norm(sex: Optional[str]) -> Optional[str]:
    if sex is None:
        return None
    s = str(sex).strip().lower()
    if s in ("m", "male", "man", "чоловік", "чоловiк"):
        return "male"
    if s in ("f", "female", "woman", "жінка", "жiнка"):
        return "female"
    return s or None


def _coerce_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    s = str(value).strip().lower()
    if s in _TRUE_TOKENS:
        return True
    if s in _FALSE_TOKENS:
        return False
    return None


def _coerce_age(raw: Any) -> Optional[float]:
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None



def _parse_one_lab(
    payload: Dict[str, Any],
    spec: _LabSpec,
    values: Dict[str, Optional[float]],
    field_meta: Dict[str, Dict[str, Any]],
) -> None:
    raw, key = _get_first_with_key(payload, ALIASES.get(spec.code, [spec.code]))
    if raw is None:
        return
    v, u = parse_value_unit(raw)
    converted = spec.converter(v, u) if v is not None else None
    if converted is not None and converted < 0:
        converted = None
    values[spec.code] = converted
    field_meta[spec.code] = {
        "source":    "input",
        "input_key": key,
        "raw":       raw if isinstance(raw, (int, float, str)) else str(raw),
        "unit_in":   u,
        "unit":      spec.canonical_unit,
    }


def _parse_fasting_context(payload: Dict[str, Any]) -> Dict[str, Any]:
    hours_raw, hours_key = _get_first_with_key(payload, ALIASES.get("fasting_hours", []))
    eight_raw, eight_key = _get_first_with_key(payload, ALIASES.get("fasting_8h", []))

    fasting_hours: Optional[float] = None
    if hours_raw is not None:
        try:
            fasting_hours = float(hours_raw)
        except (TypeError, ValueError):
            pass

    fasting_8h: Optional[bool] = _coerce_bool(eight_raw) if eight_raw is not None else None
    if fasting_8h is None and fasting_hours is not None:
        fasting_8h = fasting_hours >= 8.0

    return {
        "fasting_hours": fasting_hours,
        "fasting_8h":    fasting_8h,
        "fasting_input": {
            "fasting_hours_key": hours_key,
            "fasting_8h_key":    eight_key,
        },
    }


def _parse_clinical_context(payload: Dict[str, Any]) -> Dict[str, bool]:
    raw = payload.get("clinical_context")
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, bool] = {}
    for k, v in raw.items():
        b = _coerce_bool(v)
        if b is not None:
            out[k] = b
    return out



def _set_computed(
    values: Dict[str, Optional[float]],
    field_meta: Dict[str, Dict[str, Any]],
    computed: List[str],
    code: str,
    value: Optional[float],
    computed_from: List[str],
    formula: str,
    unit: str,
) -> None:
    if value is None:
        return
    values[code] = value
    computed.append(code)
    field_meta[code] = {
        "source":        "computed",
        "computed_from": computed_from,
        "formula":       formula,
        "unit":          unit,
        "unit_in":       None,
    }


def _compute_derived(
    payload: Dict[str, Any],
    sex: Optional[str],
    age: Optional[float],
    values: Dict[str, Optional[float]],
    field_meta: Dict[str, Dict[str, Any]],
    computed: List[str],
) -> None:
    set_c = lambda code, v, src, formula, unit: _set_computed(
        values, field_meta, computed, code, v, src, formula, unit
    )

    tchol = values.get("tchol")
    hdl   = values.get("hdl")
    trigly = values.get("trigly")
    ldl   = values.get("ldl")

    if tchol is not None and hdl is not None:
        set_c("non_hdl", tchol - hdl, ["tchol", "hdl"],
              "non_hdl = tchol - hdl", "mg/dL")

    if ldl is None and tchol is not None and hdl is not None \
       and trigly is not None and trigly < 400:
        set_c("ldl", tchol - hdl - trigly / 5.0,
              ["tchol", "hdl", "trigly"],
              "ldl = tchol - hdl - (trigly/5)", "mg/dL")

    if tchol is not None and hdl is not None and hdl > 0:
        set_c("tc_hdl_ratio", tchol / hdl, ["tchol", "hdl"],
              "tc_hdl_ratio = tchol/hdl", "ratio")

    if trigly is not None and hdl is not None and hdl > 0:
        set_c("tg_hdl_ratio", trigly / hdl, ["trigly", "hdl"],
              "tg_hdl_ratio = trigly/hdl", "ratio")

    ast, alt = values.get("ast"), values.get("alt")
    if ast is not None and alt is not None and alt > 0:
        set_c("ast_alt_ratio", ast / alt, ["ast", "alt"],
              "ast_alt_ratio = ast/alt", "ratio")

    egfr_raw, egfr_key = _get_first_with_key(payload, ALIASES.get("egfr", ["egfr"]))
    scr = values.get("creatinine")
    if egfr_raw is not None:
        egfr_val: Optional[float] = None
        if isinstance(egfr_raw, (int, float)):
            egfr_val = float(egfr_raw)
        elif isinstance(egfr_raw, str):
            num, _u = parse_value_unit(egfr_raw)
            if num is not None:
                egfr_val = float(num)
        if egfr_val is not None and egfr_val > 0:
            values["egfr"] = egfr_val
            field_meta["egfr"] = {
                "source":        "input",
                "input_key":     egfr_key or "egfr",
                "raw":           egfr_raw,
                "unit_in":       "mL/min/1.73m²",
                "unit":          "mL/min/1.73m²",
                "computed_from": None,
                "formula":       None,
            }
    elif scr is not None and age is not None \
         and sex in ("male", "female") and scr > 0 and age > 0:
        kappa     = 0.7 if sex == "female" else 0.9
        alpha     = -0.241 if sex == "female" else -0.302
        min_part  = min(scr / kappa, 1.0) ** alpha
        max_part  = max(scr / kappa, 1.0) ** -1.200
        sex_factor = 1.012 if sex == "female" else 1.0
        egfr = 142 * min_part * max_part * (0.9938 ** float(age)) * sex_factor
        set_c("egfr", egfr, ["creatinine", "age", "sex"],
              "CKD-EPI 2021", "mL/min/1.73m²")

    na, cl, hco3 = values.get("sodium"), values.get("chloride"), values.get("bicarbonate")
    if na is not None and cl is not None and hco3 is not None:
        set_c("anion_gap", na - (cl + hco3),
              ["sodium", "chloride", "bicarbonate"],
              "anion_gap = Na - (Cl + HCO3)", "mmol/L")

    ca, alb = values.get("calcium"), values.get("albumin")
    if ca is not None and alb is not None:
        set_c("calcium_corrected", ca + 0.8 * (4.0 - alb),
              ["calcium", "albumin"],
              "corr_Ca = Ca + 0.8*(4 - albumin)", "mg/dL")

    tp = values.get("total_protein")
    if tp is not None and alb is not None:
        glob = tp - alb
        set_c("globulin", glob, ["total_protein", "albumin"],
              "globulin = total_protein - albumin", "g/dL")
        if glob > 0:
            set_c("ag_ratio", alb / glob, ["albumin", "globulin"],
                  "ag_ratio = albumin / globulin", "ratio")

    iron, tibc = values.get("iron"), values.get("tibc")
    if iron is not None and tibc is not None and tibc > 0 \
       and "tsat" not in values:
        set_c("tsat", 100.0 * iron / tibc,
              ["iron", "tibc"], "tsat = 100 * iron / tibc", "%")



def _build_lab_cards(
    values: Dict[str, Optional[float]],
    field_meta: Dict[str, Dict[str, Any]],
    sex: Optional[str],
    cfg: ChemConfig,
    refs_override: Optional[Dict[str, Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    order = {c: i for i, c in enumerate(cfg.lab_order)}
    labs: List[Dict[str, Any]] = []

    for code in sorted(values.keys(), key=lambda c: (order.get(c, 10_000), c)):
        if code not in LABS and code not in _DERIVED_CODES:
            continue
        v = values.get(code)
        if v is None:
            continue

        if code in LABS:
            lab = LABS[code]
            rr = lab.ref_for(sex)
            name = lab.name
            unit = lab.unit
            what = lab.what
            tips = list(lab.tips)
        else:
            rr   = RefRange()
            name = _DERIVED_NAMES.get(code, code)
            unit = field_meta.get(code, {}).get("unit", "")
            what = "Похідний показник (обчислено з інших значень)."
            tips = ["Дивіться вихідні показники, з яких він розрахований."]

        if refs_override and code in refs_override:
            ov = refs_override[code] or {}
            lo_ov, hi_ov = ov.get("low"), ov.get("high")
            base_low  = rr.low  if isinstance(rr, RefRange) else None
            base_high = rr.high if isinstance(rr, RefRange) else None
            rr = RefRange(
                low=float(lo_ov) if lo_ov is not None else base_low,
                high=float(hi_ov) if hi_ov is not None else base_high,
            )

        v_cmp = round(float(v), 2) if isinstance(v, (int, float)) else v
        flag: Optional[str] = None
        if rr.low is not None and v_cmp < rr.low:
            flag = "low"
        if rr.high is not None and v_cmp > rr.high:
            flag = "high"

        labs.append({
            "code":          code,
            "name":          name,
            "value":         round(float(v), 4) if isinstance(v, (int, float)) else v,
            "unit":          unit,
            "ref":           {"low": rr.low, "high": rr.high},
            "flag":          flag,
            "what":          what,
            "tips":          tips,
            "source":        field_meta.get(code, {}).get("source", "input"),
            "input_key":     field_meta.get(code, {}).get("input_key"),
            "computed_from": field_meta.get(code, {}).get("computed_from"),
            "formula":       field_meta.get(code, {}).get("formula"),
            "unit_in":       field_meta.get(code, {}).get("unit_in"),
            "ref_source":    "override" if (refs_override and code in refs_override)
                              else "default",
        })

    return labs



def _sort_signals(signals: List[dict], cfg: ChemConfig) -> List[dict]:
    pr = cfg.signal_priority
    def _key(s: Dict[str, Any]) -> tuple:
        return (
            -pr.get(s.get("id", ""), 0),
            -_SEVERITY_RANK.get(s.get("severity", "low"), 0),
            s.get("id", ""),
        )
    return sorted(signals, key=_key)


def _build_headline(signals: List[dict]) -> Tuple[str, dict]:
    severe  = [s for s in signals if s.get("severity") == "high"
               and "quality" not in (s.get("tags") or [])]
    medium  = [s for s in signals if s.get("severity") == "medium"
               and "quality" not in (s.get("tags") or [])]
    low     = [s for s in signals if s.get("severity") == "low"
               and "quality" not in (s.get("tags") or [])]
    quality = [s for s in signals if "quality" in (s.get("tags") or [])]

    if quality and not (severe or medium or low):
        headline = "Недостатньо даних для повної інтерпретації біохімії."
    elif severe:
        headline = "Є сигнали високого пріоритету — бажано обговорити з лікарем."
    elif medium:
        headline = ("Є відхилення, які варто розібрати в контексті та (за потреби) "
                    "повторити аналіз/обговорити з лікарем.")
    elif low:
        headline = ("Є незначні відхилення; варто врахувати контекст і, "
                    "за потреби, перевірити в динаміці.")
    else:
        headline = "Значних відхилень не виявлено за введеними даними."

    return headline, {
        "severe":  severe,
        "medium":  medium,
        "low":     low,
        "quality": quality,
    }



def analyze_chem_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    cfg = ChemConfig()

    sex_raw, _ = _get_first_with_key(payload, ALIASES["sex"])
    age_raw, _ = _get_first_with_key(payload, ALIASES["age"])
    sex = _sex_norm(sex_raw) if sex_raw is not None else None
    age = _coerce_age(age_raw)

    context: Dict[str, Any] = _parse_fasting_context(payload)
    context["clinical"] = _parse_clinical_context(payload)

    values: Dict[str, Optional[float]] = {}
    field_meta: Dict[str, Dict[str, Any]] = {}
    for spec in _CORE_LABS:
        _parse_one_lab(payload, spec, values, field_meta)

    computed: List[str] = []
    _compute_derived(payload, sex, age, values, field_meta, computed)

    refs_override = payload.get("ref_ranges") if isinstance(payload.get("ref_ranges"), dict) else None

    flags, derived, signals, combos, recs = analyze_patterns(
        values, sex=sex, age=age,
        refs_override=refs_override, config=cfg, context=context,
    )
    signals = _sort_signals(signals, cfg)

    labs = _build_lab_cards(values, field_meta, sex, cfg, refs_override)
    headline, sev_buckets = _build_headline(signals)

    missing_core: List[str] = []
    if sev_buckets["quality"]:
        evidence = sev_buckets["quality"][0].get("evidence") or {}
        missing_core = list(evidence.get("missing") or [])

    return {
        "version": ENGINE_VERSION,
        "profile": {"sex": sex, "age": age},
        "meta": {
            "field_meta":   field_meta,
            "computed":     computed,
            "context":      context,
            "missing_core": missing_core,
        },
        "summary": {
            "headline":       headline,
            "signals_high":   len(sev_buckets["severe"]),
            "signals_medium": len(sev_buckets["medium"]),
            "notes":          list(_RESPONSE_NOTES),
        },
        "labs":            labs,
        "flags":           flags,
        "derived":         derived,
        "signals":         signals,
        "combos":          combos,
        "recommendations": recs,
        "disclaimer":      DISCLAIMER,
    }
