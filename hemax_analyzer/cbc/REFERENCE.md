# HEMAX — CBC Module Reference

> A self-contained reference for the CBC (complete blood count) interpretation
> service. Covers architecture, runtime API, data pipeline, every signal the
> engine produces, every test in the suite, and how to run the whole thing.

---

## Table of contents

1. [What this module does](#1-what-this-module-does)
2. [Folder layout](#2-folder-layout)
3. [Runtime stack](#3-runtime-stack)
4. [Data pipeline (Phases 0-3)](#4-data-pipeline-phases-0-3)
5. [HTTP API reference](#5-http-api-reference)
6. [Input contract](#6-input-contract)
7. [Output contract](#7-output-contract)
8. [Clinical signals — full catalog](#8-clinical-signals--full-catalog)
9. [Narrative layer (31 clusters)](#9-narrative-layer-31-clusters)
10. [Configuration & overrides](#10-configuration--overrides)
11. [Validation layer](#11-validation-layer)
12. [Test suite](#12-test-suite)
13. [How to run](#13-how-to-run)
14. [Design decisions & limitations](#14-design-decisions--limitations)

---

## 1. What this module does

Takes a CBC lab result (JSON) and produces a structured clinical
interpretation with:

- **40 distinct signals** — 39 clinical findings + 1 data-quality flag
- **31 narrative clusters** — patient-friendly explanations in Ukrainian
  and English
- **Adult + pediatric reference ranges** — sex-specific where biologically
  warranted
- **Empirical refs from NHANES** — data-driven severity bands derived
  from 119 k harmonised samples (1999-2020)
- **Validation & auto-correction** — catches unit confusion (Hgb 145 g/L
  → 14.5 g/dL), fraction-as-percent typos, and physiologically impossible
  values
- **Deterministic output** — identical input produces byte-identical output

The service is rule-based, not ML. Clinical logic lives in `rules.py`, is
validated against ~119 k NHANES cycles, and has no learned parameters.

---

## 2. Folder layout

```
cbc/
├── REFERENCE.md                   ← this file (the only doc)
│
├── engine/                         ← the service
│   ├── main.py                     ← FastAPI app (6 endpoints)
│   ├── Dockerfile, docker-compose.yml, requirements.txt
│   │
│   ├── cbc_api/                    ← the engine package
│   │   ├── analyze.py              ← public entry: analyze_cbc_payload()
│   │   ├── rules.py                ← all 40 clinical signals
│   │   ├── knowledge.py            ← textbook lab catalog + ref ranges
│   │   ├── pediatric_refs.py       ← age-banded pediatric refs (NHS UK)
│   │   ├── config.py               ← CBCConfig + severity bands
│   │   ├── units.py                ← unit-aware value parser
│   │   ├── validation.py           ← physiological plausibility checks
│   │   ├── empirical_refs_loader.py ← optional NHANES-derived bands
│   │   ├── spec.py                 ← NHANES variable dictionary
│   │   │
│   │   └── narrative/              ← Phase-4 patient-facing storytelling
│   │       ├── narrative_engine.py
│   │       ├── clusters.yaml       ← 31 cluster definitions
│   │       └── templates/          ← 62 .md templates (31 UK + 31 EN)
│   │
│   └── tests/                      ← test suite (10 files, 361 tests)
│       ├── conftest.py             ← 15 canonical patient fixtures
│       ├── test_units.py           ← 47 tests — unit conversion
│       ├── test_config.py          ← 18 tests — CBCConfig
│       ├── test_knowledge.py       ← 41 tests — LABS catalog
│       ├── test_pediatric.py       ← 19 tests — pediatric refs
│       ├── test_validation.py      ← 23 tests — input validation
│       ├── test_rules.py           ← 61 tests — every clinical signal
│       ├── test_analyze.py         ← 43 tests — full pipeline
│       ├── test_narrative.py       ← 25 tests — narrative engine
│       ├── test_api.py             ← 13 tests — FastAPI endpoints
│       ├── test_requirements.py    ← 32 tests — DEFENSE TESTS
│       └── test_e2e.py             ← 21 tests — 14 clinical scenarios
│
├── scripts/                        ← one-off data-pipeline tools
│   ├── fetch_nhanes_gaps.py        · download missing NHANES files
│   ├── build_nhanes_master.py      · harmonise 11 NHANES cycles
│   ├── build_healthy_cohort.py     · extract healthy adults
│   ├── derive_empirical_refs.py    · Phase 1 — empirical reference intervals
│   ├── validate_cbc_engine.py      · Phase 2 — run engine on full master
│   └── generate_engine_config.py   · Phase 3 — combine refs + severity bands
│
├── outputs/                        ← generated artefacts (bundled)
│   ├── empirical_refs.json         · structured reference intervals
│   ├── empirical_refs_report.md    · Phase 1 narrative (thesis-ready)
│   ├── engine_config.json          · opt-in runtime config (Phase 3)
│   ├── validation_metrics.json     · Phase 2 numbers
│   └── validation_report.md        · Phase 2 narrative
│
├── demo/                           ← runnable examples
│   ├── manual_patient_test.py      · 14 curated clinical cases
│   ├── compare_modes.py            · textbook vs empirical side-by-side
│   └── narrative_demo.py           · pretty-prints narratives
│
└── analyze_cbc_diploma.py          ← thesis analysis script (40 plots,
                                      8 summary metrics)
```

---

## 3. Runtime stack

| Layer | Tech | Why |
|---|---|---|
| HTTP | FastAPI + Uvicorn | Async, OpenAPI spec generation, Pydantic validation |
| Engine | Pure Python (no NumPy required for the engine itself) | Trivially deployable |
| Templates | Jinja2 (optional — graceful fallback) | Standard, well-understood |
| Tests | pytest 9 | Standard |
| Container | Python 3.11-slim | Small, deterministic |

All dependencies are pinned in `requirements.txt`. The engine itself has no
ML dependencies — only the offline scripts in `scripts/` use pandas / numpy.

---

## 4. Data pipeline (Phases 0-3)

The offline pipeline turns raw NHANES SAS files into the `outputs/`
bundle. End-users don't need to re-run this — the artefacts are committed
in `outputs/`.

| Phase | Input | Output | What it does |
|---|---|---|---|
| 0 | raw NHANES SAS | `nhanes_master.parquet` | Harmonise 11 cycles 1999-2020 (`build_nhanes_master.py`) |
| 1 | master parquet | `empirical_refs.json` + report | CLSI-style reference intervals on a healthy cohort (`derive_empirical_refs.py`) |
| 2 | master + engine | `validation_metrics.json` + report | Run engine on full population — agreement vs. clinical sensibility (`validate_cbc_engine.py`) |
| 3 | refs + validation | `engine_config.json` | Combine into runtime severity-band config (`generate_engine_config.py`) |

The pipeline is documented in `outputs/empirical_refs_report.md` and
`outputs/validation_report.md` — both ready to drop into the thesis.

---

## 5. HTTP API reference

Six endpoints, three of them analysis:

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Root: engine version & build info |
| GET | `/health` | Health check (returns `{"status":"ok","engine":"cbc_api"}`) |
| GET | `/fields` | Accepted input field names + canonical units |
| POST | `/analyze` | Analyse one CBC result |
| POST | `/analyze/batch` | Analyse up to 100 CBC results in one call |
| POST | `/analyze/narrative` | Like `/analyze` plus human-readable narrative |

OpenAPI/Swagger docs are at `http://localhost:8001/docs` once the server
is running.

### Example: POST /analyze

```bash
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "sex": "female", "age": 32,
    "wbc": 6.5, "hgb": 10.2, "plt": 380,
    "rbc": 4.5, "hct": 32, "mcv": 72, "mch": 23, "mchc": 30, "rdw": 17.5
  }'
```

Returns a JSON envelope (see [section 7](#7-output-contract)).

### Example: POST /analyze/batch

```json
{
  "records": [
    {"sex": "male", "age": 35, "wbc": 6.5, "hgb": 15.0, "plt": 250},
    {"sex": "female", "age": 28, "wbc": 6.0, "hgb": 13.5, "plt": 230}
  ]
}
```

Limit: 100 records per call.

### Example: POST /analyze/narrative?lang=en

Same payload as `/analyze`. The `lang` query parameter selects `uk` (default)
or `en`.

---

## 6. Input contract

Every endpoint accepts a flexible JSON payload. The same field can be
provided under any of its aliases — the first non-null one wins.

### 6.1 Canonical lab fields

| Canonical | Aliases | Unit |
|---|---|---|
| `sex` | `gender`, `RIAGENDR`, `riagendr` | `male` / `female` (case-insensitive); also `m/f/ч/ж` |
| `age` | `RIDAGEYR`, `ridageyr` | years (decimal allowed, e.g. 0.05 for newborn) |
| `wbc` | `WBC`, `LBXWBCSI` | 10³/µL |
| `neut_pct` | `neutrophils_pct`, `NEUT%`, `LBXNEPCT` | % |
| `lymph_pct` | `lymphocytes_pct`, `LYMPH%`, `LBXLYPCT` | % |
| `mono_pct` | `monocytes_pct`, `LBXMOPCT` | % |
| `eos_pct` | `eosinophils_pct`, `LBXEOPCT` | % |
| `baso_pct` | `basophils_pct`, `LBXBAPCT` | % |
| `anc` | `neutrophils_abs`, `LBDNENO` | 10³/µL |
| `alc` | `lymphocytes_abs`, `LBDLYMNO` | 10³/µL |
| `amc` | `monocytes_abs`, `LBDMONO` | 10³/µL |
| `aec` | `eosinophils_abs`, `LBDEONO` | 10³/µL |
| `abc` | `basophils_abs`, `LBDBANO` | 10³/µL |
| `rbc` | `RBC`, `LBXRBCSI` | 10⁶/µL |
| `hgb` | `hb`, `HGB`, `LBXHGB` | g/dL |
| `hct` | `HCT`, `LBXHCT` | % |
| `mcv` | `MCV`, `LBXMCVSI` | fL |
| `mch` | `MCH`, `LBXMCHSI` | pg |
| `mchc` | `MCHC`, `LBXMC` | g/dL |
| `rdw` | `RDW`, `LBXRDW` | % |
| `plt` | `platelets`, `PLT`, `LBXPLTSI` | 10³/µL |
| `mpv` | `MPV`, `LBXMPSI` | fL |
| `esr` | `ESR`, `ШОЕ`, `shoe`, `SOE` | mm/hr |

### 6.2 Embedded units

Numeric values may carry their unit as part of a string. Examples:

- `"hgb": "14.5 g/dL"` → parsed as 14.5
- `"hgb": "145 g/L"` → auto-converted to 14.5 (warning emitted)
- `"wbc": "6.5 x10^3/µL"` → 6.5
- `"plt": "250000 /µL"` → auto-converted to 250 (warning emitted)
- `"esr": "32 mm/hr"` → 32

### 6.3 Fraction vs. percent

If the differential percentages all sum to ≈ 1.0 (e.g. `0.60, 0.30, 0.07,
0.02, 0.01`), the engine scales them to 60/30/7/2/1. The `meta.normalized_diff`
field of the response reports what was scaled.

### 6.4 Reference range overrides

Per-request override of textbook ref ranges (e.g. for a lab that publishes
its own intervals):

```json
{
  "sex": "female", "age": 30, "hgb": 11.5,
  "ref_ranges": {
    "hgb": {"low": 11.0, "high": 15.0}
  }
}
```

### 6.5 Config overrides

Severity bands, sort order, and signal priorities can be overridden per
request:

```json
{
  "sex": "male", "age": 30, "wbc": 16.0,
  "config": {
    "severity_thresholds": {
      "wbc_high": {"mild": 11.0, "moderate": 13.0, "severe": 15.0}
    },
    "lab_order": ["hgb", "wbc", "plt"],
    "signal_priority": {"my_custom_signal": 99}
  }
}
```

### 6.6 Clinical context

Some signals adapt their messaging based on patient context:

```json
{
  "sex": "male", "age": 60, "wbc": 14.0,
  "context": {
    "on_corticosteroids": true,
    "on_oral_anticoagulants": false,
    "has_diabetes": false
  }
}
```

Recognised context keys: `on_corticosteroids` (alias: `takes_corticosteroids`),
`on_oral_anticoagulants` (alias: `takes_anticoagulants`), `has_diabetes`.

---

## 7. Output contract

Every successful response is the same envelope:

```json
{
  "version": "cbc_interpreter_prod_v1_0_max",

  "profile": {"sex": "female", "age": 32.0},

  "meta": {
    "field_meta": {
      "wbc": {"source": "input", "input_key": "wbc",
              "raw": 6.5, "unit_in": null, "unit": "10^3/µL"},
      ...
    },
    "computed_abs": ["anc", "alc", "amc", "aec", "abc"],
    "normalized_diff": {"scaled_codes": [], "rule": "none"},
    "missing_core": [],
    "context": {"clinical": {}}
  },

  "summary": {
    "headline": "Помірні відхилення: Мікроцитарна анемічна картина; ...",
    "signals_high": 0,
    "signals_medium": 2,
    "notes": ["Мікроцитарна анемічна картина", "..."]
  },

  "labs": [
    {"code": "wbc", "value": 6.5, "unit": "10^3/µL",
     "ref": {"low": 4.0, "high": 11.0}, "flag": "normal",
     "name": "Лейкоцити (WBC)", "what": "...",
     "interpretation": ["..."], "tips": ["..."], "caveats": ["..."]},
    ...
  ],

  "flags": {"wbc": "normal", "hgb": "low", "plt": "high", ...},

  "derived": {
    "nlr": 0.65,
    "plr": 84.4,
    "sii": 162.3,
    "mentzer_index": 15.6
  },

  "signals": [
    {
      "id": "microcytic_anemia_pattern",
      "severity": "medium",
      "title": "Мікроцитарна анемічна картина",
      "why": "...",
      "next": ["..."],
      "evidence": {"hgb_gdl": 10.2, "mcv_fl": 72.0, "rdw_pct": 17.5},
      "tags": ["pattern", "rbc"],
      "priority": 80
    },
    ...
  ],

  "combos": [
    {"id": "bacterial_like_pattern", "severity": "medium", ...}
  ],

  "recommendations": {
    "next_tests": [
      {"test": "Феритин, залізо, TIBC/TSAT",
       "why": "Уточнення дефіциту заліза/анемії.",
       "priority": 70, "when": "soon"},
      ...
    ],
    "ask_doctor": [
      {"question": "Яка ймовірна причина анемії?", "why": "...", "priority": 60}
    ]
  },

  "disclaimer": "Освітня інтерпретація. Не є медичною консультацією..."
}
```

### Field reference

- **`version`** (`str`): engine ID + version. Stable across releases of
  the same minor version.
- **`profile`** (`dict`): echo of input sex/age.
- **`meta.field_meta`**: for each parsed lab, how it was sourced (`input` or
  `derived`), the input key used, the raw value, the input unit (if any),
  and the canonical unit.
- **`meta.computed_abs`**: list of absolute differential counts (anc, alc, …)
  that were computed from `wbc × pct/100` because they weren't supplied
  directly.
- **`meta.normalized_diff`**: indicates whether the differential percentages
  were auto-scaled from fractions.
- **`meta.missing_core`**: list of missing core fields (wbc / hgb / plt).
- **`summary.headline`**: one-sentence patient-facing summary.
- **`summary.signals_high` / `signals_medium`**: counts.
- **`labs`**: full lab cards, sorted by `cfg.lab_order`.
- **`flags`**: per-lab string tag `"low" | "normal" | "high"`.
- **`derived`**: indices that aren't input directly. **`nlr`** (neutrophil:
  lymphocyte ratio), **`plr`** (platelet:lymphocyte), **`sii`** (systemic
  immune-inflammation index, = neut × plt / lymph), **`mentzer_index`**
  (= MCV / RBC, helps distinguish IDA from beta-thal trait).
- **`signals`**: clinical findings, sorted by (severity ↓, priority ↓, id ↑).
- **`combos`**: cross-signal patterns (e.g. "bacterial-like" = leukocytosis +
  neutrophilia).
- **`recommendations.next_tests`** / **`ask_doctor`**: actionable next steps,
  sorted by priority.
- **`disclaimer`**: educational-use disclaimer in Ukrainian. Stable string.

---

## 8. Clinical signals — full catalog

40 signal IDs total — 39 clinical + 1 data-quality.

### 8.1 Data-quality (1)

| ID | Severity | Fires when |
|---|---|---|
| `missing_core_cbc` | low | none of `wbc, hgb, plt` was supplied |

### 8.2 White-cell signals (12)

| ID | Severity | Fires when |
|---|---|---|
| `leukocytosis` | low–high | WBC > ref.high |
| `leukopenia` | low–high | WBC < ref.low |
| `neutrophilia` | low–high | ANC > ref.high |
| `neutropenia` | low–high (high if ANC < 0.5) | ANC < ref.low |
| `neutrophilic_leukocytosis` | medium | leukocytosis AND neutrophil predominance (≥75%) |
| `relative_neutrophilia` | low | neut% > ref.high but ANC normal |
| `lymphocytosis` | low–high | ALC > ref.high |
| `lymphopenia` | low–medium | ALC < ref.low |
| `relative_lymphocytosis` | low | lymph% > ref.high but ALC normal |
| `monocytosis` | low | AMC > ref.high |
| `eosinophilia` | low–medium | AEC > ref.high |
| `basophilia` | low | ABC > ref.high |

### 8.3 Red-cell signals (12)

| ID | Severity | Fires when |
|---|---|---|
| `anemia_possible` | low–high (high if Hgb < 7) | Hgb < sex-specific ref.low |
| `high_hgb` | low–medium | Hgb > ref.high |
| `high_rdw` | low | RDW > ref.high |
| `microcytic_anemia_pattern` | medium | anemia + MCV < 80 |
| `macrocytic_anemia_pattern` | medium | anemia + MCV > 100 |
| `normocytic_anemia_pattern` | medium | anemia + 80 ≤ MCV ≤ 100 |
| `microcytosis_without_anemia` | low | MCV < 80 with normal Hgb |
| `macrocytosis_without_anemia` | low | MCV > 100 with normal Hgb |
| `iron_deficiency_likely_pattern` | medium | anemia + low MCV + high RDW + (Mentzer > 13) |
| `thal_trait_like_pattern` | low | Hgb mildly low + very low MCV + **normal RDW** + normal/high RBC |
| `low_mchc_hypochromia` | low | MCHC < ref.low |
| `high_mchc_note` | info | MCHC > ref.high (mostly artefactual — note only) |
| `hemoconcentration_possible` | low | high Hgb + high Hct + signs of dehydration |

### 8.4 Platelet signals (4)

| ID | Severity | Fires when |
|---|---|---|
| `thrombocytopenia` | low–high (high if PLT < 50) | PLT < ref.low |
| `thrombocytosis` | low–medium | PLT > ref.high |
| `low_plt_high_mpv` | info | low PLT + high MPV (peripheral destruction pattern) |
| `low_plt_low_mpv` | info | low PLT + low MPV (production-deficit pattern) |

### 8.5 Multi-lineage / combination patterns (5)

| ID | Severity | Fires when |
|---|---|---|
| `pancytopenia_pattern` | high | all 3 lines low (WBC + Hgb + PLT) |
| `bicytopenia_wbc_hgb` | medium | WBC low + Hgb low |
| `bicytopenia_wbc_plt` | medium | WBC low + PLT low |
| `bicytopenia_hgb_plt` | medium | Hgb low + PLT low |
| `plt_high_microcytosis_combo` | low | thrombocytosis + microcytosis (often iron-deficiency reactive) |

### 8.6 Supportive / derived (2)

| ID | Severity | Fires when |
|---|---|---|
| `elevated_esr` | low–medium | ESR > 20 |
| `nlr_high` | low | NLR > 6 (systemic inflammation marker) |

### 8.7 Context-aware variants (3)

These replace the generic signal when patient context is provided:

| ID | Severity | Fires when |
|---|---|---|
| `anemia_with_diabetes` | medium | normocytic anemia + `has_diabetes:true` |
| `leukocytosis_on_steroids` | low | high WBC + `on_corticosteroids:true` |
| `thrombocytopenia_on_anticoagulants` | high | low PLT + `on_oral_anticoagulants:true` |

---

## 9. Narrative layer (31 clusters)

The narrative engine takes the engine's signal output and renders a
patient-friendly story in Ukrainian or English. The story is selected from
31 pre-written clusters defined in `clusters.yaml`.

Each cluster has:

- `id`: maps to template file names (`<id>.uk.md`, `<id>.en.md`)
- `tier`: `critical | abnormal | info | minor | normal` — drives the UI badge
- `priority`: tie-breaker for cluster selection
- `requires`: list of signal IDs that must be present
- `suppresses`: list of clusters this one overrides (so we don't show
  "isolated leukocytosis" alongside "bacterial pattern")

### Cluster list

| ID | Tier | Triggers on |
|---|---|---|
| `all_normal` | normal | zero clinical signals |
| `incomplete` | info | `missing_core_cbc` |
| `anemia_iron_deficiency` | abnormal | `iron_deficiency_likely_pattern` |
| `anemia_macrocytic` | abnormal | `macrocytic_anemia_pattern` |
| `anemia_normocytic` | abnormal | `normocytic_anemia_pattern` |
| `anemia_possible_isolated` | abnormal | `anemia_possible` w/o microcytic/macrocytic |
| `anemia_with_diabetes` | abnormal | `anemia_with_diabetes` |
| `elevated_esr` | minor | `elevated_esr` |
| `eosinophilia_story` | minor | `eosinophilia` |
| `hemoconcentration` | minor | `hemoconcentration_possible` |
| `infection_pattern` | abnormal | `bacterial_like_pattern` combo |
| `isolated_basophilia` | minor | `basophilia` |
| `isolated_high_rdw` | minor | `high_rdw` w/o anemia |
| `isolated_leukocytosis` | minor | `leukocytosis` without neutrophilia/lymphocytosis |
| `isolated_leukopenia` | minor | `leukopenia` |
| `isolated_macrocytosis` | minor | `macrocytosis_without_anemia` |
| `isolated_microcytosis` | minor | `microcytosis_without_anemia` |
| `isolated_monocytosis` | minor | `monocytosis` |
| `isolated_nlr_high` | minor | `nlr_high` w/o leukocytosis |
| `isolated_thrombocytopenia` | abnormal | `thrombocytopenia` w/o pancyt |
| `leukocytosis_on_steroids` | minor | `leukocytosis_on_steroids` |
| `lymphoproliferative_suspect` | abnormal | severe lymphocytosis in older adult |
| `neutrophilic_leukocytosis` | abnormal | `neutrophilic_leukocytosis` |
| `pancytopenia` | critical | `pancytopenia_pattern` |
| `polycythemia` | abnormal | `high_hgb` (severe) |
| `reactive_thrombocytosis` | minor | `thrombocytosis` |
| `severe_neutropenia` | critical | `neutropenia` (high severity) |
| `severe_thrombocytopenia` | critical | `thrombocytopenia` (high severity) |
| `severe_thrombocytosis` | abnormal | `thrombocytosis` (high severity) |
| `thalassemia_trait` | minor | `thal_trait_like_pattern` |
| `thrombocytopenia_on_anticoagulants` | critical | `thrombocytopenia_on_anticoagulants` |

= **31 clusters × 2 languages = 62 template files** (all present after
the May 2026 audit fixed the missing `neutrophilic_leukocytosis.en.md`).

---

## 10. Configuration & overrides

### 10.1 Default severity bands (textbook)

| Lab | mild | moderate | severe |
|---|---|---|---|
| `wbc_high` | 11.1 | 15.0 | 25.0 |
| `wbc_low` | 3.5 | 2.0 | 1.0 |
| `anc_high` | 7.6 | 12.0 | 20.0 |
| `anc_low` | 1.5 | 1.0 | 0.5 |
| `plt_high` | 450 | 600 | 1000 |
| `plt_low` | 150 | 100 | 50 |
| `esr_high` | 20 | 50 | 100 |
| `hgb_low_female` | 12.0 | 9.0 | 7.0 |
| `hgb_low_male` | 13.0 | 10.0 | 7.5 |

Other cutoffs: `mcv_micro = 80`, `mcv_macro = 100`, `nlr_high_cutoff = 6.0`.

### 10.2 Empirical (NHANES-derived) override

If the environment variable `CBC_ENGINE_CONFIG` points to
`outputs/engine_config.json`, those data-driven bands take precedence over
the textbook defaults. Per-request `payload["config"]` overrides win over
both.

```bash
export CBC_ENGINE_CONFIG=$(pwd)/outputs/engine_config.json
uvicorn main:app --port 8001
```

### 10.3 Per-request config

See [section 6.5](#65-config-overrides).

---

## 11. Validation layer

`validate_payload` runs before the engine and produces a structured
`ValidationResult` with two arrays:

- **`errors`** — block the request; engine should not run
- **`warnings`** — engine runs, but UI displays the warning

Coverage:

1. **Plausibility bounds** — every CBC field has hard physiological min/max.
   Values outside (e.g. negative Hgb, WBC = 10⁶) are blocked.
2. **Unit auto-correction** — common mistakes are silently fixed *with a warning*:
   - Hgb 40–240 → divide by 10 (g/L → g/dL)
   - Hct 0.08–0.75 → multiply by 100 (fraction → %)
   - PLT 1 000–3 000 000 → divide by 1 000 (/µL → 10³/µL)
   - WBC 500–500 000 → divide by 1 000 (/µL → 10³/µL)
   - RBC 500 000–8 500 000 → divide by 1 000 000 (/µL → 10⁶/µL)
   - MCHC 200–400 → divide by 10 (g/L → g/dL)
3. **Fraction-as-percent** — `neut_pct < 1` is auto-scaled to `× 100` if
   ≥2 differential fields are below 1. Eosinophils/basophils are exempt
   (their normal range includes < 1%).
4. **Required fields** — missing `sex` with red-cell labs supplied, or
   missing all core labs, surfaces a warning (not an error).
5. **NaN handling** — NaN values in numeric fields are stripped with a
   warning. (Bug fixed May 2026.)

---

## 12. Test suite

**361 tests, 10 files. Pass rate: 100%. Runtime: < 1 s.**

### test_units.py (47 tests)

| Class | Tests |
|---|---|
| `TestParseValueUnit` | int/float/None/empty/NaN/embedded units/garbage/negative/multiplier |
| `TestToKul` | All unit branches for WBC/PLT/abs conversion + unknown unit |
| `TestToMul` | Same for RBC |
| `TestToGdlHb` | g/dL passthrough, g/L conversion |
| `TestSimpleConverters` | to_pct, to_fl, to_pg, to_gdl_mchc |
| `TestSmartRound` | None, digits, invalid input |
| `test_to_kul_default_round_trip` | Parametrized property test |

### test_config.py (18 tests)

`SeverityBand` frozen, `CBCConfig` defaults, `_parse_severity_band` (partial
override, non-dict, string coercion, bad value), `load_config` (empty, env,
override severity/mcv/lab_order/signal_priority, invalid entries skipped).

### test_knowledge.py (41 tests)

`RefRange` frozen + defaults. `LABS` catalog: 16 labs, all required fields,
sane bounds, sex-specific Hgb/RBC/ESR, non-empty descriptions. `ABS_REFS`:
5 keys, ordered bounds, ANC positive.

### test_pediatric.py (19 tests)

`PED_BANDS` table structure, `get_ped_band` (newborn / 10 yo / adult / negative
age / None), `get_pediatric_ref` (newborn Hgb high, year-specific MCV indices
1-11, unknown code, adult age), `get_pediatric_abs_ref`.

### test_validation.py (23 tests)

Static tables (PLAUSIBLE_RANGES, UNIT_CONFUSION_RULES, PCT_FIELDS).
`FieldIssue` / `ValidationResult` (localised messages, has_errors). Happy path.
Unit confusion (Hgb 145→14.5, Hct 0.42→42, PLT 250 000→250, WBC 6 500→6.5,
RBC raw). Fraction-as-percent (single neut, eos exempt, baso exempt).
Plausibility errors (negative Hgb, extreme WBC, non-numeric, NaN). Required-field
warnings (sex missing with red labs, no core values).

### test_rules.py (61 tests)

- **Helpers**: `_flag` boundary closed-interval, `_sev_high` / `_sev_low` (band
  classification + None), `_sex_norm` (11 input variants, including NHANES
  numeric returns None).
- **Data-quality signal**: `missing_core_cbc` fires/doesn't fire.
- **White cells**: leukocytosis, leukopenia, neutrophilia, neutropenia
  (+ high severity), neutrophilic_leukocytosis (regression), lymphocytosis,
  lymphopenia, eosinophilia, monocytosis, basophilia.
- **Platelets**: thrombocytopenia (+ high), thrombocytosis.
- **Red cells**: anemia_possible, microcytic/macrocytic/normocytic patterns,
  high_hgb, high_rdw, iron_deficiency_likely_pattern, microcytosis/
  macrocytosis_without_anemia, thal_trait_like_pattern, low_mchc_hypochromia.
- **Combinations**: plt_high_microcytosis_combo, pancytopenia_pattern
  (+ high severity).
- **Supportive**: elevated_esr, nlr_high.
- **Context-aware variants**: anemia_with_diabetes, leukocytosis_on_steroids,
  thrombocytopenia_on_anticoagulants (+ high severity for bleeding risk).

### test_analyze.py (43 tests)

- Response envelope: every required top-level / meta / summary / recommendations key.
- Profile parsing: age coercion, string → float, invalid → None.
- Alias resolution: NHANES codes, Ukrainian ESR, completeness of `ALIASES` table.
- Abs-count derivation: from pct, no WBC → no derivation, input abs overrides.
- Diff-percent normalization: fraction input scaled, percent input passthrough.
- Reference overrides: custom Hgb low, `ref_ranges` and `ref` aliases.
- Config overrides: severity threshold reclassifies severity.
- Sorting: labs by `lab_order`, signals by severity-first.
- **Determinism**: 100 runs on same input → 1 unique hash, across all 15 fixtures.
- Edge cases: empty payload, only age, embedded-unit strings, signal/lab field
  requirements.

### test_narrative.py (25 tests)

- Clusters config: file exists, loads, all have required keys, IDs unique,
  exactly 31, priority field present.
- Template files: dir exists, every cluster has both UK + EN, total = 62,
  `neutrophilic_leukocytosis.en.md` exists (regression), non-empty, has
  `---` separator.
- `build_narrative`: returns NarrativeReport, UK and EN render, healthy →
  `all_normal`, incomplete → `incomplete`, stories have title/body/severity,
  signals_used populated.
- `chrome`: UK and EN labels present, all 5 tiers, UK ≠ EN.
- Integrity: every cluster has matching template files, no orphan files.

### test_api.py (13 tests)

GET `/`, `/health`, `/fields`, `/openapi.json`. POST `/analyze` (normal,
invalid 400, IDA detected). POST `/analyze/batch` (two patients, empty edge).
POST `/analyze/narrative` (UK default, EN via query). Cross-cutting: CORS,
gzip.

### test_requirements.py (32 tests) — DEFENSE TESTS

Each test maps to one specific project requirement:

- **R1** — Engine version + response envelope contract (5 tests)
- **R2** — Signal catalog: 40 IDs, severity values, urgent → high (4 tests)
- **R3** — 31 clusters with full UK/EN parity, 62 template files (3 tests)
- **R4** — Reference ranges: 16 adult, 5 abs, sex-specific Hgb, pediatric
  coverage (4 tests)
- **R5** — Input flexibility: NHANES codes, Ukrainian, embedded units,
  fractions, aliases (5 tests)
- **R6** — Determinism: 100 runs → byte-identical (1 test)
- **R7** — Safety: missing_core priority, empty warning, severity propagation
  (3 tests)
- **R8** — Empirical config: outputs files present & well-formed (2 tests)
- **R9** — Validation contract: PLAUSIBLE_RANGES coverage, unit-confusion
  coverage, structured result (3 tests)

### test_e2e.py (21 tests) — 14 clinical scenarios

Each scenario is a deliberate "textbook patient":

1. **IDA** — iron deficiency in menstruating woman (3 tests)
2. **B12 macrocytic** anemia (2 tests)
3. **Thalassemia trait** (vs IDA discrimination) (1 test)
4. **Bacterial-like** leukocytosis (CAP) (2 tests)
5. **Viral lymphocytosis** (mono-like) (2 tests)
6. **Severe neutropenia** (chemo nadir) (1 test)
7. **ITP** — severe isolated thrombocytopenia (1 test)
8. **Pancytopenia** (aplastic / MDS) (2 tests)
9. **Polycythemia vera-like** (2 tests)
10. **CLL-like** chronic lymphocytic leukemia (1 test)
11. **Allergic/parasitic eosinophilia** (1 test)
12. **Reactive thrombocytosis** (1 test)
13. **Steroid-induced leukocytosis** (NOT infection) — context-aware (1 test)
14. **All-normal healthy** — sanity baseline (2 tests)

---

## 13. How to run

### Locally (development)

```bash
cd cbc/engine
python3 -m pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

API docs at <http://localhost:8001/docs>.

### Tests

```bash
cd cbc/engine
pytest tests/ -v          # all 361 tests
pytest tests/test_e2e.py  # just the e2e suite
pytest tests/ -k "TestR2" # just the signal-catalog defense tests
```

### Docker

```bash
cd cbc/engine
docker build -t hemax-cbc-api .
docker run -p 8001:8001 hemax-cbc-api
```

### docker-compose

```bash
cd cbc/engine
docker-compose up --build
```

### Empirical config (optional)

```bash
export CBC_ENGINE_CONFIG=$(pwd)/outputs/engine_config.json
uvicorn main:app --port 8001
```

---

## 14. Design decisions & limitations

### 14.1 Why rule-based, not ML?

CBC interpretation is **explicit clinical reasoning**, not pattern recognition.
A rule-based engine:

- gives reasons for every decision (`why`, `evidence`, `next` in each signal)
- is fully auditable
- has no training-distribution shift
- can be updated by editing one rule rather than retraining

The trade-off is that we don't capture multivariate patterns invisible to
single-rule cutoffs. Phase 2 validation against NHANES (`outputs/
validation_report.md`) gives us the empirical confidence that the rules
have meaningful clinical lift on self-reported outcomes.

### 14.2 Why two reference systems (textbook + empirical)?

Textbook ranges are conservative defaults that work everywhere. Empirical
NHANES-derived bands are tuned to a specific population. By keeping them
**both**, users can:

- run the engine "out of the box" without any config
- opt-in to data-driven bands by setting `CBC_ENGINE_CONFIG`
- override per request for lab-specific ranges

### 14.3 Why patient-facing narrative AND structured signals?

Different consumers want different things:

- **Front-end UI** → uses `signals[]` + `recommendations[]` for filtering/sorting
- **PDF report** → uses the narrative `stories[]` for human-readable output
- **Downstream analytics** → uses `flags{}` + `derived{}` for tabular pipelines

Separating these concerns keeps each layer simple.

### 14.4 Known limitations

- **No multi-time-point reasoning.** Engine sees one CBC at a time. Dynamics
  ("WBC was 8 last week, now 18") require a wrapper.
- **No lab-specific ref intervals out of the box.** Per-lab refs require
  the consumer to pass `ref_ranges`.
- **Pediatric refs above age 12 require sex.** This is biology (puberty),
  not a bug.
- **`relative_neutrophilia` / `relative_lymphocytosis` use the % only.**
  If you have absolute counts, they're the better signal — but we surface
  the relative signal too for cases where only % was reported.
- **No coagulation labs.** PT / aPTT / fibrinogen are outside scope.

### 14.5 Bugs found and fixed during audit (May 2026)

1. **Missing EN template** for `neutrophilic_leukocytosis` — created.
   Regression test in `test_narrative.py::test_neutrophilic_leukocytosis_en_template_exists`.
2. **NaN survival** in `validate_payload` — NaN floats survived `dict(payload)`
   and propagated to the engine. Now stripped with a warning.
   Regression test in `test_validation.py::test_nan_value_treated_as_missing`.

---

*Last updated: May 2026. Generated for thesis defense.*
