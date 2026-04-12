from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import torch
import xgboost as xgb
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score, brier_score_loss, log_loss, roc_auc_score,
)

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "engine"))
from engine.model import load_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("advanced")

DATA_DIR = ROOT / "data_processed"
import os as _os
_default_nhanes = ROOT / "data" / "nhanes_master.parquet"
NHANES_FULL = Path(_os.environ.get("NHANES_FULL_PATH", str(_default_nhanes)))
MODEL_PATH = ROOT / "model_out" / "model.pt"
FIG_DIR = ROOT / "analysis" / "figures"
REPORT_DIR = ROOT / "analysis" / "reports"

plt.rcParams.update({
    "figure.dpi": 100, "savefig.dpi": 150, "savefig.bbox": "tight",
    "font.size": 10, "axes.labelsize": 11, "axes.titlesize": 12,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.3, "axes.axisbelow": True,
    "figure.facecolor": "white",
})

TASK_COLORS = {
    "depression_moderate": "#3b82f6", "depression_severe": "#ef4444",
    "sleep_deficiency": "#f59e0b", "daytime_dysfunction": "#8b5cf6",
    "suicidal_ideation": "#ec4899", "suicidal_ideation": "#10b981",
}
TASK_NAMES_EN = {
    "depression_moderate": "Depression (moderate+)", "depression_severe": "Depression (severe)",
    "sleep_deficiency": "Sleep deficiency", "daytime_dysfunction": "Daytime dysfunction",
    "suicidal_ideation": "Suicidal ideation", "suicidal_ideation": "Suicidal ideation",
}



def load_data():
    log.info("Loading data and model...")
    with open(DATA_DIR / "metadata.json") as f:
        meta = json.load(f)
    with open(DATA_DIR / "feature_stats.json") as f:
        feature_stats = json.load(f)

    feature_names = meta["feature_names"]
    target_names = meta["target_names"]
    means = np.array([feature_stats[f]["mean"] for f in feature_names], dtype=np.float32)
    stds = np.array([feature_stats[f]["std"] for f in feature_names], dtype=np.float32)
    stds = np.where(stds < 1e-6, 1.0, stds)

    def prep(df):
        feat_raw = df[feature_names].values.astype(np.float32)
        missing = np.isnan(feat_raw).astype(np.float32)
        feat_filled = np.where(np.isnan(feat_raw), means, feat_raw)
        feats = np.clip((feat_filled - means) / stds, -5.0, 5.0)
        targets_raw = df[target_names].values.astype(np.float32)
        target_mask = (~np.isnan(targets_raw)).astype(np.float32)
        targets = np.where(np.isnan(targets_raw), 0.0, targets_raw)
        return feats, missing, targets, target_mask

    df_train = pd.read_parquet(DATA_DIR / "train.parquet")
    df_val = pd.read_parquet(DATA_DIR / "val.parquet")
    df_test = pd.read_parquet(DATA_DIR / "test.parquet")

    return {
        "feature_names": feature_names,
        "target_names": target_names,
        "means": means, "stds": stds,
        "train": prep(df_train), "val": prep(df_val), "test": prep(df_test),
        "df_train": df_train, "df_val": df_val, "df_test": df_test,
    }


@torch.no_grad()
def predict_nn(model, features, missing, target_names, batch_size=512):
    model.eval()
    n = len(features)
    probs = {t: np.zeros(n, dtype=np.float32) for t in target_names}
    for start in range(0, n, batch_size):
        end = min(start + batch_size, n)
        f = torch.from_numpy(features[start:end])
        m = torch.from_numpy(missing[start:end])
        out = model(f, m, apply_temperature=True)
        for t in target_names:
            probs[t][start:end] = torch.sigmoid(out[t]).cpu().numpy()
    return probs



