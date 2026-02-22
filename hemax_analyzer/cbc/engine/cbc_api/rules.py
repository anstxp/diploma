from __future__ import annotations

from dataclasses import asdict

def smart_round(val, digits=3):
    if val is None:
        return None
    return round(float(val), digits)

from typing import Any, Dict, List, Optional, Tuple

from .knowledge import LABS, ABS_REFS, RefRange
from .pediatric_refs import get_pediatric_ref, get_pediatric_abs_ref
from .config import CBCConfig, SeverityBand
from .units import smart_round

try:
    from .empirical_refs_loader import EmpiricalConfig  # type: ignore
    _empirical_singleton: "EmpiricalConfig | None" = EmpiricalConfig.try_load_from_env()
except Exception:
    _empirical_singleton = None


def reload_empirical_config() -> "EmpiricalConfig | None":
    global _empirical_singleton
    try:
        from .empirical_refs_loader import EmpiricalConfig  # type: ignore
        _empirical_singleton = EmpiricalConfig.try_load_from_env()
    except Exception:
        _empirical_singleton = None
    return _empirical_singleton


def empirical_active() -> bool:
    return _empirical_singleton is not None

def _flag(value: Optional[float], rr: RefRange) -> Optional[str]:
    if value is None:
        return None
    if rr.low is not None and value < rr.low:
        return "low"
    if rr.high is not None and value > rr.high:
        return "high"
    return "normal"

