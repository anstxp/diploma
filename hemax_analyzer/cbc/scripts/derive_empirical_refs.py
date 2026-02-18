#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

log = logging.getLogger("empirical_refs")
rng = np.random.default_rng(42)



@dataclass(frozen=True)
class Biomarker:
    code: str
    display: str
    unit: str
    textbook_female: tuple[Optional[float], Optional[float]]
    textbook_male:   tuple[Optional[float], Optional[float]]
    plausible_min: float
    plausible_max: float

BIOMARKERS: list[Biomarker] = [
    Biomarker("wbc",       "WBC (leukocytes)",        "×10⁹/L",  (4.0, 11.0),   (4.0, 11.0),   0.5,  50.0),
    Biomarker("neut_pct",  "Neutrophils %",           "%",        (45.0, 75.0),  (45.0, 75.0),  5.0,  95.0),
    Biomarker("lymph_pct", "Lymphocytes %",           "%",        (20.0, 45.0),  (20.0, 45.0),  1.0,  90.0),
    Biomarker("mono_pct",  "Monocytes %",             "%",        (2.0, 10.0),   (2.0, 10.0),   0.0,  25.0),
    Biomarker("eos_pct",   "Eosinophils %",           "%",        (0.5, 5.0),    (0.5, 5.0),    0.0,  30.0),
    Biomarker("baso_pct",  "Basophils %",             "%",        (0.0, 1.5),    (0.0, 1.5),    0.0,  10.0),
    Biomarker("neut_abs",  "Neutrophils abs. (ANC)",  "×10⁹/L",  (1.5, 7.5),    (1.5, 7.5),    0.1,  30.0),
    Biomarker("lymph_abs", "Lymphocytes abs. (ALC)",  "×10⁹/L",  (1.0, 4.0),    (1.0, 4.0),    0.1,  15.0),
    Biomarker("mono_abs",  "Monocytes abs.",          "×10⁹/L",  (0.2, 0.8),    (0.2, 0.8),    0.0,   5.0),
    Biomarker("eos_abs",   "Eosinophils abs.",        "×10⁹/L",  (0.0, 0.5),    (0.0, 0.5),    0.0,   5.0),
    Biomarker("baso_abs",  "Basophils abs.",          "×10⁹/L",  (0.0, 0.1),    (0.0, 0.1),    0.0,   2.0),
    Biomarker("rbc",       "RBC",                     "×10¹²/L", (3.8, 5.2),    (4.2, 5.8),    2.0,   8.0),
    Biomarker("hb_gdl",    "Hemoglobin",              "g/dL",    (12.0, 16.0),  (13.0, 17.5),  5.0,  22.0),
    Biomarker("hct",       "Hematocrit",              "%",       (35.0, 47.0),  (41.0, 53.0), 15.0,  70.0),
    Biomarker("mcv",       "MCV",                     "fL",      (80.0, 100.0), (80.0, 100.0),50.0, 130.0),
    Biomarker("mch",       "MCH",                     "pg",      (27.0, 33.0),  (27.0, 33.0), 15.0,  45.0),
    Biomarker("mchc",      "MCHC",                    "g/dL",    (31.5, 36.5),  (31.5, 36.5),25.0,  40.0),
    Biomarker("rdw",       "RDW",                     "%",       (11.5, 15.0),  (11.5, 15.0),10.0,  25.0),
    Biomarker("plt",       "Platelets",               "×10⁹/L",  (150.0, 450.0),(150.0, 450.0),20.0,1200.0),
    Biomarker("mpv",       "MPV",                     "fL",      (7.0, 11.5),   (7.0, 11.5),   5.0,  15.0),
]



SELF_REPORT_EXCLUDE = [
    "told_chf","told_chd","told_angina","told_mi","told_stroke",
    "told_diabetes","told_htn","told_weak_kidney","told_dialysis",
    "told_cancer","told_liver","told_thyroid",
]
MED_EXCLUDE = ["on_htn_med","on_chol_med","on_insulin","on_oral_diabetes_med"]

