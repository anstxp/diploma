from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.multimodal_models import build_model
from engine.multimodal_dataset import (
    HAM10000Multimodal, fit_metadata_stats, get_eval_transform,
)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("multimodal_calibration")

ROOT = Path(__file__).parent.parent
PROCESSED = ROOT / "data_processed"
META_CSV = ROOT / "data" / "HAM10000_metadata.csv"
IMAGE_DIR = ROOT / "data" / "HAM10000_images"
REP = ROOT / "analysis" / "reports"
FIG = ROOT / "analysis" / "figures"


def fit_temperature(logits: np.ndarray, labels: np.ndarray) -> float:
    logits_t = torch.tensor(logits, dtype=torch.float32)
    labels_t = torch.tensor(labels, dtype=torch.long)
    T = torch.nn.Parameter(torch.ones(1) * 1.0)
    opt = torch.optim.LBFGS([T], lr=0.05, max_iter=100)

    def closure():
        opt.zero_grad()
        loss = torch.nn.functional.cross_entropy(logits_t / T, labels_t)
        loss.backward()
        return loss

    opt.step(closure)
    return float(T.item())


def expected_calibration_error(probs: np.ndarray, labels: np.ndarray,
                                 n_bins: int = 15) -> float:
    n_classes = probs.shape[1]
    eces = []
    for c in range(n_classes):
        y_true = (labels == c).astype(int)
        p = probs[:, c]
        bin_edges = np.linspace(0, 1, n_bins + 1)
        ece = 0.0
        for i in range(n_bins):
            mask = (p >= bin_edges[i]) & (p < bin_edges[i + 1])
            if mask.sum() > 0:
                bin_acc = y_true[mask].mean()
                bin_conf = p[mask].mean()
                ece += (mask.sum() / len(p)) * abs(bin_acc - bin_conf)
        eces.append(ece)
    return float(np.mean(eces))


def collect_logits(model, loader, device):
    model.eval()
    all_logits, all_labels = [], []
    with torch.no_grad():
        for images, metas, labels, _ in loader:
            images = images.to(device)
            metas = metas.to(device)
            logits = model(images, metas)
            all_logits.append(logits.cpu())
            all_labels.append(labels)
    return torch.cat(all_logits).numpy(), torch.cat(all_labels).numpy()


def main(model_dir: Path = None):
    log.info("=" * 70)
    log.info("HEMAX_DERMA — multimodal calibration")
    log.info("=" * 70)

    if model_dir is None:
        mm_dir = ROOT / "model_out" / "multimodal"
        candidates = []
        for d in mm_dir.iterdir():
            if d.is_dir():
                metrics_path = d / "metrics.json"
                if metrics_path.exists():
                    with open(metrics_path) as f:
                        m = json.load(f)
                    candidates.append((m["best_val_auc"], d, m["model_name"]))
        if not candidates:
            log.error(f"No trained models found in {mm_dir}")
            return
        candidates.sort(reverse=True)
        best_auc, model_dir, model_name = candidates[0]
        log.info(f"Best model by val AUC: {model_name} ({best_auc:.4f})")

    state = torch.load(model_dir / "model.pt", map_location="cpu",
                        weights_only=False)
    model_name = state["model_name"]
    classes = state["classes"]
    meta_stats = state["meta_stats"]
    image_size = state.get("args", {}).get("image_size", 224)

    device = torch.device("cuda" if torch.cuda.is_available()
                            else ("mps" if torch.backends.mps.is_available()
                                  else "cpu"))
    log.info(f"Device: {device}")
    log.info(f"Model: {model_name}")

    model = build_model(model_name, meta_dim=meta_stats["meta_dim"],
                         num_classes=len(classes))
    model.load_state_dict(state["model_state_dict"])
    model = model.to(device).eval()

    log.info("Loading val/test...")
    meta_df = pd.read_csv(META_CSV)
    val_df = pd.read_csv(PROCESSED / "val.csv").merge(
        meta_df[["image_id", "age", "sex", "localization"]],
        on="image_id", how="left",
    )
    test_df = pd.read_csv(PROCESSED / "test.csv").merge(
        meta_df[["image_id", "age", "sex", "localization"]],
        on="image_id", how="left",
    )

    val_ds = HAM10000Multimodal(
        val_df, IMAGE_DIR, classes, meta_stats,
        transform=get_eval_transform(image_size), image_size=image_size,
    )
    test_ds = HAM10000Multimodal(
        test_df, IMAGE_DIR, classes, meta_stats,
        transform=get_eval_transform(image_size), image_size=image_size,
    )
    val_loader = DataLoader(val_ds, batch_size=32, shuffle=False, num_workers=2)
    test_loader = DataLoader(test_ds, batch_size=32, shuffle=False, num_workers=2)

    log.info("Collecting val/test logits...")
    val_logits, val_labels = collect_logits(model, val_loader, device)
    test_logits, test_labels = collect_logits(model, test_loader, device)

    raw_probs = torch.softmax(torch.tensor(test_logits), dim=1).numpy()
    raw_ece = expected_calibration_error(raw_probs, test_labels)
    raw_acc = float((raw_probs.argmax(1) == test_labels).mean())
    log.info(f"  RAW       ECE={raw_ece:.4f}  acc={raw_acc:.4f}")

    T = fit_temperature(val_logits, val_labels)
    temp_probs = torch.softmax(
        torch.tensor(test_logits) / T, dim=1
    ).numpy()
    temp_ece = expected_calibration_error(temp_probs, test_labels)
    temp_acc = float((temp_probs.argmax(1) == test_labels).mean())
    log.info(f"  TEMP T={T:.4f}  ECE={temp_ece:.4f}  acc={temp_acc:.4f}")

    production_strategy = "temperature_only"
    log.info(f"\n  → Production: {production_strategy} (T={T:.4f})")
    log.info(f"  ECE reduction: {raw_ece:.4f} → {temp_ece:.4f} "
             f"({(raw_ece-temp_ece)/raw_ece*100:.0f}%)")

    cal_params = {
        "temperature": T,
        "isotonic": {},
        "production_strategy": production_strategy,
        "classes": classes,
        "model_name": model_name,
        "raw_ece": raw_ece,
        "temperature_ece": temp_ece,
        "raw_accuracy": raw_acc,
        "temperature_accuracy": temp_acc,
        "n_val": len(val_labels),
        "n_test": len(test_labels),
    }

    out_path = REP / f"multimodal_calibration_{model_name}.json"
    with open(out_path, "w") as f:
        json.dump(cal_params, f, indent=2)
    log.info(f"\nSaved {out_path.relative_to(ROOT)}")

    with open(model_dir / "calibration_params.json", "w") as f:
        json.dump(cal_params, f, indent=2)
    log.info(f"Saved {(model_dir / 'calibration_params.json').relative_to(ROOT)}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, default=None,
                        help="Specific model dir. Default: pick best by val AUC")
    args = parser.parse_args()
    main(args.model_dir)
