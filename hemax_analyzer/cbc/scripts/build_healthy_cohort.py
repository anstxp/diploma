#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger("healthy_cohort")


SELF_REPORT_EXCLUDE: list[tuple[str, str]] = [
    ("told_chf",         "Ever told: congestive heart failure"),
    ("told_chd",         "Ever told: coronary heart disease"),
    ("told_angina",      "Ever told: angina pectoris"),
    ("told_mi",          "Ever told: heart attack / MI"),
    ("told_stroke",      "Ever told: stroke"),
    ("told_diabetes",    "Ever told: diabetes"),
    ("told_htn",         "Ever told: high blood pressure"),
    ("told_weak_kidney", "Ever told: weak/failing kidneys"),
    ("told_dialysis",    "On dialysis in past 12 months"),
    ("told_cancer",      "Ever told: any cancer"),
    ("told_liver",       "Ever told: liver condition"),
    ("told_thyroid",     "Ever told: thyroid problem"),
]

MEDICATION_EXCLUDE: list[tuple[str, str]] = [
    ("on_htn_med",           "Taking anti-hypertensive medication"),
    ("on_chol_med",          "Taking cholesterol-lowering medication"),
    ("on_insulin",           "Taking insulin"),
    ("on_oral_diabetes_med", "Taking oral anti-diabetic medication"),
]

LAB_RANGES: dict[str, tuple[float, float]] = {
    "hb_gdl":         (10.5, 18.0),
    "wbc":            (3.5, 11.5),
    "plt":            (120, 450),
    "mcv":            (75, 100),
    "rdw":            (11, 16),
    "neut_pct":       (40, 80),
    "lymph_pct":      (15, 50),

    "alt_ul":         (5, 55),
    "ast_ul":         (5, 50),
    "alp_ul":         (30, 150),
    "bilirubin_total":(0.1, 1.5),
    "albumin_gdl":    (3.5, 5.5),
    "protein_total_gdl": (6.0, 8.5),

    "creatinine_mgdl":(0.4, 1.4),
    "bun_mgdl":       (6, 25),

    "sodium_mmoll":   (133, 147),
    "potassium_mmoll":(3.3, 5.3),
    "calcium_mgdl":   (8.3, 10.8),

    "hba1c_pct":      (4.0, 5.7),
    "glucose_fasting":(65, 100),
    "glucose_random": (65, 140),

    "tchol_mgdl":     (100, 240),
    "hdl_mgdl":       (35, 120),
    "trigly_mgdl":    (30, 200),
    "ldl_mgdl":       (40, 160),

    "hs_crp":         (0, 3.0),

    "egfr_ckd_epi_2021": (60, 200),

    "sbp":            (85, 135),
    "dbp":            (50, 85),
}



@dataclass
class Stage:
    name: str
    n_before: int
    n_dropped: int
    n_after: int

def _excl_eq(df: pd.DataFrame, col: str, value) -> pd.Series:
    if col not in df.columns:
        return pd.Series(False, index=df.index)
    return df[col].eq(value).fillna(False)

def _excl_out_of_range(df: pd.DataFrame, col: str, lo: float, hi: float) -> pd.Series:
    if col not in df.columns:
        return pd.Series(False, index=df.index)
    v = df[col]
    return (v.notna() & ((v < lo) | (v > hi)))


