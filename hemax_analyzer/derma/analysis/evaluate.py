from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import (
    confusion_matrix, classification_report, precision_recall_curve,
    roc_curve, auc, roc_auc_score, f1_score,
)
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.dataset import HAM10000Dataset, get_eval_transform
from engine.model import load_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("evaluate")

ROOT = Path(__file__).parent.parent
PROCESSED = ROOT / "data_processed"
FIG = ROOT / "analysis" / "figures"
REP = ROOT / "analysis" / "reports"
FIG.mkdir(exist_ok=True, parents=True)
REP.mkdir(exist_ok=True, parents=True)

CLASS_COLORS = {
    "akiec": "#f59e0b",
    "bcc":   "#dc2626",
    "bkl":   "#0ea5e9",
    "df":    "#22c55e",
    "mel":   "#7c1d6f",
    "nv":    "#10b981",
    "vasc":  "#ec4899",
}


def get_predictions(model, loader, classes, device):
    model.eval()
    all_probs, all_labels, all_ids = [], [], []
    with torch.no_grad():
        for imgs, labels, ids in loader:
            imgs = imgs.to(device)
            logits = model(imgs)
            probs = torch.softmax(logits, dim=1).cpu().numpy()
            all_probs.append(probs)
            all_labels.append(labels.numpy())
            all_ids.extend(list(ids))
    return np.concatenate(all_probs), np.concatenate(all_labels), all_ids


def plot_class_distribution(meta, save_to):
    splits = {}
    for name in ("train", "val", "test"):
        df = pd.read_csv(PROCESSED / f"{name}.csv")
        splits[name] = df["dx"].value_counts().reindex(meta["classes"]).fillna(0)

    fig, ax = plt.subplots(figsize=(11, 5))
    x = np.arange(len(meta["classes"]))
    w = 0.27
    for i, (name, counts) in enumerate(splits.items()):
        ax.bar(x + (i - 1) * w, counts.values, w, label=name)
    ax.set_xticks(x)
    ax.set_xticklabels(meta["classes"])
    ax.set_ylabel("# images")
    ax.set_title("HAM10000 — class distribution per split")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_to, dpi=150)
    plt.close()
    log.info(f"   {save_to.name}")


def plot_confusion(probs, labels, classes, save_to):
    preds = probs.argmax(axis=1)
    cm = confusion_matrix(labels, preds, labels=range(len(classes)))
    cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True).clip(min=1)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    for ax, (data, title, fmt) in zip(axes, [
        (cm, "Counts", "d"),
        (cm_norm, "Normalized (row=true class)", ".2f"),
    ]):
        im = ax.imshow(data, cmap="Blues", aspect="auto")
        ax.set_xticks(range(len(classes)))
        ax.set_yticks(range(len(classes)))
        ax.set_xticklabels(classes, rotation=30)
        ax.set_yticklabels(classes)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
        ax.set_title(title)
        for i in range(len(classes)):
            for j in range(len(classes)):
                ax.text(j, i, format(data[i, j], fmt),
                        ha="center", va="center",
                        color="white" if data[i, j] > data.max() * 0.5 else "black",
                        fontsize=9)
        plt.colorbar(im, ax=ax)
    plt.suptitle("HEMAX_DERMA — Confusion matrix on test set", fontsize=13)
    plt.tight_layout()
    plt.savefig(save_to, dpi=150)
    plt.close()
    log.info(f"   {save_to.name}")


def plot_roc_curves(probs, labels, classes, save_to):
    fig, ax = plt.subplots(figsize=(8, 7))
    for i, cls in enumerate(classes):
        y_true = (labels == i).astype(int)
        if y_true.sum() == 0:
            continue
        fpr, tpr, _ = roc_curve(y_true, probs[:, i])
        a = auc(fpr, tpr)
        color = CLASS_COLORS.get(cls, None)
        ax.plot(fpr, tpr, lw=2, label=f"{cls.upper()} (AUC={a:.3f})", color=color)
    ax.plot([0, 1], [0, 1], "k--", lw=1, alpha=0.5)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC curves per class (one-vs-rest)")
    ax.legend(loc="lower right")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_to, dpi=150)
    plt.close()
    log.info(f"   {save_to.name}")


