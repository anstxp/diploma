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



def _normalize_lab_to_us_units(value, lab_name: str):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None

    s = value.strip().lower()
    import re as _re
    m = _re.match(r"^[-+]?(\d+(?:[.,]\d+)?)", s)
    if not m:
        return None
    try:
        num = float(m.group(1).replace(",", "."))
    except ValueError:
        return None

    has_mmol = "mmol" in s
    has_umol = "µmol" in s or "umol" in s or "мкмоль" in s
    has_mgdl = "mg/dl" in s or "мг/дл" in s
    has_gl   = (" g/l" in s or s.endswith("g/l")
                or " г/л" in s or s.endswith("г/л"))

    name = lab_name.lower()

    if name in ("glucose", "glucose_fasting", "fasting_glucose"):
        if has_mmol:
            return round(num * 18.0182, 1)
        if has_mgdl:
            return num
        return round(num * 18.0182, 1) if num <= 25 else num

    if name in ("tchol", "total_cholesterol", "hdl", "ldl"):
        if has_mmol:
            return round(num * 38.67, 1)
        if has_mgdl:
            return num
        return round(num * 38.67, 1) if num <= 15 else num
    if name in ("trigly", "triglycerides"):
        if has_mmol:
            return round(num * 88.57, 1)
        if has_mgdl:
            return num
        return round(num * 88.57, 1) if num <= 15 else num

    if name in ("creatinine",):
        if has_umol:
            return round(num / 88.4017, 2)
        if has_mgdl:
            return num
        return num if num <= 10 else round(num / 88.4017, 2)

    if name in ("hba1c", "a1c"):
        return round(num, 1)

    if name in ("crp", "hs_crp"):
        return num

    return num


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

    lower = {str(k).lower(): bool(v) for k, v in raw.items()
             if not isinstance(v, (dict, list))}

    def any_of(*keys) -> bool:
        return any(lower.get(k, False) for k in keys)

    return {
        "has_diabetes": any_of("has_diabetes", "diabetic", "has_t2dm", "has_dm"),
        "has_hypertension": any_of("has_hypertension", "has_htn", "hypertensive"),
        "has_cardiovascular_disease": any_of(
            "has_cardiovascular_disease", "has_cv_disease", "has_cvd",
            "has_chd", "has_cad", "has_cardiac"
        ),
        "has_high_chol": any_of("has_high_chol", "has_dyslipidemia",
                                 "has_hyperlipidemia", "hypercholesterolemic"),
        "has_ckd": any_of("has_ckd", "has_kidney_disease", "ckd"),
        "has_chf": any_of("has_chf", "has_heart_failure", "has_hf"),
        "had_stroke": any_of("had_stroke", "has_stroke_history", "post_stroke"),
        "pregnant": any_of("pregnant", "is_pregnant", "pregnancy"),
        "smoker": any_of("smoker", "smokes", "current_smoker"),
        "on_statins": any_of("on_statins", "takes_statins"),
        "on_acei_arb": any_of("on_acei_arb", "takes_acei_arb", "on_acei",
                              "on_arb", "takes_acei", "takes_arb"),
        "on_diuretics": any_of("on_diuretics", "takes_diuretics"),
        "on_oral_diabetics": any_of("on_oral_diabetics", "takes_oral_diabetics",
                                     "on_oral_hypoglycemics"),
        "takes_metformin": any_of("takes_metformin", "on_metformin"),
        "on_insulin": any_of("on_insulin", "takes_insulin"),
        "on_antihypertensives": any_of("on_antihypertensives",
                                        "takes_antihypertensives", "on_bp_meds"),
        "on_oral_anticoagulants": any_of("on_oral_anticoagulants",
                                          "takes_anticoagulants", "on_doac",
                                          "on_warfarin"),
    }


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

        "hba1c": _normalize_lab_to_us_units(_lab(payload, "hba1c", "a1c"), "hba1c"),
        "glucose": _normalize_lab_to_us_units(_lab(payload, "glucose", "glucose_fasting"), "glucose"),
        "tchol": _normalize_lab_to_us_units(_lab(payload, "tchol", "total_cholesterol", "tchol_mgdl"), "tchol"),
        "hdl": _normalize_lab_to_us_units(_lab(payload, "hdl", "hdl_mgdl"), "hdl"),
        "trigly": _normalize_lab_to_us_units(_lab(payload, "trigly", "triglycerides", "trigly_mgdl"), "trigly"),
        "creatinine": _normalize_lab_to_us_units(_lab(payload, "creatinine", "creatinine_mgdl"), "creatinine"),
        "crp": _normalize_lab_to_us_units(_lab(payload, "crp", "hs_crp"), "crp"),

        "p_htn": prob("told_htn"),
        "p_diabetes": prob("told_diabetes"),
        "p_high_chol": prob("told_high_chol"),
        "p_chd": prob("told_chd"),
        "p_chf": prob("told_chf"),
        "p_stroke": prob("told_stroke"),

        "tier_htn": tier("told_htn"),
        "tier_diabetes": tier("told_diabetes"),
        "tier_high_chol": tier("told_high_chol"),
        "tier_chd": tier("told_chd"),
        "tier_chf": tier("told_chf"),
        "tier_stroke": tier("told_stroke"),

        "ratio_htn": ratio("told_htn"),
        "ratio_diabetes": ratio("told_diabetes"),
        "ratio_high_chol": ratio("told_high_chol"),
        "ratio_chd": ratio("told_chd"),
        "ratio_chf": ratio("told_chf"),
        "ratio_stroke": ratio("told_stroke"),

        "overall_tier": prediction.overall_tier,
        "n_features_provided": prediction.n_features_provided,

        "lang": lang,
    }

    ctx.update(_extract_clinical_context(payload))

    ctx["on_any_therapy"] = (
        ctx.get("on_statins") or ctx.get("on_acei_arb")
        or ctx.get("on_diuretics") or ctx.get("on_oral_diabetics")
        or ctx.get("takes_metformin") or ctx.get("on_insulin")
        or ctx.get("on_antihypertensives") or ctx.get("on_oral_anticoagulants")
    )
    ctx["has_any_chronic"] = (
        ctx.get("has_diabetes") or ctx.get("has_hypertension")
        or ctx.get("has_cardiovascular_disease") or ctx.get("has_ckd")
        or ctx.get("has_chf") or ctx.get("had_stroke")
        or ctx.get("has_high_chol")
    )

    return ctx



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
