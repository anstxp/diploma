from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("prepare_v2")

ROOT = Path(__file__).parent.parent.parent
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "data_processed_v2"
OUT_DIR.mkdir(exist_ok=True)


CBC_FEATURES = [
    "wbc", "rbc", "hb_gdl", "hct", "mcv", "mch", "mchc", "rdw",
    "plt", "mpv",
    "neut_pct", "lymph_pct", "mono_pct", "eos_pct", "baso_pct",
]
CHEM_FEATURES = [
    "glucose_fasting", "hba1c_pct",
    "creatinine_mgdl", "bun_mgdl", "uric_acid_mgdl",
    "alt_ul", "ast_ul", "alp_ul", "ggt_ul",
    "albumin_gdl", "protein_total_gdl", "bilirubin_total",
    "sodium_mmoll", "potassium_mmoll", "chloride_mmoll", "bicarbonate_mmoll",
    "calcium_mgdl", "phosphorus_mgdl",
    "tchol_mgdl", "hdl_mgdl", "trigly_mgdl",
    "hs_crp", "ferritin_ngml", "vit_d_total",
]
DEMO_FEATURES = [
    "age_years", "sex",
    "bmi", "waist_cm",
    "sbp", "dbp", "pulse",
]

V2_NEW_FEATURES = [
    "income_ratio",
    "edu_level",
    "metsyn_criteria_count",
    "arm_circ_cm",
    "iron_chem_ugdl",
    "non_hdl_mgdl",
    "fib4",
    "globulin_gdl",
    "egfr_ckd_epi_2021",
    "homa_ir",
    "sedentary_min_day",
]

ALL_FEATURES = CBC_FEATURES + CHEM_FEATURES + DEMO_FEATURES + V2_NEW_FEATURES


V1_TARGETS = [
    "depression_moderate",
    "depression_severe",
    "sleep_deficiency",
    "daytime_dysfunction",
    "suicidal_ideation",
]

V2_NEW_TARGETS = [
    "snore_high",
    "trouble_sleeping_high",
]

TARGETS = V1_TARGETS + V2_NEW_TARGETS


def build_targets(df: pd.DataFrame, full_index: pd.Index) -> pd.DataFrame:
    log.info("Building targets (5 v1 + 2 v2 new heads)...")
    targets_df = pd.DataFrame(index=full_index)
    sub = df.loc[full_index]

    def _to_num(s):
        return pd.to_numeric(s, errors="coerce") if s is not None else None

    phq_total = _to_num(sub.get("phq9_total"))
    sw = _to_num(sub.get("sleep_hours_weekday"))
    ts = _to_num(sub.get("trouble_sleeping"))
    ds = _to_num(sub.get("daytime_sleepy"))
    q9 = _to_num(sub.get("phq9_q9"))
    snore = _to_num(sub.get("snore"))

    if phq_total is not None:
        t1 = pd.Series(np.nan, index=full_index, dtype="float32")
        t1[phq_total >= 10] = 1.0
        t1[phq_total < 10] = 0.0
        targets_df["depression_moderate"] = t1

    if phq_total is not None:
        t2 = pd.Series(np.nan, index=full_index, dtype="float32")
        t2[phq_total >= 15] = 1.0
        t2[phq_total < 15] = 0.0
        targets_df["depression_severe"] = t2

    t3 = pd.Series(np.nan, index=full_index, dtype="float32")
    has_sleep = (sw.notna() if sw is not None else pd.Series(False, index=full_index)) | \
                (ts.notna() if ts is not None else pd.Series(False, index=full_index))
    short_sleep = ((sw < 6) if sw is not None else pd.Series(False, index=full_index)).fillna(False)
    troubled = ((ts >= 3) if ts is not None else pd.Series(False, index=full_index)).fillna(False)
    positive = short_sleep | troubled
    t3[has_sleep] = 0.0
    t3[positive] = 1.0
    targets_df["sleep_deficiency"] = t3

    t4 = pd.Series(np.nan, index=full_index, dtype="float32")
    if ds is not None:
        t4[ds.notna()] = 0.0
        t4[ds >= 3] = 1.0
    targets_df["daytime_dysfunction"] = t4

    t5 = pd.Series(np.nan, index=full_index, dtype="float32")
    if q9 is not None:
        t5[q9.notna()] = 0.0
        t5[q9 >= 0.5] = 1.0
    targets_df["suicidal_ideation"] = t5

    t6 = pd.Series(np.nan, index=full_index, dtype="float32")
    if snore is not None:
        t6[snore.notna()] = 0.0
        t6[snore >= 2] = 1.0
    targets_df["snore_high"] = t6

    t7 = pd.Series(np.nan, index=full_index, dtype="float32")
    if ts is not None:
        t7[ts.notna()] = 0.0
        t7[ts == 1] = 1.0
    targets_df["trouble_sleeping_high"] = t7

    for t in TARGETS:
        if t not in targets_df.columns:
            log.warning(f"   {t}: NOT BUILT (column missing in source)")
            continue
        n_pos = (targets_df[t] == 1.0).sum()
        n_neg = (targets_df[t] == 0.0).sum()
        n_unk = targets_df[t].isna().sum()
        prev = 100 * n_pos / max(n_pos + n_neg, 1)
        tag = "★ NEW" if t in V2_NEW_TARGETS else "     "
        log.info(f"   {tag} {t:<24}  pos={n_pos:>6,}  neg={n_neg:>6,}  "
                 f"unknown={n_unk:>6,}  prev={prev:.1f}%")
    return targets_df



