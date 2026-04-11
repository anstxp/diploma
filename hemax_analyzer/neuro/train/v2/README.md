# `train/v2/` — HEMAX_NEURO v2 training pipeline

Extends v1 with **11 new features** (SES, metabolic-syndrome composite,
anthropometric, new biochemistry) and **2 new task heads** (`snore_high`,
`trouble_sleeping_high`). Lives as a sub-module of `train/` to coexist
with v1 — same data, same architecture, separate output directories.

## Quick start

```bash
cd ~/Documents/diploma/hemax_analyzer/neuro

# 1. Prepare v2 splits from the same NHANES master
python -m train.v2.prepare_data_v2
#   → writes data_processed_v2/{train,val,test}.parquet
#                              {feature,target}_stats.json, metadata.json

# 2. Train v2 model (HemaxRiskNet, auto-sized to v2 features and targets)
python -m train.v2.train_v2
#   → writes model_out_v2/model.pt, metrics.json, history.json
#   ≈ 5–10 min on CPU, less on GPU

# 3. Generate head-to-head report vs v1
python -m train.v2.compare_v1_v2
#   → writes model_out_v2/comparison_v1_v2.md  (defense-ready)
#                          comparison_v1_v2.json (machine-readable)
```

## What v2 changes

### Features (v1 → v2)

```
v1:  46 features  (CBC + CHEM + demographics)
v2:  57 features  (+ 11 new)
```

The 11 v2 features added are:

| Category               | Feature                 | Univariate AUC*           |
|------------------------|-------------------------|---------------------------|
| **SES** (new category) | `income_ratio`          | 0.67 (depression_severe)  |
|                        | `edu_level`             | 0.62 (depression_severe)  |
| Composite scores       | `metsyn_criteria_count` | 0.59 (suicidal_ideation)  |
|                        | `fib4`                  | liver fibrosis            |
|                        | `egfr_ckd_epi_2021`     | kidney composite          |
| Biochemistry           | `iron_chem_ugdl`        | serum iron                |
|                        | `non_hdl_mgdl`          | better lipid marker       |
|                        | `globulin_gdl`          | inflammation              |
|                        | `homa_ir`               | insulin resistance        |
| Anthropometric         | `arm_circ_cm`           | 0.61 (snoring proxy)      |
| Activity               | `sedentary_min_day`     | sedentary minutes         |

*See `audit_features.py`-style univariate ROC-AUC on the training cohort.

### Targets (v1 → v2)

```
v1:  5 task heads
v2:  7 task heads (+ snore_high, trouble_sleeping_high)
```

The two new heads come from `prepare_data_v2.build_targets()`:

* `snore_high` ≡ NHANES `snore ≥ 2` (often or always loud snoring)
  — proxy for obstructive sleep apnea (OSA).
* `trouble_sleeping_high` ≡ NHANES `trouble_sleeping ≥ 3` (often+)
  — insomnia screen.

Both are clinically actionable independently of PHQ-9. The narrative
layer's existing `sleep_apnea_pattern` cluster can use the `snore_high`
probability as an additional gating signal alongside the subjective
`snoring` / `witnessed_apnea` flags from the questionnaire.

## What v2 does NOT change

* **Architecture** — same `HemaxRiskNet` (residual stack, missingness
  encoding, temperature scaling). The config auto-adjusts to new
  `n_features` and `target_names` from `metadata.json`. We did NOT swap
  the architecture, because then we couldn't attribute AUC gains to the
  features.
* **Hyperparameters** — same LR, batch, epochs, early-stop patience.
* **Train/val/test split** — same seed (42), same age × sex
  stratification. Test set membership is comparable.
* **Data source** — same `data/nhanes_master.parquet` (no new
  downloads, no harmonisation changes).

## Directory layout

```
hemax_neuro_v02/
├── data/
│   └── nhanes_master.parquet     # source (unchanged)
├── train/
│   ├── prepare_data.py           # v1 prep
│   ├── train.py                  # v1 trainer
│   └── v2/                       # ← NEW
│       ├── __init__.py
│       ├── prepare_data_v2.py    # adds 11 features, 2 targets
│       ├── train_v2.py           # reuses v1 train.py loops
│       ├── compare_v1_v2.py      # generates head-to-head report
│       └── README.md             # this file
├── data_processed/               # v1 splits  (unchanged)
├── data_processed_v2/            # ← v2 splits (new)
├── model_out/                    # v1 model.pt   (unchanged)
└── model_out_v2/                 # ← v2 model.pt + metrics + comparison
```

## Promoting v2 to production

When you're ready to use v2 in the running API:

1. Point the predictor at the v2 weights in `neuro_api/dependencies.py`:
   change `MODEL_PATH` from `model_out/model.pt` to `model_out_v2/model.pt`.
2. The Pydantic request schema (`neuro_api/models.py`) accepts all v2
   features already — they flow through `labs` or as top-level keys
   via the `_allow_top_level_labs` validator, and the API filters by
   `feature_names` from the loaded model, so the new features become
   active automatically once the v2 model is loaded.
3. Rebuild the container: `docker compose up -d --build neuro-api`.

If you want both v1 and v2 served simultaneously for A/B testing, run
two containers with different `MODEL_PATH` env vars and route via load
balancer or feature flag — that's a deployment decision, not a code one.

## Defense notes

This sub-module is a clean ML experiment: same architecture, same data
source, same split, more features and more heads. Any AUC change is
attributable to the data, not to confounding model changes. That makes
v2 results citable in the dissertation as a controlled ablation.