LAB_RANGES: dict[str, tuple[float, float]] = {
    "hba1c_pct":        (4.0, 5.7),
    "glucose_fasting":  (65, 100),
    "tchol_mgdl":       (100, 240),
    "hdl_mgdl":         (35, 120),
    "trigly_mgdl":      (30, 200),
    "hs_crp":           (0, 3.0),
    "egfr_ckd_epi_2021":(60, 200),
    "sbp":              (85, 135),
    "dbp":              (50, 85),
    "alt_ul":           (5, 55),
    "ast_ul":           (5, 50),
    "bilirubin_total":  (0.1, 1.5),
    "albumin_gdl":      (3.5, 5.5),
    "creatinine_mgdl":  (0.4, 1.4),
    "bun_mgdl":         (6, 25),
    "sodium_mmoll":     (133, 147),
    "potassium_mmoll":  (3.3, 5.3),
    "calcium_mgdl":     (8.3, 10.8),
}


def build_reference_population(df: pd.DataFrame, age_min: int, age_max: int) -> pd.DataFrame:
    n0 = len(df)

    df = df[df["age_years"].between(age_min, age_max, inclusive="both").fillna(False)]
    df = df[df["sex"].isin([1, 2])]
    df = df[~df.get("pregnancy", pd.Series(0, index=df.index)).eq(1).fillna(False)]
    df = df[df["bmi"].between(18.5, 30.0, inclusive="both").fillna(False)]

    core = [c for c in ["hb_gdl", "creatinine_mgdl", "hdl_mgdl", "hba1c_pct"] if c in df.columns]
    if core:
        df = df[df[core].notna().any(axis=1)]

    for col in SELF_REPORT_EXCLUDE:
        if col in df.columns:
            df = df[~df[col].eq(1).fillna(False)]

    for col in MED_EXCLUDE:
        if col in df.columns:
            df = df[~df[col].eq(1).fillna(False)]

    for col, (lo, hi) in LAB_RANGES.items():
        if col in df.columns:
            v = df[col]
            df = df[v.isna() | v.between(lo, hi, inclusive="both")]

    log.info("reference population: %d rows (from %d master rows)", len(df), n0)
    return df.reset_index(drop=True)



def remove_tukey_outliers(x: np.ndarray, k: float = 1.5) -> tuple[np.ndarray, int]:
    if len(x) < 4:
        return x, 0
    q1, q3 = np.percentile(x, [25, 75])
    iqr = q3 - q1
    lo, hi = q1 - k * iqr, q3 + k * iqr
    mask = (x >= lo) & (x <= hi)
    return x[mask], int((~mask).sum())


def percentile_ci_bootstrap(x: np.ndarray, percentile: float, n_boot: int,
                            ci: float = 0.90) -> tuple[float, float, float]:
    if len(x) == 0:
        return (np.nan, np.nan, np.nan)
    point = float(np.percentile(x, percentile))
    n = len(x)
    reps = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        sample = rng.choice(x, size=n, replace=True)
        reps[i] = np.percentile(sample, percentile)
    alpha = (1 - ci) / 2
    lo = float(np.percentile(reps, 100 * alpha))
    hi = float(np.percentile(reps, 100 * (1 - alpha)))
    return (point, lo, hi)


@dataclass
class PartitionStats:
    partition: str
    n_raw: int
    n_outliers: int
    n_final: int
    mean: float
    sd: float
    median: float
    lrl: float
    url: float
    lrl_ci: tuple[float, float]
    url_ci: tuple[float, float]


def compute_partition(values: np.ndarray, label: str, n_boot: int) -> PartitionStats:
    values = values[np.isfinite(values)]
    n_raw = len(values)
    filtered, n_out = remove_tukey_outliers(values)
    if len(filtered) < 20:
        return PartitionStats(
            partition=label, n_raw=n_raw, n_outliers=n_out, n_final=len(filtered),
            mean=np.nan, sd=np.nan, median=np.nan,
            lrl=np.nan, url=np.nan, lrl_ci=(np.nan, np.nan), url_ci=(np.nan, np.nan),
        )
    lrl, lrl_lo, lrl_hi = percentile_ci_bootstrap(filtered, 2.5, n_boot)
    url, url_lo, url_hi = percentile_ci_bootstrap(filtered, 97.5, n_boot)
    return PartitionStats(
        partition=label,
        n_raw=n_raw,
        n_outliers=n_out,
        n_final=len(filtered),
        mean=float(np.mean(filtered)),
        sd=float(np.std(filtered, ddof=1)),
        median=float(np.median(filtered)),
        lrl=lrl, url=url,
        lrl_ci=(lrl_lo, lrl_hi),
        url_ci=(url_lo, url_hi),
    )


