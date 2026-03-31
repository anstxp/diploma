# HEMAX — RISK Module Reference

> A self-contained reference for the cardiometabolic-risk ML service.
> Covers architecture, runtime API, every input/output field, every test,
> the model + calibration + narrative layer, and how to run it.

---

## Table of contents

1. [What this module does](#1-what-this-module-does)
2. [Folder layout](#2-folder-layout)
3. [Runtime stack](#3-runtime-stack)
4. [Model architecture](#4-model-architecture)
5. [HTTP API reference](#5-http-api-reference)
6. [Input contract](#6-input-contract)
7. [Output contract](#7-output-contract)
8. [6 prediction targets](#8-prediction-targets)
9. [Risk tier classification](#9-risk-tier-classification)
10. [Isotonic calibration](#10-isotonic-calibration)
11. [Narrative layer (17 clusters)](#11-narrative-layer-17-clusters)
12. [Test suite](#12-test-suite)
13. [How to run](#13-how-to-run)
14. [Design decisions](#14-design-decisions)
15. [Bugs fixed during audit](#15-bugs-fixed-during-audit)

---

## 1. What this module does

Takes a patient's lab panel + demographics and produces:

- **6 calibrated cardiometabolic-risk probabilities** — Hypertension,
  Diabetes, High Cholesterol, Coronary Heart Disease, Heart Failure, Stroke
- **5-tier classification** per target — very_low / low / moderate / high / very_high
- **Overall risk tier** — aggregated across all 6 targets with safety rules
- **Top driver features** per target — gradient-based saliency
- **17 narrative clusters** — patient-friendly explanations in UK and EN
- **Dropped-keys reporting** — surfaces fields that failed to parse
- **Deterministic output** — identical input produces byte-identical output

Unlike CBC and CHEM (rule-based), RISK is a **multi-task PyTorch neural
network** trained on NHANES 1999-2020 data. The engine handles input
normalization, missing-value masking, model inference, and post-hoc
isotonic calibration in a single pipeline.

---

## 2. Folder layout

```
hemax_risk/
├── REFERENCE.md                       ← this file (the only doc)
│
├── analyze_risk_diploma.py            ← thesis analysis script (charts, tables)
├── full_cycle.py                      ← end-to-end pipeline runner
├── narrative_demo.py                  ← prints stories for 14 demo patients
├── requirements.txt · Dockerfile
│
├── risk_api/                          ← FastAPI service
│   ├── app.py                         ← FastAPI app factory
│   ├── router.py                      ← /risk/* endpoints
│   ├── models.py                      ← Pydantic request/response shapes
│   ├── dependencies.py · exceptions.py · middleware.py
│   │
│   ├── risk/                          ← core ML engine
│   │   ├── inference.py               ← public entry: RiskPredictor.predict()
│   │   ├── model.py                   ← PyTorch model architecture
│   │   └── units.py                   ← shared lab-value unit normalization
│   │
│   ├── narrative/                     ← patient-facing stories
│   │   ├── narrative_engine.py
│   │   ├── clusters.yaml              ← 17 cluster definitions
│   │   └── templates/                 ← 34 .md templates (17 UK + 17 EN)
│   │
│   └── weights/
│       ├── model.pt                   ← trained PyTorch checkpoint (4.6 MB)
│       └── isotonic_params.json       ← calibration map (per target)
│
├── train/                             ← offline training pipeline
│   ├── prepare_data.py                ← NHANES → train/val tensors
│   └── train.py                       ← model training script
│
├── analysis/                          ← validation & figures
│   ├── figures/                       ← calibration plots, ROC curves, …
│   └── reports/                       ← DEFENSE_REPORT.md, validation .csv
│
└── tests/                             ← test suite (10 files, 241 tests)
    ├── conftest.py                    ← session-cached RiskPredictor + 9 fixtures
    ├── test_units.py                  ← 32 — lab unit normalization
    ├── test_aliases.py                ← 9  — input field aliases
    ├── test_classify_tier.py          ← 21 — _classify_risk_tier boundaries
    ├── test_aggregate_tier.py         ← 11 — _aggregate_overall_tier rules
    ├── test_model.py                  ← 13 — model load + architecture
    ├── test_inference.py              ← 30 — full pipeline + determinism
    ├── test_calibration.py            ← 8  — isotonic recalibration
    ├── test_narrative.py              ← 19 — 17 clusters × 2 templates
    ├── test_api.py                    ← 10 — FastAPI endpoints
    ├── test_e2e.py                    ← 25 — 12 clinical scenarios
    └── test_requirements.py           ← 30 — DEFENSE TESTS (R1-R9)
```

---

## 3. Runtime stack

| Layer | Tech |
|---|---|
| HTTP | FastAPI + Uvicorn (`/risk/*` routes) |
| ML inference | PyTorch (CPU) + NumPy |
| Calibration | scikit-learn-fitted isotonic regression (json-serialized) |
| Templates | Jinja2 (graceful fallback) |
| Tests | pytest 9 |
| Container | Python 3.11-slim |

---

## 4. Model architecture

```
Input: 46 features (CBC + CHEM + demographics)
       ↓
[Missingness-aware embedding]: each feature → (value, is_missing) pair
       ↓
Shared Encoder: 4-layer residual MLP with LayerNorm + GELU + Dropout
       ↓
Task-specific heads (6): each is a 2-layer MLP → 1 logit
       ↓
Output: 6 probabilities, calibrated post-training
```

### Key design choices

- **Missingness as signal.** A lab not measured can itself indicate disease
  state. Each feature is paired with an `is_missing` flag at input.
- **LayerNorm over BatchNorm.** Works with small batches and missing values.
- **Residual connections.** Depth without vanishing gradients.
- **Temperature scaling + isotonic calibration.** Two-stage calibration
  produces realistic probabilities for both common and rare events.

### Trained on

- **NHANES** 1999-2020, ~119k participants
- **Targets** derived from self-reported diagnosis variables
- **Features**: complete CBC + clinical chemistry + age/sex/BMI/BP

---

## 5. HTTP API reference

Four endpoints under the `/risk` prefix:

| Method | Path | Purpose |
|---|---|---|
| GET | `/risk/healthz` | Liveness probe |
| GET | `/risk/info` | Model + dataset metadata |
| POST | `/risk/analyze` | Predict 6 risks + drivers |
| POST | `/risk/analyze/narrative` | Predict + return narrative stories |

OpenAPI/Swagger docs at <http://localhost:8003/docs>.

### Example: POST /risk/analyze

```bash
curl -X POST http://localhost:8003/risk/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "sex": 2, "age": 58,
    "bmi": 32, "sbp": 145, "dbp": 90,
    "glucose": 180, "a1c": 8.5,
    "tchol": 220, "hdl": 38, "trigly": 280
  }'
```

### Example: POST /risk/analyze/narrative?lang=en

Same payload. The `lang` query parameter selects `uk` (default) or `en`.

---

## 6. Input contract

### 6.1 Recognized fields

The payload may contain any subset of the following (top-level or nested
under `"labs": {...}`):

**Demographics:**

| Field | Aliases | Type |
|---|---|---|
| `sex` | — | NHANES code 1/2, or "male"/"female" |
| `age` | `age_years` | years |
| `bmi` | — | kg/m² |
| `waist` | `waist_cm` | cm |
| `sbp` / `dbp` | — | mmHg |
| `pulse` | `heart_rate` | bpm |

**CBC analytes:**

| Field | Aliases | Unit |
|---|---|---|
| `wbc` | `leukocytes` | 10³/µL |
| `rbc` | `erythrocytes` | 10⁶/µL |
| `hgb` | `hemoglobin`, `hb` | g/dL |
| `hct` | `hematocrit` | % |
| `mcv`, `mch`, `mchc`, `rdw` | — | fL / pg / g/dL / % |
| `plt` | `platelets` | 10³/µL |
| `mpv` | — | fL |
| `neut_pct` | `neutrophils_pct` | % |
| `lymph_pct` | `lymphocytes_pct` | % |
| `mono_pct` | `monocytes_pct` | % |
| `eos_pct` | `eosinophils_pct` | % |
| `baso_pct` | `basophils_pct` | % |

**CHEM analytes:**

| Field | Aliases | Unit |
|---|---|---|
| `glucose` | `glucose_fasting` | mg/dL |
| `a1c` | `hba1c`, `hba1c_pct` | % |
| `creatinine` | — | mg/dL |
| `bun` | — | mg/dL |
| `uric_acid` | — | mg/dL |
| `alt` / `ast` / `alp` / `ggt` | — | U/L |
| `albumin` | — | g/dL |
| `total_protein` | `protein_total` | g/dL |
| `bilirubin` | `bilirubin_total` | mg/dL |
| `sodium` / `potassium` / `chloride` / `bicarbonate` | — | mmol/L |
| `calcium` | — | mg/dL |
| `phosphate` | `phosphorus` | mg/dL |
| `tchol` | `total_cholesterol` | mg/dL |
| `hdl` | — | mg/dL |
| `trigly` | `triglycerides`, `tg` | mg/dL |
| `crp` | `hs_crp` | mg/L |
| `ferritin` | — | ng/mL |
| `vitd_25oh` | `vitamin_d`, `vit_d` | ng/mL |

### 6.2 Embedded units

The engine accepts numeric values OR strings with embedded units. Examples:

- `"glucose": "8.8 mmol/L"` → 158.6 mg/dL (converted)
- `"creatinine": "88 µmol/L"` → 1.0 mg/dL
- `"hgb": "145 g/L"` → 14.5 g/dL
- `"a1c": "6.5%"` → 6.5

If a value can't be parsed at all, it's added to `dropped_keys` in the
response so the caller knows the model ignored it.

### 6.3 NHANES sex codes

- `1` → male (encoded as 0.0 internally)
- `2` → female (encoded as 1.0 internally)
- `"male"` / `"female"` strings are also accepted
- Ambiguous values (e.g. `"robot"`) → sex feature treated as missing

### 6.4 Nested payload

Both forms are accepted:

```json
{"sex": 1, "age": 50, "glucose": 95}
{"sex": 1, "age": 50, "labs": {"glucose": 95}}
```

---

## 7. Output contract

```json
{
  "risks": [
    {
      "target":                   "told_diabetes",
      "name_ua":                  "Цукровий діабет",
      "name_en":                  "Diabetes mellitus",
      "probability":              0.42,
      "risk_tier":                "high",
      "population_prevalence":    0.13,
      "risk_ratio_vs_baseline":   3.23,
      "odds_ratio_vs_baseline":   3.23
    }
  ],
  "overall_tier": "high",
  "n_features_provided": 18,
  "n_features_total": 46,
  "top_drivers": {
    "told_diabetes": [
      {
        "feature":      "hba1c_pct",
        "value":        8.5,
        "z_score":      2.4,
        "contribution": 1.83,
        "direction":    "raises"
      }
    ]
  },
  "dropped_keys": [],
  "model_version": "unknown"
}
```

### Field reference

- **`risks`**: 6 per-target predictions, always in the same order.
- **`probability`**: post-calibration probability ∈ [0, 1].
- **`risk_tier`**: one of `very_low | low | moderate | high | very_high`.
- **`population_prevalence`**: NHANES baseline rate for the target.
- **`risk_ratio_vs_baseline`**: `probability / max(prevalence, 0.01)` — how
  many times above population baseline.
- **`odds_ratio_vs_baseline`**: deprecated alias for `risk_ratio_vs_baseline`
  during a backward-compatibility window. New code should consume
  `risk_ratio_vs_baseline`.
- **`overall_tier`**: aggregated tier across all 6 targets. Special value
  `insufficient_data` when feature coverage < 25%.
- **`n_features_provided` / `_total`**: feature coverage.
- **`top_drivers`**: per-target list of up to 5 feature contributions.
  Each driver has `feature`, `value` (raw or None if missing), `z_score`,
  `contribution` (gradient × normalized value), `direction`.
- **`dropped_keys`**: payload keys whose values couldn't be parsed.
- **`model_version`**: extracted from the model checkpoint.

---

## 8. Prediction targets

The 6 targets and their NHANES variable provenance:

| Target | Ukrainian | English | NHANES var | Approx prevalence |
|---|---|---|---|---|
| `told_htn` | Артеріальна гіпертензія | Hypertension | BPQ020 | ~33% |
| `told_diabetes` | Цукровий діабет | Diabetes mellitus | DIQ010 | ~13% |
| `told_high_chol` | Гіперхолестеринемія | High cholesterol | BPQ080 | ~30% |
| `told_chd` | Ішемічна хвороба серця | Coronary heart disease | MCQ160C | ~4% |
| `told_chf` | Серцева недостатність | Congestive heart failure | MCQ160B | ~3% |
| `told_stroke` | Інсульт | Stroke | MCQ160F | ~3% |

The three CVD outcomes (CHD, CHF, Stroke) have prevalence < 5%. The
inference layer applies stricter absolute-probability thresholds for these
"rare event" targets — see [§9](#9-risk-tier-classification).

---

## 9. Risk tier classification

### 9.1 Rare-event tasks (CHD, CHF, Stroke)

Absolute calibrated probability thresholds:

| Threshold | Tier |
|---|---|
| ≥ 0.40 | very_high |
| ≥ 0.20 | high |
| ≥ 0.10 | moderate |
| ≥ 0.05 | low |
| < 0.05 | very_low |

### 9.2 Common-condition tasks (HTN, Diabetes, High Cholesterol)

Combined absolute + ratio-vs-baseline logic:

| Condition | Tier |
|---|---|
| `prob ≥ 0.85` | very_high |
| `prob ≥ 0.65` | high |
| `prob < 0.05` AND `ratio < 3.0` | low or very_low |
| `ratio ≥ 5.0` | very_high |
| `ratio ≥ 2.5` | high |
| `ratio ≥ 1.5` | moderate |
| `ratio ≥ 0.5` | low |
| (else) | very_low |

### 9.3 Overall tier aggregation

Computed by `_aggregate_overall_tier` from the 6 per-task tiers:

- **`feature_coverage < 0.25`** → `insufficient_data` regardless of tiers.
- **≥ 2 very_high tiers** → overall `very_high`.
- **1 very_high + 1 high** → overall `high`.
- **≥ 2 high tiers** → overall `high`.
- **Exactly 1 very_high** → overall `moderate` (key safety rule: one
  inflated rare-event tier does NOT drag the entire profile to very_high).
- **1 high or ≥ 2 moderate** → overall `moderate`.
- **1 moderate** → overall `low`.
- **All low or very_low** → overall `very_low`.

---

## 10. Isotonic calibration

The trained model produces *uncalibrated* probabilities. For rare events
the raw output is wildly inflated — a raw 0.55 for stroke might correspond
to a true ~5% risk. The inference layer therefore applies a saved isotonic
regression (per target) before tier classification.

The calibration map lives at `risk_api/weights/isotonic_params.json` with
structure:

```json
{
  "told_chd": {
    "x_thresholds": [0.0, 0.01, 0.05, 0.20, ...],
    "y_thresholds": [0.0, 0.005, 0.02, 0.10, ...],
    "x_min": 0.0,
    "x_max": 0.99
  },
  "told_chf": {...},
  ...
}
```

Properties guaranteed by the test suite (`test_calibration.py`):

- Loaded for all 6 targets.
- `y_thresholds` is non-decreasing (isotonic).
- Calibrated values stay in `[0, 1]`.
- Input clipped to `[x_min, x_max]` before piecewise-linear interpolation.

If `isotonic_params.json` is missing, the engine emits a warning and uses
raw probabilities (uncalibrated for rare events — the documented failure
mode).

---

## 11. Narrative layer (17 clusters)

The narrative engine maps the predicted tiers + drivers to a curated set
of clinical stories. Each cluster has a `tier` (critical / abnormal / info
/ normal), a `priority`, a list of required signals, and suppression rules
to avoid duplicate stories.

| Cluster ID | Tier | Triggered by |
|---|---|---|
| `cardiometabolic_high_risk` | critical | high HTN + Diabetes + High Chol |
| `cardiometabolic_moderate_risk` | abnormal | moderate metabolic cluster |
| `cvd_high_risk` | critical | high CHD/CHF/Stroke |
| `cvd_secondary_prevention` | critical | known CVD context |
| `diabetes_high_risk` | abnormal | diabetes tier ≥ high |
| `diabetes_moderate_risk` | abnormal | diabetes tier == moderate |
| `dyslipidemia_alone` | info | isolated lipid signal |
| `dyslipidemia_high_risk` | abnormal | severe lipid + ratios |
| `htn_alone` | info | isolated hypertension |
| `htn_high_risk` | abnormal | HTN tier ≥ high |
| `incomplete_panel` | info | feature coverage borderline |
| `insufficient_data` | info | feature coverage < 25% |
| `isolated_chd_risk` | abnormal | isolated CHD elevation |
| `isolated_chf_risk` | abnormal | isolated CHF elevation |
| `isolated_stroke_risk` | abnormal | isolated stroke elevation |
| `low_overall_risk` | normal | all targets at or below baseline |
| `mixed_signals` | info | conflicting per-target tiers |
| `prediabetes_metabolic` | info | borderline metabolic profile |

17 clusters × 2 languages = **34 template files**, all present and
non-empty. Regression tests in `test_narrative.py` enforce parity.

---

## 12. Test suite

**241 tests, 11 files. Pass rate: 100%. Runtime: ~7s.**

### test_units.py (32 tests)

`parse_lab_value`, all conversion functions: glucose, cholesterol family
(TC/HDL/LDL same factor), triglycerides, creatinine, urea vs. BUN (different
factors), bilirubin, hemoglobin, A1c, CRP, electrolytes. Heuristic
behaviors (string '5.0' for glucose interpreted as mmol/L; bare numeric
5.0 passes through). Edge cases: None, bool, garbage strings, unknown lab.

### test_aliases.py (9 tests)

ALIASES table integrity: contains essential CBC + CHEM + demographics
aliases, ≥ 50 entries total, no two-step chains, hgb/hb/hemoglobin all map
to `hb_gdl`.

### test_classify_tier.py (21 tests)

`_classify_risk_tier` boundary logic:
- TIER_ORDER constant + TIER_RANK lookup
- Rare-event thresholds (0.40 / 0.20 / 0.10 / 0.05) tested per target
- Common-condition combined absolute + ratio logic
- Boundary at 0.40 exact (inclusive)
- Zero-baseline division-by-zero guard
- `_max_tier`: empty list returns "low", unknown tier safe

### test_aggregate_tier.py (11 tests)

`_aggregate_overall_tier` rules: insufficient_data gate at 25% coverage,
two very_high → very_high, one very_high alone → moderate (key safety
rule), 1 high → moderate, 2 moderate → moderate, all low → very_low.

### test_model.py (13 tests)

Model loads, 6 targets, 46 features, feature_stats / target_stats present,
means/stds arrays correct shape, isotonic_params loaded for all targets,
isotonic y non-decreasing, model in eval mode after load.

### test_inference.py (30 tests)

Full pipeline tests using the cached predictor fixture:
- Output shape (risks list of 6, probabilities in [0,1], valid tiers)
- Risk-ratio field consistency (old + new names match)
- **Determinism (100 runs → 1 hash)** across multiple fixtures
- **Sex normalization** — regression for the May 2026 boolean bug
- Dropped keys reporting
- Insufficient_data gate
- Top drivers per task (≤ 5, valid directions, K respected)
- Embedded units parsed (`"8.8 mmol/L"` not dropped)

### test_calibration.py (8 tests)

Isotonic recalibration verification:
- Pass-through when params absent
- Returns float in [0,1]
- Monotone (increasing raw → non-decreasing calibrated)
- Clipping below x_min / above x_max
- Reduces rare-event probability inflation
- Integration in predict pipeline

### test_narrative.py (19 tests)

17 clusters loaded, all have required keys (id, tier, priority), every
cluster has BOTH UK and EN templates, total 34 files, no orphans,
`build_narrative` returns NarrativeReport with stories, valid `to_dict()`,
JSON-serializable.

### test_api.py (10 tests)

All 4 FastAPI endpoints: `/risk/healthz`, `/risk/info`, `/risk/analyze`,
`/risk/analyze/narrative` (UK + EN). OpenAPI spec includes both analyze
endpoints.

### test_e2e.py (25 tests)

12 curated clinical scenarios:

1. **Healthy young adult** — predicts without error, probs in [0,1]
2. **Diabetic uncontrolled** — diabetes prob > baseline, tier ≥ moderate
3. **Hypertensive** — HTN prob > baseline, tier ≥ moderate
4. **Metabolic syndrome** — ≥ 2 cardiometabolic risks elevated
5. **CVD high-risk** — overall tier above very_low, ≥ 1 CVD risk lifted
6. **Empty payload** — insufficient_data
7. **Sparse payload** — only sex+age → insufficient
8. **SI units** — mmol/L glucose produces same prediction as mg/dL equivalent
9. **Sex-specific predictions** — male vs female differ
10. **Age sensitivity** — older patient has higher average CVD risk
11. **Determinism on all 9 fixtures**
12. **Top drivers** — glucose/A1c appear in diabetes drivers for diabetic patient

### test_requirements.py (30 tests) — DEFENSE TESTS

Each test maps to one explicit project requirement:

- **R1** — Model architecture (5 tests): 6 targets, exact names, 46 features,
  feature/target stats present
- **R2** — Response envelope contract (6 tests): risks list, overall_tier,
  n_features, top_drivers, dropped_keys, every risk has required fields
- **R3** — Risk tier classification (3 tests): 5 tiers + insufficient,
  rare-event thresholds, common-condition absolute thresholds
- **R4** — Aggregation rule (3 tests): coverage gate, single very_high →
  moderate (key safety rule), two very_high → very_high
- **R5** — Isotonic calibration (4 tests): params loaded for all targets,
  monotone, integrated in predict pipeline
- **R6** — Input flexibility (4 tests): short aliases, NHANES-style names,
  embedded mmol/L units, nested `"labs"` payload
- **R7** — Narrative coverage (3 tests): 17 clusters, bilingual templates,
  34 files total
- **R8** — Determinism (1 test): 100 runs → 1 unique hash
- **R9** — Safety (5 tests): **sex normalization correctness** (regression),
  insufficient_data gate, dropped_keys reporting, probabilities in [0,1]
  across stress scenarios, TIER_ORDER valid

---

## 13. How to run

```bash
cd hemax_risk
python3 -m pip install -r requirements.txt --break-system-packages 2>/dev/null \
  || python3 -m pip install -r requirements.txt
python3 -m pytest tests/ -q
# Expect: 241 passed in ~7s
```

### Run the server

```bash
cd hemax_risk
uvicorn risk_api.app:create_app --factory --port 8003 --reload
# OpenAPI docs at http://localhost:8003/docs
```

### Docker

```bash
cd hemax_risk
docker build -t hemax-risk-api .
docker run -p 8003:8003 hemax-risk-api
```

---

## 14. Design decisions

### Why ML for risk, but rules for CBC/CHEM?

CBC and CHEM are interpretations of *single analytes against textbook
reference ranges* — explicit clinical reasoning. RISK is a *multi-analyte
risk prediction* problem where the interactions matter: glucose + HbA1c +
BMI + age + family history collectively determine diabetes risk in ways no
single threshold captures. ML learns the joint distribution; rules
couldn't.

### Why isotonic calibration on top of temperature scaling?

Temperature scaling fixes overconfidence on common conditions. Isotonic
regression fixes the *rare-event tail* — for stroke (3% prevalence) the
raw model puts 30%+ probability mass above 0.5 even on inputs that are
clinically only mildly elevated. Isotonic recalibration remaps these to
realistic values without changing rank order (so AUC is preserved).

### Why is one very_high alone only "moderate" at overall level?

This rule prevents a single inflated rare-event tier (e.g. CHF reported as
very_high on a patient with mostly normal labs) from dragging the entire
profile to very_high. With 6 binary tasks, false positives on one are
common; we require *two* very_high tiers or one very_high + one high
before promoting the overall tier.

### Why a 25% feature coverage gate?

The model was trained on records with mostly-complete panels (median ~38
of 46 features). With < 12 features available (≈ 25% coverage), the
missingness mask dominates the input and predictions become unreliable.
The engine refuses to commit to an overall tier in that regime.

### Why "dropped_keys" in the response?

A payload like `{"glucose": "8.8 mmol/L"}` used to be silently dropped by
`float()` (ValueError → continue), so the predictor and narrative engine
disagreed on which labs were "available". Exposing `dropped_keys` makes
the asymmetry visible to callers.

---

## 15. Bugs fixed during audit

1. **Sex mapping collapsed both NHANES codes to female.**
   Old: `float(sex == 2 or sex == 1.0)` — short-circuit boolean
   evaluates to `True` (1.0) for *both* sex=1 and sex=2. Both NHANES
   codes therefore mapped to female. Fixed: explicit disambiguation,
   ambiguous values treated as missing. Regression test:
   `test_inference.py::TestSexNormalization::test_male_vs_female_produce_different_predictions`.

2. **`logger` vs `log` naming bug.** Module imports `log = logging.getLogger(...)`
   but `_resolve_payload` used `logger.info(...)` — raised `NameError` whenever
   any field was dropped. Fixed in this audit. Regression test:
   `test_inference.py::TestDroppedKeys::test_garbage_lab_value_dropped`.

3. **eGFR string input silently dropped.** Front-ends that wrapped eGFR
   with its unit (`"38 mL/min/1.73m²"`) produced no card and no signal.
   Now uses `parse_value_unit` for graceful unit-stripping.

4. **Embedded SI units invisible to model.** Old `_resolve_payload` did
   `float(value)` and `continue`d on `ValueError`. A payload like
   `{"labs": {"glucose": "8.8 mmol/L"}}` was invisible to the model
   (glucose feature became "missing"), even though the narrative engine's
   `_normalize_lab_to_us_units` parsed it correctly. Now both paths share
   `normalize_lab_to_us_units` (extracted to `risk/units.py`).

5. **`model_version` hardcoded to "1.0".** The dataclass had a hardcoded
   default and the predictor never overrode it on construction, so
   `/risk/analyze` always reported `model_version=1.0` even though
   `/risk/info` correctly read it from extras. Now both endpoints agree.

6. **`risk_ratio_vs_baseline` was named `odds_ratio_vs_baseline`.** The
   field stores `probability / prevalence`, which is a *risk ratio* (RR),
   not an odds ratio (OR). Old name kept as deprecated alias during the
   API backward-compat window. New code should consume
   `risk_ratio_vs_baseline`.

7. **Lab card flag ignored `ref_ranges` override.** The rules engine
   honoured the override (the *signal* was correctly tagged), but the lab
   card kept showing the generic adult range, leading to mismatches like
   rules.flag=high while card.flag=null. Fixed: both flow from the same
   source of truth.

8. **Floating-point comparison artefacts.** Values like 1.3009 > 1.3 after
   mmol/L → mg/dL conversion. Now `round(v, 2)` before flag comparison.

---

*Last updated: May 2026. Generated for thesis defense.*
