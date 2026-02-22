from __future__ import annotations

import os
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional

try:
    import yaml                              # type: ignore
except ImportError as e:                    # pragma: no cover
    raise ImportError(
        "PyYAML is required for the narrative layer — `pip install pyyaml`"
    ) from e

try:
    from jinja2 import Environment, BaseLoader, ChainableUndefined  # type: ignore
    _HAS_JINJA = True
except ImportError:
    _HAS_JINJA = False



TIER_ORDER = {"critical": 0, "abnormal": 1, "info": 2, "minor": 3, "normal": 4}

SEV_NUMERIC = {"low": 1, "medium": 2, "high": 3}


@dataclass
class NarrativeStory:
    cluster_id: str
    tier: str
    icon: str
    title: str
    body: str
    actions: list[str] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)
    signals_used: list[str] = field(default_factory=list)
    severity: str = "low"


@dataclass
class NarrativeReport:
    stories: list[NarrativeStory] = field(default_factory=list)
    summary: str = ""
    tone: str = "normal"
    lang: str = "uk"
    patient: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "summary":  self.summary,
            "tone":     self.tone,
            "lang":     self.lang,
            "patient":  self.patient,
            "stories":  [asdict(s) for s in self.stories],
        }



_TEMPLATE_DIR = Path(__file__).parent / "templates"
_CLUSTERS_PATH = Path(__file__).parent / "clusters.yaml"

_jinja_env: Optional["Environment"] = None


def _ensure_jinja() -> Optional["Environment"]:
    global _jinja_env
    if not _HAS_JINJA:
        return None
    if _jinja_env is None:
        _jinja_env = Environment(
            loader=BaseLoader(),
            undefined=ChainableUndefined,
            trim_blocks=False,
            lstrip_blocks=True,
            keep_trailing_newline=False,
        )
    return _jinja_env


_FALLBACK_VAR = re.compile(r"\{\{\s*([a-zA-Z_][\w\.]*)\s*\}\}")
_FALLBACK_IF_BLOCK = re.compile(
    r"\{%\s*if\s+(.+?)\s*%\}(.*?)(?:\{%\s*else\s*%\}(.*?))?\{%\s*endif\s*%\}",
    re.DOTALL,
)


def _fallback_render(template_text: str, ctx: dict) -> str:
    def resolve(path: str) -> Any:
        cur: Any = ctx
        for part in path.split("."):
            if isinstance(cur, dict):
                cur = cur.get(part)
            else:
                cur = getattr(cur, part, None)
            if cur is None:
                return ""
        return cur

    def if_sub(m: re.Match) -> str:
        cond, ifblock, elseblock = m.group(1), m.group(2), m.group(3) or ""
        try:
            val = eval(cond, {"__builtins__": {}}, ctx)
        except Exception:
            val = resolve(cond)
        return ifblock if val else elseblock

    prev = None
    while template_text != prev:
        prev = template_text
        template_text = _FALLBACK_IF_BLOCK.sub(if_sub, template_text)

    return _FALLBACK_VAR.sub(lambda m: str(resolve(m.group(1)) or ""), template_text)


def _render_template(name: str, lang: str, ctx: dict) -> str:
    for candidate in (f"{name}.{lang}.md", f"{name}.en.md"):
        path = _TEMPLATE_DIR / candidate
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            env = _ensure_jinja()
            if env is not None:
                return env.from_string(text).render(**ctx)
            return _fallback_render(text, ctx)
    return ""



_CLUSTERS_CACHE: Optional[list[dict]] = None


