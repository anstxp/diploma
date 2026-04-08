from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from ..risk.inference import RiskPrediction, TaskRiskResult

log = logging.getLogger(__name__)

ROOT = Path(__file__).parent
CLUSTERS_PATH = ROOT / "clusters.yaml"
TEMPLATES_DIR = ROOT / "templates"

TIER_ORDER = ["very_low", "low", "moderate", "high", "very_high"]



@dataclass
class NarrativeStory:
    cluster_id: str
    tier: str
    icon: str
    title: str
    body: str
    actions: List[str] = field(default_factory=list)
    red_flags: List[str] = field(default_factory=list)
    severity: str = "low"
    risks_used: List[str] = field(default_factory=list)


@dataclass
class NarrativeReport:
    summary: str
    tone: str
    lang: str
    patient: Dict[str, Any]
    overall_tier: str
    stories: List[NarrativeStory] = field(default_factory=list)
    risks: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "tone": self.tone,
            "lang": self.lang,
            "patient": self.patient,
            "overall_tier": self.overall_tier,
            "stories": [asdict(s) for s in self.stories],
            "risks": self.risks,
        }



_CLUSTERS_CACHE: Optional[List[dict]] = None


def load_clusters() -> List[dict]:
    global _CLUSTERS_CACHE
    if _CLUSTERS_CACHE is None:
        with open(CLUSTERS_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        _CLUSTERS_CACHE = data["clusters"]
    return _CLUSTERS_CACHE



def _tier_idx(tier: str) -> int:
    return TIER_ORDER.index(tier) if tier in TIER_ORDER else 0


def _match_cluster(cluster: dict, prediction, payload: dict,
                   clinical_context: dict | None = None) -> bool:
    req = cluster.get("requires") or {}
    risks_by_target = {r.target: r for r in prediction.risks}
    clinical_context = clinical_context or {}

    for target, min_tier in (req.get("risk_tier_at_least") or {}).items():
        r = risks_by_target.get(target)
        if r is None or _tier_idx(r.risk_tier) < _tier_idx(min_tier):
            return False

    for target, max_tier in (req.get("risk_tier_at_most") or {}).items():
        r = risks_by_target.get(target)
        if r is None or _tier_idx(r.risk_tier) > _tier_idx(max_tier):
            return False

    for target, p_min in (req.get("probability_at_least") or {}).items():
        r = risks_by_target.get(target)
        if r is None or r.probability < p_min:
            return False

    for target, p_max in (req.get("probability_at_most") or {}).items():
        r = risks_by_target.get(target)
        if r is None or r.probability > p_max:
            return False

    aa = req.get("any_at_least")
    if aa:
        min_tier = aa.get("tier", "moderate")
        need = aa.get("count", 1)
        target_subset = aa.get("in")
        candidates = prediction.risks
        if target_subset:
            candidates = [r for r in candidates if r.target in target_subset]
        n = sum(1 for r in candidates if _tier_idx(r.risk_tier) >= _tier_idx(min_tier))
        if n < need:
            return False

    am = req.get("all_at_most")
    if am:
        max_tier = am.get("tier", "low") if isinstance(am, dict) else am
        if isinstance(am, dict):
            max_tier = am.get("tier", "low")
        for r in prediction.risks:
            if _tier_idx(r.risk_tier) > _tier_idx(max_tier):
                return False

    nf_max = req.get("n_features_provided_at_most")
    if nf_max is not None and prediction.n_features_provided > nf_max:
        return False

    nf_min = req.get("n_features_provided_at_least")
    if nf_min is not None and prediction.n_features_provided < nf_min:
        return False

    labs_req = req.get("labs") or {}
    for lab, threshold in (labs_req.get("lab_at_least") or {}).items():
        v = payload.get(lab)
        if v is None or float(v) < threshold:
            return False
    for lab, threshold in (labs_req.get("lab_at_most") or {}).items():
        v = payload.get(lab)
        if v is None or float(v) > threshold:
            return False

    ctx_req = req.get("context_requires") or {}
    for flag, expected in ctx_req.items():
        actual = bool(clinical_context.get(flag))
        if bool(expected) != actual:
            return False

    subj_req = req.get("subjective_requires") or {}
    for field, condition in subj_req.items():
        val = payload.get(field)
        if isinstance(condition, bool):
            if bool(val) != condition:
                return False
        elif isinstance(condition, dict):
            if val is None:
                return False
            try:
                num = float(val)
            except (TypeError, ValueError):
                return False
            if "min" in condition and num < condition["min"]:
                return False
            if "max" in condition and num > condition["max"]:
                return False

    return True


def _select_clusters(prediction, payload: dict) -> List[dict]:
    clinical_context = _extract_clinical_context(payload)
    matched = [c for c in load_clusters()
               if _match_cluster(c, prediction, payload, clinical_context)]
    matched.sort(key=lambda c: (-c.get("priority", 0), c["id"]))
    suppressed: set = set()
    final = []
    for c in matched:
        if c["id"] in suppressed:
            continue
        final.append(c)
        for v in (c.get("suppresses") or []):
            suppressed.add(v)

    TERMINAL = {"low_overall_risk", "incomplete_panel", "mixed_signals"}
    real = [c for c in final if c["id"] not in TERMINAL]
    if real:
        final = real
    else:
        terminal_present = {c["id"] for c in final}
        if "incomplete_panel" in terminal_present:
            final = [c for c in final if c["id"] == "incomplete_panel"]
        elif "low_overall_risk" in terminal_present:
            final = [c for c in final if c["id"] == "low_overall_risk"]
        else:
            final = [c for c in final if c["id"] == "mixed_signals"][:1]

    return final



try:
    from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
    _ENV = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=False,
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )
    _HAS_JINJA = True