def plot_decision_curves(probs, targets, masks, target_names, savepath):
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle("Decision Curve Analysis — Clinical Net Benefit",
                 fontsize=15, fontweight="bold", y=1.00)

    summary = {}
    for ax, t in zip(axes.flat, target_names):
        m = masks[t].astype(bool)
        y = targets[t][m]
        p = probs[t][m]
        if y.sum() < 10:
            continue
        prevalence = y.mean()
        n = len(y)

        thresholds = np.linspace(0.01, 0.5, 50)
        nb_model, nb_all, nb_none = [], [], []

        for pt in thresholds:
            pred = (p >= pt).astype(int)
            tp = ((pred == 1) & (y == 1)).sum()
            fp = ((pred == 1) & (y == 0)).sum()
            nb = (tp / n) - (fp / n) * (pt / (1 - pt))
            nb_model.append(nb)

            tp_all = (y == 1).sum()
            fp_all = (y == 0).sum()
            nb_a = (tp_all / n) - (fp_all / n) * (pt / (1 - pt))
            nb_all.append(nb_a)

            nb_none.append(0.0)

        color = TASK_COLORS[t]
        ax.plot(thresholds, nb_model, color=color, lw=2.5, label=f"HEMAX_RISK")
        ax.plot(thresholds, nb_all, color="#888", linestyle="--", lw=1.5, label="Treat all")
        ax.plot(thresholds, nb_none, color="black", linestyle=":", lw=1.2, label="Treat none")

        nb_model_arr = np.array(nb_model)
        nb_all_arr = np.array(nb_all)
        better = (nb_model_arr > nb_all_arr) & (nb_model_arr > 0)
        if better.any():
            ax.fill_between(thresholds, np.maximum(nb_all_arr, 0), nb_model_arr,
                            where=better, alpha=0.2, color=color,
                            label="Model superior region")

        ax.axhline(0, color="black", lw=0.5, alpha=0.5)
        ax.set_xlabel("Decision threshold probability")
        ax.set_ylabel("Net benefit")
        ax.set_title(f"{TASK_NAMES_EN[t]}\nprevalence = {prevalence*100:.1f}%")
        ax.legend(loc="upper right", fontsize=8)
        ax.set_xlim(0, 0.5)

        relative_benefit = nb_model_arr - np.maximum(nb_all_arr, 0)
        if relative_benefit.max() > 0:
            best_thr = thresholds[np.argmax(relative_benefit)]
            best_gain = relative_benefit.max()
            summary[t] = {"best_threshold": float(best_thr),
                          "max_net_benefit_gain": float(best_gain)}

    plt.tight_layout()
    plt.savefig(savepath)
    plt.close()
    log.info(f"  Saved {savepath.name}")
    return summary



def brier_decomposition(y_true, y_prob, n_bins=10):
    n = len(y_true)
    y_mean = y_true.mean()
    uncertainty = y_mean * (1 - y_mean)

    bin_edges = np.quantile(y_prob, np.linspace(0, 1, n_bins + 1))
    bin_edges[0] = 0.0
    bin_edges[-1] = 1.0
    bin_edges = np.unique(bin_edges)

    reliability = 0.0
    resolution = 0.0
    for i in range(len(bin_edges) - 1):
        if i == len(bin_edges) - 2:
            mask = (y_prob >= bin_edges[i]) & (y_prob <= bin_edges[i + 1])
        else:
            mask = (y_prob >= bin_edges[i]) & (y_prob < bin_edges[i + 1])
        if mask.sum() == 0:
            continue
        n_k = mask.sum()
        f_k = y_prob[mask].mean()
        o_k = y_true[mask].mean()
        reliability += (n_k / n) * (f_k - o_k) ** 2
        resolution += (n_k / n) * (o_k - y_mean) ** 2

    brier = reliability - resolution + uncertainty
    return brier, reliability, resolution, uncertainty


