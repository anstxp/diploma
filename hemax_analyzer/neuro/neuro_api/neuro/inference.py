from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import torch

from .model import HemaxRiskNet, ModelConfig, load_model

log = logging.getLogger(__name__)



ALIASES = {
    "wbc": "wbc", "leukocytes": "wbc",
    "rbc": "rbc", "erythrocytes": "rbc",
    "hgb": "hb_gdl", "hemoglobin": "hb_gdl", "hb": "hb_gdl",
    "hct": "hct", "hematocrit": "hct",
    "mcv": "mcv", "mch": "mch", "mchc": "mchc", "rdw": "rdw",
    "plt": "plt", "platelets": "plt",
    "mpv": "mpv",
    "neut_pct": "neut_pct", "neutrophils_pct": "neut_pct",
    "lymph_pct": "lymph_pct", "lymphocytes_pct": "lymph_pct",
    "mono_pct": "mono_pct", "monocytes_pct": "mono_pct",
    "eos_pct": "eos_pct", "eosinophils_pct": "eos_pct",
    "baso_pct": "baso_pct", "basophils_pct": "baso_pct",
    "glucose": "glucose_fasting", "glucose_fasting": "glucose_fasting",
    "a1c": "hba1c_pct", "hba1c": "hba1c_pct", "hba1c_pct": "hba1c_pct",
    "creatinine": "creatinine_mgdl", "creatinine_mgdl": "creatinine_mgdl",
    "bun": "bun_mgdl", "bun_mgdl": "bun_mgdl",
    "uric_acid": "uric_acid_mgdl",
    "alt": "alt_ul", "ast": "ast_ul", "alp": "alp_ul", "ggt": "ggt_ul",
    "albumin": "albumin_gdl",
    "total_protein": "protein_total_gdl", "protein_total": "protein_total_gdl",
    "bilirubin": "bilirubin_total", "bilirubin_total": "bilirubin_total",
    "sodium": "sodium_mmoll", "potassium": "potassium_mmoll",
    "chloride": "chloride_mmoll", "bicarbonate": "bicarbonate_mmoll",
    "calcium": "calcium_mgdl", "phosphorus": "phosphorus_mgdl", "phosphate": "phosphorus_mgdl",
    "tchol": "tchol_mgdl", "total_cholesterol": "tchol_mgdl",
    "hdl": "hdl_mgdl", "trigly": "trigly_mgdl", "triglycerides": "trigly_mgdl",
    "crp": "hs_crp", "hs_crp": "hs_crp",
    "ferritin": "ferritin_ngml",
    "vitd_25oh": "vit_d_total", "vitamin_d": "vit_d_total", "vit_d": "vit_d_total",
    "age": "age_years", "age_years": "age_years",
    "sex": "sex",
    "bmi": "bmi",
    "waist": "waist_cm", "waist_cm": "waist_cm",
    "sbp": "sbp", "dbp": "dbp",
    "pulse": "pulse", "heart_rate": "pulse",
    "income_ratio": "income_ratio",
    "poverty_income_ratio": "income_ratio",
    "pir": "income_ratio",
    "edu_level": "edu_level",
    "education": "edu_level",
    "metsyn_criteria_count": "metsyn_criteria_count",
    "metsyn_count": "metsyn_criteria_count",
    "arm_circ_cm": "arm_circ_cm",
    "arm_circumference": "arm_circ_cm",
    "iron_chem_ugdl": "iron_chem_ugdl",
    "serum_iron": "iron_chem_ugdl",
    "iron": "iron_chem_ugdl",
    "non_hdl_mgdl": "non_hdl_mgdl",
    "non_hdl": "non_hdl_mgdl",
    "fib4": "fib4",
    "fib_4": "fib4",
    "globulin_gdl": "globulin_gdl",
    "globulin": "globulin_gdl",
    "egfr_ckd_epi_2021": "egfr_ckd_epi_2021",
    "egfr": "egfr_ckd_epi_2021",
    "egfr_ckd_epi": "egfr_ckd_epi_2021",
    "homa_ir": "homa_ir",
    "sedentary_min_day": "sedentary_min_day",
    "sedentary_minutes": "sedentary_min_day",
}