def apply_filters(df: pd.DataFrame, args) -> tuple[pd.DataFrame, list[Stage]]:
    stages: list[Stage] = []
    stages.append(Stage("master-input", -1, -1, len(df)))

    def _apply(name: str, mask_drop: pd.Series):
        nonlocal df
        before = len(df)
        df = df.loc[~mask_drop].copy()
        stages.append(Stage(name, before, before - len(df), len(df)))

    _apply(f"age {args.age_min}-{args.age_max}",
           ~df["age_years"].between(args.age_min, args.age_max, inclusive="both")
             .fillna(False))

    _apply("sex known (1=M or 2=F)",
           ~df["sex"].isin([1, 2]))

    if "pregnancy" in df.columns:
        _apply("not currently pregnant", _excl_eq(df, "pregnancy", 1))

    _apply(f"bmi {args.bmi_min}-{args.bmi_max}",
           ~df["bmi"].between(args.bmi_min, args.bmi_max, inclusive="both")
             .fillna(False))

    core_labs = [c for c in ["hb_gdl", "creatinine_mgdl", "hdl_mgdl", "hba1c_pct"] if c in df.columns]
    if core_labs:
        has_any = df[core_labs].notna().any(axis=1)
        _apply("has ≥1 core lab (went through MEC)", ~has_any)

    if args.require_cbc:
        required = ["hb_gdl", "wbc", "plt"]
        present = [c for c in required if c in df.columns]
        if present:
            has_all = df[present].notna().all(axis=1)
            _apply("has complete CBC", ~has_all)

    if args.require_chem:
        required = ["alt_ul", "creatinine_mgdl", "albumin_gdl"]
        present = [c for c in required if c in df.columns]
        if present:
            has_all = df[present].notna().all(axis=1)
            _apply("has complete chem", ~has_all)

    for col, desc in SELF_REPORT_EXCLUDE:
        if col in df.columns:
            _apply(f"exclude: {desc}", _excl_eq(df, col, 1))

    for col, desc in MEDICATION_EXCLUDE:
        if col in df.columns:
            _apply(f"exclude: {desc}", _excl_eq(df, col, 1))

    hba1c_upper = 5.7 if args.strict_hba1c else 6.0
    ranges = dict(LAB_RANGES)
    if not args.strict_hba1c:
        ranges["hba1c_pct"] = (ranges["hba1c_pct"][0], hba1c_upper)
    if args.skip_inflammation:
        ranges.pop("hs_crp", None)

    for col, (lo, hi) in ranges.items():
        if col in df.columns:
            _apply(f"lab {col} ∈ [{lo}, {hi}]", _excl_out_of_range(df, col, lo, hi))

    return df, stages



def format_stages(stages: list[Stage]) -> str:
    lines = []
    lines.append(f'{"Stage":<54} {"before":>8} {"dropped":>9} {"after":>8}  {"%loss":>6}')
    lines.append("-" * 93)
    for s in stages:
        if s.n_before <= 0:
            lines.append(f'{s.name:<54} {"":>8} {"":>9} {s.n_after:>8}')
        else:
            pct = (s.n_dropped / s.n_before * 100) if s.n_before else 0
            lines.append(f'{s.name:<54} {s.n_before:>8,} {s.n_dropped:>9,} {s.n_after:>8,}  {pct:>5.1f}%')
    return "\n".join(lines)


def cohort_summary(df: pd.DataFrame) -> dict:
    out: dict = {"n_total": int(len(df))}
    if "cycle" in df.columns:
        out["by_cycle"] = df["cycle"].value_counts().sort_index().astype(int).to_dict()
    if "sex" in df.columns:
        out["by_sex"] = df["sex"].value_counts().astype(int).to_dict()
    if "age_years" in df.columns:
        q = df["age_years"].quantile([0.1, 0.25, 0.5, 0.75, 0.9]).round(1)
        out["age_quantiles"] = {f"p{int(k*100)}": float(v) for k, v in q.items()}
        out["age_mean"] = round(float(df["age_years"].mean()), 1)
    if "bmi" in df.columns:
        out["bmi_mean"] = round(float(df["bmi"].mean()), 1)
        out["bmi_quantiles"] = {f"p{int(k*100)}": round(float(v), 1)
                                for k, v in df["bmi"].quantile([0.1, 0.5, 0.9]).items()}
    lab_cols = ["hb_gdl","wbc","plt","mcv","creatinine_mgdl","alt_ul","ast_ul",
                "hba1c_pct","hdl_mgdl","tchol_mgdl","trigly_mgdl","ldl_mgdl",
                "glucose_fasting","hs_crp","ferritin_ngml","vit_d_total",
                "sbp","dbp","phq9_total"]
    cov = {}
    for c in lab_cols:
        if c in df.columns:
            cov[c] = {
                "n_nonnull": int(df[c].notna().sum()),
                "pct": round(float(df[c].notna().mean()) * 100, 1),
                "median": round(float(df[c].median()), 2) if df[c].notna().any() else None,
            }
    out["column_coverage"] = cov
    return out