def harris_boyd_z(a: PartitionStats, b: PartitionStats) -> Optional[float]:
    if any(np.isnan([a.mean, b.mean, a.sd, b.sd])) or a.n_final < 20 or b.n_final < 20:
        return None
    se = np.sqrt(a.sd**2 / a.n_final + b.sd**2 / b.n_final)
    if se <= 0:
        return None
    return abs(a.mean - b.mean) / se


def harris_boyd_crit(n_a: int, n_b: int) -> float:
    nbar = (n_a + n_b) / 2.0
    return 3.0 * np.sqrt(nbar / 120.0)



@dataclass
class BiomarkerResult:
    code: str
    display: str
    unit: str
    textbook_female: tuple[Optional[float], Optional[float]]
    textbook_male:   tuple[Optional[float], Optional[float]]
    partitions: dict[str, PartitionStats]       = field(default_factory=dict)
    harris_boyd: dict[str, dict]                = field(default_factory=dict)
    recommended_partitioning: list[str]         = field(default_factory=list)
    notes: list[str]                            = field(default_factory=list)


def evaluate_biomarker(pop: pd.DataFrame, bio: Biomarker, age_bands: list[tuple[int,int]],
                       n_boot: int) -> BiomarkerResult:
    res = BiomarkerResult(
        code=bio.code, display=bio.display, unit=bio.unit,
        textbook_female=bio.textbook_female, textbook_male=bio.textbook_male,
    )
    if bio.code not in pop.columns:
        res.notes.append(f"column '{bio.code}' not present in master")
        return res

    col = pop[bio.code]
    plausible = col.between(bio.plausible_min, bio.plausible_max, inclusive="both").fillna(False)

    for sex_code, sex_label in [(2, "female"), (1, "male")]:
        for lo, hi in age_bands:
            label = f"{sex_label}_{lo}_{hi}"
            mask = plausible & pop["sex"].eq(sex_code) & pop["age_years"].between(lo, hi, inclusive="left")
            if hi == age_bands[-1][1]:
                mask = plausible & pop["sex"].eq(sex_code) & pop["age_years"].between(lo, hi, inclusive="both")
            vals = col[mask].to_numpy(dtype=float)
            stats = compute_partition(vals, label, n_boot)
            res.partitions[label] = stats

    parts = res.partitions

    sex_z = {}
    for lo, hi in age_bands:
        a = parts.get(f"female_{lo}_{hi}")
        b = parts.get(f"male_{lo}_{hi}")
        if a and b:
            z = harris_boyd_z(a, b)
            zc = harris_boyd_crit(a.n_final, b.n_final) if z is not None else None
            sex_z[f"{lo}_{hi}"] = {
                "z": round(z, 2) if z is not None else None,
                "z_crit": round(zc, 2) if zc is not None else None,
                "justified": bool(z is not None and z > zc) if z is not None else None,
            }
    res.harris_boyd["sex_within_age"] = sex_z

    age_z = {}
    for sex_label in ("female", "male"):
        pairs = []
        bands = age_bands
        for i in range(len(bands) - 1):
            a = parts.get(f"{sex_label}_{bands[i][0]}_{bands[i][1]}")
            b = parts.get(f"{sex_label}_{bands[i+1][0]}_{bands[i+1][1]}")
            if a and b:
                z = harris_boyd_z(a, b)
                zc = harris_boyd_crit(a.n_final, b.n_final) if z is not None else None
                pairs.append({
                    "pair": f"{bands[i][0]}-{bands[i][1]} vs {bands[i+1][0]}-{bands[i+1][1]}",
                    "z":      round(z, 2)  if z  is not None else None,
                    "z_crit": round(zc, 2) if zc is not None else None,
                    "justified": bool(z is not None and z > zc) if z is not None else None,
                })
        age_z[sex_label] = pairs
    res.harris_boyd["age_within_sex"] = age_z

    sex_just = [v["justified"] for v in sex_z.values() if v["justified"] is not None]
    sex_partition = any(sex_just)

    age_justs = []
    for sex_label in ("female", "male"):
        for p in age_z.get(sex_label, []):
            if p["justified"] is not None:
                age_justs.append(p["justified"])
    age_partition = any(age_justs)

    rec = []
    if sex_partition:  rec.append("sex")
    if age_partition:  rec.append("age")
    res.recommended_partitioning = rec or ["collapsed"]

    undersized = [lbl for lbl, s in parts.items() if s.n_final < 120]
    if undersized:
        res.notes.append(
            f"{len(undersized)} partition(s) below CLSI minimum n=120: " + ", ".join(undersized)
        )

    return res



