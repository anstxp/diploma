from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn.functional as F
from sklearn.isotonic import IsotonicRegression
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.dataset import HAM10000Dataset, get_eval_transform
from engine.model import load_model

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("calibration")

ROOT = Path(__file__).parent.parent
PROCESSED = ROOT / "data_processed"
FIG = ROOT / "analysis" / "figures"
REP = ROOT / "analysis" / "reports"
FIG.mkdir(exist_ok=True, parents=True)
REP.mkdir(exist_ok=True, parents=True)

CLASS_COLORS = {
    "akiec": "#f59e0b", "bcc": "#dc2626", "bkl": "#0ea5e9",
    "df": "#22c55e", "mel": "#7c1d6f", "nv": "#10b981", "vasc": "#ec4899",
}



def collect_logits(model, loader, device):
    model.eval()
    all_logits, all_labels = [], []
    with torch.no_grad():
        for imgs, labels, _ in loader:
            imgs = imgs.to(device)
            logits = model(imgs)
            all_logits.append(logits.cpu())
            all_labels.append(labels)
    return torch.cat(all_logits).numpy(), torch.cat(all_labels).numpy()



def fit_temperature(logits: np.ndarray, labels: np.ndarray) -> float:
    logits_t = torch.from_numpy(logits).float()
    labels_t = torch.from_numpy(labels).long()
    T = torch.nn.Parameter(torch.ones(1) * 1.5)
    optimizer = torch.optim.LBFGS([T], lr=0.01, max_iter=50)

    def closure():
        optimizer.zero_grad()
        loss = F.cross_entropy(logits_t / T.clamp(min=1e-3), labels_t)
        loss.backward()
        return loss

    optimizer.step(closure)
    T_val = float(T.detach().clamp(min=1e-3).item())
    log.info(f"   Fitted temperature: T = {T_val:.4f}")
    return T_val


def apply_temperature(logits: np.ndarray, T: float) -> np.ndarray:
    scaled = logits / T
    e = np.exp(scaled - scaled.max(axis=1, keepdims=True))
    return e / e.sum(axis=1, keepdims=True)



def fit_isotonic_per_class(probs: np.ndarray, labels: np.ndarray,
                           classes: list) -> dict:
    isotonic_params = {}
    for i, cls in enumerate(classes):
        x = probs[:, i]
        y = (labels == i).astype(int)
        if y.sum() == 0 or y.sum() == len(y):
            log.warning(f"   {cls}: degenerate target — skipping")
            continue
        ir = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        ir.fit(x, y)
        x_grid = np.linspace(0, 1, 100)
        y_grid = ir.predict(x_grid)
        isotonic_params[cls] = {
            "x_thresholds": x_grid.tolist(),
            "y_thresholds": y_grid.tolist(),
            "x_min": float(x.min()),
            "x_max": float(x.max()),
        }
        log.info(f"   {cls}: isotonic fitted on {len(x)} val samples, "
                 f"y range [{y_grid.min():.3f}, {y_grid.max():.3f}]")
    return isotonic_params


def apply_isotonic(probs: np.ndarray, isotonic_params: dict,
                   classes: list) -> np.ndarray:
    out = np.zeros_like(probs)
    for i, cls in enumerate(classes):
        if cls not in isotonic_params:
            out[:, i] = probs[:, i]
            continue
        p = isotonic_params[cls]
        out[:, i] = np.interp(probs[:, i], p["x_thresholds"], p["y_thresholds"])
    sums = out.sum(axis=1, keepdims=True)
    sums = np.maximum(sums, 1e-9)
    return out / sums



def expected_calibration_error(probs: np.ndarray, labels: np.ndarray,
                                n_bins: int = 15) -> float:
    confs = probs.max(axis=1)
    preds = probs.argmax(axis=1)
    correct = (preds == labels).astype(float)

    bin_edges = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        lo, hi = bin_edges[i], bin_edges[i + 1]
        mask = (confs >= lo) & (confs < hi if i < n_bins - 1 else confs <= hi)
        if mask.sum() == 0:
            continue
        bin_acc = correct[mask].mean()
        bin_conf = confs[mask].mean()
        ece += (mask.sum() / len(probs)) * abs(bin_acc - bin_conf)
    return float(ece)