except Exception:
    _HAS_JINJA = False
    _ENV = None


def _render_template(cluster_id: str, lang: str, ctx: dict) -> str:
    name = f"{cluster_id}.{lang}.md"
    path = TEMPLATES_DIR / name
    if not path.exists():
        return ""
    if _ENV is not None:
        try:
            return _ENV.get_template(name).render(**ctx)
        except Exception as exc:
            log.warning(f"Jinja render failed for {name}: {exc}")
            return path.read_text(encoding="utf-8")
    return path.read_text(encoding="utf-8")



_FRONT_KEY_LINE = re.compile(r"^([a-z_]+)\s*:\s*(.+)$")
_LIST_ITEM = re.compile(r"^[-•]\s+(.+)$")
_SECTION_DIVIDER = "---"


def _parse_template_output(md: str, cluster: dict) -> tuple:
    sections = [s.strip() for s in md.split(f"\n{_SECTION_DIVIDER}\n")]
    while len(sections) < 4:
        sections.append("")

    title_block = sections[0]
    body = sections[1]
    actions_block = sections[2]
    red_flags_block = sections[3]

    title = ""
    icon = "ℹ"
    severity = "low"
    for line in title_block.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("# "):
            title = line[2:].strip()
            continue
        m = _FRONT_KEY_LINE.match(line)
        if m:
            k, v = m.group(1), m.group(2).strip()
            if k == "icon":
                icon = v
            elif k == "severity":
                severity = v

    def _parse_list(block: str, prefix_strip: List[str]) -> List[str]:
        items = []
        for line in block.splitlines():
            line = line.strip()
            for p in prefix_strip:
                if line.lower().startswith(p):
                    line = line[len(p):].strip()
            m = _LIST_ITEM.match(line)
            if m:
                items.append(m.group(1).strip())
        return items

    actions = _parse_list(actions_block, ["actions:"])
    red_flags = _parse_list(red_flags_block, ["red_flags:", "red flags:"])

    return title, icon, severity, body, actions, red_flags



