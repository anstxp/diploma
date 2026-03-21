from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("prepare")

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "data_processed"
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

ALL_FEATURES = CBC_FEATURES + CHEM_FEATURES + DEMO_FEATURES



TARGETS = [
    "told_htn",
    "told_diabetes",
    "told_high_chol",
    "told_chd",
    "told_chf",
    "told_stroke",
]

def _binarize(s: pd.Series) -> pd.Series:
    out = pd.Series(np.nan, index=s.index, dtype="float32")
    out[s == 1] = 1.0
    out[s == 2] = 0.0
    return out


def _augment_diabetes_target(df: pd.DataFrame) -> pd.Series:
    base = _binarize(df["told_diabetes"])
    a1c = df["hba1c_pct"]
    augmented = base.copy()
    mask_undiag = (base == 0.0) & (a1c >= 6.5)
    augmented[mask_undiag] = 1.0
    log.info(f"   Diabetes target augmented: +{mask_undiag.sum()} undiagnosed cases (HbA1c≥6.5%)")
    return augmented



def load_raw() -> pd.DataFrame:
    log.info("Loading NHANES master parquet...")
    df = pd.read_parquet(DATA_DIR / "nhanes_master.parquet")
    log.info(f"   {len(df):,} records × {len(df.columns)} columns")
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

    log.info(f"   Features: {len(available)}")
    log.info(f"   Records (adults): {len(out):,}")
    return out


def build_targets(df: pd.DataFrame, full_index: pd.Index) -> pd.DataFrame:
    log.info("Building targets...")

    targets_df = pd.DataFrame(index=full_index)

    for t in TARGETS:
        if t == "told_diabetes":
            targets_df[t] = _augment_diabetes_target(df.loc[full_index])
        else:
            targets_df[t] = _binarize(df.loc[full_index, t])

        n_pos = (targets_df[t] == 1.0).sum()
        n_neg = (targets_df[t] == 0.0).sum()
        n_unk = targets_df[t].isna().sum()
        log.info(f"   {t:<20}  pos={n_pos:>5,}  neg={n_neg:>6,}  unknown={n_unk:>6,}  "
                 f"prev={100*n_pos/(n_pos+n_neg):.1f}%")

    return targets_df


def filter_records(features_df: pd.DataFrame, targets_df: pd.DataFrame,
                   min_features: int = 15, min_targets: int = 3) -> Tuple[pd.DataFrame, pd.DataFrame]:
    log.info(f"Filtering: ≥{min_features} features and ≥{min_targets} known targets...")

    has_strata = features_df["age_years"].notna() & features_df["sex"].notna()

    n_features = features_df.notna().sum(axis=1)
    n_targets = targets_df.notna().sum(axis=1)

    keep = has_strata & (n_features >= min_features) & (n_targets >= min_targets)
    log.info(f"   {keep.sum():,} / {len(features_df):,} records pass "
             f"({100*keep.mean():.1f}%)")

    return features_df[keep], targets_df[keep]


def stratified_split(features_df: pd.DataFrame, targets_df: pd.DataFrame,
                     val_size: float = 0.15, test_size: float = 0.15,
                     random_state: int = 42) -> Dict[str, Tuple[pd.DataFrame, pd.DataFrame]]:
    log.info(f"Splitting: train / val / test = {1-val_size-test_size:.0%} / {val_size:.0%} / {test_size:.0%}")

    age = features_df["age_years"].clip(lower=18, upper=99)
    age_bucket = pd.cut(age, bins=[17, 30, 45, 60, 75, 100],
                        labels=["18-29", "30-44", "45-59", "60-74", "75+"])
    age_bucket = age_bucket.astype(str).fillna("UNK")
    sex_str = features_df["sex"].map({0.0: "M", 1.0: "F"}).fillna("U")
    strata = (age_bucket + "_" + sex_str).values

    n_nan = pd.isna(strata).sum() if hasattr(strata, "__iter__") else 0
    log.info(f"   Stratification keys: {len(set(strata))} unique buckets, {n_nan} NaN")

    idx_train_val, idx_test = train_test_split(
        features_df.index, test_size=test_size,
        random_state=random_state, stratify=strata
    )
    val_size_adj = val_size / (1 - test_size)
    strata_tv = pd.Series(strata, index=features_df.index).loc[idx_train_val].values
    idx_train, idx_val = train_test_split(
        idx_train_val, test_size=val_size_adj,
        random_state=random_state, stratify=strata_tv
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
    log.info("Computing feature statistics on train...")
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
    log.info("HEMAX_RISK — data preparation")
    log.info("=" * 70)

    df = load_raw()
    features = build_features(df)
    targets = build_targets(df, features.index)
    features, targets = filter_records(features, targets)
    splits = stratified_split(features, targets)

    train_f, train_t = splits["train"]
    feature_stats = compute_stats(train_f)
    target_stats = {
        t: {
            "prevalence": float((train_t[t] == 1.0).mean()),
            "n_pos": int((train_t[t] == 1.0).sum()),
            "n_neg": int((train_t[t] == 0.0).sum()),
            "n_unknown": int(train_t[t].isna().sum()),
            "pos_weight": float(((train_t[t] == 0.0).sum() /
                                 max((train_t[t] == 1.0).sum(), 1))),
        }
        for t in TARGETS
    }

    log.info("Saving outputs...")
    for name, (f, t) in splits.items():
        save_split(f, t, name)

    with open(OUT_DIR / "feature_stats.json", "w") as fp:
        json.dump(feature_stats, fp, indent=2)
    with open(OUT_DIR / "target_stats.json", "w") as fp:
        json.dump(target_stats, fp, indent=2)

    metadata = {
        "version": "1.0",
        "n_features": len(features.columns),
        "feature_names": list(features.columns),
        "target_names": TARGETS,
        "n_train": len(splits["train"][0]),
        "n_val": len(splits["val"][0]),
        "n_test": len(splits["test"][0]),
        "diabetes_target_augmented_with_hba1c": True,
    }
    with open(OUT_DIR / "metadata.json", "w") as fp:
        json.dump(metadata, fp, indent=2)
    log.info(f"   Saved metadata.json")

    log.info("=" * 70)
    log.info("Done!")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