@dataclass
class TaskRiskResult:
    target: str
    name_ua: str
    name_en: str
    probability: float
    risk_tier: str
    population_prevalence: float
    probability_ratio_vs_baseline: float
    @property
    def odds_ratio_vs_baseline(self) -> float:
        return self.probability_ratio_vs_baseline


@dataclass
class FeatureContribution:
    feature: str
    value: Optional[float]
    z_score: float
    contribution: float
    direction: str


@dataclass
class RiskPrediction:
    risks: List[TaskRiskResult]
    overall_tier: str
    n_features_provided: int
    n_features_total: int
    top_drivers: Dict[str, List[FeatureContribution]]
    model_version: str = "unknown"


_RARE_EVENT_TASKS = {"depression_severe", "suicidal_ideation"}

TIER_ORDER: tuple = ("very_low", "low", "moderate", "high", "very_high")
TIER_RANK: Dict[str, int] = {t: i for i, t in enumerate(TIER_ORDER)}

_RARE_THRESHOLDS = (
    (0.40, "very_high"),
    (0.20, "high"),
    (0.10, "moderate"),
    (0.05, "low"),
)
_RARE_DEFAULT_TIER = "very_low"

_COMMON_ABS_VERY_HIGH = 0.85
_COMMON_ABS_HIGH      = 0.65
_COMMON_LOW_PROB_GATE = 0.05
_COMMON_LOW_RATIO_GATE = 3.0
_COMMON_RATIO_THRESHOLDS = (
    (5.0, "very_high"),
    (2.5, "high"),
    (1.5, "moderate"),
    (0.5, "low"),
)
_COMMON_DEFAULT_TIER = "very_low"

_MIN_FEATURE_COVERAGE = 0.25

_FEATURE_ZSCORE_CLIP = 5.0

_NHANES_MALE = 1
_NHANES_FEMALE = 2


def _classify_risk_tier(prob: float, baseline: float, target: str = "") -> str:
    if target in _RARE_EVENT_TASKS:
        for threshold, tier in _RARE_THRESHOLDS:
            if prob >= threshold:
                return tier
        return _RARE_DEFAULT_TIER

    ratio = prob / max(baseline, 0.01)

    if prob >= _COMMON_ABS_VERY_HIGH:
        return "very_high"
    if prob >= _COMMON_ABS_HIGH:
        return "high"
    if prob < _COMMON_LOW_PROB_GATE and ratio < _COMMON_LOW_RATIO_GATE:
        return "very_low" if prob < baseline * 0.5 else "low"

    for threshold, tier in _COMMON_RATIO_THRESHOLDS:
        if ratio >= threshold:
            return tier
    return _COMMON_DEFAULT_TIER


def _max_tier(tiers: List[str]) -> str:
    return max(tiers, key=lambda t: TIER_RANK.get(t, 0)) if tiers else "low"


def _aggregate_overall_tier(risks: List["TaskRiskResult"],
                             feature_coverage: float) -> str:
    if feature_coverage < _MIN_FEATURE_COVERAGE:
        return "insufficient_data"

    tiers = [r.risk_tier for r in risks]
    very_high = sum(1 for t in tiers if t == "very_high")
    high = sum(1 for t in tiers if t == "high")
    moderate = sum(1 for t in tiers if t == "moderate")

    if very_high >= 2:
        return "very_high"
    if very_high >= 1 and high >= 1:
        return "high"
    if high >= 2:
        return "high"
    if very_high == 1:
        return "moderate"
    if high == 1 or moderate >= 2:
        return "moderate"
    if moderate == 1:
        return "low"
    return "very_low"


TARGET_NAMES = {
    "depression_moderate": ("Депресія (помірна+)",      "Depression (moderate+)"),
    "depression_severe":   ("Депресія (тяжка)",         "Depression (severe)"),
    "sleep_deficiency":    ("Дефіцит сну",              "Sleep deficiency"),
    "daytime_dysfunction": ("Денна дисфункція",         "Daytime dysfunction"),
    "suicidal_ideation":   ("Суїцидальні думки",        "Suicidal ideation"),
    "snore_high":             ("Хропіння (часто+)",     "Snoring (often+)"),
    "trouble_sleeping_high":  ("Проблеми зі сном",      "Trouble sleeping"),
}