def _derive_tone(stories: List[NarrativeStory]) -> str:
    if any(s.tier == "critical" for s in stories):
        return "urgent"
    if any(s.tier in ("abnormal", "info") for s in stories):
        return "attention_needed"
    return "normal"


def _summary_text(tone: str, lang: str, n_stories: int) -> str:
    if lang == "uk":
        return {
            "urgent": "Аналіз ризиків показав суттєві відхилення — варто звернутися до лікаря найближчим часом.",
            "attention_needed": "Аналіз ризиків виявив особливості, які варто обговорити з лікарем.",
            "normal": "Загальний ризик хронічних захворювань — низький. Так тримати!",
        }.get(tone, "Аналіз готовий.")
    else:
        return {
            "urgent": "Risk analysis flagged significant findings — please see a doctor soon.",
            "attention_needed": "Risk analysis identified things worth discussing with your doctor.",
            "normal": "Overall chronic disease risk is low. Keep it up!",
        }.get(tone, "Analysis ready.")


def _age_bucket(age: Optional[float]) -> Optional[str]:
    if age is None:
        return None
    if age < 18:
        return "child"
    if age < 30:
        return "young_adult"
    if age < 60:
        return "adult"
    return "senior"



def _lab(payload: dict, *keys: str):
    labs = payload.get("labs") or {}
    for k in keys:
        v = payload.get(k)
        if v is not None:
            return v
        v = labs.get(k) if isinstance(labs, dict) else None
        if v is not None:
            return v
    return None


def _baseline_pct(prediction, target: str) -> float:
    for r in prediction.risks:
        if r.target == target:
            return round(r.population_prevalence * 100, 1)
    return 0.0