def load_clusters() -> list[dict]:
    global _CLUSTERS_CACHE
    if _CLUSTERS_CACHE is None:
        with open(_CLUSTERS_PATH, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        _CLUSTERS_CACHE = raw["clusters"]
    return _CLUSTERS_CACHE



def _signals_by_id(raw: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for s in raw.get("signals", []):
        sid = s.get("id")
        if sid:
            out[sid] = s
    return out


def _match_cluster(cluster: dict, sigs: dict[str, dict], age: Optional[float],
                   labs: Optional[dict[str, dict]] = None) -> bool:
    req = cluster.get("requires", {})

    need_all = req.get("signals_all") or []
    if need_all and not all(s in sigs for s in need_all):
        return False

    need_any = req.get("signals_any") or []
    if need_any and not any(s in sigs for s in need_any):
        return False

    forbid = req.get("signals_none") or []
    if forbid and any(s in sigs for s in forbid):
        return False

    sev_req = req.get("signal_severity_at_least") or {}
    for sig_id, min_sev in sev_req.items():
        actual = sigs.get(sig_id, {}).get("severity", "low")
        if SEV_NUMERIC.get(actual, 0) < SEV_NUMERIC.get(min_sev, 0):
            return False

    labs = labs or {}
    for lab_code, threshold in (req.get("lab_at_least") or {}).items():
        v = (labs.get(lab_code) or {}).get("value")
        if v is None or float(v) < float(threshold):
            return False
    for lab_code, threshold in (req.get("lab_at_most") or {}).items():
        v = (labs.get(lab_code) or {}).get("value")
        if v is None or float(v) > float(threshold):
            return False

    age_min = req.get("age_at_least")
    if age_min is not None and (age is None or age < age_min):
        return False
    age_max = req.get("age_at_most")
    if age_max is not None and (age is None or age > age_max):
        return False

    return True


def _select_clusters(raw: dict, age: Optional[float]) -> list[dict]:
    sigs = _signals_by_id(raw)
    labs = _labs_by_code(raw)
    matched = []
    for cl in load_clusters():
        if _match_cluster(cl, sigs, age, labs):
            matched.append(cl)

    matched.sort(key=lambda c: (-c.get("priority", 0), c["id"]))

    suppressed: set[str] = set()
    final = []
    for cl in matched:
        if cl["id"] in suppressed:
            continue
        final.append(cl)
        for victim in cl.get("suppresses", []) or []:
            suppressed.add(victim)

    _TERMINAL = {"incomplete", "all_normal"}
    real_findings = [c for c in final if c["id"] not in _TERMINAL]
    if real_findings:
        final = real_findings
    else:
        terminal_ids = {c["id"] for c in final}
        if "incomplete" in terminal_ids and "all_normal" in terminal_ids:
            final = [c for c in final if c["id"] != "all_normal"]

    return final



def _labs_by_code(raw: dict) -> dict[str, dict]:
    out = {}
    for lab in raw.get("labs", []):
        code = lab.get("code")
        if code:
            out[code] = lab
    return out


def _sig_sev(sigs: dict[str, dict], sig_id: str) -> str:
    return sigs.get(sig_id, {}).get("severity", "low")


def _build_context(raw: dict) -> dict:
    prof = raw.get("profile", {}) or {}
    labs = _labs_by_code(raw)
    sigs = _signals_by_id(raw)

    _clinical = ((raw.get("meta") or {}).get("context") or {}).get("clinical") or {}
    if not isinstance(_clinical, dict):
        _clinical = {}

    def _ctx_flag(*keys):
        return any(bool(_clinical.get(k)) for k in keys)

    def labval(code: str, key: str = "value"):
        lab = labs.get(code, {})
        return lab.get(key)

    def labref(code: str, side: str):
        lab = labs.get(code, {})
        return (lab.get("ref", {}) or {}).get(side)

    age = prof.get("age")
    sex = prof.get("sex")

    sex_norm = None
    if sex is not None:
        s = str(sex).strip().lower()
        if s in {"1", "m", "male", "man", "ч"}:
            sex_norm = "male"
        elif s in {"2", "f", "female", "woman", "ж"}:
            sex_norm = "female"

    age_bucket = None
    if isinstance(age, (int, float)):
        if age < 12:     age_bucket = "child"
        elif age < 18:   age_bucket = "teen"
        elif age < 35:   age_bucket = "young_adult"
        elif age < 65:   age_bucket = "adult"
        else:            age_bucket = "senior"

    return {
        "sex":      sex_norm,
        "is_female": sex_norm == "female",
        "is_male":   sex_norm == "male",
        "age":      age,
        "age_bucket": age_bucket,

        "hgb":      labval("hgb"),
        "hgb_low":  labref("hgb", "low"),
        "hgb_high": labref("hgb", "high"),
        "mcv":      labval("mcv"),
        "mcv_low":  labref("mcv", "low"),
        "mcv_high": labref("mcv", "high"),
        "rdw":      labval("rdw"),
        "rdw_high": labref("rdw", "high"),
        "mchc":     labval("mchc"),
        "mchc_low": labref("mchc", "low"),
        "wbc":      labval("wbc"),
        "wbc_low":  labref("wbc", "low"),
        "wbc_high": labref("wbc", "high"),
        "anc":      labval("anc"),
        "alc":      labval("alc"),
        "plt":      labval("plt"),
        "plt_low":  labref("plt", "low"),
        "plt_high": labref("plt", "high"),
        "hct":      labval("hct"),
        "hct_low":  labref("hct", "low"),
        "hct_high": labref("hct", "high"),

        "anemia_sev":        _sig_sev(sigs, "anemia_possible"),
        "thrombocytopenia_sev": _sig_sev(sigs, "thrombocytopenia"),
        "leukopenia_sev":    _sig_sev(sigs, "leukopenia"),
        "neutropenia_sev":   _sig_sev(sigs, "neutropenia"),

        "has_diabetes":              bool(_clinical.get("has_diabetes")),
        "has_hypertension":          bool(_clinical.get("has_hypertension")),
        "has_ckd":                   bool(_clinical.get("has_ckd")),
        "has_liver_disease":         bool(_clinical.get("has_liver_disease")),
        "has_cardiovascular_disease": bool(_clinical.get("has_cardiovascular_disease")),
        "on_statins":                bool(_clinical.get("on_statins")),
        "on_acei_arb":               bool(_clinical.get("on_acei_arb")),
        "on_diuretics":              bool(_clinical.get("on_diuretics")),
        "on_oral_diabetics":         bool(_clinical.get("on_oral_diabetics")),
        "on_insulin":                bool(_clinical.get("on_insulin")),
        "on_corticosteroids":        _ctx_flag("on_corticosteroids", "takes_corticosteroids"),
        "on_oral_anticoagulants":    _ctx_flag("on_oral_anticoagulants", "takes_anticoagulants"),
        "pregnant":                  bool(_clinical.get("pregnant")),

        "smoker":                    bool(_clinical.get("smoker")),
        "alcohol_regular":           bool(_clinical.get("alcohol_regular")),
        "sedentary":                 bool(_clinical.get("sedentary")),
        "takes_chemotherapy":        bool(_clinical.get("takes_chemotherapy")),
        "takes_thyroid_meds":        bool(_clinical.get("takes_thyroid_meds")),
        "has_thyroid":               bool(_clinical.get("has_thyroid")),
        "has_autoimmune":            bool(_clinical.get("has_autoimmune")),
        "has_cancer_history":        bool(_clinical.get("has_cancer_history")),

        "esr":                       labval("esr"),
        "esr_high":                  (labval("esr") is not None
                                      and labref("esr", "high") is not None
                                      and labval("esr") > labref("esr", "high")),
        "crp":                       labval("crp"),
        "crp_high":                  (labval("crp") is not None
                                      and labref("crp", "high") is not None
                                      and labval("crp") > labref("crp", "high")),

        "not_known_diabetic":  not bool(_clinical.get("has_diabetes")),
        "not_on_statins":      not bool(_clinical.get("on_statins")),

        "labs":     labs,
        "signals":  sigs,
        "profile":  prof,
    }



_CHROME: dict[str, dict] = {
    "uk": {
        "tier_label": {
            "critical": "🔴 Потрібна термінова увага",
            "abnormal": "⚠️ Потребує уваги",
            "info":     "ℹ️ Варто знати",
            "minor":    "ℹ️ Дрібне відхилення",
            "normal":   "✅ Все в порядку",
        },
        "summary": {
            "urgent":            "Знайдено серйозне відхилення — зверніться до лікаря в найближчий час.",
            "attention_needed":  "Є знахідки, які варто обговорити з лікарем.",
            "normal":            "Аналіз виглядає добре — жодних значущих відхилень.",
            "incomplete":        "Аналіз неповний — недостатньо даних для інтерпретації.",
        },
        "actions_header":    "Що робити далі",
        "red_flags_header":  "Коли звертатися терміново",
        "this_is_not_diagnosis": "Цей аналіз — лише скринінг, а не діагноз. Фінальне рішення — за лікарем.",
    },
    "en": {
        "tier_label": {
            "critical": "🔴 Urgent attention needed",
            "abnormal": "⚠️ Needs attention",
            "info":     "ℹ️ Good to know",
            "minor":    "ℹ️ Minor finding",
            "normal":   "✅ Looks good",
        },
        "summary": {
            "urgent":            "A serious abnormality was found — see a doctor soon.",
            "attention_needed":  "There are findings worth discussing with your doctor.",
            "normal":            "Your results look good — no significant findings.",
            "incomplete":        "Analysis incomplete — insufficient data to interpret.",
        },
        "actions_header":    "What to do next",
        "red_flags_header":  "When to seek urgent care",
        "this_is_not_diagnosis": "This is a screening tool, not a diagnosis. Final interpretation rests with your doctor.",
    },
}


def chrome(lang: str) -> dict:
    return _CHROME.get(lang) or _CHROME["en"]



def build_narrative(raw_result: dict, lang: str = "uk") -> NarrativeReport:
    lang = lang if lang in _CHROME else "en"
    prof = raw_result.get("profile", {}) or {}
    age = prof.get("age")
    ctx = _build_context(raw_result)

    selected = _select_clusters(raw_result, age)

    stories: list[NarrativeStory] = []
    tiers_seen: set[str] = set()

    for cl in selected:
        md = _render_template(cl["id"], lang, ctx).strip()
        if not md:
            md = f"*{cl['id']}* — no narrative template available."

        story = _parse_template_output(md, cluster=cl, ctx=ctx)
        stories.append(story)
        tiers_seen.add(cl.get("tier", "info"))

    if "critical" in tiers_seen:
        tone = "urgent"
    elif "abnormal" in tiers_seen:
        tone = "attention_needed"
    elif any(s.cluster_id == "incomplete" for s in stories):
        tone = "incomplete"
    else:
        tone = "normal"

    ch = chrome(lang)
    summary = ch["summary"][tone]

    return NarrativeReport(
        stories=stories,
        summary=summary,
        tone=tone,
        lang=lang,
        patient={"sex": ctx.get("sex"), "age": ctx.get("age"),
                 "age_bucket": ctx.get("age_bucket")},
    )



_FRONT_MATTER_LINE = re.compile(r"^([a-z_]+):\s*(.+)$")
_LIST_ITEM = re.compile(r"^\s*-\s+(.+)$")

def _parse_template_output(md: str, cluster: dict, ctx: dict) -> NarrativeStory:
    parts = [p.strip() for p in md.split("\n---\n")]
    head = parts[0] if parts else ""
    body = parts[1] if len(parts) > 1 else ""
    rest = parts[2:]

    title = ""
    icon = ""
    severity = "low"
    for line in head.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("# "):
            title = line[2:].strip()
            continue
        m = _FRONT_MATTER_LINE.match(line)
        if m:
            k, v = m.group(1), m.group(2).strip()
            if k == "icon":     icon = v
            elif k == "severity": severity = v

    actions: list[str] = []
    red_flags: list[str] = []
    for block in rest:
        first_line = block.split("\n", 1)[0].strip()
        if first_line.startswith("actions:"):
            for ln in block.splitlines()[1:]:
                m = _LIST_ITEM.match(ln)
                if m: actions.append(m.group(1).strip())
        elif first_line.startswith("red_flags:"):
            for ln in block.splitlines()[1:]:
                m = _LIST_ITEM.match(ln)
                if m: red_flags.append(m.group(1).strip())

    signals_used = []
    req = cluster.get("requires", {}) or {}
    for key in ("signals_all", "signals_any"):
        for s in (req.get(key) or []):
            if s not in signals_used:
                signals_used.append(s)

    return NarrativeStory(
        cluster_id = cluster["id"],
        tier       = cluster.get("tier", "info"),
        icon       = icon or "•",
        title      = title or cluster["id"],
        body       = body,
        actions    = actions,
        red_flags  = red_flags,
        signals_used = signals_used,
        severity   = severity,
    )


__all__ = [
    "NarrativeReport",
    "NarrativeStory",
    "build_narrative",
    "load_clusters",
    "chrome",
]
