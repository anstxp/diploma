from __future__ import annotations

import argparse
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("prepare")

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
PROCESSED_DIR = ROOT / "data_processed"
PROCESSED_DIR.mkdir(exist_ok=True)


CLASSES = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]
CLASS_NAMES_EN = {
    "akiec": "Actinic keratosis",
    "bcc":   "Basal cell carcinoma",
    "bkl":   "Benign keratosis",
    "df":    "Dermatofibroma",
    "mel":   "Melanoma",
    "nv":    "Melanocytic nevus",
    "vasc":  "Vascular lesion",
}
CLASS_NAMES_UK = {
    "akiec": "Актинічний кератоз",
    "bcc":   "Базаліома",
    "bkl":   "Себорейний кератоз",
    "df":    "Дерматофіброма",
    "mel":   "Меланома",
    "nv":    "Меланоцитарний невус",
    "vasc":  "Судинне утворення",
}
CLASS_SEVERITY = {
    "mel":   "critical",
    "bcc":   "high",
    "akiec": "medium",
    "bkl":   "low",
    "nv":    "low",
    "df":    "low",
    "vasc":  "low",
}


def load_metadata() -> pd.DataFrame:
    meta_path = DATA_DIR / "HAM10000_metadata.csv"
    if not meta_path.exists():
        log.error(f"   {meta_path} not found.")
        log.error("")
        log.error("   HAM10000 download options:")
        log.error("")
        log.error("   1. Harvard Dataverse (free, requires browser):")
        log.error("      https://dataverse.harvard.edu/dataset.xhtml"
                 "?persistentId=doi:10.7910/DVN/DBW86T")
        log.error("")
        log.error("   2. Kaggle (requires kaggle CLI + auth):")
        log.error("      pip install kaggle")
        log.error("      kaggle datasets download -d kmader/skin-cancer-mnist-ham10000")
        log.error("      unzip skin-cancer-mnist-ham10000.zip -d data/")
        log.error("")
        log.error("   Expected layout after download:")
        log.error("      data/HAM10000_metadata.csv")
        log.error("      data/HAM10000_images/<image_id>.jpg  (10015 files)")
        raise FileNotFoundError(meta_path)

    df = pd.read_csv(meta_path)
    log.info(f"   Loaded {len(df):,} rows × {len(df.columns)} columns")
    log.info(f"   Columns: {list(df.columns)}")
    return df


def verify_images(df: pd.DataFrame) -> pd.DataFrame:
    img_dir = DATA_DIR / "HAM10000_images"
    if not img_dir.exists():
        for alt in ["HAM10000_images_part_1", "ham10000_images", "images"]:
            if (DATA_DIR / alt).exists():
                img_dir = DATA_DIR / alt
                log.warning(f"   Using alternate image dir: {img_dir}")
                break

    log.info(f"   Verifying images in {img_dir}...")
    df = df.copy()
    df["image_path"] = df["image_id"].apply(
        lambda iid: str(img_dir / f"{iid}.jpg")
    )
    df["exists"] = df["image_path"].apply(lambda p: Path(p).exists())
    n_missing = (~df["exists"]).sum()
    if n_missing:
        log.warning(f"   {n_missing:,} images missing on disk — dropping")
    df = df[df["exists"]].drop(columns=["exists"]).reset_index(drop=True)
    log.info(f"   Kept {len(df):,} usable records")
    return df


def split_lesion_aware(df: pd.DataFrame, val_size=0.15, test_size=0.15,
                       seed=42) -> Dict[str, pd.DataFrame]:
    log.info("   Lesion-aware splitting (avoiding image leakage)...")
    rng = np.random.default_rng(seed)

    splits: Dict[str, List[int]] = {"train": [], "val": [], "test": []}
    for cls in CLASSES:
        cls_df = df[df["dx"] == cls]
        unique_lesions = list(cls_df["lesion_id"].unique())
        rng.shuffle(unique_lesions)
        n = len(unique_lesions)
        n_test = int(n * test_size)
        n_val = int(n * val_size)
        test_lesions = set(unique_lesions[:n_test])
        val_lesions = set(unique_lesions[n_test:n_test + n_val])

        for _, row in cls_df.iterrows():
            lid = row["lesion_id"]
            if lid in test_lesions:
                splits["test"].append(row.name)
            elif lid in val_lesions:
                splits["val"].append(row.name)
            else:
                splits["train"].append(row.name)

    out = {name: df.loc[idxs].reset_index(drop=True)
           for name, idxs in splits.items()}
    for name, sdf in out.items():
        log.info(f"   {name:<5}: n={len(sdf):>5,}  classes={sdf['dx'].value_counts().to_dict()}")
    return out


def compute_class_weights(train_df: pd.DataFrame) -> Dict[str, float]:
    counts = train_df["dx"].value_counts().to_dict()
    total = len(train_df)
    n_cls = len(CLASSES)
    weights = {}
    for cls in CLASSES:
        n = counts.get(cls, 1)
        weights[cls] = total / (n_cls * n)
    log.info(f"   Class weights: {weights}")
    return weights


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    log.info("=" * 70)
    log.info("HEMAX_DERMA — data preparation")
    log.info("=" * 70)

    df = load_metadata()
    df = verify_images(df)
    if "lesion_id" not in df.columns:
        log.warning("   No lesion_id — using image_id as lesion identifier")
        df["lesion_id"] = df["image_id"]
    if "dx" not in df.columns:
        log.error("   FATAL: 'dx' column missing in metadata")
        return

    splits = split_lesion_aware(df, seed=args.seed)
    weights = compute_class_weights(splits["train"])

    log.info("Saving outputs...")
    for name, sdf in splits.items():
        out_path = PROCESSED_DIR / f"{name}.csv"
        sdf.to_csv(out_path, index=False)
        log.info(f"   {out_path.name}  rows={len(sdf):,}")

    metadata = {
        "version": "1.0",
        "service": "hemax_derma",
        "n_classes": len(CLASSES),
        "classes": CLASSES,
        "class_names_en": CLASS_NAMES_EN,
        "class_names_uk": CLASS_NAMES_UK,
        "class_severity": CLASS_SEVERITY,
        "n_train": len(splits["train"]),
        "n_val":   len(splits["val"]),
        "n_test":  len(splits["test"]),
        "class_weights": weights,
        "image_size": 224,
        "imagenet_mean": [0.485, 0.456, 0.406],
        "imagenet_std":  [0.229, 0.224, 0.225],
    }
    with open(PROCESSED_DIR / "metadata.json", "w") as fp:
        json.dump(metadata, fp, indent=2, ensure_ascii=False)

    log.info("=" * 70)
    log.info("Done!")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
