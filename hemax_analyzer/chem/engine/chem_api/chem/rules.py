from __future__ import annotations

import re

from dataclasses import asdict
from typing import Any, Dict, List, Optional, Tuple

from .knowledge import LABS
from .spec import RefRange
from .config import ChemConfig, SeverityBand

def _sex_norm(sex: Optional[str]) -> Optional[str]:
    if sex is None:
        return None
    s = str(sex).strip().lower()
    if s in ("m","male","man","чоловік","чоловiк"):
        return "male"
    if s in ("f","female","woman","жінка","жiнка"):
        return "female"
    return s or None

def _flag(value: Optional[float], rr: RefRange) -> Optional[str]:
    if value is None:
        return None
    v_cmp = round(float(value), 2)
    if rr.low is not None and v_cmp < rr.low:
        return "low"
    if rr.high is not None and v_cmp > rr.high:
        return "high"
    return None

def _sev_high(v: Optional[float], band: SeverityBand) -> Optional[str]:
    if v is None:
        return None
    if v >= band.severe:
        return "high"
    if v >= band.moderate:
        return "medium"
    if v >= band.mild:
        return "low"
    return None

def _sev_low(v: Optional[float], band: SeverityBand) -> Optional[str]:
    if v is None:
        return None
    if v <= band.severe:
        return "high"
    if v <= band.moderate:
        return "medium"
    if v <= band.mild:
        return "low"
    return None

def _signal(sig_id: str, severity: str, title: str, why: str, next_steps: List[str], evidence: Dict[str, Any], tags: Optional[List[str]]=None) -> Dict[str, Any]:
    return {
        "id": sig_id,
        "severity": severity,
        "title": title,
        "why": why,
        "next": next_steps,
        "evidence": evidence,
        "tags": tags or [],
    }


def _uniq_append(items: List[Dict[str, Any]], key: str, item: Dict[str, Any]) -> None:
    seen = {x.get(key) for x in items}
    if item.get(key) not in seen:
        items.append(item)

def _norm_test_key(s: str) -> str:
    s = (s or "").lower()
    s = s.replace("–", "-")
    s = re.sub(r"\(.*?\)", "", s)
    s = s.split("—")[0]
    s = re.sub(r"[^0-9a-zа-яіїєё]+", "", s, flags=re.IGNORECASE)
    return s

def _add_next_test(next_tests: List[Dict[str, Any]], test: str, reason: str, priority: int = 50, when: str = "soon", aliases: Optional[List[str]] = None) -> None:
    aliases = aliases or []
    new_keys = [_norm_test_key(test)] + [_norm_test_key(a) for a in aliases]
    for x in next_tests:
        ex = _norm_test_key(str(x.get("test", "")))
        if not ex:
            continue
        for nk in new_keys:
            if not nk:
                continue
            if nk == ex or (nk in ex) or (ex in nk):
                return
    next_tests.append({"test": test, "reason": reason, "priority": int(priority), "when": when})

def _add_question(questions: List[Dict[str, Any]], question: str, why: str, priority: int = 50) -> None:
    _uniq_append(questions, "question", {"question": question, "why": why, "priority": int(priority)})

def _hdl_low(sx: Optional[str], hdl_mgdl: float) -> bool:
    if sx == "male":
        return hdl_mgdl < 40
    if sx == "female":
        return hdl_mgdl < 50
    return hdl_mgdl < 40