_SAFETY_CRITICAL = {"suicidal_ideation"}



class RiskPredictor:

    def __init__(self, model_path: Path, device: str = "cpu",
                 isotonic_path: Optional[Path] = None):
        self.device = device
        log.info(f"Loading risk model from {model_path}")
        self.model, self.extras = load_model(model_path, device=device)
        self.model.eval()

        self.feature_names: List[str] = self.extras["feature_names"]
        self.target_names: List[str] = self.extras["target_names"]
        self.feature_stats: Dict[str, Dict] = self.extras["feature_stats"]
        self.target_stats: Dict[str, Dict] = self.extras["target_stats"]

        self.means = np.array(
            [self.feature_stats[f]["mean"] for f in self.feature_names],
            dtype=np.float32
        )
        self.stds = np.array(
            [self.feature_stats[f]["std"] for f in self.feature_names],
            dtype=np.float32
        )
        self.stds = np.where(self.stds < 1e-6, 1.0, self.stds)

        self.isotonic_params: Optional[Dict[str, Dict]] = None
        if isotonic_path is None:
            isotonic_path = model_path.parent / "isotonic_params.json"
        if isotonic_path.exists():
            with open(isotonic_path) as f:
                self.isotonic_params = json.load(f)
            log.info(f"Loaded isotonic calibration from {isotonic_path} "
                     f"(tasks: {list(self.isotonic_params.keys())})")
        else:
            log.warning(f"Isotonic params not found at {isotonic_path} — "
                        f"using raw probabilities (uncalibrated for rare events)")

    def _apply_isotonic(self, target: str, raw_prob: float) -> float:
        if self.isotonic_params is None or target not in self.isotonic_params:
            return raw_prob
        params = self.isotonic_params[target]
        xs = params["x_thresholds"]
        ys = params["y_thresholds"]
        x_min = params.get("x_min", xs[0])
        x_max = params.get("x_max", xs[-1])
        clipped = max(x_min, min(x_max, float(raw_prob)))
        return float(np.interp(clipped, xs, ys))


    def _resolve_payload(self, payload: Dict[str, Any]) -> Dict[str, float]:
        resolved = {}

        flat: Dict[str, Any] = {}
        for k, v in payload.items():
            if k == "labs" and isinstance(v, dict):
                flat.update(v)
            else:
                flat[k] = v

        # Sex normalization
        # NHANES encoding: 1 = male, 2 = female.
        # Internal model convention: 0.0 = male, 1.0 = female.
        #
        # Bug fix: the old expression `float(sex_raw == 2 or sex_raw == 1.0)`
        # treated NHANES "1" (male) as a truthy `1.0 == 1.0` → True → 1.0,
        # i.e. it flipped male into female. Explicit per-value mapping below.
        sex_raw = flat.pop("sex", None)
        if sex_raw is not None:
            if isinstance(sex_raw, bool):
                resolved["sex"] = 1.0 if sex_raw else 0.0
            elif isinstance(sex_raw, (int, float)):
                if int(sex_raw) == _NHANES_MALE:
                    resolved["sex"] = 0.0
                elif int(sex_raw) == _NHANES_FEMALE:
                    resolved["sex"] = 1.0
            else:
                s = str(sex_raw).lower().strip()
                if s in ("f", "female", "ж"):
                    resolved["sex"] = 1.0
                elif s in ("m", "male", "ч"):
                    resolved["sex"] = 0.0

        from .units import normalize_lab_to_us_units

        for raw_key, value in flat.items():
            canonical = ALIASES.get(raw_key.lower())
            if canonical is None:
                continue
            num = normalize_lab_to_us_units(value, canonical)
            if num is None:
                try:
                    num = float(value)
                except (TypeError, ValueError):
                    log.warning(
                        "Could not parse lab value %r=%r — neither unit-aware "
                        "nor float() parser recognised it; treating as missing.",
                        raw_key, value,
                    )
                    continue
            resolved[canonical] = num
        return resolved

    def _build_tensors(self, resolved: Dict[str, float]) -> tuple:
        n = len(self.feature_names)
        values = np.zeros(n, dtype=np.float32)
        missing = np.ones(n, dtype=np.float32)
        for i, fname in enumerate(self.feature_names):
            if fname in resolved and not np.isnan(resolved[fname]):
                values[i] = resolved[fname]
                missing[i] = 0.0
        values_filled = np.where(missing > 0.5, self.means, values)
        normalized = (values_filled - self.means) / self.stds
        normalized = np.clip(normalized, -_FEATURE_ZSCORE_CLIP, _FEATURE_ZSCORE_CLIP)
        return (
            torch.from_numpy(normalized).unsqueeze(0),
            torch.from_numpy(missing).unsqueeze(0),
            values,
            missing,
        )

    @torch.no_grad()
    def _predict_logits(self, features: torch.Tensor, missing: torch.Tensor) -> Dict[str, float]:
        outputs = self.model(features.to(self.device), missing.to(self.device),
                            apply_temperature=True)
        return {t: float(outputs[t][0]) for t in self.target_names}

    def _gradient_top_drivers(self, features: torch.Tensor, missing: torch.Tensor,
                              target_idx: int, top_k: int = 5,
                              raw_values: Optional[np.ndarray] = None,
                              raw_missing: Optional[np.ndarray] = None) -> List[FeatureContribution]:
        target = self.target_names[target_idx]
        features = features.clone().to(self.device).requires_grad_(True)
        missing = missing.to(self.device)

        outputs = self.model(features, missing, apply_temperature=False)
        logit = outputs[target][0]
        logit.backward()

        grads = features.grad[0].detach().cpu().numpy()
        feats_z = features[0].detach().cpu().numpy()

        contribs = grads * feats_z

        if raw_missing is not None:
            contribs = contribs * (1 - raw_missing)

        order = np.argsort(-np.abs(contribs))[:top_k]
        out = []
        for idx in order:
            fname = self.feature_names[idx]
            raw_v = float(raw_values[idx]) if raw_values is not None else float("nan")
            if raw_missing is not None and raw_missing[idx] > 0.5:
                raw_v = None
            z = float(feats_z[idx])
            c = float(contribs[idx])
            direction = "raises" if c > 0.05 else ("lowers" if c < -0.05 else "neutral")
            out.append(FeatureContribution(
                feature=fname, value=raw_v, z_score=z,
                contribution=c, direction=direction,
            ))
        return out


    def predict(self, payload: Dict[str, Any], top_k_drivers: int = 5) -> RiskPrediction:
        resolved = self._resolve_payload(payload)
        features_t, missing_t, raw_values, raw_missing = self._build_tensors(resolved)

        logits = self._predict_logits(features_t, missing_t)
        raw_probs = {t: 1.0 / (1.0 + np.exp(-l)) for t, l in logits.items()}

        probs = {t: self._apply_isotonic(t, p) for t, p in raw_probs.items()}

        risks = []
        for t in self.target_names:
            baseline = self.target_stats[t]["prevalence"]
            tier = _classify_risk_tier(probs[t], baseline, target=t)
            name_ua, name_en = TARGET_NAMES.get(t, (t, t))
            risks.append(TaskRiskResult(
                target=t,
                name_ua=name_ua, name_en=name_en,
                probability=float(probs[t]),
                risk_tier=tier,
                population_prevalence=float(baseline),
                probability_ratio_vs_baseline=float(probs[t] / max(baseline, 0.01)),
            ))

        top_drivers = {}
        for i, t in enumerate(self.target_names):
            top_drivers[t] = self._gradient_top_drivers(
                features_t, missing_t, target_idx=i,
                top_k=top_k_drivers,
                raw_values=raw_values, raw_missing=raw_missing,
            )

        n_provided = int((1 - raw_missing).sum())
        n_total = len(self.feature_names)
        feature_coverage = n_provided / max(n_total, 1)
        overall_tier = _aggregate_overall_tier(risks, feature_coverage)

        return RiskPrediction(
            risks=risks,
            overall_tier=overall_tier,
            n_features_provided=n_provided,
            n_features_total=n_total,
            top_drivers=top_drivers,
            model_version=str(self.extras.get("model_version", "unknown")),
        )



