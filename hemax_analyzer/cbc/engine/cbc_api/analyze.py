from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from .config import CBCConfig, load_config
from .rules import analyze_patterns, make_lab_cards
from .units import (
    parse_value_unit,
    smart_round,
    to_fl,
    to_gdl_hb,
    to_gdl_mchc,
    to_kul,
    to_mul,
    to_pct,
    to_pg,
)



ENGINE_VERSION = "cbc_interpreter_prod_v1_0_max"

DISCLAIMER = (
    "Освітня інтерпретація. Не є медичною консультацією або діагнозом. "
    "При поганому самопочутті або дуже відхилених значеннях зверніться до "
    "лікаря/невідкладної допомоги."
)

_SEVERITY_RANK: Dict[str, int] = {"high": 3, "medium": 2, "low": 1}

_TAG_PRIORITY_DELTA: Dict[str, int] = {
    "urgent":  +50,
    "pattern": +10,
    "derived":  -5,
    "quality": -200,
}

_DIFF_PCT_CODES: Tuple[str, ...] = (
    "neut_pct", "lymph_pct", "mono_pct", "eos_pct", "baso_pct"
)

_PCT_TO_ABS: Dict[str, str] = {
    "neut_pct":  "anc",
    "lymph_pct": "alc",
    "mono_pct":  "amc",
    "eos_pct":   "aec",
    "baso_pct":  "abc",
}

_FRACTION_SUM_TARGET = 1.0
_FRACTION_SUM_TOL = 0.20
_PERCENT_SUM_TARGET = 100.0
_PERCENT_SUM_TOL = 20.0
_FRACTION_VALUE_MAX = 1.5
_FRACTION_SUM_FALLBACK_MAX = 2.0



ALIASES: Dict[str, List[str]] = {
    "sex":       ["sex", "gender", "RIAGENDR", "riagendr"],
    "age":       ["age", "RIDAGEYR", "ridageyr"],

    "wbc":       ["wbc", "WBC", "LBXWBCSI", "lbxwbcsi"],
    "neut_pct":  ["neutrophils_pct", "neut_pct", "NEUT%", "LBXNEPCT", "lbxnepct"],
    "lymph_pct": ["lymphocytes_pct", "lymph_pct", "LYMPH%", "LBXLYPCT", "lbxlypct"],
    "mono_pct":  ["monocytes_pct", "mono_pct", "LBXMOPCT", "lbxmopct"],
    "eos_pct":   ["eosinophils_pct", "eos_pct", "LBXEOPCT", "lbxeopct"],
    "baso_pct":  ["basophils_pct", "baso_pct", "LBXBAPCT", "lbxbapct"],

    "anc":       ["anc", "neutrophils_abs", "LBDNENO", "lbdneno"],
    "alc":       ["alc", "lymphocytes_abs", "LBDLYMNO", "lbdlymno"],
    "amc":       ["amc", "monocytes_abs", "LBDMONO", "lbdmono"],
    "aec":       ["aec", "eosinophils_abs", "LBDEONO", "lbdeono"],
    "abc":       ["abc", "basophils_abs", "LBDBANO", "lbdbano"],

    "rbc":       ["rbc", "RBC", "LBXRBCSI", "lbxrbcsi"],
    "hgb":       ["hgb", "hb", "HGB", "LBXHGB", "lbxhgb"],
    "hct":       ["hct", "HCT", "LBXHCT", "lbxhct"],
    "mcv":       ["mcv", "MCV", "LBXMCVSI", "lbxmcvsi"],
    "mch":       ["mch", "MCH", "LBXMCHSI", "lbxmchsi"],
    "mchc":      ["mchc", "MCHC", "LBXMC", "lbxmc"],
    "rdw":       ["rdw", "RDW", "LBXRDW", "lbxrdw"],

    "plt":       ["platelets", "plt", "PLT", "LBXPLTSI", "lbxpltsi"],
    "mpv":       ["mpv", "MPV", "LBXMPSI", "lbxmpsi"],

    "esr":       ["esr", "ESR", "ШОЕ", "shoe", "SOE"],
}