def _fmt_ref(lo: Optional[float], hi: Optional[float]) -> str:
    if lo is None and hi is None: return "—"
    if lo is None:                return f"≤ {hi:g}"
    if hi is None:                return f"≥ {lo:g}"
    return f"{lo:g}–{hi:g}"

def _fmt_interval(stats: PartitionStats) -> str:
    if np.isnan(stats.lrl) or np.isnan(stats.url): return "—"
    return f"{stats.lrl:.2f}–{stats.url:.2f}"

def generate_markdown(results: list[BiomarkerResult], age_bands: list[tuple[int,int]],
                       n_pop: int, n_total_master: int) -> str:
    lines: list[str] = []
    a = lines.append

    a("# Empirical CBC Reference Intervals — NHANES Healthy Cohort")
    a("")
    a("**Methodology.** Non-parametric reference intervals (2.5th and 97.5th "
      "percentiles) were derived from a healthy reference population drawn from "
      "the harmonised NHANES 1999–2023 master dataset, following the Clinical and "
      "Laboratory Standards Institute document EP28-A3c. Within each partition, "
      "Tukey-fence outliers (1.5 × IQR) were removed prior to percentile "
      "estimation. Ninety-percent confidence intervals for each reference limit "
      "were obtained by non-parametric bootstrap (R = 1000 resamples with "
      "replacement). Partitioning of the reference population by sex and by "
      "age band was evaluated using the Harris-Boyd z-statistic "
      "z = |μ₁ − μ₂| / √(s₁²/n₁ + s₂²/n₂) with a critical value of "
      "3 × √(n̄/120); partitioning was considered statistically justified when "
      "|z| exceeded that threshold.")
    a("")
    bands_txt = ", ".join(f"{lo}–{hi}" for lo, hi in age_bands)
    a(f"**Inclusion criteria (healthy cohort).** Adults aged "
      f"{age_bands[0][0]}–{age_bands[-1][1]} (age bands: {bands_txt}), not pregnant, "
      f"body-mass index 18.5–30 kg/m², no self-reported history of "
      f"cardiovascular disease, diabetes, hypertension, chronic kidney disease, "
      f"cancer, liver or thyroid disease, no anti-hypertensive / lipid-lowering "
      f"/ glucose-lowering medications, and companion lipid, glycaemic, renal "
      f"and hepatic indices within conventional normal ranges.")
    a("")
    a(f"**Reference population size:** {n_pop:,} participants "
      f"(from {n_total_master:,} available in the master NHANES dataset).")
    a("")
    a("---")
    a("")

    a("## 1. Summary — empirical vs textbook intervals")
    a("")
    a("Intervals shown are pooled across the age bands within each sex, "
      "with sex collapsed to a single interval only when Harris-Boyd testing "
      "showed no justification for a sex partition at any age.")
    a("")
    a("| Biomarker | Unit | Textbook ♀ | Empirical ♀ | Textbook ♂ | Empirical ♂ | Partitioning |")
    a("|---|---|---|---|---|---|---|")
    for r in results:
        f_parts = [r.partitions[f"female_{lo}_{hi}"] for lo, hi in age_bands
                   if f"female_{lo}_{hi}" in r.partitions]
        m_parts = [r.partitions[f"male_{lo}_{hi}"]   for lo, hi in age_bands
                   if f"male_{lo}_{hi}"   in r.partitions]
        def pooled(ps):
            lrls = [p.lrl for p in ps if not np.isnan(p.lrl)]
            urls = [p.url for p in ps if not np.isnan(p.url)]
            if not lrls or not urls: return "—"
            return f"{min(lrls):.2f}–{max(urls):.2f}"
        tb_f = _fmt_ref(*r.textbook_female)
        tb_m = _fmt_ref(*r.textbook_male)
        part = "+".join(r.recommended_partitioning)
        a(f"| {r.display} | {r.unit} | {tb_f} | {pooled(f_parts)} | {tb_m} | {pooled(m_parts)} | {part} |")
    a("")
    a("---")
    a("")

    a("## 2. Per-biomarker tables")
    a("")
    for r in results:
        a(f"### 2.{results.index(r)+1} {r.display} ({r.unit}) — code `{r.code}`")
        a("")
        a(f"*Textbook:* ♀ {_fmt_ref(*r.textbook_female)}, ♂ {_fmt_ref(*r.textbook_male)}")
        a("")
        a("| Partition | n (raw) | outliers | n (final) | median | LRL (2.5%) | URL (97.5%) | LRL 90% CI | URL 90% CI |")
        a("|---|---:|---:|---:|---:|---:|---:|---|---|")
        for lbl, s in r.partitions.items():
            pretty = lbl.replace("_", " ").replace("female", "♀").replace("male", "♂")
            if s.n_final == 0:
                a(f"| {pretty} | {s.n_raw} | — | 0 | — | — | — | — | — |")
                continue
            lrl_ci = f"[{s.lrl_ci[0]:.2f}, {s.lrl_ci[1]:.2f}]" if not np.isnan(s.lrl_ci[0]) else "—"
            url_ci = f"[{s.url_ci[0]:.2f}, {s.url_ci[1]:.2f}]" if not np.isnan(s.url_ci[0]) else "—"
            a(f"| {pretty} | {s.n_raw} | {s.n_outliers} | {s.n_final} | "
              f"{s.median:.2f} | {s.lrl:.2f} | {s.url:.2f} | {lrl_ci} | {url_ci} |")
        a("")
        sex_hb = r.harris_boyd.get("sex_within_age", {})
        if sex_hb:
            a("*Harris-Boyd — sex partition within age bands:*")
            for band, v in sex_hb.items():
                if v["z"] is None:
                    a(f"- {band}: insufficient data")
                else:
                    verdict = "**partition justified**" if v["justified"] else "not justified (collapse)"
                    a(f"- {band}: z = {v['z']:.2f}, z_crit = {v['z_crit']:.2f} → {verdict}")
            a("")
        age_hb = r.harris_boyd.get("age_within_sex", {})
        if age_hb:
            a("*Harris-Boyd — age partition within each sex:*")
            for sex_label in ("female","male"):
                for p in age_hb.get(sex_label, []):
                    if p["z"] is None: continue
                    verdict = "justified" if p["justified"] else "not justified"
                    a(f"- {sex_label}, {p['pair']}: z = {p['z']:.2f}, z_crit = {p['z_crit']:.2f} → {verdict}")
            a("")
        if r.notes:
            a("*Notes:* " + "; ".join(r.notes))
            a("")
        a("---")
        a("")

    return "\n".join(lines)