def _build_combos_and_recs(
    values: Dict[str, Optional[float]],
    flags: Dict[str, Optional[str]],
    derived: Dict[str, Any],
    signals: List[Dict[str, Any]],
    refs: Dict[str, RefRange],
    sx: Optional[str],
    age: Optional[float],
    cfg: ChemConfig,
    context: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    combos: List[Dict[str, Any]] = []
    next_tests: List[Dict[str, Any]] = []
    ask_doctor: List[Dict[str, Any]] = []

    sig_ids = {s.get("id") for s in signals}
    fasting_8h = bool((context or {}).get("fasting_8h")) if context else False
    fasting_known = (context or {}).get("fasting_8h") is not None if context else False

    if any("urgent" in (s.get("tags") or []) for s in signals):
        _add_question(ask_doctor, "Чи потрібна термінова оцінка сьогодні (невідкладна допомога/швидка)?",
                      "Є маркери, які інколи потребують невідкладної перевірки (особливо електроліти/глюкоза).", priority=95)
        _add_next_test(next_tests, "Повторити ключові критичні показники (повторний забір)",
                       "Щоб виключити лабораторну помилку/гемоліз та підтвердити відхилення.", priority=95, when="now")

    g = values.get("glucose")
    a1c = values.get("a1c")
    if "glucose_diabetes_range" in sig_ids or "a1c_diabetes_range" in sig_ids:
        _add_next_test(next_tests, "HbA1c (якщо ще не було)", "Підтвердження середнього рівня глюкози за ~3 місяці.", 90)
        _add_next_test(next_tests, "Глюкоза натще (повтор)", "Для підтвердження/уточнення діапазону глюкози.", 90)
        _add_next_test(next_tests, "Альбумін/креатинін у сечі (ACR)", "Скринінг ураження нирок при гіперглікемії/діабеті.", 70)
        _add_question(ask_doctor, "Чи потрібно підтвердження діагнозу (повтор глюкози натще / HbA1c / OGTT)?",
                      "Діагностика діабету вимагає контексту і, часто, підтвердження.", 85)

    if "glucose_ifg_range" in sig_ids:
        if fasting_known and not fasting_8h:
            _add_question(ask_doctor, "Чи здавав(ла) я аналіз натще? Чи варто перездати натще 8–12 год?",
                          "Порогові значення IFG коректні саме для натще.", 70)
        _add_next_test(next_tests, "HbA1c", "Оцінка ризику предіабету/діабету, якщо не здавалось.", 70)
        _add_next_test(next_tests, "Глюкоза натще (8–12 год) або OGTT", "Уточнення толерантності до глюкози.", 60)


    ldl = values.get("ldl")
    tchol = values.get("tchol")
    hdl = values.get("hdl")
    tg = values.get("trigly")

    if ldl is not None and ldl >= 190:
        combos.append({
            "id": "fh_like_ldl_ge190",
            "severity": "medium",
            "title": "LDL дуже високий (можливий спадковий компонент)",
            "why": "LDL ≥ 190 mg/dL інколи асоціюється зі спадковою гіперхолестеринемією або вторинними причинами.",
            "evidence": {"ldl_mgdl": ldl},
            "next": ["Обговоріть з лікарем оцінку сімейного ризику та вторинних причин (TSH, печінка, нирки)."],
            "tags": ["lipids", "combo"],
        })
        _add_question(ask_doctor, "Чи є підозра на сімейну гіперхолестеринемію і чи потрібні додаткові тести (ApoB, Lp(a))?",
                      "Дуже високий LDL часто вимагає ширшої оцінки ризику.", 80)
        _add_next_test(next_tests, "Apolipoprotein B (ApoB)", "Краще відображає кількість атерогенних часток.", 60)
        _add_next_test(next_tests, "Lipoprotein(a) [Lp(a)]", "Незалежний фактор ризику; важливий при високому LDL/сімейній історії.", 60)
        _add_next_test(next_tests, "TSH", "Виключити гіпотиреоз як причину дисліпідемії.", 55)

    if "hypertriglyceridemia" in sig_ids and tg is not None and tg >= 500:
        combos.append({
            "id": "tg_very_high_pancreatitis_risk",
            "severity": "high",
            "title": "Тригліцериди дуже високі (ризик панкреатиту)",
            "why": "TG ≥ 500 mg/dL підвищують ризик гострого панкреатиту; важлива швидка медична оцінка.",
            "evidence": {"trigly_mgdl": tg},
            "next": ["Зверніться до лікаря швидко; якщо є сильний біль у животі/нудота — невідкладно."],
            "tags": ["lipids", "urgent", "combo"],
        })
        _add_question(ask_doctor, "Чи є ризик панкреатиту і чи потрібні амілаза/ліпаза або невідкладна оцінка?",
                      "Дуже високі TG можуть бути небезпечними.", 95)
        _add_next_test(next_tests, "Ліпаза/амілаза (якщо є симптоми болю у животі)", "Оцінка панкреатиту при симптомах.", 90)

    alt = values.get("alt")
    ast = values.get("ast")
    alt_high = (flags.get("alt") == "high") if alt is not None else False
    ast_high = (flags.get("ast") == "high") if ast is not None else False
    ir_like = (tg is not None and tg >= 150) and (hdl is not None and _hdl_low(sx, hdl))
    liver_like = alt_high or ast_high or ("transaminitis" in sig_ids)
    gly_like = ("a1c_prediabetes_range" in sig_ids) or ("glucose_ifg_range" in sig_ids)

    if ir_like and liver_like:
        sev = "medium" if gly_like else "low"
        combos.append({
            "id": "insulin_resistance_nafld_like",
            "severity": sev,
            "title": "Комбінація: TG↑ + HDL↓ + ферменти печінки↑",
            "why": "Такий профіль часто зустрічається при інсулінорезистентності та жировій хворобі печінки (NAFLD), але це не діагноз.",
            "evidence": {"trigly_mgdl": tg, "hdl_mgdl": hdl, "alt_ul": alt, "ast_ul": ast},
            "next": [
                "Оцініть фактори ризику (вага/талія, тиск, глюкоза натще, HbA1c).",
                "Обговоріть з лікарем доцільність УЗД печінки та повтору печінкових проб.",
            ],
            "tags": ["metabolic", "liver", "combo"],
        })
        _add_question(ask_doctor, "Чи може це відповідати жировій хворобі печінки (NAFLD) і чи потрібне УЗД печінки?",
                      "Комбінація ліпідів і ферментів печінки підказує метаболічний контекст.", 75)
        _add_next_test(next_tests, "Печінкова панель (ALT, AST, GGT, ALP, білірубін) — повтор", "Уточнення та підтвердження відхилень.", 70)
        _add_next_test(next_tests, "Глюкоза натще (8–12 год)", "Оцінка метаболічного контексту; бажано інтерпретувати натще.", 65, aliases=["Глюкоза натще"])
        _add_next_test(next_tests, "Інсулін натще (опціонально)", "Іноді використовують для оцінки інсулінорезистентності (HOMA-IR) — за рішенням лікаря.", 35)
        _add_next_test(next_tests, "УЗД печінки", "Оцінка стеатозу, якщо ферменти підвищені/є ризики.", 60)

    egfr = values.get("egfr") if values.get("egfr") is not None else derived.get("egfr_ckd_epi_2021")
    scr = values.get("creatinine")
    k = values.get("potassium")
    if egfr is not None and egfr < 60 and (scr is not None):
        sev = "high" if egfr < 30 else "medium"
        combos.append({
            "id": "kidney_function_reduced",
            "severity": sev,
            "title": "Знижена функція нирок (eGFR↓) + креатинін↑",
            "why": "Понижений eGFR може свідчити про хронічне або гостре порушення функції нирок; важливі повтор і причина.",
            "evidence": {"egfr": round(float(egfr), 1), "creatinine_mgdl": scr, "potassium_mmolL": k},
            "next": ["Обговоріть з лікарем повтор аналізів, ліки (НПЗП/діуретики), гідратацію, та аналіз сечі."],
            "tags": ["kidney", "combo"] + (["urgent"] if egfr < 30 else []),
        })
        _add_question(ask_doctor, "Це схоже на гостре чи хронічне погіршення функції нирок? Які причини треба виключити?",
                      "Тактика різна залежно від давності та причини.", 85)
        _add_next_test(next_tests, "Загальний аналіз сечі + альбумін/креатинін (ACR)", "Пошук протеїнурії/гематурії як підказки причини.", 75)
        _add_next_test(next_tests, "Електроліти (Na/K/Cl/HCO3) — повтор", "Контроль небезпечних змін при порушенні функції нирок.", 75)

    na = values.get("sodium")
    if na is not None and g is not None and na < 135 and g > 200:
        corrected = na + 1.6 * ((g - 100.0) / 100.0)
        combos.append({
            "id": "hyponatremia_with_hyperglycemia_corrected_na",
            "severity": "low",
            "title": "Низький натрій при високій глюкозі (корекція натрію)",
            "why": "При значній гіперглікемії натрій може виглядати нижчим через перерозподіл води. Коригований Na дає підказку.",
            "evidence": {"sodium_measured": na, "glucose_mgdl": g, "sodium_corrected_est": round(float(corrected), 1)},
            "next": ["Обговоріть з лікарем інтерпретацію Na з урахуванням глюкози та причин гіперглікемії."],
            "tags": ["electrolytes", "combo"],
        })

    if "iron_deficiency_likely" in sig_ids:
        _add_next_test(next_tests, "CBC (ОАК) + ретикулоцити", "Оцінка анемії та реакції кісткового мозку.", 60)
        _add_next_test(next_tests, "Феритин + залізо + TIBC/TSAT — повтор", "Підтвердження дефіциту та динаміка.", 55)
        _add_question(ask_doctor, "Яка можлива причина дефіциту заліза (харчування/втрати/ШКТ/гінекологія) і чи потрібні додаткові обстеження?",
                      "Причину важливо знайти, а не лише підняти феритин.", 70)

    if "transaminitis" in sig_ids:
        _add_next_test(next_tests, "GGT та ALP", "Уточнення типу ураження печінки (холестаз vs цитоліз).", 55)
        _add_next_test(next_tests, "HBsAg та Anti-HCV (за показами)", "Скринінг вірусних гепатитів при стійкому підвищенні ферментів.", 40)
        _add_question(ask_doctor, "Чи можуть ліки/алкоголь/жирова печінка пояснити підвищені ферменти? Коли повторити аналіз?",
                      "Для безпечної тактики важливий контекст і повтор.", 60)

    next_tests.sort(key=lambda x: (-x.get("priority", 0), x.get("test", "")))
    ask_doctor.sort(key=lambda x: (-x.get("priority", 0), x.get("question", "")))

    recs = {"next_tests": next_tests, "ask_doctor": ask_doctor}
    return combos, recs



def analyze_patterns(
    values: Dict[str, Optional[float]],
    sex: Optional[str],
    age: Optional[float],
    refs_override: Optional[Dict[str, Dict[str, float]]] = None,
    config: Optional[ChemConfig] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Optional[str]], Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    cfg = config or ChemConfig()
    sx = _sex_norm(sex)

    refs: Dict[str, RefRange] = {}
    for code, lab in LABS.items():
        if refs_override and code in refs_override:
            o = refs_override[code]
            refs[code] = RefRange(low=o.get("low"), high=o.get("high"))
        else:
            refs[code] = lab.ref_for(sx)

    flags: Dict[str, Optional[str]] = {}
    for code, v in values.items():
        if code in refs:
            flags[code] = _flag(v, refs[code])

    derived: Dict[str, Any] = {}
    signals: List[Dict[str, Any]] = []

    tchol = values.get("tchol")
    hdl = values.get("hdl")
    trigly = values.get("trigly")
    ldl = values.get("ldl")
    if tchol is not None and hdl is not None:
        derived["non_hdl"] = tchol - hdl
    if ldl is None and tchol is not None and hdl is not None and trigly is not None and trigly < 400:
        derived["ldl_friedewald"] = tchol - hdl - (trigly/5.0)
    if tchol is not None and hdl is not None and hdl > 0:
        derived["tc_hdl_ratio"] = tchol / hdl
    if trigly is not None and hdl is not None and hdl > 0:
        derived["tg_hdl_ratio"] = trigly / hdl

    ast = values.get("ast"); alt = values.get("alt")
    if ast is not None and alt is not None and alt > 0:
        derived["ast_alt_ratio"] = ast / alt

    scr = values.get("creatinine")
    if scr is not None and age is not None and sx in ("male","female") and scr > 0 and age > 0:
        kappa = 0.7 if sx == "female" else 0.9
        alpha = -0.241 if sx == "female" else -0.302
        min_part = min(scr/kappa, 1) ** alpha
        max_part = max(scr/kappa, 1) ** -1.200
        sex_factor = 1.012 if sx == "female" else 1.0
        derived["egfr_ckd_epi_2021"] = 142 * min_part * max_part * (0.9938 ** float(age)) * sex_factor

    na = values.get("sodium"); cl = values.get("chloride"); hco3 = values.get("bicarbonate")
    if na is not None and cl is not None and hco3 is not None:
        derived["anion_gap"] = na - (cl + hco3)

    ca = values.get("calcium"); alb = values.get("albumin")
    if ca is not None and alb is not None:
        derived["calcium_corrected"] = ca + 0.8*(4.0 - alb)

    tp = values.get("total_protein")
    if tp is not None and alb is not None:
        glob = tp - alb
        derived["globulin"] = glob
        if glob > 0:
            derived["ag_ratio"] = alb / glob

    iron = values.get("iron"); tibc = values.get("tibc")
    if iron is not None and tibc is not None and tibc > 0 and values.get("tsat") is None:
        derived["tsat_calc"] = 100.0 * iron / tibc
        values["tsat"] = derived["tsat_calc"]

    core_missing: List[str] = []
    if values.get("glucose") is None and values.get("a1c") is None:
        core_missing.append("glucose або a1c")
    if values.get("creatinine") is None:
        core_missing.append("creatinine")
    if values.get("alt") is None and values.get("ast") is None:
        core_missing.append("alt або ast")
    _lipid_missing = [
        code for code in ("tchol", "hdl", "trigly") if values.get(code) is None
    ]
    if _lipid_missing:
        _lipid_labels = {"tchol": "загальний холестерин", "hdl": "HDL", "trigly": "тригліцериди"}
        _lipid_str = ", ".join(_lipid_labels[c] for c in _lipid_missing)
        core_missing.append(f"ліпідна панель неповна — бракує: {_lipid_str}")

    if core_missing:
        signals.append(_signal(
            "missing_core_chem",
            "low",
            "Неповна біохімія",
            "Для повноцінної інтерпретації бракує деяких ключових показників.",
            [f"Для точнішого аналізу здайте: {', '.join(core_missing)}."],
            {"missing": core_missing},
            tags=["quality"],
        ))

    g = values.get("glucose")
    if g is not None:
        if g < cfg.glucose_low.mild:
            sev = _sev_low(g, cfg.glucose_low) or "low"
            sig_id = "severe_hypoglycemia" if sev == "high" else "hypoglycemia"
            signals.append(_signal(
                sig_id, sev,
                "Глюкоза низька",
                "Низька глюкоза може викликати слабкість, тремор, пітливість, запаморочення; інколи потребує невідкладної оцінки.",
                ["Якщо є симптоми — не зволікайте; при виражених симптомах зверніться по невідкладну допомогу."],
                {"glucose_mgdl": g},
                tags=["glycemia"],
            ))
        elif g >= cfg.glucose_high.moderate:
            sev = _sev_high(g, cfg.glucose_high) or "medium"
            signals.append(_signal(
                "glucose_diabetes_range", sev,
                "Глюкоза у діабетичному діапазоні",
                "Підвищена глюкоза (особливо натще) може відповідати діабету; потрібне підтвердження/контекст.",
                ["Якщо аналіз натще — обговоріть з лікарем підтвердження (повтор, HbA1c)."],
                {"glucose_mgdl": g},
                tags=["glycemia"],
            ))
        elif g >= cfg.glucose_high.mild:
            signals.append(_signal(
                "glucose_ifg_range", "low",
                "Глюкоза підвищена (IFG/предіабет-подібно)",
                "Значення вище типового натще-референсу може відповідати порушеній глікемії натще.",
                ["Зверніть увагу на натще/ненатще; корисно перевірити HbA1c."],
                {"glucose_mgdl": g},
                tags=["glycemia"],
            ))

    a1c = values.get("a1c")
    if a1c is not None:
        if a1c >= 6.5:
            signals.append(_signal(
                "a1c_diabetes_range", "medium" if a1c < 8 else "high",
                "HbA1c у діабетичному діапазоні",
                "HbA1c відображає середню глікемію; >=6.5% часто відповідає діабету (залежить від контексту).",
                ["Обговоріть з лікарем підтвердження та план ведення.", "Якщо є симптоми та дуже високі значення — не зволікайте."],
                {"a1c_pct": a1c},
                tags=["glycemia"],
            ))
        elif a1c >= 5.7:
            signals.append(_signal(
                "a1c_prediabetes_range", "low",
                "HbA1c у предіабетичному діапазоні",
                "HbA1c 5.7–6.4% часто відповідає предіабету.",
                ["Корисно оцінити спосіб життя, вагу, рух, сон; повторити контроль у динаміці."],
                {"a1c_pct": a1c},
                tags=["glycemia"],
            ))

    k = values.get("potassium")
    if k is not None:
        if k > 5.1:
            sev = "high" if k >= cfg.potassium_high.moderate else (_sev_high(k, cfg.potassium_high) or "low")
            signals.append(_signal(
                "hyperkalemia", sev,
                "Калій підвищений",
                "Підвищений калій може впливати на серцевий ритм; важливий контекст та повтор/перевірка гемолізу.",
                ["Якщо значення значно підвищене або є симптоми/аритмія — зверніться до лікаря терміново."],
                {"potassium_mmolL": k},
                tags=["electrolytes"] + (["urgent"] if (k is not None and k >= cfg.potassium_high.moderate) else []),
            ))
        elif k < 3.5:
            sev = _sev_low(k, cfg.potassium_low) or "low"
            signals.append(_signal(
                "hypokalemia", sev,
                "Калій знижений",
                "Низький калій може викликати слабкість, судоми, порушення ритму.",
                ["Обговоріть можливі причини (діуретики, втрати рідини). При вираженому зниженні — терміново."],
                {"potassium_mmolL": k},
                tags=["electrolytes"] + (["urgent"] if k <= cfg.potassium_low.severe else []),
            ))

    na = values.get("sodium")
    if na is not None:
        if na > 145:
            sev = _sev_high(na, cfg.sodium_high) or "low"
            signals.append(_signal(
                "hypernatremia", sev,
                "Натрій підвищений",
                "Часто пов'язано із зневодненням або порушенням водного балансу.",
                ["Перевірте гідратацію, прийом солі/ліків; при значних відхиленнях — лікар."],
                {"sodium_mmolL": na},
                tags=["electrolytes"] + (["urgent"] if na >= cfg.sodium_high.severe else []),
            ))
        elif na < 135:
            sev = "high" if na <= 124 else (_sev_low(na, cfg.sodium_low) or "low")
            signals.append(_signal(
                "hyponatremia", sev,
                "Натрій знижений",
                "Низький натрій може бути небезпечним при значних відхиленнях; причини різні (надлишок води, ліки, ендокринні).",
                ["Не коригуйте самостійно при значних відхиленнях; зверніться до лікаря."],
                {"sodium_mmolL": na},
                tags=["electrolytes"] + (["urgent"] if na <= 124 else []),
            ))

    if scr is not None:
        rr = refs.get("creatinine", RefRange())
        if rr.high is not None and scr > rr.high:
            signals.append(_signal(
                "creatinine_high", "medium" if scr < 2.0 else "high",
                "Креатинін підвищений",
                "Може вказувати на знижену функцію нирок або зневоднення; оцінюють разом з eGFR і клінікою.",
                ["Перевірте eGFR (якщо доступно) та повторіть аналіз у контексті гідратації/ліків."],
                {"creatinine_mgdl": scr, "ref": asdict(rr)},
                tags=["kidney"],
            ))
    egfr = values.get("egfr") if values.get("egfr") is not None else derived.get("egfr_ckd_epi_2021")
    if egfr is not None and egfr < 60:
        if egfr < 15:
            sev = "high"
            title = "eGFR критично знижений (термінальна ниркова недостатність)"
            why = "eGFR < 15 відповідає 5-й стадії ХХН (термінальна ниркова недостатність). Потрібна термінова консультація нефролога."
            next_steps = [
                "Термінова консультація нефролога.",
                "Оцінити потребу в нирковозамісній терапії (діаліз/трансплантація).",
                "Контроль калію, натрію, бікарбонату, фосфору.",
                "Перевірити ліки на нефротоксичність та скоригувати дози.",
            ]
            tags = ["kidney", "urgent", "critical"]
        elif egfr < 30:
            sev = "high"
            title = "eGFR значно знижений (ХХН 4 стадія)"
            why = "eGFR 15–29 відповідає 4-й стадії ХХН. Потрібна консультація нефролога."
            next_steps = [
                "Консультація нефролога.",
                "Моніторинг електролітів, гемоглобіну, фосфору.",
                "Підготовка до нирковозамісної терапії за потреби.",
            ]
            tags = ["kidney", "urgent"]
        else:
            sev = "medium"
            title = "eGFR знижений"
            why = "Знижений eGFR може відповідати хронічній хворобі нирок, якщо зберігається >=3 місяці."
            next_steps = ["Підтвердіть у динаміці, обговоріть з лікарем. Важливо врахувати альбумінурію та АТ."]
            tags = ["kidney"]
        signals.append(_signal(
            "egfr_low", sev, title, why, next_steps,
            {"egfr": round(float(egfr), 1)},
            tags=tags,
        ))

    if alt is not None or ast is not None:
        high_any = False
        if alt is not None and refs.get("alt") and refs["alt"].high is not None and alt > refs["alt"].high:
            high_any = True
        if ast is not None and refs.get("ast") and refs["ast"].high is not None and ast > refs["ast"].high:
            high_any = True
        if high_any:
            sev = "medium"
            if (alt is not None and refs["alt"].high is not None and alt > 3*refs["alt"].high) or (ast is not None and refs["ast"].high is not None and ast > 3*refs["ast"].high):
                sev = "high"
            signals.append(_signal(
                "transaminitis", sev,
                "Печінкові ферменти підвищені (АЛТ/АСТ)",
                "Підвищення може бути при жировій хворобі печінки, вірусних гепатитах, ліках, алкоголі, м'язових причинах (AST).",
                ["Оцініть разом з ALP/GGT/білірубіном; обговоріть з лікарем при стійкому підвищенні."],
                {"alt": alt, "ast": ast},
                tags=["liver"],
            ))

    bili = values.get("bilirubin_total")
    if bili is not None and refs.get("bilirubin_total") and refs["bilirubin_total"].high is not None and bili > refs["bilirubin_total"].high:
        sev = "high" if bili >= 3.0 else "medium"
        signals.append(_signal(
            "bilirubin_high", sev,
            "Білірубін підвищений",
            "Потрібно відрізнити прямий/непрямий білірубін та оцінити печінкові ферменти.",
            ["Якщо є жовтяниця/темна сеча/світлий кал — зверніться до лікаря терміново."],
            {"bilirubin_total_mgdl": bili},
            tags=["liver"],
        ))

    crp = values.get("crp")
    if crp is not None:
        sev = "low"
        tags = ["inflammation"]
        if crp >= 50:
            sev = "high"
            tags.append("urgent")
        elif crp >= 10:
            sev = "medium"
        elif crp >= 3:
            sev = "low"
        else:
            sev = None
        if sev is not None:
            signals.append(_signal(
                "crp_high", sev,
                "CRP підвищений",
                "CRP — маркер запалення. Інтерпретація залежить від симптомів і того, чи це hs-CRP (кардіоризик) чи звичайний CRP (запалення).",
                ["Оцініть симптоми/температуру, нещодавні інфекції; за потреби — повтор у динаміці та консультація лікаря."],
                {"crp_mgl": crp},
                tags=tags,
            ))

    if trigly is not None and trigly >= cfg.trigly_high.mild:
        sev = "high" if trigly >= cfg.trigly_high.severe else ("medium" if trigly >= cfg.trigly_high.moderate else "low")
        signals.append(_signal(
            "hypertriglyceridemia", sev,
            "Тригліцериди підвищені",
            "Високі ТГ часто пов'язані з інсулінорезистентністю, алкоголем, надлишком калорій/цукру; дуже високі ТГ підвищують ризик панкреатиту.",
            ["Якщо ТГ дуже високі (>=500) — обговоріть з лікарем швидке зниження ризику."],
            {"trigly_mgdl": trigly},
            tags=["lipids"],
        ))

    if hdl is not None and _hdl_low(sx, hdl):
        sev = "medium" if hdl < 25 else "low"
        signals.append(_signal(
            "low_hdl", sev,
            "HDL знижений",
            "Низький HDL асоціюється з підвищеним кардіометаболічним ризиком (особливо разом з ТГ↑/глюкозою↑).",
            ["Оцініть ліпіди в цілому (LDL/non-HDL), вагу/талію, АТ; обговоріть з лікарем контекст ризику."],
            {"hdl_mgdl": hdl, "sex": sx},
            tags=["lipids"],
        ))

    if tchol is not None and tchol >= 200:
        sev = "medium" if tchol >= 240 else "low"
        signals.append(_signal(
            "tchol_high", sev,
            "Холестерин загальний підвищений",
            "Загальний холестерин сам по собі не визначає ризик; важливі LDL/non-HDL та інші фактори.",
            ["Перевірте/уточніть LDL або non-HDL; обговоріть цілі з лікарем залежно від ризику."],
            {"tchol_mgdl": tchol},
            tags=["lipids"],
        ))

    non_hdl = values.get("non_hdl")
    if non_hdl is not None:
        sev = "low"
        if non_hdl >= 190:
            sev = "medium"
        elif non_hdl >= 160:
            sev = "medium"
        elif non_hdl >= 130:
            sev = "low"
        if non_hdl >= 130:
            signals.append(_signal(
                "non_hdl_high", sev,
                "Non-HDL холестерин підвищений",
                "Non-HDL (TC−HDL) включає всі атерогенні фракції і часто добре відображає ризик.",
                ["Оцініть ApoB (за потреби) та узгодьте цілі лікування/способу життя з лікарем."],
                {"non_hdl_mgdl": round(float(non_hdl), 1)},
                tags=["lipids"],
            ))

    tg_hdl = values.get("tg_hdl_ratio")
    if tg_hdl is not None and tg_hdl >= 3.5:
        sev = "medium" if tg_hdl >= 6.0 else "low"
        signals.append(_signal(
            "tg_hdl_ratio_high", sev,
            "Підвищений коефіцієнт TG/HDL",
            "Це непрямий маркер, який інколи корелює з інсулінорезистентністю. Інтерпретація залежить від контексту.",
            ["Розгляньте оцінку глюкози натще/HbA1c, талії, АТ та способу життя."],
            {"tg_hdl_ratio": round(float(tg_hdl), 2)},
            tags=["metabolic", "lipids"],
        ))

    if trigly is not None and hdl is not None and trigly >= 150 and ((sx=="female" and hdl < 50) or (sx=="male" and hdl < 40)):
        signals.append(_signal(
            "atherogenic_dyslipidemia_pattern", "low",
            "Атерогенний дисліпідемічний патерн (ТГ↑ + HDL↓)",
            "Комбінація часто відповідає інсулінорезистентності/метаболічному синдрому.",
            ["Корисно оцінити талію, АТ, глюкозу/HbA1c та спосіб життя."],
            {"trigly_mgdl": trigly, "hdl_mgdl": hdl},
            tags=["lipids"],
        ))

    tsat = values.get("tsat")
    if tsat is not None:
        rr = refs.get("tsat", RefRange())
        low_thr = rr.low if rr.low is not None else 20
        high_thr = rr.high if rr.high is not None else 50
        if tsat < low_thr:
            sev = "high" if tsat < 5 else "medium"
            signals.append(_signal(
                "low_tsat", sev,
                "Сатурація трансферину (TSAT) знижена",
                "Низька TSAT підтримує дефіцит заліза (особливо разом з низьким феритином) або порушення утилізації заліза.",
                ["Оцініть разом з феритином, CBC (Hb/MCV/RDW) та причинами втрат/запалення."],
                {"tsat_pct": round(float(tsat), 1), "ref": asdict(rr)},
                tags=["iron"],
            ))
        elif tsat > high_thr:
            signals.append(_signal(
                "high_tsat", "low",
                "Сатурація трансферину (TSAT) підвищена",
                "Може бути при надлишку заліза або деяких станах; важливо інтерпретувати разом з феритином та печінковими тестами.",
                ["Не робіть висновків самостійно; обговоріть з лікарем, якщо є підозра на перевантаження залізом."],
                {"tsat_pct": round(float(tsat), 1), "ref": asdict(rr)},
                tags=["iron"],
            ))
    ferr = values.get("ferritin")
    if ferr is not None:
        rr = refs.get("ferritin", RefRange())
        if rr.low is not None and ferr < rr.low:
            signals.append(_signal(
                "iron_deficiency_likely", "medium",
                "Низький феритин (дефіцит заліза ймовірний)",
                "Феритин відображає запаси заліза; низькі значення часто відповідають дефіциту.",
                ["Оцініть CBC (Hb/MCV/RDW) та можливі причини втрат/харчування."],
                {"ferritin_ngml": ferr, "ref": asdict(rr)},
                tags=["iron"],
            ))
        elif rr.high is not None and ferr > rr.high:
            signals.append(_signal(
                "ferritin_high_possible_inflammation", "low",
                "Феритин підвищений",
                "Феритин може зростати при запаленні, хворобах печінки, надлишку заліза тощо.",
                ["Оцініть CRP/печінкові ферменти та інші контексти; не робіть висновок лише по феритину."],
                {"ferritin_ngml": ferr, "ref": asdict(rr)},
                tags=["iron"],
            ))


    uric = values.get("uric_acid")
    if uric is not None:
        rr_uric = refs.get("uric_acid", RefRange())
        if rr_uric.high is not None and uric > rr_uric.high:
            sev = "medium" if uric > (rr_uric.high + 2.0) else "low"
            signals.append(_signal(
                "uric_acid_high", sev,
                "Сечова кислота підвищена",
                "Підвищена сечова кислота може бути пов'язана з подагрою, метаболічним синдромом, нирковою недостатністю або певними ліками.",
                ["Оцініть симптоми суглобів, нирки, ліки та харчування; обговоріть з лікарем при стійкому підвищенні."],
                {"uric_acid_mgdl": round(float(uric), 2), "sex": sx},
                tags=["metabolic"],
            ))

    vitd = values.get("vitd_25oh")
    if vitd is not None:
        if vitd < 20:
            sev = "medium"
            signals.append(_signal(
                "vitd_deficiency", sev,
                "Дефіцит вітаміну D",
                "25-OH D < 20 ng/mL зазвичай відповідає дефіциту; може впливати на кістки, м'язи, імунітет.",
                ["Обговоріть з лікарем доцільність та дозу корекції; разом з Ca/PTH за показами."],
                {"vitd_25ohd_ngml": round(float(vitd), 1)},
                tags=["vitamins"],
            ))
        elif vitd < 30:
            signals.append(_signal(
                "vitd_insufficiency", "low",
                "Недостатність вітаміну D",
                "25-OH D 20-29 ng/mL — недостатність за більшістю гайдлайнів.",
                ["Розгляньте корекцію способу життя або добавки; уточніть у лікаря."],
                {"vitd_25ohd_ngml": round(float(vitd), 1)},
                tags=["vitamins"],
            ))
        elif vitd > 100:
            signals.append(_signal(
                "vitd_high", "low",
                "Вітамін D підвищений",
                "Дуже високий рівень 25-OH D може свідчити про надлишок добавок.",
                ["Оцініть прийом добавок; при >150 ng/mL — консультація лікаря."],
                {"vitd_25ohd_ngml": round(float(vitd), 1)},
                tags=["vitamins"],
            ))

    hco3_val = values.get("bicarbonate")
    if hco3_val is not None:
        rr_hco3 = refs.get("bicarbonate", RefRange())
        if rr_hco3.low is not None and hco3_val < rr_hco3.low:
            sev = "high" if hco3_val < 15 else ("medium" if hco3_val < 18 else "low")
            signals.append(_signal(
                "bicarbonate_low", sev,
                "Бікарбонат знижений (можливий ацидоз)",
                "Низький HCO3 може свідчити про метаболічний ацидоз: ниркова недостатність, ДКА, діарея тощо.",
                ["Оцініть аніонну щілину та клінічний контекст; при значному зниженні — консультація лікаря."],
                {"bicarbonate_mmolL": round(float(hco3_val), 1)},
                tags=["electrolytes"] + (["urgent"] if hco3_val < 15 else []),
            ))
        elif rr_hco3.high is not None and hco3_val > rr_hco3.high:
            sev = "medium" if hco3_val > 35 else "low"
            signals.append(_signal(
                "bicarbonate_high", sev,
                "Бікарбонат підвищений (можливий алкалоз)",
                "Підвищений HCO3 може свідчити про метаболічний алкалоз: блювота, діуретики, гіпокаліємія.",
                ["Оцініть клінічний контекст та інші електроліти; при значному підвищенні — консультація лікаря."],
                {"bicarbonate_mmolL": round(float(hco3_val), 1)},
                tags=["electrolytes"],
            ))

    cl_val = values.get("chloride")
    if cl_val is not None:
        rr_cl = refs.get("chloride", RefRange())
        if rr_cl.low is not None and cl_val < rr_cl.low:
            signals.append(_signal(
                "chloride_low", "low",
                "Хлор знижений",
                "Гіпохлоремія може бути при блюванні, діуретиках або метаболічному алкалозі.",
                ["Оцініть разом з натрієм та бікарбонатом; уточніть причину у лікаря."],
                {"chloride_mmolL": round(float(cl_val), 1)},
                tags=["electrolytes"],
            ))
        elif rr_cl.high is not None and cl_val > rr_cl.high:
            signals.append(_signal(
                "chloride_high", "low",
                "Хлор підвищений",
                "Гіперхлоремія може бути при діареї, нирковому тубулярному ацидозі або надмірному введенні NaCl.",
                ["Оцініть разом з бікарбонатом та аніонною щілиною; уточніть причину у лікаря."],
                {"chloride_mmolL": round(float(cl_val), 1)},
                tags=["electrolytes"],
            ))

    combos, recs = _build_combos_and_recs(values, flags, derived, signals, refs, sx, age, cfg, context=context)

    return flags, derived, signals, combos, recs