def _build_context(prediction, payload: dict, lang: str) -> dict:
    risks_by_target = {r.target: r for r in prediction.risks}

    def prob(t):
        r = risks_by_target.get(t)
        return round(r.probability * 100, 1) if r else None

    def tier(t):
        r = risks_by_target.get(t)
        return r.risk_tier if r else None

    def ratio(t):
        r = risks_by_target.get(t)
        return round(r.odds_ratio_vs_baseline, 1) if r else None

    sex_raw = payload.get("sex")
    if isinstance(sex_raw, str):
        is_female = sex_raw.lower() in ("female", "f", "ж")
        is_male = sex_raw.lower() in ("male", "m", "ч")
    elif isinstance(sex_raw, (int, float)):
        is_female = sex_raw == 2
        is_male = sex_raw == 1
    else:
        is_female = is_male = False

    age = payload.get("age")
    age_int = int(age) if age is not None else None

    ctx = {
        "sex": sex_raw,
        "is_female": is_female,
        "is_male": is_male,
        "age": age_int,
        "age_bucket": _age_bucket(age),
        "bmi": payload.get("bmi"),
        "waist": payload.get("waist_cm"),
        "sbp": payload.get("sbp"),
        "dbp": payload.get("dbp"),

        "hba1c": _lab(payload, "hba1c", "a1c"),
        "glucose": _lab(payload, "glucose", "glucose_fasting"),
        "tchol": _lab(payload, "tchol", "total_cholesterol", "tchol_mgdl"),
        "hdl": _lab(payload, "hdl", "hdl_mgdl"),
        "trigly": _lab(payload, "trigly", "triglycerides", "trigly_mgdl"),
        "creatinine": _lab(payload, "creatinine", "creatinine_mgdl"),
        "crp": _lab(payload, "crp", "hs_crp"),
        "vit_d": _lab(payload, "vit_d_total", "vit_d", "vitamin_d"),
        "ferritin": _lab(payload, "ferritin_ngml", "ferritin"),
        "rdw": _lab(payload, "rdw"),

        "p_depression_moderate": prob("depression_moderate"),
        "p_depression_severe": prob("depression_severe"),
        "p_sleep_deficiency": prob("sleep_deficiency"),
        "p_daytime_dysfunction": prob("daytime_dysfunction"),
        "p_suicidal_ideation": prob("suicidal_ideation"),
        "p_snore_high": prob("snore_high"),
        "p_trouble_sleeping_high": prob("trouble_sleeping_high"),

        "tier_depression_moderate": tier("depression_moderate"),
        "tier_depression_severe": tier("depression_severe"),
        "tier_sleep_deficiency": tier("sleep_deficiency"),
        "tier_daytime_dysfunction": tier("daytime_dysfunction"),
        "tier_suicidal_ideation": tier("suicidal_ideation"),
        "tier_snore_high": tier("snore_high"),
        "tier_trouble_sleeping_high": tier("trouble_sleeping_high"),

        "ratio_depression_moderate": ratio("depression_moderate"),
        "ratio_depression_severe": ratio("depression_severe"),
        "ratio_sleep_deficiency": ratio("sleep_deficiency"),
        "ratio_daytime_dysfunction": ratio("daytime_dysfunction"),
        "ratio_suicidal_ideation": ratio("suicidal_ideation"),
        "ratio_snore_high": ratio("snore_high"),
        "ratio_trouble_sleeping_high": ratio("trouble_sleeping_high"),

        "baseline_depression_moderate": _baseline_pct(prediction, "depression_moderate"),
        "baseline_depression_severe": _baseline_pct(prediction, "depression_severe"),
        "baseline_sleep_deficiency": _baseline_pct(prediction, "sleep_deficiency"),
        "baseline_daytime_dysfunction": _baseline_pct(prediction, "daytime_dysfunction"),
        "baseline_suicidal_ideation": _baseline_pct(prediction, "suicidal_ideation"),
        "baseline_snore_high": _baseline_pct(prediction, "snore_high"),
        "baseline_trouble_sleeping_high": _baseline_pct(prediction, "trouble_sleeping_high"),

        "overall_tier": prediction.overall_tier,
        "n_features_provided": prediction.n_features_provided,

        "lang": lang,
    }

    for fld in ("sleep_hours_avg", "sleep_latency_min", "night_awakenings",
                "early_morning_awakening", "sleep_quality_subjective",
                "uses_sleep_meds", "naps_per_week",
                "screen_time_before_bed_min", "caffeine_servings_per_day",
                "shift_work", "snoring", "witnessed_apnea",
                "phq9_score", "gad7_score", "recent_life_stressors",
                "exercise_minutes_per_week", "social_support_low",
                "chronic_pain"):
        ctx[fld] = payload.get(fld)

    ctx.update(_extract_clinical_context(payload))

    _DEFAULTS = (
        "sleep_hours_avg", "sleep_latency_min", "night_awakenings",
        "early_morning_awakening", "sleep_quality_subjective",
        "uses_sleep_meds", "naps_per_week", "screen_time_before_bed_min",
        "caffeine_servings_per_day", "shift_work", "snoring",
        "witnessed_apnea",
        "phq9_score", "gad7_score", "recent_life_stressors",
        "exercise_minutes_per_week", "social_support_low", "chronic_pain",
        "has_depression_history", "has_anxiety_history", "has_bipolar",
        "has_hypothyroidism", "has_diabetes", "has_chronic_pain",
        "has_hypertension", "has_cardiovascular_disease",
        "on_antidepressants", "on_anxiolytics", "on_sleep_meds",
        "on_thyroid_meds", "on_stimulants",
        "alcohol_regular", "smoker", "sedentary",
    )
    for _flag in _DEFAULTS:
        ctx.setdefault(_flag, None)

    return ctx