def results_to_json(results: list[BiomarkerResult], meta: dict) -> dict:
    def _ps_to_dict(ps: PartitionStats) -> dict:
        d = asdict(ps)
        d["lrl_ci"] = list(ps.lrl_ci)
        d["url_ci"] = list(ps.url_ci)
        return d
    out = {"metadata": meta, "biomarkers": {}}
    for r in results:
        out["biomarkers"][r.code] = {
            "display": r.display,
            "unit": r.unit,
            "textbook_female": list(r.textbook_female),
            "textbook_male":   list(r.textbook_male),
            "partitions": {k: _ps_to_dict(v) for k, v in r.partitions.items()},
            "harris_boyd": r.harris_boyd,
            "recommended_partitioning": r.recommended_partitioning,
            "notes": r.notes,
        }
    return out



def _parse_bands(s: str) -> list[tuple[int, int]]:
    bands = []
    for part in s.split(","):
        lo, hi = part.split("-")
        bands.append((int(lo), int(hi)))
    return bands


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--master",    type=Path, required=True)
    p.add_argument("--out-dir",   type=Path, required=True)
    p.add_argument("--age-bands", type=str,  default="20-40,40-60,60-80")
    p.add_argument("--bootstrap-n", type=int, default=1000)
    p.add_argument("--log-level", default="INFO")
    args = p.parse_args()

    logging.basicConfig(level=args.log_level,
                        format="%(asctime)s %(levelname)-7s %(message)s",
                        datefmt="%H:%M:%S")

    if not args.master.is_file():
        sys.exit(f"--master does not exist: {args.master}")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    age_bands = _parse_bands(args.age_bands)
    age_min, age_max = age_bands[0][0], age_bands[-1][1]
    log.info("age bands: %s", age_bands)

    log.info("loading %s", args.master)
    master = pd.read_parquet(args.master)
    log.info("master: %d rows × %d cols", len(master), master.shape[1])

    pop = build_reference_population(master, age_min, age_max)

    results: list[BiomarkerResult] = []
    for bio in BIOMARKERS:
        log.info("%-10s evaluating...", bio.code)
        r = evaluate_biomarker(pop, bio, age_bands, args.bootstrap_n)
        results.append(r)

    meta = {
        "source": "NHANES 1999-2023 (harmonised master dataset)",
        "method": "CLSI EP28-A3c non-parametric (2.5 / 97.5 percentile, bootstrap 90% CI)",
        "outlier_rule": "Tukey fence, k=1.5 × IQR",
        "bootstrap_n": args.bootstrap_n,
        "age_bands": [f"{lo}-{hi}" for lo, hi in age_bands],
        "n_master": int(len(master)),
        "n_reference_population": int(len(pop)),
        "partitioning_test": "Harris-Boyd z, z_crit = 3·√(n̄/120)",
    }
    json_doc = results_to_json(results, meta)
    json_path = args.out_dir / "empirical_refs.json"
    with open(json_path, "w") as f:
        json.dump(json_doc, f, indent=2, default=str)
    log.info("wrote %s", json_path)

    md = generate_markdown(results, age_bands, n_pop=len(pop), n_total_master=len(master))
    md_path = args.out_dir / "empirical_refs_report.md"
    with open(md_path, "w") as f:
        f.write(md)
    log.info("wrote %s", md_path)

    print()
    print("=" * 92)
    print(f"Reference population: {len(pop):,} / {len(master):,} master rows")
    print(f"Age bands: {age_bands}")
    print(f"Bootstrap reps: {args.bootstrap_n}")
    print()
    print(f"{'Biomarker':<28}{'♀ pooled empirical':<22}{'♂ pooled empirical':<22}{'partition':<14}")
    print("-" * 86)
    for r in results:
        def pooled(sex):
            ps = [r.partitions[f"{sex}_{lo}_{hi}"] for lo, hi in age_bands
                  if f"{sex}_{lo}_{hi}" in r.partitions]
            lrls = [p.lrl for p in ps if not np.isnan(p.lrl)]
            urls = [p.url for p in ps if not np.isnan(p.url)]
            if not lrls or not urls: return "—"
            return f"{min(lrls):.2f}–{max(urls):.2f}"
        part = "+".join(r.recommended_partitioning)
        print(f"{r.display:<28}{pooled('female'):<22}{pooled('male'):<22}{part:<14}")
    print()
    print(f"JSON:    {json_path}")
    print(f"Report:  {md_path}")


if __name__ == "__main__":
    main()
