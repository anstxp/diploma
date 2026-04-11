from __future__ import annotations

import json
import logging
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss

ROOT = Path(__file__).parent.parent.parent
DATA_DIR = ROOT / "data_processed_v2"
MODEL_DIR = ROOT / "model_out_v2"
WEIGHTS_DIR = ROOT / "neuro_api" / "weights"

sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT))

from model import load_model  # noqa: E402

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("calibrate_v2")


def compute_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    if len(y_true) < 2:
        return float("nan")
    bin_edges = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        lo, hi = bin_edges[i], bin_edges[i + 1]
        mask = (y_prob > lo) & (y_prob <= hi) if i > 0 else (y_prob >= lo) & (y_prob <= hi)
        n_in = mask.sum()
        if n_in == 0:
            continue
        conf = y_prob[mask].mean()
        acc = y_true[mask].mean()
        ece += (n_in / len(y_true)) * abs(conf - acc)
    return float(ece)


def load_prepared_v2_data() -> dict:
    with open(DATA_DIR / "metadata.json") as f:
        meta = json.load(f)
    with open(DATA_DIR / "feature_stats.json") as f:
        feature_stats = json.load(f)

    feature_names = meta["feature_names"]
    target_names = meta["target_names"]
    means = np.array([feature_stats[f]["mean"] for f in feature_names], dtype=np.float32)
    stds = np.array([feature_stats[f]["std"] for f in feature_names], dtype=np.float32)
    stds = np.where(stds < 1e-6, 1.0, stds)

    def prep(df: pd.DataFrame):
        feat_raw = df[feature_names].values.astype(np.float32)
        missing = np.isnan(feat_raw).astype(np.float32)
        feat_filled = np.where(np.isnan(feat_raw), means, feat_raw)
        feats = (feat_filled - means) / stds
        feats = np.clip(feats, -5.0, 5.0)
        targets_raw = df[target_names].values.astype(np.float32)
        target_mask = (~np.isnan(targets_raw)).astype(np.float32)
        targets = np.where(np.isnan(targets_raw), 0.0, targets_raw)
        return feats, missing, targets, target_mask

    df_val = pd.read_parquet(DATA_DIR / "val.parquet")
    df_test = pd.read_parquet(DATA_DIR / "test.parquet")
    return {
        "feature_names": feature_names,
        "target_names": target_names,
        "val": prep(df_val),
        "test": prep(df_test),
    }


def predict_all(model, features: np.ndarray, missing: np.ndarray,
                target_names: list, batch_size: int = 512) -> dict:
    model.eval()
    n = len(features)
    probs = {t: np.zeros(n, dtype=np.float32) for t in target_names}
    with torch.no_grad():
        for start in range(0, n, batch_size):
            end = min(start + batch_size, n)
            f = torch.from_numpy(features[start:end])
            m = torch.from_numpy(missing[start:end])
            out = model(f, m, apply_temperature=True)
            for t in target_names:
                probs[t][start:end] = torch.sigmoid(out[t]).cpu().numpy()
    return probs


def fit_isotonic_per_task(probs_val: dict, targets_val: np.ndarray,
                          masks_val: np.ndarray, target_names: list) -> dict:
    isotonics: dict[str, IsotonicRegression | None] = {}
    for i, t in enumerate(target_names):
        m = masks_val[:, i].astype(bool)
        y_true = targets_val[m, i]
        y_prob = probs_val[t][m]
        n_pos = int(y_true.sum())
        if n_pos < 30:
            log.warning(f"  {t:<24} skip — only {n_pos} positives in val")
            isotonics[t] = None
            continue
        ir = IsotonicRegression(out_of_bounds="clip", y_min=0.001, y_max=0.999)
        ir.fit(y_prob, y_true)
        isotonics[t] = ir
        log.info(f"  {t:<24} fitted on n={m.sum():,} (n_pos={n_pos:,})")
    return isotonics


def serialize_isotonics(isotonics: dict) -> dict:
    out = {}
    for t, ir in isotonics.items():
        if ir is None:
            out[t] = None
            continue
        out[t] = {
            "x_min": float(ir.X_min_),
            "x_max": float(ir.X_max_),
            "x_thresholds": [float(x) for x in ir.X_thresholds_.tolist()],
            "y_thresholds": [float(y) for y in ir.y_thresholds_.tolist()],
        }
    return out


def apply_isotonic(probs: dict, isotonics: dict, target_names: list) -> dict:
    out = {}
    for t in target_names:
        out[t] = (probs[t] if isotonics[t] is None
                  else isotonics[t].transform(probs[t]))
    return out