@dataclass(frozen=True)
class _LabSpec:
    code: str
    converter: Callable[[float, Optional[str]], float]
    canonical_unit: str


_CORE_LABS: Tuple[_LabSpec, ...] = (
    _LabSpec("wbc",  to_kul,       "10^3/µL"),
    _LabSpec("plt",  to_kul,       "10^3/µL"),
    _LabSpec("rbc",  to_mul,       "10^6/µL"),
    _LabSpec("hgb",  to_gdl_hb,    "g/dL"),
    _LabSpec("hct",  to_pct,       "%"),
    _LabSpec("mcv",  to_fl,        "fL"),
    _LabSpec("mch",  to_pg,        "pg"),
    _LabSpec("mchc", to_gdl_mchc,  "g/dL"),
    _LabSpec("rdw",  to_pct,       "%"),
    _LabSpec("mpv",  to_fl,        "fL"),
)



def _get_first(payload: Dict[str, Any], keys: List[str]) -> Any:
    for k in keys:
        if k in payload and payload[k] is not None:
            return payload[k]
    return None


def _get_first_with_key(
    payload: Dict[str, Any],
    keys: List[str],
) -> Tuple[Any, Optional[str]]:
    for k in keys:
        if k in payload and payload[k] is not None:
            return payload[k], k
    return None, None


def _parse_one_lab(
    payload: Dict[str, Any],
    spec: _LabSpec,
    values: Dict[str, Optional[float]],
    field_meta: Dict[str, Dict[str, Any]],
) -> None:
    raw, key = _get_first_with_key(payload, ALIASES[spec.code])
    if raw is None:
        return
    v, u = parse_value_unit(raw)
    values[spec.code] = spec.converter(v, u) if v is not None else None
    field_meta[spec.code] = {
        "source":    "input",
        "input_key": key,
        "raw":       raw if isinstance(raw, (int, float, str)) else str(raw),
        "unit_in":   u,
        "unit":      spec.canonical_unit,
    }


def _parse_esr(
    payload: Dict[str, Any],
    values: Dict[str, Optional[float]],
    field_meta: Dict[str, Dict[str, Any]],
) -> None:
    raw, key = _get_first_with_key(payload, ALIASES["esr"])
    if raw is None:
        return
    try:
        if isinstance(raw, str):
            num_part = "".join(c for c in raw if c.isdigit() or c in ".,")
            num_part = num_part.replace(",", ".")
            values["esr"] = float(num_part) if num_part else None
        else:
            values["esr"] = float(raw)
        field_meta["esr"] = {
            "source":    "input",
            "input_key": key,
            "raw":       raw if isinstance(raw, (int, float, str)) else str(raw),
            "unit_in":   "mm/hr",
            "unit":      "mm/hr",
        }
    except (TypeError, ValueError):
        pass


def _parse_percent_raw(x: Any) -> Optional[float]:
    v, _unit = parse_value_unit(x)
    if v is None:
        return None
    return float(v)


def _normalize_diff_percents(values: Dict[str, Optional[float]]) -> None:
    present = [(c, values.get(c)) for c in _DIFF_PCT_CODES if values.get(c) is not None]
    if not present:
        return

    if len(present) == 1:
        return

    nums = [float(v) for _, v in present if v is not None]
    s = sum(nums)

    def _close(x: float, target: float, tol: float) -> bool:
        return abs(x - target) <= tol

    if _close(s, _FRACTION_SUM_TARGET, _FRACTION_SUM_TOL) and \
       all(0.0 <= n <= _FRACTION_VALUE_MAX for n in nums):
        for c, v in present:
            if v is not None:
                values[c] = v * 100.0
        return

    if _close(s, _PERCENT_SUM_TARGET, _PERCENT_SUM_TOL):
        return

    if s <= _FRACTION_SUM_FALLBACK_MAX and \
       all(0.0 <= n <= _FRACTION_VALUE_MAX for n in nums):
        for c, v in present:
            if v is not None:
                values[c] = v * 100.0