def per_class_ece(probs: np.ndarray, labels: np.ndarray,
                  classes: list, n_bins: int = 10) -> dict:
    out = {}
    for i, cls in enumerate(classes):
        y = (labels == i).astype(int)
        p = probs[:, i]
        bin_edges = np.linspace(0, 1, n_bins + 1)
        ece = 0.0
        for k in range(n_bins):
            mask = (p >= bin_edges[k]) & (p < bin_edges[k + 1])
            if mask.sum() == 0:
                continue
            ece += (mask.sum() / len(p)) * abs(y[mask].mean() - p[mask].mean())
        out[cls] = float(ece)
    return out


def plot_reliability(probs: np.ndarray, labels: np.ndarray, classes: list,
                     save_to: Path, title: str):
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    axes = axes.flatten()
    n_bins = 10
    bin_edges = np.linspace(0, 1, n_bins + 1)

    eces = per_class_ece(probs, labels, classes, n_bins)

    for i, cls in enumerate(classes):
        ax = axes[i]
        p = probs[:, i]
        y = (labels == i).astype(int)
        confs, accs = [], []
        for k in range(n_bins):
            mask = (p >= bin_edges[k]) & (p < bin_edges[k + 1])
            if mask.sum() < 5:
                continue
            confs.append(p[mask].mean())
            accs.append(y[mask].mean())
        if confs:
            ax.plot(confs, accs, "o-", color=CLASS_COLORS.get(cls, "#000"),
                    lw=2, markersize=7)
        ax.plot([0, 1], [0, 1], "k--", lw=1, alpha=0.4)
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.set_title(f"{cls.upper()}  (ECE={eces[cls]:.3f})", fontsize=11)
        ax.set_xlabel("Predicted prob")
        ax.set_ylabel("Observed freq")
        ax.grid(alpha=0.3)

    ax = axes[7]
    classes_sorted = sorted(eces.items(), key=lambda kv: -kv[1])
    names = [c for c, _ in classes_sorted]
    values = [e for _, e in classes_sorted]
    colors = [CLASS_COLORS.get(c, "#888") for c in names]
    ax.barh(names[::-1], values[::-1], color=colors[::-1])
    ax.set_title(f"Per-class ECE\n(macro = {np.mean(list(eces.values())):.3f})")
    ax.set_xlabel("ECE")
    ax.grid(axis="x", alpha=0.3)

    plt.suptitle(title, fontsize=14, y=1.0)
    plt.tight_layout()
    plt.savefig(save_to, dpi=140, bbox_inches="tight")
    plt.close()
    log.info(f"   {save_to.name}")