def load_raw() -> pd.DataFrame:
    log.info(f"Loading {DATA_DIR / 'nhanes_master.parquet'} ...")
    df = pd.read_parquet(DATA_DIR / "nhanes_master.parquet")
    log.info(f"   {len(df):,} records × {len(df.columns)} columns")
    missing = [c for c in V2_NEW_FEATURES if c not in df.columns]
    if missing:
        log.warning(f"   v2 features NOT in source: {missing}")
    return df


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    log.info("Selecting features...")
    available = [c for c in ALL_FEATURES if c in df.columns]
    missing = set(ALL_FEATURES) - set(available)
    if missing:
        log.warning(f"   Features not in dataset (skipping): {sorted(missing)}")
    out = df[available].copy()
    if "sex" in out.columns:
        out["sex"] = (out["sex"] == 2).astype("float32")
    if "age_years" in out.columns:
        out = out[out["age_years"] >= 18]
    n_v1 = len([f for f in (CBC_FEATURES + CHEM_FEATURES + DEMO_FEATURES) if f in available])
    n_v2_new = len([f for f in V2_NEW_FEATURES if f in available])
    log.info(f"   Features: {len(available)}  ({n_v1} v1 base + {n_v2_new} v2 new)")
    log.info(f"   Records (adults): {len(out):,}")
    return out


def filter_records(features_df: pd.DataFrame, targets_df: pd.DataFrame,
                   min_features: int = 15,
                   min_targets: int = 2) -> Tuple[pd.DataFrame, pd.DataFrame]:
    log.info(f"Filtering: ≥{min_features} features and ≥{min_targets} known targets...")
    has_strata = features_df["age_years"].notna() & features_df["sex"].notna()
    n_features = features_df.notna().sum(axis=1)
    n_targets = targets_df.notna().sum(axis=1)
    keep = has_strata & (n_features >= min_features) & (n_targets >= min_targets)
    log.info(f"   {keep.sum():,} / {len(features_df):,} records pass "
             f"({100 * keep.mean():.1f}%)")
    return features_df[keep], targets_df[keep]


def stratified_split(features_df: pd.DataFrame, targets_df: pd.DataFrame,
                     val_size: float = 0.15, test_size: float = 0.15,
                     random_state: int = 42) -> Dict[str, Tuple[pd.DataFrame, pd.DataFrame]]:
    log.info(f"Splitting: train / val / test = {1 - val_size - test_size:.0%} / "
             f"{val_size:.0%} / {test_size:.0%}  (seed={random_state})")
    age = features_df["age_years"].clip(lower=18, upper=99)
    age_bucket = pd.cut(age, bins=[17, 30, 45, 60, 75, 100],
                        labels=["18-29", "30-44", "45-59", "60-74", "75+"])
    age_bucket = age_bucket.astype(str).fillna("UNK")
    sex_str = features_df["sex"].map({0.0: "M", 1.0: "F"}).fillna("U")
    strata = (age_bucket + "_" + sex_str).values
    idx_train_val, idx_test = train_test_split(
        features_df.index, test_size=test_size,
        random_state=random_state, stratify=strata,
    )
    val_size_adj = val_size / (1 - test_size)
    strata_tv = pd.Series(strata, index=features_df.index).loc[idx_train_val].values
    idx_train, idx_val = train_test_split(
        idx_train_val, test_size=val_size_adj,
        random_state=random_state, stratify=strata_tv,
    )
    splits = {
        "train": (features_df.loc[idx_train], targets_df.loc[idx_train]),
        "val":   (features_df.loc[idx_val],   targets_df.loc[idx_val]),
        "test":  (features_df.loc[idx_test],  targets_df.loc[idx_test]),
    }
    for name, (f, t) in splits.items():
        log.info(f"   {name:<5}  n={len(f):>6,}")
    return splits