def _compute_normalized_diff_meta(
    values_before: Dict[str, Optional[float]],
    values_after: Dict[str, Optional[float]],
) -> Dict[str, Any]:
    scaled: List[str] = []
    for c in _DIFF_PCT_CODES:
        before = values_before.get(c)
        after = values_after.get(c)
        if before is not None and after is not None and before != after:
            scaled.append(c)
    return {
        "scaled_codes": scaled,
        "rule": "fractions_to_percent" if scaled else "none",
    }


def _sort_lab_cards(labs: List[dict], cfg: CBCConfig) -> List[dict]:
    order = {code: i for i, code in enumerate(cfg.lab_order)}
    LAST = 10 ** 6
    return sorted(labs, key=lambda x: (order.get(x.get("code"), LAST), str(x.get("code"))))


def _sort_signals(signals: List[dict], cfg: CBCConfig) -> List[dict]:
    out: List[dict] = []
    for s in signals:
        sid = str(s.get("id", ""))
        tags = set(s.get("tags") or [])
        base = cfg.signal_priority.get(sid, 0)
        for tag, delta in _TAG_PRIORITY_DELTA.items():
            if tag in tags:
                base += delta
        s["priority"] = base
        out.append(s)

    return sorted(out, key=lambda s: (
        -_SEVERITY_RANK.get(s.get("severity"), 0),
        -(s.get("priority") or 0),
        str(s.get("id")),
    ))


def _build_headline_and_notes(
    signals: List[dict],
    missing_core: List[str],
) -> Tuple[str, List[str]]:
    notes = [s.get("title", s.get("id", "")) for s in signals]

    if missing_core:
        headline = (
            f"Аналіз неповний: відсутні ключові показники ({', '.join(missing_core)}). "
            f"Інтерпретація обмежена."
        )
        return headline, notes

    high = [s for s in signals if s.get("severity") == "high"]
    medium = [s for s in signals if s.get("severity") == "medium"]

    if high:
        titles = "; ".join(s.get("title", s["id"]) for s in high[:2])
        headline = f"Високий пріоритет: {titles}."
    elif medium:
        titles = "; ".join(s.get("title", s["id"]) for s in medium[:2])
        headline = f"Помірні відхилення: {titles}."
    elif signals:
        headline = "Знайдені окремі легкі відхилення."
    else:
        headline = "Відхилень за CBC не виявлено."
    return headline, notes