def _signal(
    id: str,
    severity: str,
    title: str,
    why: str,
    next_steps: List[str],
    evidence: Dict[str, Any],
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    s = {
        "id": id,
        "severity": severity,
        "title": title,
        "why": why,
        "next": next_steps,
        "evidence": evidence,
    }
    if tags:
        s["tags"] = tags
    return s

def _severity_by_value(
    value: Optional[float],
    mild_high: float,
    moderate_high: float,
    severe_high: float,
    mild_low: float,
    moderate_low: float,
    severe_low: float,
) -> Optional[str]:
    if value is None:
        return None
    if value >= severe_high or value <= severe_low:
        return "high"
    if value >= moderate_high or value <= moderate_low:
        return "medium"
    if value >= mild_high or value <= mild_low:
        return "low"
    return None


def _sev_high(value: Optional[float], band: SeverityBand) -> Optional[str]:
    if value is None:
        return None
    if value >= band.severe:
        return "high"
    if value >= band.moderate:
        return "medium"
    if value >= band.mild:
        return "low"
    return None

def _sev_low(value: Optional[float], band: SeverityBand) -> Optional[str]:
    if value is None:
        return None
    if value < band.severe:
        return "high"
    if value < band.moderate:
        return "medium"
    return "low"

def _sex_norm(sex: Optional[str]) -> Optional[str]:
    if sex is None:
        return None
    s = str(sex).strip().lower()
    if s in {"f", "female", "woman", "ж", "жінка"}:
        return "female"
    if s in {"m", "male", "man", "ч", "чоловік"}:
        return "male"
    return None

def _get_ref(
    code: str,
    sex: Optional[str],
    age: Optional[float],
    override: Optional[Dict[str, Dict[str, float]]] = None,
) -> RefRange:
    if override and code in override:
        o = override[code]
        return RefRange(low=o.get("low"), high=o.get("high"))
    sx = _sex_norm(sex)

    ped = get_pediatric_ref(code, age, sx)
    if ped is not None:
        return ped

    if _empirical_singleton is not None and age is not None and age >= 18.0:
        emp = _empirical_singleton.get_ref(code, sx, age)
        if emp is not None:
            return emp

    lab = LABS.get(code)
    if lab is None:
        return RefRange()
    return lab.ref_female if sx == "female" else lab.ref_male

def _get_abs_ref(
    code: str,
    sex: Optional[str],
    age: Optional[float],
    override_abs: Optional[Dict[str, Dict[str, float]]] = None,
) -> RefRange:
    if override_abs and code in override_abs:
        o = override_abs[code]
        return RefRange(low=o.get("low"), high=o.get("high"))

    sx = _sex_norm(sex)
    ped = get_pediatric_abs_ref(code, age, sx)
    if ped is not None:
        return ped

    return ABS_REFS.get(code, RefRange())

def _ref_source(code: str, sex: Optional[str], age: Optional[float], override: Optional[Dict[str, Dict[str, float]]]) -> str:
    if override and code in override:
        return "override"
    sx = _sex_norm(sex)
    ped = get_pediatric_ref(code, age, sx)
    if ped is not None:
        return "pediatric"
    if _empirical_singleton is not None and age is not None and age >= 18.0:
        if _empirical_singleton.get_ref(code, sx, age) is not None:
            return "empirical"
    return "default" if code in LABS else "missing"

def _abs_ref_source(code: str, sex: Optional[str], age: Optional[float], override_abs: Optional[Dict[str, Dict[str, float]]]) -> str:
    if override_abs and code in override_abs:
        return "override"
    sx = _sex_norm(sex)
    ped = get_pediatric_abs_ref(code, age, sx)
    if ped is not None:
        return "pediatric"
    return "default" if code in ABS_REFS else "missing"

def make_lab_cards(
    values: Dict[str, Optional[float]],
    sex: Optional[str],
    age: Optional[float],
    refs_override: Optional[Dict[str, Dict[str, float]]],
    field_meta: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    cards: List[Dict[str, Any]] = []
    for code, lab in LABS.items():
        if code not in values:
            continue
        v = values.get(code)
        rr = _get_ref(code, sex, age, refs_override)
        fl = _flag(v, rr)
        if v is None:
            continue
        interp: List[str] = []
        if fl == "low":
            interp.extend(lab.low_means)
        elif fl == "high":
            interp.extend(lab.high_means)
        else:
            interp.append("В межах типового референсу (за умови коректних референсів вашої лабораторії).")
        cards.append({
            "code": code,
            "name": lab.name_uk,
            "value": smart_round(v, 3),
            "unit": lab.unit,
            "ref": {"low": rr.low, "high": rr.high},
            "flag": fl,
            "what": lab.what,
            "interpretation": interp,
            "tips": lab.tips,
            "caveats": lab.caveats,
        })
    abs_names = {
        "anc": "Нейтрофіли, абсолютні (ANC)",
        "alc": "Лімфоцити, абсолютні (ALC)",
        "amc": "Моноцити, абсолютні (AMC)",
        "aec": "Еозинофіли, абсолютні (AEC)",
        "abc": "Базофіли, абсолютні (ABC)",
    }
    for code, nm in abs_names.items():
        if code not in values:
            continue
        v = values.get(code)
        if v is None:
            continue
        rr = _get_abs_ref(code, sex, age, None)
        fl = _flag(v, rr)
        interp: List[str] = []
        if fl == "low":
            if code == "anc":
                interp.append("Нейтропенія (низький ANC) — може підвищувати ризик інфекцій, особливо якщо значення дуже низьке.")
            elif code == "alc":
                interp.append("Лімфопенія (низький ALC) — інколи при стресі, стероїдах, гострих інфекціях; потребує контексту.")
            else:
                interp.append("Низьке абсолютне значення: інтерпретується в контексті всього CBC і симптомів.")
        elif fl == "high":
            if code == "anc":
                interp.append("Нейтрофілія (високий ANC) — часто при бактеріальному запаленні, стресі, стероїдах.")
            elif code == "alc":
                interp.append("Лімфоцитоз (високий ALC) — часто при вірусних інфекціях або відновленні після них.")
            elif code == "aec":
                interp.append("Еозинофілія — часто алергія/астма/паразити/реакції на ліки.")
            else:
                interp.append("Високе абсолютне значення: інтерпретується в контексті.")
        else:
            interp.append("В межах типового референсу.")
        cards.append({
            "code": code,
            "name": nm,
            "value": smart_round(v, 3),
            "unit": "10^3/µL",
            "ref": {"low": rr.low, "high": rr.high},
            "flag": fl,
            "what": "Абсолютна кількість клітин (не відсоток).",
            "interpretation": interp,
            "tips": ["Абсолютні значення часто інформативніші за відсотки."],
            "source": (field_meta or {}).get(code, {}).get("source", "input"),
            "input_key": (field_meta or {}).get(code, {}).get("input_key"),
            "computed_from": (field_meta or {}).get(code, {}).get("computed_from"),
            "formula": (field_meta or {}).get(code, {}).get("formula"),
            "unit_in": (field_meta or {}).get(code, {}).get("unit_in"),
            "ref_source": _abs_ref_source(code, sex, age, None),
            "caveats": ["Референси відрізняються між лабораторіями."],
        })
    return cards

def analyze_patterns(
    values: Dict[str, Optional[float]],
    sex: Optional[str],
    age: Optional[float],
    refs_override: Optional[Dict[str, Dict[str, float]]] = None,
    config: Optional[CBCConfig] = None,
    patient_context: Optional[Dict[str, bool]] = None,
) -> Tuple[Dict[str, Optional[str]], Dict[str, Any], List[Dict[str, Any]]]:
    sx = _sex_norm(sex)
    cfg = config or CBCConfig()
    refs = {k: _get_ref(k, sex, age, refs_override) for k in LABS.keys()}

    wbc = values.get("wbc")
    plt = values.get("plt")
    rbc = values.get("rbc")
    hgb = values.get("hgb")
    hct = values.get("hct")
    mcv = values.get("mcv")
    mch = values.get("mch")
    mchc = values.get("mchc")
    rdw = values.get("rdw")
    mpv = values.get("mpv")

    neut_pct = values.get("neut_pct")
    lymph_pct = values.get("lymph_pct")
    mono_pct = values.get("mono_pct")
    eos_pct = values.get("eos_pct")
    baso_pct = values.get("baso_pct")

    anc = values.get("anc")
    alc = values.get("alc")
    amc = values.get("amc")
    aec = values.get("aec")
    abc = values.get("abc")

    flags: Dict[str, Optional[str]] = {}
    for code in ["wbc","plt","rbc","hgb","hct","mcv","mch","mchc","rdw","mpv",
                 "neut_pct","lymph_pct","mono_pct","eos_pct","baso_pct"]:
        if code in values:
            flags[code] = _flag(values.get(code), refs.get(code, RefRange()))

    abs_refs = {k: _get_abs_ref(k, sex, age, None) for k in ["anc","alc","amc","aec","abc"]}
    for code in ["anc","alc","amc","aec","abc"]:
        if code in values and values.get(code) is not None:
            flags[code] = _flag(values.get(code), abs_refs[code])

    derived: Dict[str, Any] = {}
    derived["anc_kul"] = smart_round(anc, 3)
    derived["alc_kul"] = smart_round(alc, 3)
    derived["amc_kul"] = smart_round(amc, 3)
    derived["aec_kul"] = smart_round(aec, 3)
    derived["abc_kul"] = smart_round(abc, 3)

    if anc is not None and alc is not None and alc > 0:
        derived["nlr"] = smart_round(anc / alc, 3)
    if plt is not None and alc is not None and alc > 0:
        derived["plr"] = smart_round(plt / alc, 3)
    if plt is not None and anc is not None and alc is not None and alc > 0:
        derived["sii"] = smart_round((plt * anc) / alc, 3)

    if mcv is not None and rbc is not None and rbc > 0:
        derived["mentzer_index"] = smart_round(mcv / rbc, 3)

    signals: List[Dict[str, Any]] = []

    missing_core = [k for k in ["wbc","hgb","plt"] if values.get(k) is None]
    if missing_core:
        signals.append(_signal(
            "missing_core_cbc",
            "low",
            "Неповний CBC",
            "Для повнішої інтерпретації бракує ключових показників CBC.",
            [f"Додайте значення: {', '.join(missing_core)}."],
            {"missing": missing_core},
            tags=["quality"]
        ))

    if flags.get("wbc") == "high":
        sev = _sev_high(wbc, cfg.wbc_high) or "low"
        signals.append(_signal(
            "leukocytosis",
            sev,
            "Лейкоцити підвищені (лейкоцитоз)",
            "Лейкоцити вище типового референсу. Часті причини: інфекція/запалення, стрес, куріння, деякі ліки. Найкраще оцінювати разом із формулою (нейтрофіли/лімфоцити/інші) та симптомами.",
            [
                "Подивіться, яка фракція підвищена (ANC/ALC/інші).",
                "Якщо були симптоми (температура, біль, кашель, дизурія) — це підсилює інтерпретацію.",
                "Якщо значення дуже високе або є погане самопочуття — звернутися до лікаря."
            ],
            {"wbc_kul": smart_round(wbc,3), "ref": {"low": refs["wbc"].low, "high": refs["wbc"].high}},
            tags=["wbc"]
        ))

        anc_high = (anc is not None
                    and abs_refs.get("anc")
                    and anc > abs_refs["anc"].high)
        approx_anc_high = (anc is None
                           and neut_pct is not None
                           and wbc is not None
                           and (wbc * neut_pct / 100.0) > 7.5)
        neut_pct_high = (neut_pct is not None and neut_pct > 75)
        if anc_high or approx_anc_high or neut_pct_high:
            signals.append(_signal(
                "neutrophilic_leukocytosis",
                "medium",
                "Нейтрофільний лейкоцитоз — ознака активного запалення",
                "Підвищений рівень лейкоцитів за рахунок нейтрофілів. Це класична картина **активного запалення**, бактеріальної інфекції, стрес-реакції або застосування кортикостероїдів. Потрібна клінічна оцінка для пошуку джерела.",
                [
                    "Подумайте чи є симптоми інфекції: температура, біль, кашель, дизурія, виділення з рани.",
                    "Здайте додатково: С-реактивний білок (СРБ), прокальцитонін (за наявності), повторний CBC через 5-7 днів.",
                    "Якщо є гарячка ≥38°C або погане самопочуття — зверніться до лікаря сьогодні.",
                    "Якщо приймаєте кортикостероїди або були під стресом (травма, операція) — реактивне підвищення можливе.",
                ],
                {
                    "wbc_kul": smart_round(wbc, 3),
                    "anc_kul": smart_round(anc, 3) if anc is not None else None,
                    "neut_pct": smart_round(neut_pct, 1) if neut_pct is not None else None,
                },
                tags=["wbc", "inflammation"]
            ))
    elif flags.get("wbc") == "low":
        sev = _sev_low(wbc, cfg.wbc_low) or "low"
        signals.append(_signal(
            "leukopenia",
            sev,
            "Лейкоцити знижені (лейкопенія)",
            "Лейкоцити нижче типового референсу. Важливо з'ясувати, за рахунок чого (найчастіше нейтрофіли). Причини: вірусні інфекції, ліки, аутоімунні стани, пригнічення кісткового мозку.",
            [
                "Перевірте абсолютні нейтрофіли (ANC) — саме вони визначають ризик інфекцій.",
                "Якщо є гарячка/погане самопочуття або ANC дуже низький — звернутися до лікаря терміново.",
                "Порівняйте з попередніми аналізами (динаміка важлива)."
            ],
            {"wbc_kul": smart_round(wbc,3), "ref": {"low": refs["wbc"].low, "high": refs["wbc"].high}},
            tags=["wbc"]
        ))

    if anc is not None:
        anc_flag = flags.get("anc")
        if anc_flag == "high":
            sev = _sev_high(anc, cfg.anc_high) or "low"
            signals.append(_signal(
                "neutrophilia",
                sev,
                "Нейтрофіли підвищені (нейтрофілія)",
                "Підвищений ANC часто супроводжує бактеріальне запалення, стрес-реакцію, прийом стероїдів. Оцінюють разом із симптомами та іншими маркерами (CRP, температура тощо).",
                [
                    "Якщо є симптоми інфекції — зверніть увагу на джерело (горло/легені/сечові шляхи тощо).",
                    "Якщо стероїди/стрес/тренування — можливе реактивне підвищення.",
                ],
                {"anc_kul": smart_round(anc,3), "ref": asdict(abs_refs["anc"])},
                tags=["diff"]
            ))
        elif anc_flag == "low":
            sev = _sev_low(anc, cfg.anc_low) or "low"
            signals.append(_signal(
                "neutropenia",
                sev,
                "Нейтрофіли знижені (нейтропенія)",
                "Низький ANC може підвищувати ризик інфекцій. Ступінь ризику залежить від глибини нейтропенії та симптомів. Причини: вірусні інфекції, ліки, аутоімунні стани, дефіцити, проблеми кісткового мозку тощо.",
                [
                    "Якщо є гарячка або ознаки інфекції — звернутися за медичною допомогою негайно.",
                    "Перегляньте ліки (деякі можуть знижувати ANC) та недавні інфекції.",
                    "Важлива динаміка: повторний CBC за рекомендацією лікаря."
                ],
                {"anc_kul": smart_round(anc,3), "thresholds_kul": {"mild": 1.0, "moderate": 0.5, "severe": 0.5}},
                tags=["urgent","diff"]
            ))

    if alc is not None:
        alc_flag = flags.get("alc")
        if alc_flag == "high":
            signals.append(_signal(
                "lymphocytosis",
                "low",
                "Лімфоцити підвищені (лімфоцитоз)",
                "Часто буває при вірусних інфекціях або у фазі відновлення. Значення інтерпретують з урахуванням симптомів та тривалості.",
                ["Якщо симптоми вірусної інфекції — це може бути реактивною зміною.", "Якщо підвищення тримається довго без пояснення — варто обговорити з лікарем."],
                {"alc_kul": smart_round(alc,3), "ref": asdict(abs_refs["alc"])},
                tags=["diff"]
            ))
        elif alc_flag == "low":
            signals.append(_signal(
                "lymphopenia",
                "low",
                "Лімфоцити знижені (лімфопенія)",
                "Може бути при стресі, гострих інфекціях, прийомі стероїдів, деяких хронічних станах. Оцінка залежить від контексту.",
                ["Оцініть загальне самопочуття та прийом ліків.", "Якщо є часті/важкі інфекції — обговорити з лікарем."],
                {"alc_kul": smart_round(alc,3), "ref": asdict(abs_refs["alc"])},
                tags=["diff"]
            ))

    if aec is not None and flags.get("aec") == "high":
        signals.append(_signal(
            "eosinophilia",
            "low",
            "Еозинофіли підвищені (еозинофілія)",
            "Часто пов'язано з алергіями/астмою/атопією, паразитарними інфекціями або реакціями на ліки. Потрібен клінічний контекст.",
            ["Перевірте, чи є алергічні симптоми або нові ліки.", "За потреби — обговорити з лікарем додаткові обстеження."],
            {"aec_kul": smart_round(aec,3), "ref": asdict(abs_refs["aec"])},
            tags=["diff"]
        ))
    if amc is not None and flags.get("amc") == "high":
        signals.append(_signal(
            "monocytosis",
            "low",
            "Моноцити підвищені (моноцитоз)",
            "Може бути при хронічному запаленні, інфекціях або у фазі відновлення. Інтерпретується разом з іншими показниками.",
            ["Подивіться загальну картину CBC і симптоми.", "Якщо зберігається тривало — обговорити з лікарем."],
            {"amc_kul": smart_round(amc,3), "ref": asdict(abs_refs["amc"])},
            tags=["diff"]
        ))
    if abc is not None and flags.get("abc") == "high":
        signals.append(_signal(
            "basophilia",
            "low",
            "Базофіли підвищені (базофілія)",
            "Невелике підвищення може бути при алергії/запаленні. Суттєва базофілія вимагає оцінки причини лікарем у контексті CBC.",
            ["Якщо значення сильно підвищене або є інші відхилення — звернутися до лікаря."],
            {"abc_kul": smart_round(abc,3), "ref": asdict(abs_refs["abc"])},
            tags=["diff"]
        ))

    esr = values.get("esr")
    if esr is not None:
        upper = 20.0 if sex == "female" else 15.0
        if esr > upper:
            sev = _sev_high(esr, cfg.esr_high) or "low"
            signals.append(_signal(
                "elevated_esr",
                sev,
                f"ШОЕ підвищена ({esr:g} мм/год)",
                "ШОЕ — неспецифічний маркер запалення. Підвищення може вказувати на запальний процес, інфекцію, аутоімунне захворювання, анемію або інші стани.",
                [
                    "Оцініть наявність симптомів запалення/інфекції.",
                    "Якщо ШОЕ дуже високий (>50) або є інші відхилення — обов\u02bcязково звернутися до лікаря.",
                    "Розглянути СРБ для додаткової оцінки.",
                ],
                {"esr_value": esr, "ref_upper": upper},
                tags=["esr", "inflammation"]
            ))

    if flags.get("plt") == "high":
        sev = _sev_high(plt, cfg.plt_high) or "low"
        signals.append(_signal(
            "thrombocytosis",
            sev,
            "Тромбоцити підвищені (тромбоцитоз)",
            "Тромбоцити вище референсу. Часто буває реактивно (запалення/інфекція), при дефіциті заліза, після крововтрати. Рідше — первинні мієлопроліферативні стани.",
            [
                "Перевірте ознаки запалення/інфекції та історію нещодавніх крововтрат/операцій.",
                "Якщо є ознаки анемії або мікроцитоз — обговоріть феритин/залізо.",
                "Якщо тромбоцити дуже високі або є тромбози/кровотечі в анамнезі — лікар."
            ],
            {"plt_kul": smart_round(plt,3), "ref": {"low": refs["plt"].low, "high": refs["plt"].high}},
            tags=["plt"]
        ))
    elif flags.get("plt") == "low":
        sev = _sev_low(plt, cfg.plt_low) or "low"
        signals.append(_signal(
            "thrombocytopenia",
            sev,
            "Тромбоцити знижені (тромбоцитопенія)",
            "Низькі тромбоцити можуть підвищувати ризик кровотеч. Причини різні: вірусні інфекції, ліки, аутоімунні процеси, захворювання печінки/селезінки, кісткового мозку. Важлива тяжкість і симптоми.",
            [
                "Якщо є кровотечі, петехії, великі синці — звернутися до лікаря.",
                "Перегляньте ліки (деякі знижують PLT) та недавні інфекції.",
                "Повторити аналіз за рекомендацією лікаря (важлива динаміка)."
            ],
            {"plt_kul": smart_round(plt,3), "thresholds_kul": {"mild": 150, "moderate": 100, "severe": 50}},
            tags=["urgent","plt"]
        ))

    anemia_flag = None
    if hgb is not None:
        hgb_rr = refs["hgb"]
        anemia_flag = "low" if (hgb_rr.low is not None and hgb < hgb_rr.low) else ("high" if (hgb_rr.high is not None and hgb > hgb_rr.high) else "normal")
        if anemia_flag == "low":
            band = cfg.hgb_low_female if sx == "female" else (cfg.hgb_low_male if sx == "male" else cfg.hgb_low_female)
            sev = _sev_low(hgb, band) or "low"
            signals.append(_signal(
                "anemia_possible",
                sev,
                "Гемоглобін нижче порогу (можлива анемія)",
                "Низький Hb — не діагноз, але причина визначити тип анемії за індексами (MCV/RDW) і, часто, додатковими аналізами.",
                [
                    "Подивіться MCV: мікро-/нормо-/макроцитарний тип.",
                    "Якщо є симптоми (втома, задишка, блідість) — обговорити з лікарем.",
                    "Типові дообстеження за призначенням: феритин/залізо, B12/фолати, ретикулоцити."
                ],
                {"hgb_gdl": smart_round(hgb,3), "threshold_low_gdl": hgb_rr.low, "mcv_fl": smart_round(mcv,3), "rdw_pct": smart_round(rdw,3)},
                tags=["rbc"]
            ))
        elif anemia_flag == "high":
            signals.append(_signal(
                "high_hgb",
                "medium",
                "Гемоглобін підвищений",
                "Підвищений Hb може бути при зневодненні (гемоконцентрація), курінні, хронічній гіпоксії, висоті. Рідше — при поліцитемії. Потрібен контекст і підтвердження повторним аналізом.",
                ["Перевірте гематокрит (Hct) і ознаки зневоднення.", "Якщо підвищення стійке — обговорити з лікарем."],
                {"hgb_gdl": smart_round(hgb,3), "ref": {"low": hgb_rr.low, "high": hgb_rr.high}},
                tags=["rbc"]
            ))

    if hgb is not None and anemia_flag == "low" and mcv is not None:
        if mcv < cfg.mcv_micro:
            why = "Низький Hb + низький MCV = мікроцитарна анемічна картина. Часті причини: дефіцит заліза; іноді — гемоглобінопатії (напр., таласемія)."
            nexts = ["Обговоріть з лікарем феритин/залізо (підтвердження дефіциту заліза).", "Оцініть RDW і RBC (може допомогти відрізнити варіанти)."]
            evidence = {"hgb_gdl": smart_round(hgb,3), "mcv_fl": smart_round(mcv,3), "rdw_pct": smart_round(rdw,3)}
            mentzer = derived.get("mentzer_index")
            if mentzer is not None:
                evidence["mentzer_index"] = mentzer
                if mentzer < 13:
                    nexts.append("Mentzer < 13 інколи більше відповідає таласемії-носійству, але це не діагноз (потрібне підтвердження).")
                elif mentzer > 13:
                    nexts.append("Mentzer > 13 інколи більше відповідає дефіциту заліза, але потрібен феритин/залізо.")
            signals.append(_signal("microcytic_anemia_pattern", "medium", "Мікроцитарна анемічна картина", why, nexts, evidence, tags=["pattern","rbc"]))
        elif mcv > cfg.mcv_macro:
            signals.append(_signal(
                "macrocytic_anemia_pattern",
                "medium",
                "Макроцитарна анемічна картина",
                "Низький Hb + високий MCV = макроцитарна анемічна картина. Можливі причини: дефіцит B12/фолатів, алкоголь, печінка, гіпотиреоз, деякі ліки.",
                ["Обговоріть з лікарем доцільність B12/фолатів, TSH, печінкових проб.", "Оцініть RDW: при дефіцитах часто підвищений."],
                {"hgb_gdl": smart_round(hgb,3), "mcv_fl": smart_round(mcv,3), "rdw_pct": smart_round(rdw,3)},
                tags=["pattern","rbc"]
            ))
        else:
            signals.append(_signal(
                "normocytic_anemia_pattern",
                "medium",
                "Нормоцитарна анемічна картина",
                "Низький Hb + нормальний MCV = нормоцитарна картина. Причини: крововтрата, хронічне запалення, хвороби нирок, гемоліз (потрібні додаткові дані).",
                ["Обговоріть з лікарем контекст: крововтрата, хронічні хвороби, нирки.", "За потреби: ретикулоцити, феритин, креатинін, CRP — за призначенням."],
                {"hgb_gdl": smart_round(hgb,3), "mcv_fl": smart_round(mcv,3), "rdw_pct": smart_round(rdw,3)},
                tags=["pattern","rbc"]
            ))

    if rdw is not None and rdw > (refs["rdw"].high or 15.0):
        signals.append(_signal(
            "high_rdw",
            "low",
            "RDW підвищений",
            "Підвищений RDW означає, що еритроцити різні за розміром (анізоцитоз). Найчастіше це інформативно разом із Hb та MCV.",
            ["Подивіться Hb і MCV. Якщо Hb низький — обговоріть тип анемії з лікарем."],
            {"rdw_pct": smart_round(rdw,3), "ref": {"low": refs["rdw"].low, "high": refs["rdw"].high}},
            tags=["rbc"]
        ))
        if mcv is not None and mcv < cfg.mcv_micro and (hgb is None or anemia_flag=="low"):
            signals.append(_signal(
                "iron_deficiency_likely_pattern",
                "medium",
                "Патерн, сумісний із дефіцитом заліза (ймовірно)",
                "Комбінація мікроцитозу (низький MCV) та підвищеного RDW часто зустрічається при дефіциті заліза. Але підтвердження потребує феритину/заліза.",
                ["Не починайте залізо “наосліп” без підтвердження, якщо є нетипові причини.", "Обговоріть з лікарем феритин/залізо."],
                {"mcv_fl": smart_round(mcv,3), "rdw_pct": smart_round(rdw,3), "hgb_gdl": smart_round(hgb,3)},
                tags=["pattern","rbc"]
            ))

    if flags.get("plt") == "high" and mcv is not None and mcv < cfg.mcv_micro:
        signals.append(_signal(
            "plt_high_microcytosis_combo",
            "medium",
            "Тромбоцитоз + мікроцитоз: часта комбінація при дефіциті заліза",
            "Реактивний тромбоцитоз часто поєднується з дефіцитом заліза, який також може давати низький MCV. Потрібне підтвердження аналізами заліза.",
            ["Обговоріть з лікарем феритин/залізо.", "Оцініть Hb та RDW."],
            {"plt_kul": smart_round(plt,3), "mcv_fl": smart_round(mcv,3), "hgb_gdl": smart_round(hgb,3)},
            tags=["pattern"]
        ))

    low_wbc = (flags.get("wbc") == "low")
    low_hgb = (anemia_flag == "low")
    low_plt = (flags.get("plt") == "low")
    if low_wbc and low_hgb and low_plt:
        signals.append(_signal(
            "pancytopenia_pattern",
            "high",
            "Панцитопенія (низькі WBC + Hb + PLT) — потрібна оцінка лікарем",
            "Комбінація знижених лейкоцитів, гемоглобіну і тромбоцитів може свідчити про значущі проблеми кровотворення або інші серйозні причини. Потрібен терміновий медичний розбір.",
            ["Звернутися до лікаря найближчим часом (або негайно при симптомах).", "Не відкладати повторний CBC та дообстеження за призначенням."],
            {"wbc_kul": smart_round(wbc,3), "hgb_gdl": smart_round(hgb,3), "plt_kul": smart_round(plt,3)},
            tags=["urgent","pattern"]
        ))
    else:
        if low_wbc and low_hgb and not low_plt:
            signals.append(_signal(
                "bicytopenia_wbc_hgb",
                "medium",
                "Знижені WBC + Hb (біцитопенія)",
                "Комбінація може мати різні причини (інфекції/ліки/дефіцити/кістковий мозок). Важлива тяжкість і динаміка.",
                ["Оцініть ANC, симптоми, ліки. Обговоріть з лікарем за потреби."],
                {"wbc_kul": smart_round(wbc,3), "hgb_gdl": smart_round(hgb,3)},
                tags=["pattern"]
            ))
        if low_hgb and low_plt and not low_wbc:
            signals.append(_signal(
                "bicytopenia_hgb_plt",
                "medium",
                "Низькі Hb + PLT (біцитопенія)",
                "Комбінація анемії та тромбоцитопенії потребує клінічної оцінки, особливо при кровотечах/синцях.",
                ["Якщо є кровотечі/синці — лікар.", "Оцініть інші індекси та історію ліків/інфекцій."],
                {"hgb_gdl": smart_round(hgb,3), "plt_kul": smart_round(plt,3)},
                tags=["pattern"]
            ))
        if low_wbc and low_plt and not low_hgb:
            signals.append(_signal(
                "bicytopenia_wbc_plt",
                "medium",
                "Низькі WBC + PLT (біцитопенія)",
                "Потребує контексту: інфекції, ліки, аутоімунні стани тощо.",
                ["Оцініть ANC, симптоми, ліки; обговоріть з лікарем."],
                {"wbc_kul": smart_round(wbc,3), "plt_kul": smart_round(plt,3)},
                tags=["pattern"]
            ))

    nlr = derived.get("nlr")
    if nlr is not None:
        if nlr >= cfg.nlr_high_cutoff:
            signals.append(_signal(
                "nlr_high",
                "low",
                "NLR підвищений (відношення нейтрофіли/лімфоцити)",
                "Високий NLR інколи супроводжує гострий стрес/запалення, але це неспецифічний індекс і не є діагнозом.",
                ["Оцініть разом із симптомами та іншими маркерами (CRP тощо)."],
                {"nlr": nlr},
                tags=["derived"]
            ))


    if mcv is not None and (hgb is None or anemia_flag != "low"):
        if mcv < cfg.mcv_micro:
            signals.append(_signal(
                "microcytosis_without_anemia",
                "low",
                "MCV знижений (мікроцитоз) без явної анемії",
                "Низький MCV може бути раннім проявом дефіциту заліза або особливістю при деяких гемоглобінопатіях. Навіть без зниженого Hb інколи доцільно перевірити залізо/феритин у правильному контексті.",
                ["Оцініть RDW та RBC (якщо доступні).", "За потреби обговоріть з лікарем феритин/залізо."],
                {"mcv_fl": smart_round(mcv,3), "hgb_gdl": smart_round(hgb,3), "rdw_pct": smart_round(rdw,3), "mentzer_index": derived.get("mentzer_index")},
                tags=["rbc"]
            ))
        elif mcv > cfg.mcv_macro:
            signals.append(_signal(
                "macrocytosis_without_anemia",
                "low",
                "MCV підвищений (макроцитоз) без явної анемії",
                "Макроцитоз може бути при дефіциті B12/фолатів, алкоголі, захворюваннях печінки, гіпотиреозі або через деякі ліки — навіть якщо Hb ще в нормі.",
                ["Оцініть RDW; за потреби обговоріть B12/фолати, TSH, печінкові проби з лікарем."],
                {"mcv_fl": smart_round(mcv,3), "hgb_gdl": smart_round(hgb,3), "rdw_pct": smart_round(rdw,3)},
                tags=["rbc"]
            ))

    mentzer = derived.get("mentzer_index")
    if mcv is not None and mcv < cfg.mcv_micro and rbc is not None and rdw is not None and mentzer is not None:
        rdw_high_cut = refs["rdw"].high or 15.0
        if rbc >= 5.2 and rdw <= rdw_high_cut and mentzer < 13.0:
            signals.append(_signal(
                "thal_trait_like_pattern",
                "low",
                "Патерн, сумісний з носійством таласемії (припущення)",
                "Комбінація мікроцитозу з відносно високим RBC, нормальним RDW та низьким індексом Mentzer інколи зустрічається при таласемії-носійстві. Це не діагноз і потребує підтвердження.",
                ["Обговоріть з лікарем доцільність електрофорезу Hb/генетичних тестів, особливо якщо є сімейний анамнез.", "Виключіть дефіцит заліза (феритин)."],
                {"mcv_fl": smart_round(mcv,3), "rbc_mul": smart_round(rbc,3), "rdw_pct": smart_round(rdw,3), "mentzer_index": mentzer},
                tags=["pattern","rbc"]
            ))

    if mchc is not None and refs["mchc"].low is not None and mchc < refs["mchc"].low:
        signals.append(_signal(
            "low_mchc_hypochromia",
            "low",
            "MCHC знижений (ознаки гіпохромії)",
            "Знижений MCHC часто поєднується з дефіцитом заліза або мікроцитозом. Підтвердження — через феритин/залізо та клінічний контекст.",
            ["Оцініть MCV/MCH/RDW.", "За потреби — феритин/залізо за призначенням."],
            {"mchc_gdl": smart_round(mchc,3), "mcv_fl": smart_round(mcv,3), "rdw_pct": smart_round(rdw,3)},
            tags=["rbc"]
        ))
    if mchc is not None and refs["mchc"].high is not None and mchc > refs["mchc"].high:
        signals.append(_signal(
            "high_mchc_note",
            "low",
            "MCHC підвищений (рідко, інколи артефакт)",
            "Підвищений MCHC зустрічається рідко; інколи це технічний артефакт (наприклад, холодові аглютиніни). Потребує перевірки в контексті інших індексів.",
            ["Якщо значення несподіване — обговоріть з лікарем/лабораторією; інколи доречно повторити аналіз."],
            {"mchc_gdl": smart_round(mchc,3)},
            tags=["rbc"]
        ))

    if mpv is not None and plt is not None and flags.get("plt") == "low":
        if mpv > (refs["mpv"].high or 11.5):
            signals.append(_signal(
                "low_plt_high_mpv",
                "low",
                "Низькі тромбоцити + високий MPV (припущення про периферичне руйнування)",
                "Комбінація низького PLT з високим MPV інколи зустрічається, коли тромбоцити активно утворюються у відповідь на підвищене руйнування. Це не діагноз.",
                ["Потрібна оцінка причин лікарем, особливо якщо є кровотечі/синці."],
                {"plt_kul": smart_round(plt,3), "mpv_fl": smart_round(mpv,3)},
                tags=["plt"]
            ))
        elif mpv < (refs["mpv"].low or 7.0):
            signals.append(_signal(
                "low_plt_low_mpv",
                "low",
                "Низькі тромбоцити + низький MPV (припущення про знижене утворення)",
                "Комбінація низького PLT з низьким MPV інколи вказує на знижене утворення тромбоцитів у кістковому мозку. Потрібен клінічний контекст.",
                ["Обговоріть з лікарем, особливо якщо є інші цитопенії (WBC/Hb) або симптоми."],
                {"plt_kul": smart_round(plt,3), "mpv_fl": smart_round(mpv,3)},
                tags=["plt"]
            ))

    if hgb is not None and hct is not None and anemia_flag == "high" and flags.get("hct") == "high":
        signals.append(_signal(
            "hemoconcentration_possible",
            "low",
            "Hb і Hct підвищені: можлива гемоконцентрація (зневоднення) або еритроцитоз",
            "Коли Hb і Hct підвищені одночасно, одна з частих причин — зневоднення. Якщо підвищення стійке, обговорюють інші причини (гіпоксія, куріння, висота, поліцитемія).",
            ["Оцініть гідратацію та повторіть аналіз у стабільному стані за потреби.", "Якщо підвищення повторюється — лікар."],
            {"hgb_gdl": smart_round(hgb,3), "hct_pct": smart_round(hct,3)},
            tags=["pattern","rbc"]
        ))

    if wbc is not None and anc is None and neut_pct is not None and flags.get("wbc") in {"high","normal"}:
        if neut_pct > 75:
            signals.append(_signal(
                "relative_neutrophilia",
                "low",
                "Відносна нейтрофілія (за %)",
                "Нейтрофіли у відсотках підвищені. Це краще підтверджувати абсолютним ANC, але навіть за % інколи відповідає бактеріальному запаленню/стресу.",
                ["За можливості додайте абсолютні нейтрофіли (ANC) або дозвольте програмі обчислити їх з WBC+%.", "Оцініть симптоми."],
                {"wbc_kul": smart_round(wbc,3), "neut_pct": smart_round(neut_pct,1)},
                tags=["diff"]
            ))
    if wbc is not None and alc is None and lymph_pct is not None and flags.get("wbc") in {"high","normal"}:
        if lymph_pct > 45:
            signals.append(_signal(
                "relative_lymphocytosis",
                "low",
                "Відносний лімфоцитоз (за %)",
                "Лімфоцити у відсотках підвищені. Часто при вірусних інфекціях/відновленні. Абсолютний ALC інформативніший.",
                ["За можливості додайте абсолютні лімфоцити (ALC) або дозвольте програмі обчислити їх з WBC+%.", "Оцініть симптоми."],
                {"wbc_kul": smart_round(wbc,3), "lymph_pct": smart_round(lymph_pct,1)},
                tags=["diff"]
            ))


    ctx = patient_context or {}

    def _ctx(*keys):
        return any(bool(ctx.get(k)) for k in keys)

    has_diabetes = _ctx("has_diabetes")
    on_steroids  = _ctx("on_corticosteroids", "takes_corticosteroids")
    on_anticoag  = _ctx("on_oral_anticoagulants", "takes_anticoagulants")

    if (has_diabetes and hgb is not None and hgb < 12.0
            and mcv is not None
            and cfg.mcv_micro <= mcv <= cfg.mcv_macro):
        signals.append(_signal(
            "anemia_with_diabetes",
            "medium",
            "Анемія при цукровому діабеті",
            "Анемія у пацієнтів з діабетом може бути проявом ураження нирок (нефропатії), коли знижується продукція еритропоетину. Але це не єдина можлива причина — потрібна додаткова оцінка.",
            [
                "Перевірте креатинін та ШКФ — для оцінки функції нирок.",
                "Здайте альбумін/креатинін у сечі (ACR або мікроальбумін) — це ключовий маркер діабетичної хвороби нирок.",
                "Здайте феритин і насичення трансферину — щоб виключити дефіцит заліза.",
                "Зверніться до ендокринолога або нефролога — вони оцінять усі чинники.",
            ],
            {"hgb": smart_round(hgb, 1)},
            tags=["context", "diabetes", "anemia"]
        ))

    if on_steroids and wbc is not None and wbc > 9.0:
        signals.append(_signal(
            "leukocytosis_on_steroids",
            "low",
            "Лейкоцитоз на тлі кортикостероїдів",
            "Кортикостероїди фізіологічно підвищують лейкоцити (демаргінація нейтрофілів). Це не обов'язково інфекція.",
            [
                "Оцініть симптоми інфекції окремо від рівня лейкоцитів.",
                "Якщо немає температури або ознак запалення — підвищення може бути нормальним для вашої терапії.",
            ],
            {"wbc": smart_round(wbc, 1)},
            tags=["context", "steroids"]
        ))

    if on_anticoag and plt is not None and plt < 150.0:
        signals.append(_signal(
            "thrombocytopenia_on_anticoagulants",
            "high",
            "Тромбоцитопенія при прийомі антикоагулянтів",
            "Поєднання знижених тромбоцитів і антикоагулянтної терапії значно підвищує ризик кровотеч.",
            [
                "Терміново звернутися до лікаря для корекції терапії.",
                "Не припиняйте прийом самостійно — це може спричинити тромбоз.",
                "Будьте обережні з фізичними травмами.",
            ],
            {"plt": smart_round(plt, 0)},
            tags=["context", "anticoagulants", "alert"]
        ))

    return flags, derived, signals