def _extract_clinical_context(payload: dict) -> dict:
    ctx_root = payload.get("context") or {}
    if not isinstance(ctx_root, dict):
        return {}

    clin = ctx_root.get("clinical")
    if isinstance(clin, dict) and clin:
        raw = clin
    else:
        raw = ctx_root

    if not isinstance(raw, dict):
        return {}

    out: Dict[str, bool] = {}

    def b(k):
        v = raw.get(k)
        return bool(v) if v is not None else False

    direct = (
        "has_depression_history", "has_anxiety_history", "has_bipolar",
        "has_hypothyroidism", "has_diabetes", "has_chronic_pain",
        "on_antidepressants", "on_anxiolytics", "on_sleep_meds",
        "on_thyroid_meds", "on_stimulants",
        "alcohol_regular", "smoker", "sedentary",
    )
    for k in direct:
        if k in raw:
            out[k] = bool(raw[k])

    pairs = [
        ("has_depression_history", ("has_mdd", "depressed", "depression_history")),
        ("has_anxiety_history",    ("has_gad", "anxious", "anxiety_history")),
        ("on_antidepressants",     ("takes_antidepressants", "on_ssri", "on_snri",
                                    "on_tca", "takes_ssri")),
        ("on_anxiolytics",         ("takes_benzo", "takes_benzodiazepines",
                                    "on_benzodiazepines", "on_benzos")),
        ("on_sleep_meds",          ("takes_sleep_aids", "on_hypnotics",
                                    "on_zolpidem", "on_melatonin")),
        ("has_hypothyroidism",     ("has_hypothyroid", "low_thyroid")),
        ("on_thyroid_meds",        ("takes_thyroid", "on_levothyroxine")),
        ("chronic_pain",           ("has_chronic_pain", "fibromyalgia",
                                    "has_fibro")),
    ]
    for canonical, aliases in pairs:
        if canonical in out and out[canonical]:
            continue
        for a in aliases:
            if a in raw and bool(raw[a]):
                out[canonical] = True
                break

    if out.get("on_thyroid_meds"):
        out.setdefault("has_hypothyroidism", True)
    if out.get("on_antidepressants"):
        out.setdefault("has_depression_history", True)
    if out.get("on_anxiolytics"):
        out.setdefault("has_anxiety_history", True)

    return out



def _insufficient_data_report(prediction, payload: dict, lang: str) -> "NarrativeReport":
    n_provided = prediction.n_features_provided
    n_total = prediction.n_features_total

    if lang == "uk":
        summary = ("Даних недостатньо для надійної оцінки ризику. "
                   "Будь ласка, надайте розширену панель аналізів.")
        title = "Недостатньо даних для оцінки"
        body = (
            "Модель отримала лише {n_provided} з {n_total} очікуваних показників. "
            "Цього замало для побудови повноцінного ризик-профілю.\n\n"
            "Для коректної роботи моделі рекомендовано надати:\n"
            "• Загальний аналіз крові (CBC): WBC, RBC, Hb, Hct, MCV, RDW, PLT\n"
            "• Біохімію (CHEM): глюкоза, HbA1c, креатинін, ALT/AST, "
            "ліпідограма (загальний холестерин, HDL, тригліцериди)\n"
            "• Артеріальний тиск (систолічний і діастолічний)\n"
            "• Антропометричні дані: BMI, окружність талії"
        ).format(n_provided=n_provided, n_total=n_total)
        actions = [
            "Звернутися до сімейного лікаря для повного обстеження",
            "Здати загальний і біохімічний аналізи крові",
            "Виміряти артеріальний тиск (3-7 днів зранку і ввечері)",
            "Повторно запустити аналіз з повнішими даними",
        ]
        red_flags: List[str] = []
    else:
        summary = ("Insufficient data for a reliable risk estimate. "
                   "Please provide a broader laboratory panel.")
        title = "Insufficient data for assessment"
        body = (
            "The model received only {n_provided} of {n_total} expected features. "
            "This is not enough to build a reliable risk profile.\n\n"
            "For meaningful results, please provide:\n"
            "• Complete blood count (CBC): WBC, RBC, Hb, Hct, MCV, RDW, PLT\n"
            "• Chemistry panel: glucose, HbA1c, creatinine, ALT/AST, "
            "lipid panel (total cholesterol, HDL, triglycerides)\n"
            "• Blood pressure (systolic and diastolic)\n"
            "• Anthropometrics: BMI, waist circumference"
        ).format(n_provided=n_provided, n_total=n_total)
        actions = [
            "See your primary care physician for a comprehensive workup",
            "Get a CBC and full chemistry panel",
            "Measure blood pressure (morning and evening for 3-7 days)",
            "Re-run the analysis with a more complete dataset",
        ]
        red_flags = []

    story = NarrativeStory(
        cluster_id="insufficient_data",
        tier="info",
        icon="ℹ️",
        title=title,
        body=body,
        actions=actions,
        red_flags=red_flags,
        severity="low",
        risks_used=[r.target for r in prediction.risks],
    )

    sex_raw = payload.get("sex")
    sex_str = (str(sex_raw).lower() if sex_raw is not None else None)
    patient = {
        "sex": sex_str,
        "age": payload.get("age"),
        "age_bucket": _age_bucket(payload.get("age")),
    }

    risks_serialized = [
        {
            "target": r.target,
            "name_ua": r.name_ua,
            "name_en": r.name_en,
            "probability": round(r.probability, 4),
            "risk_tier": "uncertain",
            "population_prevalence": round(r.population_prevalence, 4),
            "odds_ratio_vs_baseline": round(r.odds_ratio_vs_baseline, 3),
        }
        for r in prediction.risks
    ]

    return NarrativeReport(
        summary=summary,
        tone="neutral",
        lang=lang,
        patient=patient,
        overall_tier="insufficient_data",
        stories=[story],
        risks=risks_serialized,
    )