def _build_combos_and_recs(
    signals: List[dict],
    values: Dict[str, Optional[float]],
) -> Tuple[List[dict], Dict[str, List[dict]]]:
    sig_ids = {s.get("id") for s in signals}
    combos: List[dict] = []
    next_tests: List[dict] = []
    ask_doctor: List[dict] = []

    def _add_test(test: str, why: str, priority: int = 50, when: str = "soon") -> None:
        next_tests.append({"test": test, "why": why, "priority": priority, "when": when})

    def _add_q(question: str, why: str, priority: int = 50) -> None:
        ask_doctor.append({"question": question, "why": why, "priority": priority})

    if "leukocytosis" in sig_ids and "neutrophilia" in sig_ids:
        sev = "high" if any(
            s.get("id") in ("leukocytosis", "neutrophilia") and s.get("severity") == "high"
            for s in signals
        ) else "medium"
        combos.append({
            "id": "bacterial_like_pattern",
            "severity": sev,
            "title": "Комбінація: лейкоцитоз + нейтрофілія",
            "why": (
                "Такий патерн часто буває при бактеріальному запаленні/стресі/"
                "кортикостероїдах, але потребує клінічного контексту."
            ),
            "evidence": {
                "wbc": values.get("wbc"),
                "neut_pct": values.get("neut_pct"),
                "anc": values.get("anc"),
            },
            "next": ["Оцініть симптоми (температура, біль, кашель), ліки, нещодавні інфекції."],
            "tags": ["combo", "wbc"],
        })
        _add_test("CRP або hs-CRP",
                  "Може допомогти оцінити запалення разом із клінікою.", 55)
        _add_test("Повтор CBC через 24–72 год (або за призначенням)",
                  "Перевірка динаміки, особливо якщо симптоми.", 60)
        _add_q("Чи потрібні додаткові обстеження/антибіотики, чи достатньо спостереження?",
               "Комбінація потребує контексту симптомів та огляду.", 55)

    if "lymphocytosis" in sig_ids and "neutrophilia" not in sig_ids:
        combos.append({
            "id": "viral_like_pattern",
            "severity": "low",
            "title": "Комбінація: відносний лімфоцитоз",
            "why": (
                "Часто зустрічається при вірусних інфекціях або відновленні після них; "
                "важливі симптоми та повтор у динаміці."
            ),
            "evidence": {
                "wbc": values.get("wbc"),
                "lymph_pct": values.get("lymph_pct"),
                "alc": values.get("alc"),
            },
            "next": ["Якщо є симптоми або тривале відхилення — обговоріть з лікарем."],
            "tags": ["combo", "wbc"],
        })

    if "neutropenia" in sig_ids:
        _add_test("Повтор CBC + мазок периферичної крові",
                  "Підтвердження нейтропенії та оцінка морфології.", 80)
        _add_q("Чи є ознаки інфекції/лихоманка і чи потрібна термінова оцінка?",
               "Низькі нейтрофіли підвищують ризик інфекцій.", 85)

    if "anemia_possible" in sig_ids or "microcytic_anemia_pattern" in sig_ids:
        _add_test("Феритин, залізо, TIBC/TSAT",
                  "Уточнення дефіциту заліза/анемії.", 70)
        _add_q("Яка ймовірна причина анемії і чи потрібні додаткові обстеження "
               "(харчування/втрати/ШКТ)?",
               "Причину важливо знайти.", 60)

    if "macrocytic_anemia_pattern" in sig_ids:
        _add_test("Вітамін B12 та фолати", "Часті причини макроцитозу.", 70)
        _add_test("TSH", "Гіпотиреоз може впливати на MCV.", 40)

    if "thrombocytopenia" in sig_ids:
        _add_test("Повтор CBC у пробірці з цитратом (за потреби)",
                  "Виключити псевдотромбоцитопенію через злипання.", 80)
        _add_test("Мазок периферичної крові",
                  "Оцінка тромбоцитів та інших ліній крові.", 70)
        _add_q("Чи можуть ліки/інфекція/аутоімунні причини пояснювати низькі тромбоцити?",
               "Потребує клінічного контексту.", 60)

    if "thrombocytosis" in sig_ids:
        _add_test("CRP/феритин (за контекстом)",
                  "Тромбоцитоз часто реактивний (запалення/дефіцит заліза).", 45)

    if "pancytopenia_pattern" in sig_ids:
        _add_test("Повтор CBC + мазок", "Підтвердження та оцінка морфології.",
                  90, when="now")
        _add_q("Чи потрібна термінова консультація гематолога?",
               "Панцитопенія може потребувати швидкої оцінки.", 95)

    next_tests.sort(key=lambda x: (-x.get("priority", 0), x.get("test", "")))
    ask_doctor.sort(key=lambda x: (-x.get("priority", 0), x.get("question", "")))

    return combos, {"next_tests": next_tests, "ask_doctor": ask_doctor}



