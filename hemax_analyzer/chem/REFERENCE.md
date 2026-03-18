# HEMAX — CHEM Module Reference

> A self-contained reference for the clinical-chemistry (CHEM) interpretation
> service. Covers architecture, runtime API, every signal & combo, every test,
> and how to run it.

---

## Table of contents

1. [What this module does](#1-what-this-module-does)
2. [Folder layout](#2-folder-layout)
3. [Runtime stack](#3-runtime-stack)
4. [HTTP API reference](#4-http-api-reference)
5. [Input contract](#5-input-contract)
6. [Output contract](#6-output-contract)
7. [Clinical signals — full catalog (32+)](#7-clinical-signals--full-catalog)
8. [Combo patterns — full catalog (5)](#8-combo-patterns--full-catalog)
9. [Narrative layer (48 clusters)](#9-narrative-layer-48-clusters)
10. [Derived analytes](#10-derived-analytes)
11. [Configuration](#11-configuration)
12. [Test suite](#12-test-suite)
13. [How to run](#13-how-to-run)
14. [Design decisions](#14-design-decisions)

---

## 1. What this module does

Takes a clinical-chemistry panel (JSON) and produces a structured medical
interpretation with:

- **34 analytes** — full CMP + lipid panel + iron panel + vitamin D
- **32+ distinct signal IDs** — isolated abnormalities + data-quality flag
- **5 multi-marker combo patterns** — cross-analyte clinical syndromes
- **48 narrative clusters** — patient-friendly explanations in UK and EN
- **9 derived analytes** — eGFR (CKD-EPI 2021), anion gap, non-HDL,
  TC/HDL, TG/HDL, AST/ALT, corrected calcium, globulin, A/G ratio, TSAT
- **Sex-specific reference ranges** where biologically warranted
- **Deterministic output** — identical input produces byte-identical output

The service is rule-based, not ML. Clinical logic lives in `rules.py`. No
training data, no learned parameters.

---

## 2. Folder layout

```
chem/
├── REFERENCE.md                     ← this file (the only doc)
│
├── engine/                          ← the service
│   ├── Dockerfile · requirements.txt · .env.example
│   │
│   ├── chem_api/                    ← the engine package
│   │   ├── app.py                   ← FastAPI app factory
│   │   ├── router.py                ← HTTP route definitions (6 endpoints)
│   │   ├── models.py                ← Pydantic request/response shapes
│   │   ├── dependencies.py · exceptions.py · middleware.py
│   │   │
│   │   ├── chem/                    ← core engine
│   │   │   ├── analyze.py           ← public entry: analyze_chem_payload()
│   │   │   ├── rules.py             ← all 32+ clinical signals + 5 combos
│   │   │   ├── derived.py           ← shared derivation helpers
│   │   │   ├── knowledge.py         ← LABS catalog (34 analytes)
│   │   │   ├── refs.py              ← reference-range overrides
│   │   │   ├── render.py            ← labs-card builders
│   │   │   ├── parse.py             ← alternative number+unit parser
│   │   │   ├── units.py             ← 17 unit-conversion helpers
│   │   │   ├── config.py            ← ChemConfig + severity bands
│   │   │   └── spec.py              ← RefRange + LabDef dataclasses
│   │   │
│   │   └── narrative/               ← Phase 4 — patient-facing stories
│   │       ├── narrative_engine.py
│   │       ├── clusters.yaml        ← 48 cluster definitions
│   │       └── templates/           ← 96 .md templates (48 UK + 48 EN)
│   │
│   └── tests/                       ← test suite (10 files, 349 tests)
│       ├── conftest.py              ← 15 patient fixtures
│       ├── test_units.py            ← 41 — 17 unit conversions
│       ├── test_parse.py            ← 12 — alternative parser
│       ├── test_config.py           ← 12 — ChemConfig + SeverityBand
│       ├── test_knowledge.py        ← 79 — LABS catalog integrity
│       ├── test_derived.py          ← 20 — eGFR, lipid ratios, etc.
│       ├── test_rules.py            ← 41 — every clinical signal
│       ├── test_analyze.py          ← 50 — full pipeline + determinism
│       ├── test_narrative.py        ← 18 — 48 clusters × 2 templates
│       ├── test_api.py              ← 11 — FastAPI endpoints
│       ├── test_e2e.py              ← 23 — 21 clinical scenarios
│       └── test_requirements.py     ← 35 — DEFENSE TESTS (R1-R9)
│
├── demo/                            ← runnable examples
│   ├── manual_patient_test.py       ← 21 curated patients
│   └── narrative_demo.py            ← pretty-prints stories
│
└── analyze_chem_diploma.py          ← thesis analysis script
```

---

## 3. Runtime stack

| Layer | Tech |
|---|---|
| HTTP | FastAPI + Uvicorn (`/chem/*` routes) |
| Engine | Pure Python (no NumPy required) |
| Templates | Jinja2 (with graceful fallback) |
| Tests | pytest 9 |
| Container | Python 3.11-slim |

---

## 4. HTTP API reference

Six endpoints, all under the `/chem` prefix:

| Method | Path | Purpose |
|---|---|---|
| GET | `/chem/health` | Health check |
| GET | `/chem/info` | Module metadata |
| GET | `/chem/labs` | List all supported lab codes |
| GET | `/chem/labs/{code}` | Detail for one lab |
| POST | `/chem/analyze` | Analyze a chemistry panel |
| POST | `/chem/analyze/narrative` | Analyze + return narrative stories |

OpenAPI/Swagger docs at <http://localhost:8001/docs> once the server runs.

### Example: POST /chem/analyze

```bash
curl -X POST http://localhost:8001/chem/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "sex": "female", "age": 58,
    "glucose": 180, "a1c": 8.5,
    "creatinine": 1.1,
    "tchol": 230, "hdl": 40, "trigly": 200
  }'
```

### Example: POST /chem/analyze/narrative?lang=en

Same payload as `/chem/analyze`. The `lang` query parameter selects `uk`
(default) or `en`.

---

## 5. Input contract

### 5.1 Canonical analyte fields

34 analytes are recognized. Each accepts multiple aliases — the first
non-null one wins.

| Canonical | Common aliases | NHANES code | Unit |
|---|---|---|---|
| `glucose` | `glu` | `LBXGLU` | mg/dL |
| `a1c` | `hba1c`, `HbA1c` | `LBXGH` | % |
| `creatinine` | `scr` | `LBXSCR` | mg/dL |
| `urea` | — | — | mg/dL |
| `bun` | — | `LBXSCBUN` | mg/dL |
| `alt` | `SGPT` | `LBXSAT` | U/L |
| `ast` | `SGOT` | `LBXSAS` | U/L |
| `alp` | `alk_phos` | — | U/L |
| `ggt` | `gamma_gt` | — | U/L |
| `bilirubin_total` | `tbil`, `bilirubin` | `LBXSTB` | mg/dL |
| `bilirubin_direct` | `dbil` | — | mg/dL |
| `albumin` | `alb` | `LBDSAL` | g/dL |
| `total_protein` | `tp` | `LBXSTP` | g/dL |
| `tchol` | `cholesterol`, `total_cholesterol` | `LBXTC` | mg/dL |
| `hdl` | — | `LBXHDD`, `LBXHDL` | mg/dL |
| `ldl` | — | `LBDLDL` | mg/dL |
| `trigly` | `triglycerides` | `LBXTR` | mg/dL |
| `crp` | `hscrp` | `LBXCRP` | mg/L |
| `sodium` | `na` | `LBXSNA` | mmol/L |
| `potassium` | `k` | `LBXSKSI` | mmol/L |
| `chloride` | `cl` | — | mmol/L |
| `bicarbonate` | `co2`, `tco2`, `hco3` | — | mmol/L |
| `calcium` | `ca` | — | mg/dL |
| `magnesium` | `mg` | — | mg/dL |
| `phosphate` | `phos`, `phosphorus` | — | mg/dL |
| `iron` | `fe` | — | µg/dL |
| `ferritin` | `fer` | — | ng/mL |
| `tibc` | — | — | µg/dL |
| `tsat` | `transferrin_saturation` | — | % |
| `uric_acid` | `uric`, `ua` | — | mg/dL |
| `amylase` | `amy` | — | U/L |
| `lipase` | `lip` | — | U/L |
| `ck` | `cpk`, `creatine_kinase` | — | U/L |
| `ldh` | `lactate_dehydrogenase` | — | U/L |
| `vitd_25oh` | `vitd`, `vitamin_d`, `25ohd` | — | ng/mL |
| `egfr` | `gfr` | — | mL/min/1.73m² |

### 5.2 Embedded units

Numeric values may carry units inline. The engine auto-converts to the
canonical unit (column above):

- `"glucose": "5.0 mmol/L"` → 90 mg/dL
- `"creatinine": "88 umol/L"` → ~1.0 mg/dL
- `"bun": "7 mmol/L"` → ~19.6 mg/dL (NOT 42 — BUN ≠ urea, see units.py)
- `"hgb": "145 g/L"` → 14.5 g/dL
- `"sodium": "140 mmol/L"` → 140
- `"a1c": "6.1%"` → 6.1

### 5.3 Context fields

```json
{
  "sex": "female", "age": 58,
  "glucose": 180,
  "fasting_hours": 10,
  "fasting_8h": true,
  "clinical_context": {
    "has_diabetes": true,
    "on_statins": false,
    "on_metformin": true
  }
}
```

- `fasting_hours` — numeric hours since last meal
- `fasting_8h` — explicit boolean; accepts `true`/`false`/`1`/`0`/`yes`/`no`/`так`/`ні`
- If only `fasting_hours` is given, `fasting_8h` is derived as `hours ≥ 8`
- `clinical_context` — dict of boolean-coercible flags; non-boolean values
  are silently dropped

### 5.4 Reference range overrides

```json
{
  "sex": "male", "age": 30, "glucose": 95,
  "ref_ranges": {
    "glucose": {"low": 60, "high": 90}
  }
}
```

Overrides flow both to the rules engine and to the lab cards on the
response — `ref_source: "override"` is set so the UI can show a badge.

---

## 6. Output contract

```json
{
  "version": "chem_interpreter_prod_v1_2_max",

  "profile": {"sex": "female", "age": 58.0},

  "meta": {
    "field_meta": {
      "glucose": {"source": "input", "input_key": "glucose",
                  "raw": 180, "unit_in": null, "unit": "mg/dL"},
      "egfr":    {"source": "computed", "computed_from": ["creatinine","age","sex"],
                  "formula": "CKD-EPI 2021", "unit": "mL/min/1.73m²"}
    },
    "computed": ["non_hdl", "tc_hdl_ratio", "tg_hdl_ratio", "egfr"],
    "context": {
      "fasting_hours": 10.0,
      "fasting_8h": true,
      "clinical": {"has_diabetes": true},
      "fasting_input": {"fasting_hours_key": "fasting_hours", ...}
    },
    "missing_core": []
  },

  "summary": {
    "headline": "Є сигнали високого пріоритету — бажано обговорити з лікарем.",
    "signals_high": 1,
    "signals_medium": 2,
    "notes": [
      "Це освітня інтерпретація, не діагноз.",
      "Точні референси залежать від лабораторії. ...",
      "Окремі показники (глюкоза, ліпіди) важливо інтерпретувати ..."
    ]
  },

  "labs": [
    {
      "code": "glucose",
      "name": "Глюкоза",
      "value": 180,
      "unit": "mg/dL",
      "ref": {"low": 70, "high": 99},
      "flag": "high",
      "what": "...",
      "tips": ["..."],
      "source": "input",
      "input_key": "glucose",
      "computed_from": null,
      "formula": null,
      "unit_in": null,
      "ref_source": "default"
    }
  ],

  "flags": {"glucose": "high", "a1c": "high", "creatinine": "normal", ...},

  "derived": {"egfr": 65.2, "anion_gap": 13, "non_hdl": 190, ...},

  "signals": [
    {
      "id": "glucose_diabetes_range",
      "severity": "high",
      "title": "...",
      "why": "...",
      "evidence": {"glucose_mgdl": 180, ...},
      "tags": ["glucose"]
    }
  ],

  "combos": [
    {"id": "atherogenic_dyslipidemia_pattern", "severity": "medium", ...}
  ],

  "recommendations": [...],

  "disclaimer": "Освітня інтерпретація. Не є медичною консультацією. ..."
}
```

---

## 7. Clinical signals — full catalog

32 distinct isolated-signal IDs, grouped by analyte system:

### 7.1 Data-quality (1)

| ID | Severity | Fires when |
|---|---|---|
| `missing_core_chem` | low | core panels (glucose/A1c, creatinine, ALT/AST, lipids) are absent |

### 7.2 Glucose homeostasis (6)

| ID | Severity | Trigger |
|---|---|---|
| `glucose_diabetes_range` | low–high | glucose ≥ 126 mg/dL (fasting) or ≥ 200 (random) |
| `glucose_ifg_range` | low | glucose 100-125 (IFG) |
| `a1c_diabetes_range` | medium–high | A1c ≥ 6.5% |
| `a1c_prediabetes_range` | low | A1c 5.7-6.4% |
| `hypoglycemia` | low–medium | glucose < 70 |
| `severe_hypoglycemia` | high | glucose < 40 |

### 7.3 Electrolytes (8)

| ID | Severity | Trigger |
|---|---|---|
| `hyperkalemia` | low–high | K > 5.5 mmol/L |
| `hypokalemia` | low–high | K < 3.5 mmol/L |
| `hyponatremia` | low–high | Na < 135 mmol/L |
| `hypernatremia` | low–high | Na > 145 mmol/L |
| `bicarbonate_high` | low | HCO3 > 30 |
| `bicarbonate_low` | low | HCO3 < 22 |
| `chloride_high` | low | Cl > 110 |
| `chloride_low` | low | Cl < 95 |

### 7.4 Renal (2)

| ID | Severity | Trigger |
|---|---|---|
| `creatinine_high` | low–medium | Cr > sex-specific upper limit |
| `egfr_low` | low–high | eGFR < 60 (CKD G3+) |

### 7.5 Liver (2)

| ID | Severity | Trigger |
|---|---|---|
| `transaminitis` | low–medium | ALT or AST > 2× upper limit |
| `bilirubin_high` | low–medium | total bilirubin > 1.2 |

### 7.6 Lipids (5 isolated)

| ID | Severity | Trigger |
|---|---|---|
| `tchol_high` | low | TC > 200 |
| `low_hdl` | low | HDL < 40 (M) / 50 (F) |
| `non_hdl_high` | low–medium | non-HDL > 130 |
| `hypertriglyceridemia` | low–medium | TG > 150 |
| `tg_hdl_ratio_high` | low | TG/HDL > 3 |
| `atherogenic_dyslipidemia_pattern` | medium | high TG + low HDL + high TG/HDL |

### 7.7 Inflammation / metabolic (8)

| ID | Severity | Trigger |
|---|---|---|
| `crp_high` | low–medium | CRP > 10 mg/L |
| `uric_acid_high` | low | UA > 7 (M) / 6 (F) |
| `iron_deficiency_likely` | low–medium | low ferritin + low iron + low TSAT |
| `ferritin_high_possible_inflammation` | low | ferritin > 300 (M) / 200 (F) |
| `high_tsat` | low | TSAT > 50% |
| `low_tsat` | low | TSAT < 16% |
| `vitd_deficiency` | low | 25(OH)D < 20 ng/mL |
| `vitd_insufficiency` | low | 25(OH)D 20-29 ng/mL |
| `vitd_high` | low | 25(OH)D > 80 ng/mL (toxicity range) |

---

## 8. Combo patterns — full catalog

5 multi-marker patterns that fire as `combos[]` (separate from signals):

| ID | Severity | Trigger |
|---|---|---|
| `kidney_function_reduced` | medium–high | egfr < 60 + creatinine high (high if egfr < 30) |
| `tg_very_high_pancreatitis_risk` | high | TG ≥ 500 |
| `fh_like_ldl_ge190` | medium | LDL ≥ 190 (suspect FH) |
| `insulin_resistance_nafld_like` | low–medium | high TG + low HDL + elevated ALT/AST |
| `hyponatremia_with_hyperglycemia_corrected_na` | low | Na < 135 + glucose > 250 (calculates corrected Na) |

---

## 9. Narrative layer (48 clusters)

Each cluster is a pre-written clinical story rendered in UK or EN. Cluster
selection is driven by which signals/combos fired; suppression rules avoid
duplicates (e.g. "iron_deficiency" suppresses "isolated_low_iron").

The 48 clusters cover all major clinical scenarios — from `all_normal` and
`incomplete` (data-quality) through `pancreatitis_pattern`,
`rhabdomyolysis_pattern`, `severe_hypoglycemia`, etc.

**31 cluster IDs × 2 languages = 96 template files**, all present and
non-empty. Regression tests in `test_narrative.py` enforce parity.

---

## 10. Derived analytes

9 analytes are auto-computed when their inputs are available:

| Code | Formula | Inputs | Unit |
|---|---|---|---|
| `egfr` | CKD-EPI 2021 (race-free) | creatinine + age + sex | mL/min/1.73m² |
| `non_hdl` | TC - HDL | tchol, hdl | mg/dL |
| `ldl` (Friedewald) | TC - HDL - TG/5 (only when TG < 400) | tchol, hdl, trigly | mg/dL |
| `tc_hdl_ratio` | TC / HDL | tchol, hdl | ratio |
| `tg_hdl_ratio` | TG / HDL | trigly, hdl | ratio |
| `ast_alt_ratio` | AST / ALT | ast, alt | ratio |
| `anion_gap` | Na - (Cl + HCO3) | sodium, chloride, bicarbonate | mmol/L |
| `calcium_corrected` | Ca + 0.8 × (4 - albumin) | calcium, albumin | mg/dL |
| `globulin` | total_protein - albumin | total_protein, albumin | g/dL |
| `ag_ratio` | albumin / globulin | (derived from globulin) | ratio |
| `tsat` | 100 × iron / TIBC | iron, tibc | % |

Each derived value's provenance is recorded in `meta.field_meta[code]` with
`computed_from`, `formula`, and `source: "computed"`.

---

## 11. Configuration

### Severity bands (default thresholds)

| Threshold | mild | moderate | severe |
|---|---|---|---|
| `glucose_high` | 110 | 126 | 250 |
| `glucose_low` | 70 | 54 | 40 |
| `potassium_high` | 5.5 | 6.0 | 6.5 |
| `potassium_low` | 3.4 | 3.0 | 2.5 |
| `sodium_high` | 146 | 150 | 160 |
| `sodium_low` | 134 | 130 | 120 |
| `trigly_high` | 150 | 200 | 500 |

### Signal priorities (highest first)

```
hyperkalemia, hypokalemia               120
hyponatremia, hypernatremia, severe_hypoglycemia   110
...
```

---

## 12. Test suite

**349 tests, 10 files. Pass rate: 100%. Runtime: < 1 s.**

| File | Tests | Coverage |
|---|---|---|
| `test_units.py` | 41 | All 17 unit-conversion functions: glucose, lipids, creatinine, urea, **BUN (≠ urea)**, bilirubin, uric acid, albumin/protein, CRP, electrolytes, minerals, iron, percent. |
| `test_parse.py` | 12 | `parse_number_and_unit` — int/float/None/empty/embedded unit/µ-normalization/garbage. |
| `test_config.py` | 12 | `ChemConfig` defaults, severity bands, signal priorities, lab_order completeness. |
| `test_knowledge.py` | 79 | LABS catalog: all 34 analytes present, required fields, sex-specific HDL/creatinine, realistic ranges. |
| `test_derived.py` | 20 | eGFR (input vs computed, sex factor, age dependence, CKD-EPI 2021), Friedewald LDL (skipped when TG ≥ 400), ratios, anion gap, corrected calcium, globulin, A/G, TSAT. |
| `test_rules.py` | 41 | Every clinical signal: glucose (6), electrolytes (8), renal (2), liver (2), lipids (7), inflammation/uric/iron/vitD (9). Combos via separate helper. |
| `test_analyze.py` | 50 | Response envelope, profile parsing, alias resolution, embedded units, fasting context, clinical context, ref_ranges override, negative value rejection, **determinism (100 runs)**, edge cases. |
| `test_narrative.py` | 18 | 48 clusters loaded, every cluster has BOTH UK + EN templates, total 96 files, no orphans, build_narrative returns NarrativeReport. |
| `test_api.py` | 11 | All 6 FastAPI endpoints: `/health`, `/info`, `/labs`, `/labs/{code}`, `/analyze`, `/analyze/narrative`. |
| `test_e2e.py` | 23 | 21 curated clinical scenarios: established T2D, prediabetes, metabolic syndrome, severe TG, FH suspect, atherogenic dyslipidemia, CKD G3b-G4, urgent electrolytes, hepatocellular injury, cholestatic pattern, IDA, hyperuricemia, vitD deficiency/insufficiency, severe hypoglycemia, acute inflammation, pseudohyponatremia, iron overload, hypochloremia, mild hyponatremia, all-normal baseline. |
| `test_requirements.py` | 35 | **DEFENSE TESTS — R1-R9** (see below). |

### Defense tests (test_requirements.py)

Each test maps directly to one project requirement:

- **R1** — Engine version + response envelope contract (5 tests)
- **R2** — Signal catalog: 32+ IDs, missing_core_chem data-quality, severity classification (4 tests)
- **R3** — Combo catalog: 5 multi-marker patterns (5 tests)
- **R4** — Narrative coverage: 48 clusters × 2 langs = 96 templates (3 tests)
- **R5** — Reference ranges: 34 analytes, sex-specific HDL/creatinine, realistic K/glucose (4 tests)
- **R6** — Input flexibility: NHANES codes, embedded units (mmol/L → mg/dL), Ukrainian fasting tokens (4 tests)
- **R7** — Derived analytes: eGFR (CKD-EPI 2021), anion gap, lipid ratios, corrected calcium (5 tests)
- **R8** — Determinism: 100 runs → 1 unique hash (1 test)
- **R9** — Safety: data-quality flag, severity sorting, urgent-first priority (4 tests)

---

## 13. How to run

```bash
cd chem/engine
python3 -m pip install -r requirements.txt --break-system-packages 2>/dev/null \
  || python3 -m pip install -r requirements.txt
python3 -m pytest tests/ -q
# Expect: 349 passed in < 2 s
```

### Run the server

```bash
cd chem/engine
uvicorn chem_api.app:create_app --factory --port 8001 --reload
# OpenAPI docs at http://localhost:8001/docs
```

### Docker

```bash
cd chem/engine
docker build -t hemax-chem-api .
docker run -p 8001:8001 hemax-chem-api
```

---

## 14. Design decisions

### Why rule-based?

Clinical chemistry interpretation is **explicit reasoning**, not pattern
recognition. A rule-based engine:

- gives reasons for every decision (the `why`, `evidence`, `next` fields)
- is fully auditable
- can be updated by editing one rule rather than retraining
- is fully deterministic — same input → same output

### Why a `_CORE_LABS` table?

The legacy `analyze.py` had a 70-line `if/elif` block routing each analyte
to its converter. The refactor replaces that with a single declarative
table:

```python
_CORE_LABS = (
    _LabSpec("glucose",    to_mgdl_glucose,    "mg/dL"),
    _LabSpec("creatinine", to_mgdl_creatinine, "mg/dL"),
    ...
)
```

Adding a new analyte = adding one tuple, not editing an if-chain.

### Why isolate combos from signals?

A `signal` describes one abnormal analyte. A `combo` describes a *pattern*
across multiple analytes — like "atherogenic dyslipidemia" (high TG + low
HDL + high TG/HDL). Keeping them in separate response keys lets the UI
treat them differently (combos get more screen real estate; signals are
listed in a sortable table).

### Known limitations

- **BUN ≠ urea.** Common bug: routing both through the same converter
  gives a 3× error. CHEM uses `to_mgdl_bun` (factor ~2.8) for BUN and
  `to_mgdl_urea` (factor ~6.0) for urea-molecule. Regression test in
  `test_units.py::TestToMgdlBun`.
- **Friedewald LDL invalid above TG = 400.** The engine refuses to compute
  LDL in that regime. Use direct LDL measurement.
- **eGFR requires age + sex.** Without both, no eGFR is computed.
- **Sex-specific references only apply when sex is recognized.** Unknown
  sex falls back to combined ranges.

### Bugs found and fixed during audit (May 2026)

1. **BUN was routed through `to_mgdl_urea`** — gave 7 mmol/L → 42 mg/dL
   (false kidney-failure). Now uses correct BUN factor → 7 mmol/L →
   19.6 mg/dL. Regression test: `test_units.py::TestToMgdlBun::test_mmol_to_mgdl_bun`.
2. **eGFR string input was silently dropped** — front-ends that wrapped
   eGFR with its unit (`"38 mL/min/1.73m²"`) produced no card and no
   signal. Now parsed via `parse_value_unit`. Regression test:
   `test_derived.py::TestEGFR::test_egfr_input_string_with_unit`.
3. **Lab card flag used adult ref even with override** — fixed: card now
   honours `ref_ranges` overrides. Regression test:
   `test_analyze.py::TestRefRangesOverride::test_override_changes_flag`.
4. **Floating-point comparison artefacts** — values like 1.3009 > 1.3 after
   mmol/L → mg/dL conversion. Now `round(v, 2)` before flag comparison.

---

*Last updated: May 2026. Generated for thesis defense.*