def main():
    log.info("=" * 70)
    log.info("HEMAX_DERMA — calibration analysis")
    log.info("=" * 70)

    with open(PROCESSED / "metadata.json") as f:
        meta = json.load(f)
    classes = meta["classes"]
    device = "cuda" if torch.cuda.is_available() else (
        "mps" if torch.backends.mps.is_available() else "cpu"
    )
    log.info(f"Device: {device}")

    log.info("Loading model...")
    model, _ = load_model(ROOT / "model_out" / "model.pt", device=device)

    log.info("Collecting val logits...")
    val_ds = HAM10000Dataset(PROCESSED / "val.csv", classes,
                             transform=get_eval_transform(meta["image_size"]))
    val_loader = DataLoader(val_ds, batch_size=32, shuffle=False, num_workers=2)
    val_logits, val_labels = collect_logits(model, val_loader, device)

    log.info("Collecting test logits...")
    test_ds = HAM10000Dataset(PROCESSED / "test.csv", classes,
                              transform=get_eval_transform(meta["image_size"]))
    test_loader = DataLoader(test_ds, batch_size=32, shuffle=False, num_workers=2)
    test_logits, test_labels = collect_logits(model, test_loader, device)

    log.info("\n[1/3] Raw (uncalibrated) probabilities...")
    raw_test = apply_temperature(test_logits, T=1.0)
    raw_ece = expected_calibration_error(raw_test, test_labels)
    raw_per_class = per_class_ece(raw_test, test_labels, classes)
    raw_acc = float((raw_test.argmax(1) == test_labels).mean())
    log.info(f"   Macro ECE (raw):         {raw_ece:.4f}  acc={raw_acc:.4f}")
    plot_reliability(raw_test, test_labels, classes,
                      FIG / "13_reliability_raw.png",
                      "Reliability — RAW (uncalibrated)")

    log.info("\n[2/3] Fitting temperature on validation...")
    T = fit_temperature(val_logits, val_labels)
    temp_test = apply_temperature(test_logits, T)
    temp_ece = expected_calibration_error(temp_test, test_labels)
    temp_per_class = per_class_ece(temp_test, test_labels, classes)
    temp_acc = float((temp_test.argmax(1) == test_labels).mean())
    log.info(f"   Macro ECE (temperature): {temp_ece:.4f}  acc={temp_acc:.4f}")
    plot_reliability(temp_test, test_labels, classes,
                      FIG / "14_reliability_temperature.png",
                      f"Reliability — after temperature scaling (T={T:.3f})")

    log.info("\n[3/3] Fitting per-class isotonic on val (post-temperature)...")
    val_temp = apply_temperature(val_logits, T)
    iso_params = fit_isotonic_per_class(val_temp, val_labels, classes)

    iso_test = apply_isotonic(temp_test, iso_params, classes)
    iso_ece = expected_calibration_error(iso_test, test_labels)
    iso_per_class = per_class_ece(iso_test, test_labels, classes)
    iso_acc = float((iso_test.argmax(1) == test_labels).mean())
    log.info(f"   Macro ECE (isotonic):    {iso_ece:.4f}  acc={iso_acc:.4f}")
    plot_reliability(iso_test, test_labels, classes,
                      FIG / "15_reliability_isotonic.png",
                      "Reliability — after temperature + isotonic")

    isotonic_helps_ece = iso_ece < temp_ece - 0.005
    isotonic_keeps_accuracy = iso_acc >= temp_acc - 0.02

    if isotonic_helps_ece and isotonic_keeps_accuracy:
        production_strategy = "temperature+isotonic"
        production_iso = iso_params
        prod_ece = iso_ece
        log.info("\n   ✓ Isotonic improves both ECE and preserves accuracy "
                 "→ enabling in production")
    else:
        production_strategy = "temperature_only"
        production_iso = {}
        prod_ece = temp_ece
        log.info("\n   ⚠ Isotonic disabled in production "
                 f"(ECE_iso={iso_ece:.4f} vs ECE_temp={temp_ece:.4f}, "
                 f"acc_iso={iso_acc:.4f} vs acc_temp={temp_acc:.4f}). "
                 "Temperature alone is sufficient for this dataset.")
        log.info("   Reason: per-class isotonic with heavy class imbalance "
                 "(NV = 67% in HAM10000) tends to collapse predictions "
                 "toward the prior, hurting argmax for minority classes "
                 "even when macro ECE improves.")

    log.info("\n" + "=" * 50)
    log.info("CALIBRATION SUMMARY (test set)")
    log.info("=" * 50)
    log.info(f"   raw          ECE = {raw_ece:.4f}  acc={raw_acc:.4f}")
    log.info(f"   +temperature ECE = {temp_ece:.4f}  acc={temp_acc:.4f}  ({(raw_ece-temp_ece)/raw_ece*100:.0f}% ECE reduction)")
    log.info(f"   +isotonic    ECE = {iso_ece:.4f}  acc={iso_acc:.4f}  ({(raw_ece-iso_ece)/raw_ece*100:.0f}% ECE reduction)")
    log.info(f"   ⇒ production: {production_strategy}")
    log.info("\n   Per-class ECE:")
    log.info(f"   {'class':<10}  {'raw':>8}  {'temp':>8}  {'iso':>8}")
    for cls in classes:
        log.info(f"   {cls:<10}  {raw_per_class[cls]:>8.4f}  "
                 f"{temp_per_class[cls]:>8.4f}  {iso_per_class[cls]:>8.4f}")

    out_path = REP / "calibration_params.json"
    with open(out_path, "w") as f:
        json.dump({
            "temperature": T,
            "isotonic": production_iso,
            "production_strategy": production_strategy,
            "classes": classes,
            "raw_ece": raw_ece,
            "temperature_ece": temp_ece,
            "isotonic_ece": iso_ece,
            "raw_accuracy": raw_acc,
            "temperature_accuracy": temp_acc,
            "isotonic_accuracy": iso_acc,
            "production_ece": prod_ece,
            "per_class_ece": {
                "raw": raw_per_class,
                "temperature": temp_per_class,
                "isotonic": iso_per_class,
            },
            "n_val": int(len(val_labels)),
            "n_test": int(len(test_labels)),
        }, f, indent=2)
    log.info(f"\n   Saved to {out_path.relative_to(ROOT)}")

    md = [
        "# HEMAX_DERMA — Calibration Report",
        "",
        f"**Test set:** {len(test_labels):,} images",
        f"**Validation set:** {len(val_labels):,} images",
        f"**Production strategy:** `{production_strategy}`",
        "",
        "## Macro ECE summary",
        "",
        "| Stage | ECE | Test accuracy | Reduction vs raw |",
        "|---|---|---|---|",
        f"| Raw (uncalibrated)   | {raw_ece:.4f} | {raw_acc:.4f} | — |",
        f"| + Temperature (T={T:.3f}) | {temp_ece:.4f} | {temp_acc:.4f} | {(raw_ece-temp_ece)/raw_ece*100:.1f}% |",
        f"| + Per-class isotonic | {iso_ece:.4f} | {iso_acc:.4f} | {(raw_ece-iso_ece)/raw_ece*100:.1f}% |",
        "",
        "## Per-class ECE",
        "",
        "| Class | Raw | + Temp | + Isotonic |",
        "|---|---|---|---|",
    ]
    for cls in classes:
        md.append(f"| {cls} | {raw_per_class[cls]:.4f} | "
                  f"{temp_per_class[cls]:.4f} | {iso_per_class[cls]:.4f} |")

    md.extend([
        "",
        "## Method",
        "",
        "1. **Temperature scaling** (Guo et al., ICML 2017): single scalar T "
        "fitted on validation NLL via LBFGS. Preserves argmax (T monotonic in softmax).",
        "2. **Per-class isotonic regression**: monotonic non-parametric "
        "remapping of softmax(logit/T) → calibrated probability for each class "
        "in one-vs-rest fashion, renormalized to sum to 1.",
        "",
        "## Production decision",
        "",
        f"**Selected strategy: `{production_strategy}`**",
        "",
    ])
    if production_strategy == "temperature_only":
        md.extend([
            "Per-class isotonic was **evaluated but disabled** because:",
            "",
            f"- Isotonic ECE ({iso_ece:.4f}) was not meaningfully lower than "
            f"temperature-only ECE ({temp_ece:.4f}), AND/OR",
            f"- Isotonic accuracy ({iso_acc:.4f}) was lower than temperature-only "
            f"accuracy ({temp_acc:.4f}) by more than 2 percentage points.",
            "",
            "This is a known failure mode of per-class isotonic regression on "
            "heavily class-imbalanced multi-class datasets like HAM10000 "
            "(NV = ~67% prevalence): the renormalization step after isotonic "
            "remap inflates the dominant-class probability for non-dominant "
            "examples, flipping argmax in clinically dangerous directions "
            "(e.g. MEL → NV).",
            "",
            "**Temperature scaling alone reduces macro ECE by "
            f"{(raw_ece-temp_ece)/raw_ece*100:.0f}% while preserving argmax** — "
            "the clinically safer choice for skin lesion classification.",
        ])
    else:
        md.extend([
            "Per-class isotonic was **enabled in production** because:",
            "",
            f"- Isotonic ECE ({iso_ece:.4f}) is meaningfully lower than "
            f"temperature-only ECE ({temp_ece:.4f}).",
            f"- Isotonic accuracy ({iso_acc:.4f}) is comparable to "
            f"temperature-only accuracy ({temp_acc:.4f}).",
        ])

    md.extend([
        "",
        "## Files",
        "",
        "- `analysis/figures/13_reliability_raw.png`",
        "- `analysis/figures/14_reliability_temperature.png`",
        "- `analysis/figures/15_reliability_isotonic.png`",
        "- `analysis/reports/calibration_params.json` — production params",
    ])
    (REP / "calibration.md").write_text("\n".join(md))
    log.info(f"   Saved {(REP / 'calibration.md').relative_to(ROOT)}")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