def analyze_cbc_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    sex = _get_first(payload, ALIASES["sex"])
    age_raw = _get_first(payload, ALIASES["age"])
    age: Optional[float] = None
    if age_raw is not None:
        try:
            age = float(age_raw)
        except (TypeError, ValueError):
            age = None

    refs_override = payload.get("ref_ranges") or payload.get("ref")
    cfg = load_config(payload)

    values: Dict[str, Optional[float]] = {}
    field_meta: Dict[str, Dict[str, Any]] = {}

    for spec in _CORE_LABS:
        _parse_one_lab(payload, spec, values, field_meta)

    for code in _DIFF_PCT_CODES:
        raw, key = _get_first_with_key(payload, ALIASES[code])
        if raw is not None:
            v = _parse_percent_raw(raw)
            values[code] = v
            field_meta[code] = {
                "source":    "input",
                "input_key": key,
                "raw":       raw if isinstance(raw, (int, float, str)) else str(raw),
                "unit_in":   "%",
                "unit":      "%",
            }

    values_before_diff = {c: values.get(c) for c in _DIFF_PCT_CODES}
    _normalize_diff_percents(values)
    normalized_diff = _compute_normalized_diff_meta(values_before_diff, values)

    computed_abs: List[str] = []
    for abs_code in ("anc", "alc", "amc", "aec", "abc"):
        raw, key = _get_first_with_key(payload, ALIASES[abs_code])
        if raw is not None:
            v, u = parse_value_unit(raw)
            values[abs_code] = to_kul(v, u) if v is not None else None
            field_meta[abs_code] = {
                "source":    "input",
                "input_key": key,
                "raw":       raw if isinstance(raw, (int, float, str)) else str(raw),
                "unit_in":   u,
                "unit":      "10^3/µL",
            }

    wbc = values.get("wbc")
    if wbc is not None:
        for pct_code, abs_code in _PCT_TO_ABS.items():
            if values.get(abs_code) is None and values.get(pct_code) is not None:
                derived_val = wbc * values[pct_code] / 100.0
                values[abs_code] = smart_round(derived_val, 3)
                field_meta[abs_code] = {
                    "source":    "derived",
                    "input_key": None,
                    "raw":       None,
                    "unit_in":   None,
                    "unit":      "10^3/µL",
                    "formula":   f"{pct_code} × wbc / 100",
                }
                computed_abs.append(abs_code)

    _parse_esr(payload, values, field_meta)

    patient_context = payload.get("context") if isinstance(payload.get("context"), dict) else None
    refs_override_dict = refs_override if isinstance(refs_override, dict) else None
    flags, derived, signals_raw = analyze_patterns(
        values=values,
        sex=sex,
        age=age,
        refs_override=refs_override_dict,
        config=cfg,
        patient_context=patient_context,
    )

    lab_cards = make_lab_cards(
        values=values,
        sex=sex,
        age=age,
        refs_override=refs_override_dict,
        field_meta=field_meta,
    )
    lab_cards = _sort_lab_cards(lab_cards, cfg)

    signals = _sort_signals(signals_raw, cfg)
    severe = [s for s in signals if s.get("severity") == "high"]
    medium = [s for s in signals if s.get("severity") == "medium"]
    missing_core = [k for k in ("wbc", "hgb", "plt") if values.get(k) is None]

    headline, notes = _build_headline_and_notes(signals, missing_core)
    combos, recommendations = _build_combos_and_recs(signals, values)

    return {
        "version": ENGINE_VERSION,
        "profile": {"sex": sex, "age": age},
        "meta": {
            "field_meta":      field_meta,
            "computed_abs":    computed_abs,
            "normalized_diff": normalized_diff,
            "missing_core":    missing_core,
            "context":         {"clinical": patient_context or {}},
        },
        "summary": {
            "headline":       headline,
            "signals_high":   len(severe),
            "signals_medium": len(medium),
            "notes":          notes,
        },
        "labs":            lab_cards,
        "flags":           flags,
        "derived":         derived,
        "signals":         signals,
        "combos":          combos,
        "recommendations": recommendations,
        "disclaimer":      DISCLAIMER,
    }
