from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.inference import DermaPredictor

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("gradcam")

ROOT = Path(__file__).parent.parent
FIG = ROOT / "analysis" / "figures"
REP = ROOT / "analysis" / "reports"
FIG.mkdir(exist_ok=True, parents=True)


def load_predictor() -> DermaPredictor:
    return DermaPredictor(ROOT / "model_out" / "model.pt", device="cpu")


def load_test_predictions() -> pd.DataFrame:
    return pd.read_csv(REP / "test_predictions.csv")


def gallery(predictor: DermaPredictor, sample_df: pd.DataFrame,
            test_df: pd.DataFrame, save_to: Path, title: str,
            n_cols: int = 4):
    n = len(sample_df)
    n_rows = (n + n_cols - 1) // n_cols
    fig, axes = plt.subplots(n_rows * 2, n_cols,
                              figsize=(n_cols * 4, n_rows * 8))
    axes = np.atleast_2d(axes)

    for i, (_, row) in enumerate(sample_df.iterrows()):
        r = i // n_cols * 2
        c = i % n_cols

        match = test_df[test_df["image_id"] == row["image_id"]]
        if match.empty:
            continue
        test_orig = pd.read_csv(ROOT / "data_processed" / "test.csv")
        img_match = test_orig[test_orig["image_id"] == row["image_id"]]
        if img_match.empty:
            continue
        img_path = img_match.iloc[0]["image_path"]

        try:
            pred, overlay = predictor.gradcam(img_path)
        except Exception as e:
            log.warning(f"   gradcam failed for {row['image_id']}: {e}")
            continue

        orig = Image.open(img_path).convert("RGB").resize(
            (predictor.image_size, predictor.image_size))

        ax_o = axes[r, c]
        ax_o.imshow(orig)
        true_lbl = row["true_label"]
        pred_lbl = row["pred_label"]
        is_correct = (true_lbl == pred_lbl)
        color = "green" if is_correct else "red"
        ax_o.set_title(f"{row['image_id']}\nTrue: {true_lbl.upper()}",
                       fontsize=10, color=color)
        ax_o.axis("off")

        ax_g = axes[r + 1, c]
        ax_g.imshow(overlay)
        top3_str = "\n".join(f"  {cls.upper()} {p*100:.0f}%"
                             for cls, p in pred.top_k[:3])
        prefix = "✓" if is_correct else "✗"
        ax_g.set_title(f"{prefix} Pred: {pred_lbl.upper()}\n{top3_str}",
                       fontsize=9, color=color)
        ax_g.axis("off")

    for k in range(n, n_rows * n_cols):
        r = k // n_cols * 2
        c = k % n_cols
        axes[r, c].axis("off")
        axes[r + 1, c].axis("off")

    plt.suptitle(title, fontsize=14, y=0.995)
    plt.tight_layout()
    plt.savefig(save_to, dpi=130, bbox_inches="tight")
    plt.close()
    log.info(f"   {save_to.name}")


def pick_correct_examples(test_df: pd.DataFrame, classes: List[str]) -> pd.DataFrame:
    rows = []
    for cls in classes:
        sub = test_df[(test_df["true_label"] == cls) & (test_df["correct"])]
        if sub.empty:
            continue
        col = f"prob_{cls}"
        if col in sub.columns:
            sub = sub.sort_values(col, ascending=False)
        rows.append(sub.iloc[0])
    return pd.DataFrame(rows)


def pick_error_examples(test_df: pd.DataFrame, n: int = 6) -> pd.DataFrame:
    wrong = test_df[~test_df["correct"]].copy()
    if wrong.empty:
        return wrong
    confs = []
    for _, row in wrong.iterrows():
        confs.append(row[f"prob_{row['pred_label']}"])
    wrong["pred_conf"] = confs
    return wrong.sort_values("pred_conf", ascending=False).head(n)


def pick_melanoma_focus(test_df: pd.DataFrame, n_correct: int = 4,
                        n_missed: int = 2) -> pd.DataFrame:
    correct_mel = test_df[
        (test_df["true_label"] == "mel") & (test_df["correct"])
    ].sort_values("prob_mel", ascending=False).head(n_correct)
    missed_mel = test_df[
        (test_df["true_label"] == "mel") & (~test_df["correct"])
    ].sort_values("prob_mel", ascending=False).head(n_missed)
    return pd.concat([correct_mel, missed_mel])