def plot_pr_curves(probs, labels, classes, save_to):
    fig, ax = plt.subplots(figsize=(8, 7))
    for i, cls in enumerate(classes):
        y_true = (labels == i).astype(int)
        if y_true.sum() == 0:
            continue
        prec, rec, _ = precision_recall_curve(y_true, probs[:, i])
        from sklearn.metrics import average_precision_score
        ap = average_precision_score(y_true, probs[:, i])
        color = CLASS_COLORS.get(cls, None)
        ax.plot(rec, prec, lw=2, label=f"{cls.upper()} (AP={ap:.3f})", color=color)
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title("Precision-Recall curves per class")
    ax.legend(loc="lower left")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_to, dpi=150)
    plt.close()
    log.info(f"   {save_to.name}")


def plot_per_class_metrics(probs, labels, classes, save_to):
    preds = probs.argmax(axis=1)
    report = classification_report(labels, preds,
                                    labels=range(len(classes)),
                                    target_names=classes,
                                    output_dict=True, zero_division=0)
    metrics = []
    for cls in classes:
        r = report[cls]
        try:
            y_true = (labels == classes.index(cls)).astype(int)
            auc_v = roc_auc_score(y_true, probs[:, classes.index(cls)])
        except Exception:
            auc_v = float("nan")
        metrics.append({
            "class": cls,
            "precision": r["precision"],
            "recall":    r["recall"],
            "f1":        r["f1-score"],
            "auc":       auc_v,
        })
    df = pd.DataFrame(metrics)
    fig, ax = plt.subplots(figsize=(11, 5))
    x = np.arange(len(classes))
    w = 0.2
    for i, m in enumerate(["precision", "recall", "f1", "auc"]):
        ax.bar(x + (i - 1.5) * w, df[m].fillna(0), w, label=m.upper())
    ax.set_xticks(x)
    ax.set_xticklabels(classes)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Score")
    ax.set_title("Per-class metrics on test set")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_to, dpi=150)
    plt.close()
    log.info(f"   {save_to.name}")
    df.to_csv(REP / "per_class_metrics.csv", index=False)


def plot_calibration(probs, labels, classes, save_to):
    fig, ax = plt.subplots(figsize=(7, 7))
    n_bins = 10
    bin_edges = np.linspace(0, 1, n_bins + 1)

    for i, cls in enumerate(classes):
        y_true = (labels == i).astype(int)
        y_prob = probs[:, i]
        if y_true.sum() == 0:
            continue
        bins = np.digitize(y_prob, bin_edges) - 1
        bins = np.clip(bins, 0, n_bins - 1)
        accs = []
        confs = []
        for b in range(n_bins):
            mask = bins == b
            if mask.sum() < 10:
                continue
            confs.append(y_prob[mask].mean())
            accs.append(y_true[mask].mean())
        if not confs:
            continue
        color = CLASS_COLORS.get(cls, None)
        ax.plot(confs, accs, "o-", label=cls.upper(), color=color, lw=2, markersize=6)
    ax.plot([0, 1], [0, 1], "k--", lw=1, alpha=0.5, label="Perfect calibration")
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Empirical fraction positive")
    ax.set_title("Reliability diagrams (per class)")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_to, dpi=150)
    plt.close()
    log.info(f"   {save_to.name}")


def plot_top_confusions(probs, labels, classes, save_to):
    preds = probs.argmax(axis=1)
    cm = confusion_matrix(labels, preds, labels=range(len(classes)))
    confusions = []
    for i in range(len(classes)):
        for j in range(len(classes)):
            if i != j and cm[i, j] > 0:
                confusions.append((classes[i], classes[j], int(cm[i, j])))
    confusions.sort(key=lambda x: -x[2])
    top = confusions[:10]
    if not top:
        log.warning("   No confusions to plot")
        return

    labels_str = [f"{a}→{b}" for a, b, _ in top]
    counts = [c for _, _, c in top]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(labels_str[::-1], counts[::-1], color="#dc2626")
    ax.set_xlabel("# misclassified")
    ax.set_title("Top 10 confusion pairs (true → predicted)")
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_to, dpi=150)
    plt.close()
    log.info(f"   {save_to.name}")