def main():
    p = argparse.ArgumentParser(description="Build a healthy cohort from NHANES master dataset.")
    p.add_argument("--master",  type=Path, required=True,
                   help="Path to nhanes_master.parquet.")
    p.add_argument("--out-dir", type=Path, required=True,
                   help="Where to write healthy_cohort.parquet + manifest.")
    p.add_argument("--age-min", type=int, default=20)
    p.add_argument("--age-max", type=int, default=65)
    p.add_argument("--bmi-min", type=float, default=18.5)
    p.add_argument("--bmi-max", type=float, default=30.0)
    p.add_argument("--strict-hba1c", action="store_true", default=True,
                   help="Exclude HbA1c ≥ 5.7%% (default). Use --no-strict-hba1c to allow up to 6.0%%.")
    p.add_argument("--no-strict-hba1c", action="store_false", dest="strict_hba1c")
    p.add_argument("--skip-inflammation", action="store_true",
                   help="Do not filter on hs-CRP (keeps more people).")
    p.add_argument("--require-cbc",  action="store_true",
                   help="Require full CBC (hb, wbc, plt) to be present.")
    p.add_argument("--require-chem", action="store_true",
                   help="Require full chem panel (alt, creatinine, albumin).")
    p.add_argument("--log-level",    default="INFO")
    args = p.parse_args()

    logging.basicConfig(level=args.log_level,
                        format="%(asctime)s %(levelname)-7s %(message)s",
                        datefmt="%H:%M:%S")

    if not args.master.is_file():
        sys.exit(f"--master does not exist: {args.master}")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    log.info("loading %s", args.master)
    df = pd.read_parquet(args.master)
    log.info("master shape: %d rows × %d cols", len(df), df.shape[1])

    cohort, stages = apply_filters(df, args)
    log.info("healthy cohort: %d rows × %d cols", len(cohort), cohort.shape[1])

    out_parquet = args.out_dir / "healthy_cohort.parquet"
    cohort.to_parquet(out_parquet, index=False)
    log.info("wrote %s (%.1f MB)", out_parquet, out_parquet.stat().st_size / 1024 / 1024)

    manifest = {
        "source_master": str(args.master),
        "filter_settings": {
            "age_min": args.age_min, "age_max": args.age_max,
            "bmi_min": args.bmi_min, "bmi_max": args.bmi_max,
            "strict_hba1c": args.strict_hba1c,
            "skip_inflammation": args.skip_inflammation,
            "require_cbc": args.require_cbc,
            "require_chem": args.require_chem,
        },
        "self_report_excluded": [c for c,_ in SELF_REPORT_EXCLUDE if c in df.columns],
        "medications_excluded": [c for c,_ in MEDICATION_EXCLUDE if c in df.columns],
        "lab_ranges_applied":   {k: list(v) for k, v in LAB_RANGES.items() if k in df.columns},
        "filter_stages": [
            {"stage": s.name, "n_before": s.n_before, "n_dropped": s.n_dropped, "n_after": s.n_after}
            for s in stages
        ],
        "cohort_summary": cohort_summary(cohort),
    }
    out_manifest = args.out_dir / "healthy_cohort_manifest.json"
    with open(out_manifest, "w") as f:
        json.dump(manifest, f, indent=2, default=str)
    log.info("wrote %s", out_manifest)

    print()
    print("=" * 93)
    print(f"Healthy cohort: {len(cohort):,} rows from {len(df):,} input ({len(cohort)/len(df)*100:.1f}%)")
    print(f"  parquet:  {out_parquet}")
    print(f"  manifest: {out_manifest}")
    print()
    print("Filter pipeline:")
    print(format_stages(stages))
    print()
    print(f"Cohort by cycle:")
    print(cohort["cycle"].value_counts().sort_index().to_string())
    if "sex" in cohort.columns:
        m = int((cohort["sex"]==1).sum()); f = int((cohort["sex"]==2).sum())
        print(f"\nSex balance: M={m:,} ({m/(m+f)*100:.1f}%)  F={f:,} ({f/(m+f)*100:.1f}%)")
    print(f"Age: {cohort['age_years'].mean():.1f} ± {cohort['age_years'].std():.1f} "
          f"(range {cohort['age_years'].min():.0f}-{cohort['age_years'].max():.0f})")
    print(f"BMI: {cohort['bmi'].mean():.1f} ± {cohort['bmi'].std():.1f}")


if __name__ == "__main__":
    main()