if __name__ == "__main__":
    import sys
    from pathlib import Path

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    model_path = Path(__file__).parent.parent / "model_out" / "model.pt"
    predictor = RiskPredictor(model_path)

    print("\n" + "=" * 70)
    print("SMOKE TEST — три типові пацієнти")
    print("=" * 70)

    print("\n--- Пацієнт 1: Здорова молода жінка ---")
    p1 = {
        "sex": "female", "age": 28, "bmi": 22, "waist_cm": 72,
        "labs": {
            "hgb": 13.2, "wbc": 6.1, "plt": 240, "mcv": 90,
            "glucose": 88, "hba1c": 5.2, "creatinine": 0.8,
            "alt": 18, "ast": 20, "tchol": 175, "hdl": 65, "trigly": 75,
            "crp": 0.8, "sodium": 140, "potassium": 4.2,
        },
        "sbp": 115, "dbp": 72, "pulse": 70,
    }
    r1 = predictor.predict(p1)
    print(f"Overall tier: {r1.overall_tier}  (features: {r1.n_features_provided}/{r1.n_features_total})")
    for r in r1.risks:
        print(f"  {r.name_ua:<32}  P={r.probability:.3f}  ({r.risk_tier:<10}) "
              f"ratio={r.odds_ratio_vs_baseline:.2f}x")

    print("\n--- Пацієнт 2: Чоловік 55, ожиріння, переддіабет ---")
    p2 = {
        "sex": "male", "age": 55, "bmi": 32, "waist_cm": 108,
        "labs": {
            "hgb": 14.5, "wbc": 7.5, "plt": 280, "mcv": 88,
            "glucose": 118, "hba1c": 6.3, "creatinine": 1.0,
            "alt": 38, "ast": 32, "tchol": 215, "hdl": 38, "trigly": 195,
            "crp": 4.1, "sodium": 140, "potassium": 4.4,
        },
        "sbp": 142, "dbp": 92, "pulse": 78,
    }
    r2 = predictor.predict(p2)
    print(f"Overall tier: {r2.overall_tier}  (features: {r2.n_features_provided}/{r2.n_features_total})")
    for r in r2.risks:
        print(f"  {r.name_ua:<32}  P={r.probability:.3f}  ({r.risk_tier:<10}) "
              f"ratio={r.odds_ratio_vs_baseline:.2f}x")
    print("Top drivers for diabetes:")
    for d in r2.top_drivers["depression_severe"][:5]:
        v = f"{d.value:.1f}" if d.value is not None else "—"
        print(f"  {d.feature:<22}  value={v:>7}  contribution={d.contribution:+.3f}  ({d.direction})")

    print("\n--- Пацієнт 3: Жінка 70, відомі hypertension і high chol ---")
    p3 = {
        "sex": "female", "age": 70, "bmi": 28, "waist_cm": 98,
        "labs": {
            "hgb": 12.8, "wbc": 7.0, "plt": 260, "mcv": 92,
            "glucose": 102, "hba1c": 5.9, "creatinine": 1.3,
            "alt": 28, "ast": 30, "tchol": 240, "hdl": 48, "trigly": 165,
            "crp": 3.2, "sodium": 138, "potassium": 4.5,
        },
        "sbp": 152, "dbp": 88, "pulse": 75,
    }
    r3 = predictor.predict(p3)
    print(f"Overall tier: {r3.overall_tier}  (features: {r3.n_features_provided}/{r3.n_features_total})")
    for r in r3.risks:
        print(f"  {r.name_ua:<32}  P={r.probability:.3f}  ({r.risk_tier:<10}) "
              f"ratio={r.odds_ratio_vs_baseline:.2f}x")