def plot_training_history(save_to):
    metrics_path = ROOT / "model_out" / "metrics.json"
    if not metrics_path.exists():
        log.warning("   model_out/metrics.json not found — skipping history plot")
        return
    with open(metrics_path) as f:
        m = json.load(f)
    hist = m["history"]
    if not hist:
        return
    epochs = [h["epoch"] for h in hist]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    axes[0].plot(epochs, [h["train_loss"] for h in hist], label="train")
    axes[0].set_title("Loss"); axes[0].set_xlabel("epoch"); axes[0].grid(alpha=0.3)
    axes[1].plot(epochs, [h["train_acc"] for h in hist], label="train")
    axes[1].plot(epochs, [h["val_acc"] for h in hist], label="val")
    axes[1].set_title("Accuracy"); axes[1].set_xlabel("epoch")
    axes[1].legend(); axes[1].grid(alpha=0.3)
    axes[2].plot(epochs, [h["val_f1"] for h in hist], label="val_f1")
    axes[2].plot(epochs, [h["val_auc"] for h in hist], label="val_auc")
    axes[2].set_title("Val macro-F1 / macro-AUC"); axes[2].set_xlabel("epoch")
    axes[2].legend(); axes[2].grid(alpha=0.3)
    plt.suptitle(f"Training history (best at epoch {m['best_epoch']})")
    plt.tight_layout()
    plt.savefig(save_to, dpi=150)
    plt.close()
    log.info(f"   {save_to.name}")


def main():
    log.info("=" * 70)
    log.info("HEMAX_DERMA — comprehensive evaluation")
    log.info("=" * 70)

    with open(PROCESSED / "metadata.json") as f:
        meta = json.load(f)
    classes = meta["classes"]
    device = "cuda" if torch.cuda.is_available() else (
        "mps" if torch.backends.mps.is_available() else "cpu"
    )
    log.info(f"Device: {device}")

    log.info("Loading model...")
    model_path = ROOT / "model_out" / "model.pt"
    model, _ = load_model(model_path, device=device)

    log.info("Loading test set...")
    test_ds = HAM10000Dataset(
        PROCESSED / "test.csv", classes,
        transform=get_eval_transform(meta["image_size"]),
        image_size=meta["image_size"],
    )
    test_loader = DataLoader(test_ds, batch_size=32, shuffle=False, num_workers=2)

    log.info("Running inference on test set...")
    probs, labels, ids = get_predictions(model, test_loader, classes, device)

    preds = probs.argmax(axis=1)
    macro_f1 = f1_score(labels, preds, average="macro")
    accuracy = (preds == labels).mean()
    aucs = []
    for i in range(len(classes)):
        y_true = (labels == i).astype(int)
        if y_true.sum() > 0 and y_true.sum() < len(y_true):
            aucs.append(roc_auc_score(y_true, probs[:, i]))
    macro_auc = np.mean(aucs)

    log.info(f"TEST  acc={accuracy:.4f}  macro_f1={macro_f1:.4f}  macro_auc={macro_auc:.4f}")

    log.info("Generating figures...")
    plot_class_distribution(meta, FIG / "01_class_distribution.png")
    plot_confusion(probs, labels, classes, FIG / "02_confusion_matrix.png")
    plot_roc_curves(probs, labels, classes, FIG / "03_roc_curves.png")
    plot_pr_curves(probs, labels, classes, FIG / "04_pr_curves.png")
    plot_per_class_metrics(probs, labels, classes, FIG / "05_per_class_metrics.png")
    plot_calibration(probs, labels, classes, FIG / "06_calibration.png")
    plot_top_confusions(probs, labels, classes, FIG / "07_top_confusions.png")
    plot_training_history(FIG / "08_training_history.png")

    with open(REP / "test_metrics.json", "w") as f:
        json.dump({
            "accuracy": float(accuracy),
            "macro_f1": float(macro_f1),
            "macro_auc": float(macro_auc),
            "n_test": int(len(labels)),
        }, f, indent=2)

    pd.DataFrame({
        "image_id": ids,
        "true_label_idx": labels,
        "true_label": [classes[i] for i in labels],
        "pred_label_idx": preds,
        "pred_label": [classes[i] for i in preds],
        "correct": (preds == labels),
        **{f"prob_{c}": probs[:, i] for i, c in enumerate(classes)},
    }).to_csv(REP / "test_predictions.csv", index=False)

    log.info("=" * 70)
    log.info("Done — figures in analysis/figures/, reports in analysis/reports/")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
