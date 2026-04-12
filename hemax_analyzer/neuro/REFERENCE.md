# HEMAX — NEURO Module Reference

> A self-contained reference for the mental-health & sleep ML service.
> Covers architecture, runtime API, every input/output field, every test,
> the model + calibration + narrative layer, safety considerations, and
> how to run it.

---

## Table of contents

1. [What this module does](#1-what-this-module-does)
2. [Folder layout](#2-folder-layout)
3. [Runtime stack](#3-runtime-stack)
4. [Model architecture](#4-model-architecture)
5. [HTTP API reference](#5-http-api-reference)
6. [Input contract](#6-input-contract)
7. [Output contract](#7-output-contract)
8. [7 prediction targets](#8-prediction-targets)
9. [Risk tier classification](#9-risk-tier-classification)
10. [Isotonic calibration](#10-isotonic-calibration)
11. [Narrative layer (13 clusters)](#11-narrative-layer-13-clusters)
12. [Test suite](#12-test-suite)
13. [How to run](#13-how-to-run)
14. [Safety considerations](#14-safety-considerations)
15. [Design decisions](#15-design-decisions)
16. [Bugs fixed during audit](#16-bugs-fixed-during-audit)

---

## 1. What this module does

Takes a patient's lab panel + demographics + SES indicators and produces:

- **7 calibrated mental-health & sleep probabilities** — Depression
  (moderate+ and severe), Sleep deficiency, Daytime dysfunction,
  **Suicidal ideation (SAFETY-CRITICAL)**, Snoring (often+), Trouble
  sleeping
- **5-tier classification** per target — very_low / low / moderate / high / very_high
- **Overall tier** — aggregated with safety rules
- **Top driver features** per target — gradient-based saliency
- **13 narrative clusters** — patient-friendly explanations in UK and EN
- **Deterministic output** — identical input produces byte-identical output

NEURO is a **sister module to RISK** — same multi-task neural-network
architecture, but trained on PHQ-9 questionnaire + NHANES sleep
behaviour targets instead of cardiovascular endpoints.

**Important:** The model PREDICTS mental-health/sleep targets from
PHYSIOLOGY (CBC + CHEM + demographics + SES). PHQ-9 scores and sleep
questionnaire answers are NOT inputs — they're the labels the model
learned to predict from physiological + socio-demographic signals.

---

## 2. Folder layout

```
hemax_neuro_v02/
├── REFERENCE.md                     ← this file (the only doc)
│
├── analyze_neuro_diploma.py         ← thesis analysis (charts, tables)
├── narrative_demo.py                ← prints stories for demo patients
├── requirements.txt · Dockerfile
│
├── neuro_api/                       ← FastAPI service
│   ├── app.py                       ← FastAPI app factory
│   ├── router.py                    ← /neuro/* endpoints
│   ├── models.py                    ← Pydantic request/response shapes
│   ├── dependencies.py · exceptions.py · middleware.py
│   │
│   ├── neuro/                       ← core ML engine
│   │   ├── inference.py             ← RiskPredictor.predict() (despite name)
│   │   ├── model.py                 ← PyTorch model architecture
│   │   └── units.py                 ← shared unit normalization
│   │
│   ├── narrative/                   ← patient-facing stories
│   │   ├── narrative_engine.py
│   │   ├── clusters.yaml            ← 13 cluster definitions
│   │   └── templates/               ← 26 .md templates (13 UK + 13 EN)
│   │
│   └── weights/
│       ├── MODEL_VERSION.txt        ← version metadata
│       ├── model.pt                 ← trained PyTorch checkpoint (4.6 MB)
│       └── isotonic_params.json     ← calibration map (per target)
│
├── train/                           ← offline training pipeline
│   └── v2/                          ← v2 training scripts
│       ├── prepare_data_v2.py       ← NHANES → train/val tensors
│       ├── train_v2.py              ← model training
│       ├── calibrate_v2.py          ← isotonic calibration fit
│       ├── promote_to_production.py ← copy artifacts to risk_api/weights/
│       └── compare_v1_v2.py         ← validation script
│
├── data_processed_v2/               ← preprocessed training data
│   ├── train.parquet · test.parquet
│   ├── feature_stats.json · target_stats.json · metadata.json
│
├── model_out_v2/                    ← training artefacts
│   ├── model.pt · isotonic_params.json
│   ├── metrics.json · history.json
│   └── calibration_summary_v2.json
│
├── analysis/                        ← validation & figures
│   ├── figures/                     ← ROC curves, calibration plots, …
│   └── reports/                     ← DEFENSE_REPORT_NEURO.md
│
└── tests/                           ← test suite (11 files, 228 tests)
    ├── conftest.py                  ← session-cached predictor + 9 fixtures
    ├── test_units.py                ← 31 — lab unit normalization
    ├── test_aliases.py              ← 11 — input field aliases incl. v2
    ├── test_classify_tier.py        ← 24 — _classify_risk_tier boundaries
    ├── test_aggregate_tier.py       ← 12 — _aggregate_overall_tier rules
    ├── test_model.py                ← 13 — model load + architecture
    ├── test_inference.py            ← 32 — full pipeline + determinism
    ├── test_calibration.py          ←  9 — isotonic recalibration
    ├── test_narrative.py            ← 18 — 13 clusters × 2 templates
    ├── test_api.py                  ← 10 — FastAPI endpoints
    ├── test_e2e.py                  ← 24 — 12 clinical + safety scenarios
    └── test_requirements.py         ← 34 — DEFENSE TESTS (R1-R9)
```

---

## 3. Runtime stack

| Layer | Tech |
|---|---|
| HTTP | FastAPI + Uvicorn (`/neuro/*` routes) |
| ML inference | PyTorch (CPU) + NumPy |
| Calibration | scikit-learn-fitted isotonic regression (json-serialized) |
| Templates | Jinja2 (graceful fallback) |
| Tests | pytest 9 |
| Container | Python 3.11-slim |

---

## 4. Model architecture

```
Input: 57 features
       (46 RISK features + 11 NEURO v2 features)
       ↓
[Missingness-aware embedding]: each feature → (value, is_missing) pair
       ↓
Shared Encoder: 4-layer residual MLP with LayerNorm + GELU + Dropout
       ↓
Task-specific heads (7): each is a 2-layer MLP → 1 logit
       ↓
Output: 7 probabilities, calibrated post-training via isotonic regression
```

### Key design choices

- **Forked from RISK.** Same multi-task architecture; only the targets +
  feature set differ. Code structure mirrors RISK so improvements can be
  shared.
- **+11 v2 features** beyond RISK's 46 — SES (income_ratio, edu_level),
  composite indices (metsyn_count, FIB-4, eGFR CKD-EPI 2021, HOMA-IR),
  serum iron, non-HDL, globulin, mid-upper arm circumference, sedentary
  minutes/day. Selected by univariate-AUC audit (see
  `train/v2/audit_features.py`).
- **+2 v2 task heads** beyond v1's 5 — `snore_high` (proxy for OSA, AUC
  ≈ 0.82 proof-of-concept) and `trouble_sleeping_high` (insomnia screen,
  AUC ≈ 0.68).

### Trained on

- **NHANES** 1999-2020, ~119k participants
- **Targets** derived from PHQ-9 questionnaire + NHANES sleep behaviour
  variables:
  - `depression_moderate` ← PHQ-9 ≥ 10
  - `depression_severe` ← PHQ-9 ≥ 15
  - `sleep_deficiency` ← < 6h weekday OR trouble_sleeping ≥ 3
  - `daytime_dysfunction` ← daytime_sleepy ≥ 3
  - `suicidal_ideation` ← PHQ-9 q9 ≥ 1
  - `snore_high` ← SLQ030 ≥ 3 (often)
  - `trouble_sleeping_high` ← SLQ050 ≥ 3 (often)
- **Features**: CBC + clinical chemistry + age/sex/BMI/BP + SES + composite indices

---

## 5. HTTP API reference

Four endpoints under the `/neuro` prefix:

| Method | Path | Purpose |
|---|---|---|
| GET | `/neuro/healthz` | Liveness probe |
| GET | `/neuro/info` | Model + dataset metadata |
| POST | `/neuro/analyze` | Predict 7 targets + drivers |
| POST | `/neuro/analyze/narrative` | Predict + return narrative stories |

OpenAPI/Swagger docs at <http://localhost:8004/docs>.

### Example: POST /neuro/analyze

```bash
curl -X POST http://localhost:8004/neuro/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "sex": 2, "age": 50,
    "bmi": 32, "sbp": 145,
    "glucose": 115, "a1c": 6.0,
    "tchol": 220, "hdl": 38, "trigly": 240,
    "crp": 6.5, "vitd_25oh": 14,
    "income_ratio": 1.2
  }'
```

### Example: POST /neuro/analyze/narrative?lang=en

Same payload. `lang` query parameter selects `uk` (default) or `en`.

---

## 6. Input contract

### 6.1 Demographics + standard CBC + CHEM

Same as RISK (see RISK REFERENCE for the full table) — `sex`, `age`,
`bmi`, `waist`, `sbp`/`dbp`, `pulse`, plus all CBC and CHEM analytes.

### 6.2 NEURO v2 features (11 new)

| Field | Aliases | Description |
|---|---|---|
| `income_ratio` | `pir`, `poverty_income_ratio` | Poverty-income ratio (NHANES INDFMPIR) |
| `edu_level` | `education` | Education level (years/grade band) |
| `metsyn_criteria_count` | `metsyn_count` | Metabolic syndrome criteria count (0-5) |
| `fib4` | `fib_4` | FIB-4 liver fibrosis index |
| `egfr_ckd_epi_2021` | — | eGFR (CKD-EPI 2021 formula) |
| `iron_chem_ugdl` | `serum_iron`, `iron` | Serum iron (chem panel) |
| `non_hdl_mgdl` | `non_hdl` | Non-HDL cholesterol |
| `globulin_gdl` | — | Serum globulin |
| `homa_ir` | — | HOMA-IR (insulin resistance index) |
| `arm_circ_cm` | `arm_circumference` | Mid-upper arm circumference |
| `sedentary_min_day` | — | Sedentary minutes per day |

### 6.3 Embedded units

Same parser as RISK — `"glucose": "8.8 mmol/L"` is converted to mg/dL
before the model sees it. See `neuro_api/neuro/units.py`.

### 6.4 NHANES sex codes

- `1` → male (encoded as 0.0 internally)
- `2` → female (encoded as 1.0 internally)
- `"male"` / `"female"` / `"м"` / `"ж"` strings are also accepted

---

## 7. Output contract

```json
{
  "risks": [
    {
      "target":                         "depression_moderate",
      "name_ua":                        "Депресія (помірна+)",
      "name_en":                        "Depression (moderate+)",
      "probability":                    0.32,
      "risk_tier":                      "moderate",
      "population_prevalence":          0.10,
      "probability_ratio_vs_baseline":  3.20,
      "odds_ratio_vs_baseline":         3.20
    },
    {
      "target":                         "suicidal_ideation",
      "name_ua":                        "Суїцидальні думки",
      "name_en":                        "Suicidal ideation",
      "probability":                    0.06,
      "risk_tier":                      "low",
      "population_prevalence":          0.04,
      "probability_ratio_vs_baseline":  1.50,
      "odds_ratio_vs_baseline":         1.50
    }
  ],
  "overall_tier": "moderate",
  "n_features_provided": 22,
  "n_features_total": 57,
  "top_drivers": {
    "depression_moderate": [
      {
        "feature":      "hs_crp",
        "value":        6.5,
        "z_score":      1.8,
        "contribution": 0.84,
        "direction":    "raises"
      }
    ]
  },
  "model_version": "neuro_v2_20260513"
}
```

### Field reference

- **`risks`**: 7 per-target predictions, always in the same order.
- **`probability`**: post-calibration probability ∈ [0, 1].
- **`risk_tier`**: one of `very_low | low | moderate | high | very_high`.
- **`population_prevalence`**: training-set base rate for the target.
- **`probability_ratio_vs_baseline`**: probability / max(prevalence, 0.01).
- **`odds_ratio_vs_baseline`**: deprecated alias (property returning
  `probability_ratio_vs_baseline`). New code uses the correct name.
- **`overall_tier`**: aggregated tier. Special value `insufficient_data`
  when feature coverage < 25%.
- **`top_drivers`**: per-target list of up to 5 feature contributions.
- **`model_version`**: filled from the model checkpoint metadata.

---

## 8. Prediction targets

The 7 targets and their NHANES variable provenance:

| Target | Ukrainian | English | NHANES var | Approx prevalence | Risk model |
|---|---|---|---|---|---|
| `depression_moderate` | Депресія (помірна+) | Depression (moderate+) | PHQ-9 ≥ 10 | ~8% | Common |
| `depression_severe` | Депресія (тяжка) | Depression (severe) | PHQ-9 ≥ 15 | ~3.5% | **Rare** |
| `sleep_deficiency` | Дефіцит сну | Sleep deficiency | <6h OR trouble | ~25% | Common |
| `daytime_dysfunction` | Денна дисфункція | Daytime dysfunction | sleepy ≥ 3 | ~15% | Common |
| `suicidal_ideation` | Суїцидальні думки | Suicidal ideation | PHQ-9 q9 ≥ 1 | ~4% | **Rare & SAFETY-CRITICAL** |
| `snore_high` | Хропіння (часто+) | Snoring (often+) | SLQ030 ≥ 3 | ~30% | Common |
| `trouble_sleeping_high` | Проблеми зі сном | Trouble sleeping | SLQ050 ≥ 3 | ~25% | Common |

The two rare-event tasks (depression_severe, suicidal_ideation) have
prevalence < 5%. The inference layer applies stricter absolute-probability
thresholds for these targets — see [§9](#9-risk-tier-classification).

---

## 9. Risk tier classification

### 9.1 Rare-event tasks (depression_severe, suicidal_ideation)

Absolute calibrated probability thresholds:

| Threshold | Tier |
|---|---|
| ≥ 0.40 | very_high |
| ≥ 0.20 | high |
| ≥ 0.10 | moderate |
| ≥ 0.05 | low |
| < 0.05 | very_low |

### 9.2 Common tasks (depression_moderate, sleep_*, daytime_*, snore, trouble)

Combined absolute + ratio-vs-baseline logic (identical to RISK):

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

KEY SAFETY RULE: a single isolated very_high task → overall `moderate`,
NOT very_high. This specifically protects against a false-positive
**suicidal_ideation** prediction (which would otherwise drag the entire
profile to very_high alert level).

- **`feature_coverage < 0.25`** → `insufficient_data`.
- **≥ 2 very_high tiers** → overall `very_high`.
- **1 very_high + 1 high** → overall `high`.
- **≥ 2 high tiers** → overall `high`.
- **Exactly 1 very_high** → overall `moderate` (safety gate).
- **1 high or ≥ 2 moderate** → overall `moderate`.
- **1 moderate** → overall `low`.
- **All low or very_low** → overall `very_low`.

---

## 10. Isotonic calibration

Same approach as RISK. The trained model produces *uncalibrated*
probabilities. For rare events (depression_severe, suicidal_ideation)
raw outputs are inflated. The inference layer applies a saved isotonic
regression (per target) before tier classification.

**Calibration is loaded for ALL 7 targets** including the
safety-critical `suicidal_ideation`. Test coverage in
`test_calibration.py::TestSafetyCriticalCalibration`.

The calibration map lives at `neuro_api/weights/isotonic_params.json`.

### Where the file came from (regression fix)

The training pipeline writes isotonic_params.json to `model_out_v2/`.
The inference layer expects it next to the model weights at
`neuro_api/weights/`. Previously the file was only in `model_out_v2/`,
so inference fell back to raw probabilities. This audit copies the file
to the correct location and adds a regression test
(`test_requirements.py::TestR5_IsotonicCalibration::test_isotonic_loaded`).

---

## 11. Narrative layer (13 clusters)

| Cluster ID | Tier | Triggered by |
|---|---|---|
| `circadian_disruption` | abnormal | sleep_deficiency + daytime_dysfunction combo |
| `daytime_dysfunction_alone` | info | isolated daytime sleepiness |
| `depression_moderate` | abnormal | depression_moderate tier ≥ moderate |
| `depression_severe` | critical | depression_severe tier ≥ high |
| `low_overall_risk` | normal | all targets at or below baseline |
| `mixed_burnout` | abnormal | sleep + depression + chronic-disease cluster |
| `mixed_signals` | info | conflicting per-target tiers |
| `sleep_apnea_pattern` | abnormal | snore_high + daytime_dysfunction |
| `sleep_deficiency_alone` | info | isolated sleep deficiency |
| `sleep_disorder` | abnormal | trouble_sleeping_high + daytime_dysfunction |
| `snore_high_alone` | info | isolated snoring |
| `suicidal_ideation` | critical | suicidal_ideation tier ≥ moderate |
| `trouble_sleeping_alone` | info | isolated trouble sleeping |

13 clusters × 2 languages = **26 template files**, all present and
non-empty. Regression tests in `test_narrative.py` enforce parity.

---

## 12. Test suite

**228 tests, 11 files. Pass rate: 100%. Runtime: ~8s.**

### test_units.py (31 tests)

Lab unit normalization: glucose, cholesterol, triglycerides, creatinine,
urea vs. BUN (different factors), bilirubin, hemoglobin, A1c, CRP,
electrolytes. Heuristic behaviors (string '5.0' for glucose ↔ mmol/L).
Edge cases: None, bool, garbage, unknown lab.

### test_aliases.py (11 tests)

ALIASES table integrity, all v2 SES aliases tested (`pir`, `education`,
`metsyn_count`, `fib_4`, `non_hdl`, `serum_iron`). ≥ 60 entries total.

### test_classify_tier.py (24 tests)

`_classify_risk_tier` boundary logic:
- TIER_ORDER, TIER_RANK constants
- **suicidal_ideation and depression_severe both confirmed as rare-event tasks**
- Rare-event thresholds tested for both rare targets
- Common-condition combined absolute + ratio logic
- Boundary at 0.40 exact (inclusive)
- Zero-baseline guard

### test_aggregate_tier.py (12 tests)

`_aggregate_overall_tier` for 7 risks:
- insufficient_data gate at 25%
- two very_high → very_high
- **single very_high → moderate (key safety rule)**

### test_model.py (13 tests)

7 targets exact, **suicidal_ideation present**, 57 features, all 11 v2
features present, feature_stats / target_stats present, **isotonic
loaded for ALL 7 targets**, isotonic y monotone, model in eval mode.

### test_inference.py (32 tests)

Full pipeline:
- Output shape (risks list of 7, probabilities in [0,1], valid tiers)
- Probability ratio fields (new + old name match)
- **Determinism (100 runs → 1 hash)** across all 9 fixtures
- **Sex normalization** (regression test for the May 2026 boolean bug)
- **Garbage values don't crash** (regression for logger→log bug)
- Insufficient_data gate
- Top drivers per task
- Embedded units parsed

### test_calibration.py (9 tests)

Isotonic recalibration:
- Pass-through when params absent
- Returns float in [0,1]
- Monotone (increasing raw → non-decreasing calibrated)
- Clipping below x_min / above x_max
- **Suicidal_ideation specifically confirmed calibrated**
- **Depression_severe specifically confirmed calibrated**

### test_narrative.py (18 tests)

13 clusters loaded, required keys present, **depression + sleep clusters
present**, every cluster has BOTH UK and EN templates, total 26 files,
no orphans, `build_narrative` returns NarrativeReport.

### test_api.py (10 tests)

All 4 endpoints: `/neuro/healthz`, `/neuro/info`, `/neuro/analyze`,
`/neuro/analyze/narrative` (UK + EN). OpenAPI spec includes both
analyze endpoints. Empty payload accepted.

### test_e2e.py (24 tests)

12 clinical scenarios:

1. **Healthy young adult** — predicts without error, probs in [0,1]
2. **Low-risk young active** — overall tier NOT severe
3. **Metabolic at-risk** — ≥ 1 mental-health risk elevated
4. **Low SES + high inflammation** — ≥ 1 depression/sleep signal lifted
5. **Chronic disease burden** — overall tier above very_low
6. **Elderly at-risk** — all 3 sleep targets present
7. **Empty payload** — insufficient_data
8. **Sparse payload** — only sex+age → insufficient
9. **SI units handling** — mmol/L glucose produces sensible predictions
10. **Sex-specific predictions** — male vs female differ
11. **Determinism on all 8 fixtures**
12. **SAFETY scenarios**:
    - suicidal_ideation always reported in response
    - healthy patient NOT flagged high/very_high for suicidal
    - suicidal_ideation calibration confirmed

### test_requirements.py (34 tests) — DEFENSE TESTS

- **R1** — Model architecture (8 tests): 7 targets, suicidal present,
  v2 task heads present, 57 features, v2 features present
- **R2** — Response envelope (6 tests): risks list, fields per risk,
  model_version filled from extras
- **R3** — Tier classification (4 tests): 5 tiers, **rare tasks include
  suicidal_ideation**, rare thresholds for suicidal verified
- **R4** — Aggregation (3 tests): coverage gate, **single very_high →
  moderate (suicidal safety)**
- **R5** — Isotonic calibration (5 tests): **regression — loaded from
  correct path**, all 7 targets, suicidal calibrated, monotone
- **R6** — Input flexibility (3 tests): short aliases, v2 SES aliases,
  embedded units
- **R7** — Narrative coverage (3 tests): 13 clusters, bilingual, 26 files
- **R8** — Determinism (1 test): 100 runs → 1 unique hash
- **R9** — Safety (5 tests): **sex normalization**, insufficient_data,
  **logger→log regression**, **suicidal_ideation always reported**,
  probabilities in [0,1] across stress scenarios

---

## 13. How to run

```bash
cd neuro
python3 -m pip install -r requirements.txt --break-system-packages 2>/dev/null \
  || python3 -m pip install -r requirements.txt
python3 -m pytest tests/ -q
# Expect: 228 passed in ~8 s
```

### Run the server

```bash
cd neuro
uvicorn neuro_api.app:create_app --factory --port 8004 --reload
# OpenAPI docs at http://localhost:8004/docs
```

### Docker

```bash
cd neuro
docker build -t hemax-neuro-api .
docker run -p 8004:8004 hemax-neuro-api
```

### Retrain (optional)

```bash
cd neuro
python3 train/v2/prepare_data_v2.py
python3 train/v2/train_v2.py
python3 train/v2/calibrate_v2.py
python3 train/v2/promote_to_production.py
```

---

## 14. Safety considerations

**This module predicts suicidal ideation.** Special handling:

1. **Always reported.** `suicidal_ideation` appears in every response,
   even for healthy patients with low probability. Regression test:
   `test_requirements.py::TestR9_Safety::test_suicidal_target_always_reported`.

2. **Calibrated.** The probability passes through isotonic regression
   before tier classification. Without calibration, the raw model output
   would inflate rare-event probabilities.

3. **Absolute thresholds.** Tier is assigned by absolute probability
   (not ratio-vs-baseline). A 0.40 calibrated probability — clinically
   significant — produces `very_high`. A 0.07 — slightly above baseline
   — produces `low`.

4. **Overall-tier protection.** A single very_high task (the most likely
   false-positive scenario for rare events) → overall `moderate`, not
   `very_high`. Prevents one false-positive suicidal_ideation prediction
   from flagging the entire profile as urgent.

5. **Top drivers required.** Suicidal_ideation always has top drivers
   for explainability — the clinician can see WHICH features are
   contributing to the prediction.

6. **Narrative cluster.** A dedicated `suicidal_ideation` narrative
   cluster (tier: critical) is rendered when the predicted tier is
   ≥ moderate, with appropriate clinical guidance.

**This module is intended as a screening tool, not a diagnostic.** All
documentation, narrative templates, and clinical disclaimers reflect
this.

---

## 15. Design decisions

### Why fork RISK instead of building from scratch?

The two modules share the same data source (NHANES), same physiological
inputs (CBC + CHEM + demographics), same multi-task NN architecture, and
same engineering constraints (deterministic inference, calibrated
probabilities, top-driver explanations). Forking the codebase saves
maintenance: improvements to one cascade to the other via diff-and-port.

### Why add 11 v2 features for NEURO?

NHANES audit showed that several SES + composite indices have stronger
univariate AUC for mental-health targets than for cardiovascular targets:

- `income_ratio` (PIR): poverty correlates with depression
- `edu_level`: education protects against cognitive decline
- `metsyn_criteria_count`: metabolic syndrome and depression are bidirectional
- `homa_ir`: insulin resistance is in the depression literature
- `sedentary_min_day`: sedentary behaviour predicts sleep + mood

These were added to the v2 model alongside the two new task heads
(snore, trouble_sleeping).

### Why is the public class called `RiskPredictor` (not `NeuroPredictor`)?

Historical artifact of the fork from RISK. The class name was kept so
that the same client SDK can target both modules with minimal changes.
The API surface is identical.

### Why a 25% feature coverage gate?

Same reasoning as RISK — with < ~14 features available (≈25% of 57), the
missingness mask dominates the input and predictions become unreliable.
The engine refuses to commit to an overall tier in that regime.

---

## 16. Bugs fixed during audit

1. **`isotonic_params.json` was missing from `neuro_api/weights/`.**
   The training pipeline writes the file to `model_out_v2/`. The
   inference layer expects it at `neuro_api/weights/isotonic_params.json`
   (next to `model.pt`). Without it, the predictor silently fell back to
   uncalibrated raw probabilities — a SAFETY CONCERN for the rare-event
   targets including `suicidal_ideation`. Fixed in this audit by copying
   the file to the correct location. Regression test:
   `test_requirements.py::TestR5_IsotonicCalibration::test_isotonic_loaded`.

2. **`logger` vs `log` naming bug.** Module imports
   `log = logging.getLogger(...)` but line 439 used `logger.warning(...)`.
   This raised `NameError` whenever any field was dropped during payload
   resolution. Same bug as in RISK. Fixed. Regression test:
   `test_requirements.py::TestR9_Safety::test_garbage_lab_value_no_exception`.

3. **Sex normalization** (`float(sex == 2 or sex == 1.0)`). Same RISK bug
   pattern — short-circuit boolean evaluates True for both sexes. Already
   fixed before this audit; regression test added:
   `test_requirements.py::TestR9_Safety::test_sex_mapping_correct`.

4. **`model_version` hardcoded.** Same RISK bug — dataclass default
   `"unknown"` was never overridden. Already fixed before this audit;
   regression test added.

---

*Last updated: May 2026. Generated for thesis defense.*