def plot_brier_decomposition(probs, targets, masks, target_names, savepath):
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle("Brier Score Decomposition: Reliability − Resolution + Uncertainty",
                 fontsize=14, fontweight="bold", y=1.00)

    rows = []
    for t in target_names:
        m = masks[t].astype(bool)
        y = targets[t][m]
        p = probs[t][m]
        if y.sum() < 10:
            continue
        brier, rel, res, unc = brier_decomposition(y, p)
        rows.append({"task": TASK_NAMES_EN[t], "task_key": t,
                     "Brier": brier, "Reliability": rel,
                     "Resolution": res, "Uncertainty": unc,
                     "color": TASK_COLORS[t]})

    df = pd.DataFrame(rows)

    ax = axes[0]
    x = np.arange(len(df))
    width = 0.6
    ax.bar(x, df["Reliability"], width, color="#ef4444", label="Reliability (miscal., ↓ better)")
    ax.bar(x, -df["Resolution"], width, color="#10b981", label="Resolution (informative, ↑ better)")
    ax.bar(x, df["Uncertainty"], width, bottom=df["Reliability"],
           color="#94a3b8", label="Uncertainty (irreducible)")

    ax.plot(x, df["Brier"], "o", color="black", markersize=10, label="Brier score (sum)")
    for i, b in enumerate(df["Brier"]):
        ax.annotate(f"{b:.3f}", (i, b), textcoords="offset points", xytext=(8, 8), fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(df["task"], rotation=20, ha="right", fontsize=9)
    ax.axhline(0, color="black", lw=0.5)
    ax.set_ylabel("Component value")
    ax.set_title("Decomposition components per task")
    ax.legend(loc="upper right", fontsize=9)

    ax = axes[1]
    df["info_ratio"] = df["Resolution"] / (df["Reliability"] + 0.001)
    bars = ax.barh(df["task"][::-1], df["info_ratio"][::-1],
                   color=[c for c in df["color"][::-1]], alpha=0.85)
    for bar, val in zip(bars, df["info_ratio"][::-1]):
        ax.text(val + 0.5, bar.get_y() + bar.get_height()/2,
                f"{val:.1f}×", va="center", fontsize=10, fontweight="bold")
    ax.set_xlabel("Resolution / Reliability ratio (higher = more informative vs miscalibrated)")
    ax.set_title("Information ratio per task")
    ax.axvline(1.0, color="#888", linestyle="--", lw=1, label="Equal")
    ax.legend()

    plt.tight_layout()
    plt.savefig(savepath)
    plt.close()
    log.info(f"  Saved {savepath.name}")
    return df.drop(columns=["color"]).to_dict(orient="records")



def plot_calibration_regression(probs, targets, masks, target_names, savepath):
    fig, ax = plt.subplots(figsize=(11, 7))

    rows = []
    for t in target_names:
        m = masks[t].astype(bool)
        y = targets[t][m]
        p = np.clip(probs[t][m], 1e-6, 1 - 1e-6)
        if y.sum() < 30:
            continue
        logit_p = np.log(p / (1 - p))
        lr = LogisticRegression(C=1e9, fit_intercept=True, max_iter=1000)
        lr.fit(logit_p.reshape(-1, 1), y)
        slope = float(lr.coef_[0, 0])
        intercept = float(lr.intercept_[0])
        rows.append({"task": TASK_NAMES_EN[t], "task_key": t,
                     "slope": slope, "intercept": intercept,
                     "color": TASK_COLORS[t]})

    df = pd.DataFrame(rows)

    for _, row in df.iterrows():
        ax.scatter(row["slope"], row["intercept"], s=200, color=row["color"],
                   edgecolors="black", linewidth=1.5, zorder=3)
        ax.annotate(row["task"], (row["slope"], row["intercept"]),
                    textcoords="offset points", xytext=(10, 8), fontsize=10)

    ax.scatter([1], [0], marker="*", s=400, color="gold", edgecolors="black",
               linewidth=1.5, zorder=4, label="Perfect calibration (slope=1, intercept=0)")

    ax.axhline(0, color="#888", linestyle="--", lw=1, alpha=0.6)
    ax.axvline(1, color="#888", linestyle="--", lw=1, alpha=0.6)

    ax.text(1.5, 1.5, "Slope > 1\n(under-confident)", fontsize=9, color="#666",
            ha="center", alpha=0.7)
    ax.text(0.5, -1.5, "Slope < 1\n(over-confident)", fontsize=9, color="#666",
            ha="center", alpha=0.7)

    ax.set_xlabel("Calibration slope (1 = perfect)")
    ax.set_ylabel("Calibration intercept (0 = perfect)")
    ax.set_title("Calibration Regression: Formal Calibration Metrics per Task\n"
                 "(further from gold star = more miscalibrated)",
                 fontsize=13, fontweight="bold")
    ax.legend(loc="upper left", fontsize=9)
    ax.set_aspect("equal")

    plt.tight_layout()
    plt.savefig(savepath)
    plt.close()
    log.info(f"  Saved {savepath.name}")
    return df.drop(columns=["color"]).to_dict(orient="records")



def fit_baselines(data, target_names):
    X_train, _, y_train, mask_train = data["train"]
    X_test, _, y_test, mask_test = data["test"]

    results = {"lr": {}, "xgb": {}}
    for i, t in enumerate(target_names):
        log.info(f"  Fitting baselines for {t}...")
        m_train = mask_train[:, i].astype(bool)
        m_test = mask_test[:, i].astype(bool)
        y_tr = y_train[m_train, i]
        y_te = y_test[m_test, i]

        n_pos = y_tr.sum()
        n_neg = len(y_tr) - n_pos
        scale_pos_weight = n_neg / max(n_pos, 1)

        lr = LogisticRegression(max_iter=2000, class_weight="balanced", C=0.1)
        lr.fit(X_train[m_train], y_tr)
        p_lr = lr.predict_proba(X_test[m_test])[:, 1]
        auc_lr = roc_auc_score(y_te, p_lr) if y_te.sum() > 0 else np.nan
        auprc_lr = average_precision_score(y_te, p_lr) if y_te.sum() > 0 else np.nan
        results["lr"][t] = {"auc": float(auc_lr), "auprc": float(auprc_lr)}

        xgb_model = xgb.XGBClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.05,
            scale_pos_weight=scale_pos_weight, eval_metric="auc",
            n_jobs=1, random_state=42, verbosity=0,
        )
        xgb_model.fit(X_train[m_train], y_tr)
        p_xgb = xgb_model.predict_proba(X_test[m_test])[:, 1]
        auc_xgb = roc_auc_score(y_te, p_xgb) if y_te.sum() > 0 else np.nan
        auprc_xgb = average_precision_score(y_te, p_xgb) if y_te.sum() > 0 else np.nan
        results["xgb"][t] = {"auc": float(auc_xgb), "auprc": float(auprc_xgb)}

    return results