def compute_stats(train_features: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    log.info("Computing feature statistics on train split...")
    stats = {}
    for col in train_features.columns:
        values = train_features[col].dropna()
        if len(values) > 0:
            stats[col] = {
                "mean": float(values.mean()),
                "std": float(values.std() or 1.0),
                "median": float(values.median()),
                "p1": float(values.quantile(0.01)),
                "p99": float(values.quantile(0.99)),
                "n_non_null": int(len(values)),
            }
    return stats


def save_split(features_df: pd.DataFrame, targets_df: pd.DataFrame, name: str):
    combined = pd.concat([features_df, targets_df], axis=1)
    out_path = OUT_DIR / f"{name}.parquet"
    combined.to_parquet(out_path)
    log.info(f"   Saved {out_path.name} ({out_path.stat().st_size / 1024:.0f} KB)")


def main():
    log.info("=" * 70)
    log.info("HEMAX_NEURO v2 — data preparation")
    log.info(f"  Output: {OUT_DIR}")
    log.info("=" * 70)

    df = load_raw()
    features = build_features(df)
    targets = build_targets(df, features.index)
    features, targets = filter_records(features, targets)
    splits = stratified_split(features, targets)

    train_f, train_t = splits["train"]
    feature_stats = compute_stats(train_f)
    target_stats = {}
    for t in TARGETS:
        if t not in train_t.columns:
            continue
        n_pos = int((train_t[t] == 1.0).sum())
        n_neg = int((train_t[t] == 0.0).sum())
        n_unknown = int(train_t[t].isna().sum())
        denom = n_pos + n_neg
        target_stats[t] = {
            "prevalence": float(n_pos / denom) if denom > 0 else 0.0,
            "n_pos": n_pos,
            "n_neg": n_neg,
            "n_unknown": n_unknown,
            "pos_weight": float(n_neg / max(n_pos, 1)),
        }

    log.info("Saving outputs...")
    for name, (f, t) in splits.items():
        save_split(f, t, name)
    with open(OUT_DIR / "feature_stats.json", "w") as fp:
        json.dump(feature_stats, fp, indent=2)
    with open(OUT_DIR / "target_stats.json", "w") as fp:
        json.dump(target_stats, fp, indent=2)
    metadata = {
        "version": "2.0",
        "service": "hemax_neuro",
        "extends_version": "1.0",
        "n_features": len(features.columns),
        "n_features_v1": len(CBC_FEATURES + CHEM_FEATURES + DEMO_FEATURES),
        "n_features_v2_new": len([f for f in V2_NEW_FEATURES if f in features.columns]),
        "feature_names": list(features.columns),
        "v2_new_features": [f for f in V2_NEW_FEATURES if f in features.columns],
        "target_names": [t for t in TARGETS if t in train_t.columns],
        "v2_new_targets": [t for t in V2_NEW_TARGETS if t in train_t.columns],
        "n_train": len(splits["train"][0]),
        "n_val":   len(splits["val"][0]),
        "n_test":  len(splits["test"][0]),
        "target_definitions": {
            "depression_moderate":     "PHQ-9 total ≥10 (Kroenke 2001 treatment cutoff)",
            "depression_severe":       "PHQ-9 total ≥15 (moderately-severe + severe)",
            "sleep_deficiency":        "sleep_hours_weekday <6 OR trouble_sleeping ≥3",
            "daytime_dysfunction":     "daytime_sleepy ≥3 (often or always)",
            "suicidal_ideation":       "PHQ-9 q9 ≥1 (any thoughts of self-harm). SAFETY-CRITICAL.",
            "snore_high":              "snore ≥2 (often or always loud snoring). Proxy for OSA. NEW in v2.",
            "trouble_sleeping_high":   "trouble_sleeping ≥3 (often+). Insomnia screen. NEW in v2.",
        },
    }
    with open(OUT_DIR / "metadata.json", "w") as fp:
        json.dump(metadata, fp, indent=2)
    log.info(f"   Saved metadata.json")
    log.info("=" * 70)
    log.info("v2 preparation complete!")
    log.info(f"  Next: python -m train.v2.train_v2")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