def build_narrative(prediction, lang: str = "uk", payload: Optional[dict] = None) -> NarrativeReport:
    if lang not in ("uk", "en"):
        lang = "en"
    payload = payload or {}

    if prediction.overall_tier == "insufficient_data":
        return _insufficient_data_report(prediction, payload, lang)

    selected = _select_clusters(prediction, payload)
    ctx = _build_context(prediction, payload, lang)

    stories: List[NarrativeStory] = []
    for cluster in selected:
        md = _render_template(cluster["id"], lang, ctx).strip()
        if not md:
            md = f"# {cluster['id']}\nicon: ℹ\nseverity: low\n---\nNo template available.\n---\nactions:\n---\nred_flags:"
        title, icon, severity, body, actions, red_flags = _parse_template_output(md, cluster)
        stories.append(NarrativeStory(
            cluster_id=cluster["id"],
            tier=cluster.get("tier", "info"),
            icon=icon,
            title=title or cluster["id"].replace("_", " ").title(),
            body=body,
            actions=actions,
            red_flags=red_flags,
            severity=severity,
            risks_used=[r.target for r in prediction.risks],
        ))

    tone = _derive_tone(stories)
    summary = _summary_text(tone, lang, len(stories))

    sex_raw = payload.get("sex")
    sex_str = (str(sex_raw).lower() if sex_raw is not None else None)

    patient = {
        "sex": sex_str,
        "age": payload.get("age"),
        "age_bucket": _age_bucket(payload.get("age")),
    }

    risks_serialized = [
        {
            "target": r.target,
            "name_ua": r.name_ua,
            "name_en": r.name_en,
            "probability": round(r.probability, 4),
            "risk_tier": r.risk_tier,
            "population_prevalence": round(r.population_prevalence, 4),
            "odds_ratio_vs_baseline": round(r.odds_ratio_vs_baseline, 3),
        }
        for r in prediction.risks
    ]

    return NarrativeReport(
        summary=summary,
        tone=tone,
        lang=lang,
        patient=patient,
        overall_tier=prediction.overall_tier,
        stories=stories,
        risks=risks_serialized,
    )