def attention_summary(predictor: DermaPredictor, test_df: pd.DataFrame,
                      classes: List[str], save_to: Path,
                      n_per_class: int = 5):
    test_orig = pd.read_csv(ROOT / "data_processed" / "test.csv")
    central_means = {c: [] for c in classes}
    peripheral_means = {c: [] for c in classes}

    for cls in classes:
        sub = test_df[(test_df["true_label"] == cls) & (test_df["correct"])]
        sub = sub.head(n_per_class)
        for _, row in sub.iterrows():
            img_match = test_orig[test_orig["image_id"] == row["image_id"]]
            if img_match.empty:
                continue
            img_path = img_match.iloc[0]["image_path"]
            try:
                _, overlay = predictor.gradcam(img_path)
                gray = np.mean(overlay.astype(float), axis=2) / 255.0
                h, w = gray.shape
                cy, cx = h // 2, w // 2
                ry, rx = h // 4, w // 4
                central = gray[cy - ry:cy + ry, cx - rx:cx + rx]
                mask = np.ones_like(gray, dtype=bool)
                mask[cy - ry:cy + ry, cx - rx:cx + rx] = False
                central_means[cls].append(central.mean())
                peripheral_means[cls].append(gray[mask].mean())
            except Exception as e:
                log.warning(f"   skip {row['image_id']}: {e}")

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(classes))
    w = 0.35
    central_avg = [np.mean(central_means[c]) if central_means[c] else 0 for c in classes]
    peri_avg = [np.mean(peripheral_means[c]) if peripheral_means[c] else 0 for c in classes]
    ax.bar(x - w / 2, central_avg, w, label="Central 50% (lesion area)",
           color="#dc2626")
    ax.bar(x + w / 2, peri_avg, w, label="Peripheral (background)",
           color="#9ca3af")
    ax.set_xticks(x)
    ax.set_xticklabels(classes)
    ax.set_ylabel("Mean Grad-CAM intensity")
    ax.set_title("Does the model focus on the lesion vs. background?\n"
                 "(higher central than peripheral = model looks at the lesion)")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_to, dpi=150)
    plt.close()
    log.info(f"   {save_to.name}")


def main():
    log.info("=" * 70)
    log.info("HEMAX_DERMA — Grad-CAM gallery generation")
    log.info("=" * 70)

    if not (REP / "test_predictions.csv").exists():
        log.error("   test_predictions.csv not found. Run evaluate.py first.")
        return

    predictor = load_predictor()
    test_df = load_test_predictions()
    classes = predictor.classes
    log.info(f"   Test set: {len(test_df):,} predictions")

    log.info("\n[1/4] Generating correct-prediction gallery (one per class)...")
    correct_samples = pick_correct_examples(test_df, classes)
    if len(correct_samples) > 0:
        gallery(predictor, correct_samples, test_df,
                FIG / "09_gradcam_correct.png",
                "HEMAX_DERMA — Grad-CAM on correctly classified examples\n"
                "(green = correct prediction; heatmap shows where the model looked)")

    log.info("\n[2/4] Generating error gallery...")
    error_samples = pick_error_examples(test_df, n=6)
    if len(error_samples) > 0:
        gallery(predictor, error_samples, test_df,
                FIG / "10_gradcam_errors.png",
                "Most-confident errors — what was the model looking at when wrong?\n"
                "(red = misclassified; insight into systematic failures)")

    log.info("\n[3/4] Generating melanoma focus...")
    mel_samples = pick_melanoma_focus(test_df)
    if len(mel_samples) > 0:
        gallery(predictor, mel_samples, test_df,
                FIG / "11_gradcam_melanoma.png",
                "Safety-critical: melanoma detection\n"
                "(green = caught | red = missed — the latter is what we worry about)")

    log.info("\n[4/4] Computing attention summary...")
    attention_summary(predictor, test_df, classes, FIG / "12_attention_summary.png")

    log.info("=" * 70)
    log.info("Done!")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