def plot_model_comparison(data, target_names, nn_probs_test, savepath):
    log.info("Fitting baseline models (LR + XGBoost) — this takes ~1 minute...")
    baselines = fit_baselines(data, target_names)

    _, _, y_test, mask_test = data["test"]
    nn_results = {}
    for i, t in enumerate(target_names):
        m = mask_test[:, i].astype(bool)
        y = y_test[m, i]
        p = nn_probs_test[t][m]
        nn_results[t] = {"auc": roc_auc_score(y, p), "auprc": average_precision_score(y, p)}

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle("HEMAX_RISK (NN) vs Logistic Regression vs XGBoost",
                 fontsize=14, fontweight="bold", y=1.00)

    x = np.arange(len(target_names))
    width = 0.27

    ax = axes[0]
    aucs_lr = [baselines["lr"][t]["auc"] for t in target_names]
    aucs_xgb = [baselines["xgb"][t]["auc"] for t in target_names]
    aucs_nn = [nn_results[t]["auc"] for t in target_names]

    ax.bar(x - width, aucs_lr, width, label="Logistic Regression", color="#94a3b8")
    ax.bar(x, aucs_xgb, width, label="XGBoost", color="#f59e0b")
    ax.bar(x + width, aucs_nn, width, label="HEMAX_RISK (Neural Network)", color="#3b82f6")

    for i, (lr_v, xgb_v, nn_v) in enumerate(zip(aucs_lr, aucs_xgb, aucs_nn)):
        ax.text(i - width, lr_v + 0.005, f"{lr_v:.3f}", ha="center", fontsize=8)
        ax.text(i, xgb_v + 0.005, f"{xgb_v:.3f}", ha="center", fontsize=8)
        ax.text(i + width, nn_v + 0.005, f"{nn_v:.3f}", ha="center", fontsize=8, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels([TASK_NAMES_EN[t] for t in target_names], rotation=20, ha="right", fontsize=9)
    ax.set_ylabel("ROC-AUC")
    ax.set_title("Discrimination (AUC)")
    ax.legend(loc="lower right", fontsize=9)
    ax.set_ylim(0.5, 1.02)

    ax = axes[1]
    auprcs_lr = [baselines["lr"][t]["auprc"] for t in target_names]
    auprcs_xgb = [baselines["xgb"][t]["auprc"] for t in target_names]
    auprcs_nn = [nn_results[t]["auprc"] for t in target_names]

    ax.bar(x - width, auprcs_lr, width, label="Logistic Regression", color="#94a3b8")
    ax.bar(x, auprcs_xgb, width, label="XGBoost", color="#f59e0b")
    ax.bar(x + width, auprcs_nn, width, label="HEMAX_RISK (Neural Network)", color="#3b82f6")

    ax.set_xticks(x)
    ax.set_xticklabels([TASK_NAMES_EN[t] for t in target_names], rotation=20, ha="right", fontsize=9)
    ax.set_ylabel("AUPRC")
    ax.set_title("Precision-Recall (AUPRC)")
    ax.legend(loc="upper right", fontsize=9)

    plt.tight_layout()
    plt.savefig(savepath)
    plt.close()
    log.info(f"  Saved {savepath.name}")

    return {"nn": nn_results, "lr": baselines["lr"], "xgb": baselines["xgb"]}



def compute_permutation_importance(model, features, missing, targets, masks,
                                    target_names, feature_names, n_repeats=3, sample_size=2000):
    log.info("Computing permutation importance (this takes a couple minutes)...")
    rng = np.random.RandomState(42)

    n = min(sample_size, len(features))
    idx = rng.choice(len(features), size=n, replace=False)
    feats_sub = features[idx].copy()
    miss_sub = missing[idx].copy()

    baseline_probs = predict_nn(model, feats_sub, miss_sub, target_names)
    baseline_aucs = {}
    for i, t in enumerate(target_names):
        m = masks[idx][:, i].astype(bool)
        y = targets[idx][m, i]
        p = baseline_probs[t][m]
        if y.sum() > 5:
            baseline_aucs[t] = roc_auc_score(y, p)

    importance = {t: np.zeros(len(feature_names)) for t in target_names}

    for j, fname in enumerate(feature_names):
        for rep in range(n_repeats):
            feats_perm = feats_sub.copy()
            miss_perm = miss_sub.copy()
            shuffled = rng.permutation(feats_sub[:, j])
            feats_perm[:, j] = shuffled
            miss_perm[:, j] = rng.permutation(miss_sub[:, j])
            probs_perm = predict_nn(model, feats_perm, miss_perm, target_names)
            for i, t in enumerate(target_names):
                if t not in baseline_aucs:
                    continue
                m = masks[idx][:, i].astype(bool)
                y = targets[idx][m, i]
                p = probs_perm[t][m]
                try:
                    auc_perm = roc_auc_score(y, p)
                    importance[t][j] += (baseline_aucs[t] - auc_perm) / n_repeats
                except ValueError:
                    pass

        if (j + 1) % 10 == 0:
            log.info(f"    Permuted {j+1}/{len(feature_names)} features")

    return importance, baseline_aucs


def plot_permutation_importance(importance, feature_names, target_names, savepath, top_k=15):
    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    fig.suptitle(f"Permutation Importance — Top {top_k} per Task\n"
                 "(drop in AUC when feature is randomly shuffled)",
                 fontsize=14, fontweight="bold", y=1.00)

    for ax, t in zip(axes.flat, target_names):
        imp = importance[t]
        order = np.argsort(-imp)[:top_k]
        labels = [feature_names[i] for i in order]
        values = imp[order]

        colors = [TASK_COLORS[t] if v > 0 else "#cbd5e1" for v in values[::-1]]
        ax.barh(np.arange(top_k), values[::-1], color=colors, alpha=0.85)
        ax.set_yticks(np.arange(top_k))
        ax.set_yticklabels(labels[::-1], fontsize=9)
        ax.set_xlabel("ΔAUC when shuffled")
        ax.set_title(f"{TASK_NAMES_EN[t]}")
        ax.axvline(0, color="black", lw=0.5)

    plt.tight_layout()
    plt.savefig(savepath)
    plt.close()
    log.info(f"  Saved {savepath.name}")



def plot_learning_curves(data, target_names, savepath):
    log.info("Computing learning curves (training XGBoost at 5 sample sizes)...")
    X_train, _, y_train, mask_train = data["train"]
    X_test, _, y_test, mask_test = data["test"]

    fractions = [0.05, 0.10, 0.25, 0.50, 1.00]
    rng = np.random.RandomState(42)

    fig, ax = plt.subplots(figsize=(11, 7))

    summary = {}
    for t_idx, t in enumerate(target_names):
        m_tr = mask_train[:, t_idx].astype(bool)
        m_te = mask_test[:, t_idx].astype(bool)
        X_tr_full = X_train[m_tr]
        y_tr_full = y_train[m_tr, t_idx]
        X_te = X_test[m_te]
        y_te = y_test[m_te, t_idx]

        n_tr = len(X_tr_full)
        aucs = []
        sizes = []
        for frac in fractions:
            n_sub = int(frac * n_tr)
            idx = rng.choice(n_tr, size=n_sub, replace=False)
            scale_pos = (y_tr_full[idx] == 0).sum() / max((y_tr_full[idx] == 1).sum(), 1)
            xgb_model = xgb.XGBClassifier(
                n_estimators=100, max_depth=4, learning_rate=0.1,
                scale_pos_weight=scale_pos, n_jobs=1, random_state=42, verbosity=0,
            )
            try:
                xgb_model.fit(X_tr_full[idx], y_tr_full[idx])
                p = xgb_model.predict_proba(X_te)[:, 1]
                aucs.append(roc_auc_score(y_te, p))
                sizes.append(n_sub)
            except Exception as e:
                log.warning(f"    Skipping {t} at frac={frac}: {e}")

        if aucs:
            ax.plot(sizes, aucs, "o-", color=TASK_COLORS[t], lw=2, label=TASK_NAMES_EN[t],
                    markersize=8)
            summary[t] = {"sizes": sizes, "aucs": aucs}

    ax.set_xscale("log")
    ax.set_xlabel("Training set size (log scale)")
    ax.set_ylabel("Test AUC")
    ax.set_title("Learning Curves: AUC vs Training Set Size (XGBoost baseline)\n"
                 "Saturation suggests more data won't help further",
                 fontsize=13, fontweight="bold")
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(True, which="both", alpha=0.3)

    plt.tight_layout()
    plt.savefig(savepath)
    plt.close()
    log.info(f"  Saved {savepath.name}")
    return summary



def plot_multitask_correlation(probs, targets, masks, target_names, savepath):
    fig, axes = plt.subplots(1, 2, figsize=(15, 7))
    fig.suptitle("Multi-Task Coherence: Predicted Probability and Outcome Correlations",
                 fontsize=14, fontweight="bold", y=1.00)

    n = len(probs[target_names[0]])
    pred_matrix = np.zeros((n, len(target_names)))
    for i, t in enumerate(target_names):
        pred_matrix[:, i] = probs[t]
    corr_pred = np.corrcoef(pred_matrix.T)

    out_matrix_pairs = np.zeros((len(target_names), len(target_names)))
    for i, t1 in enumerate(target_names):
        for j, t2 in enumerate(target_names):
            m = masks[t1].astype(bool) & masks[t2].astype(bool)
            if m.sum() < 10:
                out_matrix_pairs[i, j] = np.nan
            else:
                out_matrix_pairs[i, j] = np.corrcoef(targets[t1][m], targets[t2][m])[0, 1]

    labels = [TASK_NAMES_EN[t] for t in target_names]
    sns.heatmap(corr_pred, annot=True, fmt=".2f", cmap="RdYlBu_r", center=0,
                vmin=-1, vmax=1, xticklabels=labels, yticklabels=labels,
                ax=axes[0], cbar_kws={"label": "Pearson r"},
                annot_kws={"fontsize": 10})
    axes[0].set_title("Predicted probability correlations\n(model-level)")

    sns.heatmap(out_matrix_pairs, annot=True, fmt=".2f", cmap="RdYlBu_r", center=0,
                vmin=-1, vmax=1, xticklabels=labels, yticklabels=labels,
                ax=axes[1], cbar_kws={"label": "Pearson r"},
                annot_kws={"fontsize": 10})
    axes[1].set_title("Actual outcome correlations\n(ground truth)")

    for ax in axes:
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    plt.tight_layout()
    plt.savefig(savepath)
    plt.close()
    log.info(f"  Saved {savepath.name}")

    mask_lower = np.tri(len(target_names), k=-1, dtype=bool)
    valid_lower = ~np.isnan(out_matrix_pairs[mask_lower])
    if valid_lower.any():
        coherence = np.corrcoef(corr_pred[mask_lower][valid_lower],
                                 out_matrix_pairs[mask_lower][valid_lower])[0, 1]
    else:
        coherence = np.nan

    return {"pred_corr": corr_pred.tolist(),
            "outcome_corr": np.where(np.isnan(out_matrix_pairs), None, out_matrix_pairs).tolist(),
            "coherence_score": float(coherence) if not np.isnan(coherence) else None}



def plot_temporal_validation(model, target_names, feature_names, means, stds, savepath):
    log.info("Loading full NHANES master for temporal validation...")
    df_full = pd.read_parquet(NHANES_FULL)
    df_full = df_full[df_full["age_years"].notna() & (df_full["age_years"] >= 18)]

    cycles = sorted(df_full["cycle"].unique())
    log.info(f"  Cycles: {cycles}")

    cycle_results = {t: [] for t in target_names}
    cycle_n = {t: [] for t in target_names}

    for cycle in cycles:
        sub = df_full[df_full["cycle"] == cycle].copy()
        if len(sub) < 100:
            continue

        missing_cols = [c for c in feature_names if c not in sub.columns]
        if missing_cols:
            log.warning(f"    Cycle {cycle} missing cols: {missing_cols[:3]}... skipping")
            continue

        feat_raw = sub[feature_names].values.astype(np.float32)
        missing = np.isnan(feat_raw).astype(np.float32)
        feat_filled = np.where(np.isnan(feat_raw), means, feat_raw)
        feats = np.clip((feat_filled - means) / stds, -5.0, 5.0)

        probs = predict_nn(model, feats, missing, target_names)

        for t in target_names:
            if t not in sub.columns:
                continue
            y_raw = sub[t].values.astype(np.float32)
            m = ~np.isnan(y_raw)
            y = y_raw[m]
            p = probs[t][m]
            if y.sum() < 10 or y.sum() == len(y):
                continue
            try:
                auc = roc_auc_score(y, p)
                cycle_results[t].append(auc)
                cycle_n[t].append(int(m.sum()))
            except ValueError:
                pass

    cycle_labels = [c for c in cycles if any(len(cycle_results[t]) > 0 for t in target_names)]
    valid_cycles_per_task = {}
    for t in target_names:
        if len(cycle_results[t]) == len(cycles):
            valid_cycles_per_task[t] = cycles
        else:
            valid = []
            for c in cycles:
                if any(c in str(cl) for cl in cycle_results[t]):
                    valid.append(c)

    fig, ax = plt.subplots(figsize=(13, 7))

    summary = {}
    for t in target_names:
        if not cycle_results[t]:
            continue
        n_results = len(cycle_results[t])
        x_pos = np.arange(n_results)
        ax.plot(x_pos, cycle_results[t], "o-", color=TASK_COLORS[t], lw=2,
                label=TASK_NAMES_EN[t], markersize=8)
        summary[t] = {"cycles": cycles[:n_results],
                      "aucs": cycle_results[t],
                      "ns": cycle_n[t]}

    n_x = max(len(v["cycles"]) for v in summary.values()) if summary else 0
    if n_x > 0:
        ax.set_xticks(range(n_x))
        ax.set_xticklabels(cycles[:n_x], rotation=30, ha="right", fontsize=9)

    ax.set_xlabel("NHANES cycle")
    ax.set_ylabel("ROC-AUC")
    ax.set_title("Temporal Validation: Model Performance Across NHANES Cycles 1999-2023\n"
                 "(stable performance suggests generalization across time/health policy changes)",
                 fontsize=13, fontweight="bold")
    ax.legend(loc="lower left", fontsize=9, ncol=2)
    ax.grid(alpha=0.3)
    ax.set_ylim(0.55, 1.0)

    plt.tight_layout()
    plt.savefig(savepath)
    plt.close()
    log.info(f"  Saved {savepath.name}")

    return summary



def main():
    log.info("=" * 70)
    log.info("HEMAX_RISK — Phase 2 Advanced Analyses")
    log.info("=" * 70)

    data = load_data()
    target_names = data["target_names"]

    log.info("Loading model...")
    model, _ = load_model(MODEL_PATH)

    X_test, miss_test, y_test, mask_test = data["test"]
    nn_probs_test = predict_nn(model, X_test, miss_test, target_names)
    targets_test = {t: y_test[:, i] for i, t in enumerate(target_names)}
    masks_test = {t: mask_test[:, i] for i, t in enumerate(target_names)}

    metrics = {}

    log.info("\n[13] Decision Curve Analysis...")
    metrics["decision_curves"] = plot_decision_curves(
        nn_probs_test, targets_test, masks_test, target_names,
        FIG_DIR / "13_decision_curves.png"
    )

    log.info("\n[14] Brier score decomposition...")
    metrics["brier_decomp"] = plot_brier_decomposition(
        nn_probs_test, targets_test, masks_test, target_names,
        FIG_DIR / "14_brier_decomposition.png"
    )

    log.info("\n[15] Calibration regression (slope + intercept)...")
    metrics["calibration_regression"] = plot_calibration_regression(
        nn_probs_test, targets_test, masks_test, target_names,
        FIG_DIR / "15_calibration_regression.png"
    )

    log.info("\n[16] Model comparison: NN vs LR vs XGBoost...")
    metrics["model_comparison"] = plot_model_comparison(
        data, target_names, nn_probs_test,
        FIG_DIR / "16_model_comparison.png"
    )

    log.info("\n[17] Permutation feature importance...")
    perm_imp, baseline_aucs = compute_permutation_importance(
        model, X_test, miss_test, y_test, mask_test,
        target_names, data["feature_names"], n_repeats=3, sample_size=2000,
    )
    plot_permutation_importance(
        perm_imp, data["feature_names"], target_names,
        FIG_DIR / "17_permutation_importance.png", top_k=15
    )
    metrics["permutation_importance"] = {
        t: {"top_features": [(data["feature_names"][i], float(perm_imp[t][i]))
                              for i in np.argsort(-perm_imp[t])[:10]]}
        for t in target_names
    }

    log.info("\n[18] Learning curves...")
    metrics["learning_curves"] = plot_learning_curves(
        data, target_names, FIG_DIR / "18_learning_curves.png"
    )

    log.info("\n[19] Multi-task correlation heatmap...")
    metrics["multitask_corr"] = plot_multitask_correlation(
        nn_probs_test, targets_test, masks_test, target_names,
        FIG_DIR / "19_multitask_correlation.png"
    )

    with open(REPORT_DIR / "advanced_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    log.info(f"\nSaved advanced_metrics.json")

    log.info("\n" + "=" * 70)
    log.info("ALL 7 ADVANCED FIGURES DONE — see analysis/figures/13-19*.png")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