def main() -> int:
    log.info("=" * 70)
    log.info("  HEMAX_NEURO v2 — isotonic calibration on validation set")
    log.info("=" * 70)

    if not (MODEL_DIR / "model.pt").exists():
        log.error(f"  ✗ v2 model not found: {MODEL_DIR / 'model.pt'}")
        log.error(f"     Run: python -m train.v2.train_v2 first")
        return 1

    log.info(f"Loading v2 model from {MODEL_DIR / 'model.pt'}")
    model, _extras = load_model(MODEL_DIR / "model.pt")
    log.info("Loading v2 splits...")
    data = load_prepared_v2_data()
    target_names = data["target_names"]
    log.info(f"  features: {len(data['feature_names'])}  targets: {len(target_names)}")

    feats_val, miss_val, tgt_val, mask_val = data["val"]
    feats_te, miss_te, tgt_te, mask_te = data["test"]
    log.info(f"  val: {len(feats_val):,}  test: {len(feats_te):,}")

    log.info("\nInference on val with temperature scaling...")
    probs_val = predict_all(model, feats_val, miss_val, target_names)
    log.info("Inference on test...")
    probs_test = predict_all(model, feats_te, miss_te, target_names)

    log.info("\nFitting per-task isotonic regression on validation set...")
    isotonics = fit_isotonic_per_task(probs_val, tgt_val, mask_val, target_names)

    log.info("\nCalibration improvement on test set:")
    log.info(f"  {'Target':<24} {'ECE temp':>10} {'ECE iso':>10} "
             f"{'Brier temp':>12} {'Brier iso':>12} {'ECE Δ%':>8}")
    log.info("  " + "-" * 78)
    probs_test_iso = apply_isotonic(probs_test, isotonics, target_names)
    summary: list[dict] = []
    for i, t in enumerate(target_names):
        m = mask_te[:, i].astype(bool)
        if m.sum() < 100 or tgt_te[m, i].sum() < 10:
            log.info(f"  {t:<24}  -- skipped (too few samples)")
            continue
        y = tgt_te[m, i]
        p_temp = probs_test[t][m]
        p_iso = probs_test_iso[t][m]
        ece_temp = compute_ece(y, p_temp)
        ece_iso = compute_ece(y, p_iso)
        brier_temp = brier_score_loss(y, p_temp)
        brier_iso = brier_score_loss(y, p_iso)
        improvement = (ece_temp - ece_iso) / max(ece_temp, 1e-6) * 100
        marker = "▼" if improvement > 5 else "·"
        log.info(f"  {t:<24} {ece_temp:>10.4f} {ece_iso:>10.4f} "
                 f"{brier_temp:>12.4f} {brier_iso:>12.4f} {improvement:>7.1f}% {marker}")
        summary.append({
            "target": t,
            "ece_temp": float(ece_temp),
            "ece_iso": float(ece_iso),
            "brier_temp": float(brier_temp),
            "brier_iso": float(brier_iso),
            "ece_improvement_pct": float(improvement),
        })

    log.info("\nProbability distribution shrinkage on test (rare-event targets):")
    log.info(f"  {'Target':<24} {'temp p99':>10} {'iso p99':>10} "
             f"{'temp mean':>10} {'iso mean':>10}")
    log.info("  " + "-" * 68)
    for t in target_names:
        m = mask_te[:, target_names.index(t)].astype(bool)
        if m.sum() < 100: continue
        p_temp = probs_test[t][m]
        p_iso = probs_test_iso[t][m]
        log.info(f"  {t:<24} {np.percentile(p_temp, 99):>10.4f} "
                 f"{np.percentile(p_iso, 99):>10.4f} "
                 f"{p_temp.mean():>10.4f} {p_iso.mean():>10.4f}")

    iso_data = serialize_isotonics(isotonics)

    trace_path = MODEL_DIR / "isotonic_params.json"
    with open(trace_path, "w") as f:
        json.dump(iso_data, f, indent=2)
    log.info(f"\n✓ Saved (traceability): {trace_path}")

    diag_path = MODEL_DIR / "calibration_summary_v2.json"
    with open(diag_path, "w") as f:
        json.dump({
            "diagnostic": summary,
            "n_val": len(feats_val),
            "n_test": len(feats_te),
            "target_names": target_names,
        }, f, indent=2)
    log.info(f"✓ Saved diagnostic: {diag_path}")

    prod_path = WEIGHTS_DIR / "isotonic_params.json"
    shutil.copy(trace_path, prod_path)
    log.info(f"✓ Installed to production: {prod_path}")

    log.info("\n" + "=" * 70)
    log.info("✅ CALIBRATION DONE")
    log.info("=" * 70)
    log.info("")
    log.info("Restart neuro-api so it picks up isotonic_params.json:")
    log.info("  cd ..")
    log.info("  docker compose up -d --force-recreate neuro-api")
    log.info("")
    log.info("Then verify in logs that isotonic was loaded:")
    log.info("  docker logs hemax-neuro 2>&1 | grep -i 'isotonic'")
    log.info("  # expect:  Loaded isotonic calibration from /app/.../isotonic_params.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
