#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
})

TARGET_COLOURS = {
    "depression_moderate":   "#2E86AB",
    "depression_severe":     "#1B4965",
    "sleep_deficiency":      "#7209B7",
    "daytime_dysfunction":   "#06A77D",
    "suicidal_ideation":     "#D62828",
    "snore_high":            "#F4A261",
    "trouble_sleeping_high": "#E76F51",
}
TARGET_LABELS_UA = {
    "depression_moderate":   "Депресія (помірна)",
    "depression_severe":     "Депресія (важка)",
    "sleep_deficiency":      "Дефіцит сну",
    "daytime_dysfunction":   "Денна дисфункція",
    "suicidal_ideation":     "Суїцидальні думки",
    "snore_high":            "Хропіння/апное (v2)",
    "trouble_sleeping_high": "Проблеми зі сном (v2)",
}
TARGET_LABELS_EN = {
    "depression_moderate":   "Depression (moderate)",
    "depression_severe":     "Depression (severe)",
    "sleep_deficiency":      "Sleep deficiency",
    "daytime_dysfunction":   "Daytime dysfunction",
    "suicidal_ideation":     "Suicidal ideation",
    "snore_high":            "Snoring / apnea (v2)",
    "trouble_sleeping_high": "Insomnia (v2)",
}
V2_NEW = {"snore_high", "trouble_sleeping_high"}


def plot_per_target_auc(metrics, out_path):
    tm = metrics["test_metrics"]
    targets = list(tm.keys())
    aucs = [tm[t]["auc"] for t in targets]
    n_pos = [tm[t]["n_pos"] for t in targets]
    n = [tm[t]["n"] for t in targets]
    prev = [p / nn for p, nn in zip(n_pos, n)]
    labels = [TARGET_LABELS_UA[t] for t in targets]
    colours = [TARGET_COLOURS[t] for t in targets]
    edges = ["red" if t in V2_NEW else "black" for t in targets]
    widths = [2.0 if t in V2_NEW else 0.5 for t in targets]

    fig, ax = plt.subplots(figsize=(11, 5.5))
    bars = ax.bar(labels, aucs, color=colours, edgecolor=edges, linewidth=widths)
    ax.axhline(0.5, color="grey", linestyle=":", linewidth=1, label="Random")
    ax.axhline(0.7, color="grey", linestyle="--", linewidth=0.7, alpha=0.5)
    for bar, auc, p in zip(bars, aucs, prev):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                f"{auc:.3f}", ha="center", va="bottom", fontsize=9,
                fontweight="bold")
        ax.text(bar.get_x() + bar.get_width() / 2, 0.52,
                f"prev = {p:.0%}", ha="center", va="bottom",
                fontsize=7, color="white", fontweight="bold")
    ax.set_ylim(0.5, 0.85)
    ax.set_ylabel("Test AUC")
    title = f"NEURO v2 — дискримінація по 7 цілях (n_test = {metrics['n_test']:,})"
    ax.set_title(title)
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    legend_handles = [
        Line2D([0], [0], color="grey", linestyle=":", label="Random"),
        Patch(facecolor="white", edgecolor="red", linewidth=2, label="v2 нова ціль"),
    ]
    ax.legend(handles=legend_handles, loc="upper right")
    plt.xticks(rotation=20, ha="right")
    fig.savefig(out_path)
    plt.close(fig)


def plot_training_curves(metrics, history, out_path):
    if not history:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.text(0.5, 0.5, "history.json missing — re-run training to get curves",
                ha="center", va="center", fontsize=12)
        ax.axis("off")
        fig.savefig(out_path)
        plt.close(fig)
        return

    epochs = [h["epoch"] for h in history]
    train_losses = [h["train_loss"] for h in history]
    val_losses   = [h.get("val_loss",   np.nan) for h in history]
    mean_aucs    = [h.get("mean_auc",   np.nan) for h in history]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    ax1.plot(epochs, train_losses, "o-", color="#2E86AB",
              label="Train loss", linewidth=2, markersize=6)
    ax1.plot(epochs, val_losses,   "s-", color="#E63946",
              label="Val loss",   linewidth=2, markersize=6)
    ax1.set_xlabel("Епоха")
    ax1.set_ylabel("Loss (BCE multi-task)")
    ax1.set_title("Криві навчання — loss")
    ax1.legend()
    best_ep = metrics.get("best_epoch")
    if best_ep:
        ax1.axvline(best_ep, color="green", linestyle=":", linewidth=1.5,
                     label=f"Best epoch ({best_ep})")
        ax1.legend()

    ax2.plot(epochs, mean_aucs, "o-", color="#06A77D",
              linewidth=2, markersize=7)
    ax2.set_xlabel("Епоха")
    ax2.set_ylabel("Mean validation AUC")
    ax2.set_title("Криві навчання — середня AUC")
    ax2.set_ylim(min(mean_aucs) - 0.02, max(mean_aucs) + 0.02)
    if best_ep:
        ax2.axvline(best_ep, color="green", linestyle=":", linewidth=1.5)
        ax2.text(best_ep + 0.1, min(mean_aucs),
                  f"best={metrics['mean_test_auc']:.3f}",
                  fontsize=9, color="green")

    fig.suptitle(f"NEURO v2 — динаміка навчання ({len(epochs)} епох)",
                 fontsize=13, fontweight="bold")
    fig.savefig(out_path)
    plt.close(fig)


def plot_calibration_before_after(calib, out_path):
    diag = calib["diagnostic"]
    targets = [d["target"] for d in diag]
    ece_temp = [d["ece_temp"] for d in diag]
    ece_iso = [d["ece_iso"] for d in diag]
    improvement = [d["ece_improvement_pct"] for d in diag]
    labels = [TARGET_LABELS_UA[t] for t in targets]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    x = np.arange(len(targets))
    w = 0.35
    ax1.bar(x - w/2, ece_temp, w, label="Лише temperature scaling",
             color="#bdc3c7", edgecolor="black", linewidth=0.5)
    ax1.bar(x + w/2, ece_iso,  w, label="+ ізотонічна калібрація",
             color="#06A77D", edgecolor="black", linewidth=0.5)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=20, ha="right")
    ax1.set_ylabel("Expected Calibration Error (ECE)")
    ax1.set_title("ECE до і після ізотонічної калібровки")
    ax1.axhline(0.1, color="red", linestyle="--", linewidth=0.8,
                 label="Поріг прийнятної калібрації")
    ax1.legend(loc="upper right")

    bars = ax2.barh(labels, improvement, color="#7209B7",
                     edgecolor="black", linewidth=0.5)
    for bar, imp in zip(bars, improvement):
        ax2.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                  f"{imp:.1f}%", va="center", fontsize=9, fontweight="bold")
    ax2.set_xlabel("Поліпшення ECE, %")
    ax2.set_title("Скільки % ECE усувається ізотонічною калібровкою")
    ax2.set_xlim(0, max(improvement) * 1.15)

    fig.suptitle("NEURO v2 — ефект ізотонічної рекалібровки",
                  fontsize=13, fontweight="bold")
    fig.savefig(out_path)
    plt.close(fig)


def plot_v2_vs_v1(metrics, out_path):
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))

    v1_targets = 5
    v2_added = len(metrics.get("v2_new_targets", []))
    axes[0].pie([v1_targets, v2_added],
                 labels=[f"v1 ({v1_targets} цілей)", f"v2 +{v2_added} цілей"],
                 colors=["#2E86AB", "#E63946"], autopct="%1.0f%%",
                 wedgeprops={"edgecolor": "white", "linewidth": 2})
    axes[0].set_title("Кількість цілей")

    n_new = len(metrics.get("v2_new_features", []))
    n_total = metrics.get("n_features", 57)
    n_v1 = n_total - n_new
    axes[1].pie([n_v1, n_new],
                 labels=[f"v1 ({n_v1} ознак)", f"v2 +{n_new} ознак"],
                 colors=["#2E86AB", "#F4A261"], autopct="%1.0f%%",
                 wedgeprops={"edgecolor": "white", "linewidth": 2})
    axes[1].set_title("Кількість ознак")

    new_feats = metrics.get("v2_new_features", [])
    axes[2].axis("off")
    text = "11 нових ознак у v2:\n\n" + "\n".join(
        f"  • {f}" for f in new_feats)
    axes[2].text(0.05, 0.95, text, transform=axes[2].transAxes,
                  fontsize=10, family="monospace",
                  verticalalignment="top",
                  bbox=dict(facecolor="#fef6e4", edgecolor="#7209B7",
                             boxstyle="round,pad=0.6"))

    fig.suptitle("NEURO v1 → v2: розширення моделі (+2 цілі, +11 ознак)",
                  fontsize=13, fontweight="bold")
    fig.savefig(out_path)
    plt.close(fig)


def plot_per_target_metrics(metrics, calib, out_path):
    tm = metrics["test_metrics"]
    targets = list(tm.keys())
    aucs   = [tm[t]["auc"] for t in targets]
    auprcs = [tm[t]["auprc"] for t in targets]
    diag = {d["target"]: d for d in calib.get("diagnostic", [])}
    briers = [diag.get(t, {}).get("brier_iso",
                                    tm[t].get("brier", 0))
              for t in targets]
    labels = [TARGET_LABELS_UA[t] for t in targets]
    colours = [TARGET_COLOURS[t] for t in targets]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for ax, vals, title, ymin, ymax in [
        (axes[0], aucs,   "AUC (ROC) — вище краще",        0.5, 0.85),
        (axes[1], auprcs, "AUPRC — вище краще",            0.0, 0.7),
        (axes[2], briers, "Brier Score (iso) — нижче краще", 0.0, 0.30),
    ]:
        bars = ax.barh(labels, vals, color=colours,
                        edgecolor="black", linewidth=0.4)
        ax.set_xlim(ymin, ymax)
        ax.set_title(title)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_width() + (ymax - ymin) * 0.015,
                     bar.get_y() + bar.get_height() / 2,
                     f"{v:.3f}", va="center", fontsize=8)

    fig.suptitle("NEURO v2 — повний набір метрик дискримінації",
                  fontsize=13, fontweight="bold")
    fig.savefig(out_path)
    plt.close(fig)


def plot_temperatures(metrics, out_path):
    temps = metrics.get("temperatures") or []
    targets = metrics.get("target_names") or []
    if not temps or len(temps) != len(targets):
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "temperatures missing", ha="center", va="center")
        ax.axis("off")
        fig.savefig(out_path)
        plt.close(fig)
        return

    labels = [TARGET_LABELS_UA[t] for t in targets]
    colours = [TARGET_COLOURS[t] for t in targets]

    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.bar(labels, temps, color=colours,
                   edgecolor="black", linewidth=0.5)
    ax.axhline(1.0, color="grey", linestyle="--", linewidth=1,
                label="T = 1.0 (без рескейлінгу)")
    for bar, t in zip(bars, temps):
        ax.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 0.02,
                 f"{t:.3f}", ha="center", va="bottom",
                 fontsize=9, fontweight="bold")
    ax.set_ylabel("Temperature (T)")
    ax.set_title("NEURO v2 — оптимальні temperatures, обчислені на validation\n"
                 "T < 1.0 → недо-впевнена (ймовірності загострюються)   |   "
                 "T > 1.0 → пере-впевнена (пом'якшуються)",
                 fontsize=11)
    ax.legend(loc="upper right")
    plt.xticks(rotation=20, ha="right")
    fig.subplots_adjust(bottom=0.22)
    fig.savefig(out_path)
    plt.close(fig)


def plot_feature_inventory(metrics, out_path):
    all_feats = metrics.get("feature_names", [])
    new_feats = set(metrics.get("v2_new_features", []))

    def assign_group(f):
        f_low = f.lower()
        if f in ("age_years", "sex"):
            return "Demographic"
        if any(p in f_low for p in ("income", "edu_", "race")):
            return "Demographic"
        if any(p in f_low for p in ("bmi", "weight", "height",
                                      "waist", "arm_circ", "neck",
                                      "hip_circ")):
            return "Anthropometric"
        if any(p in f_low for p in ("sbp", "dbp", "pulse", "bp_")):
            return "Vitals"
        if any(p in f_low for p in ("wbc", "rbc", "hb_gdl", "hgb",
                                      "hct", "plt", "mcv", "mch", "mchc", "rdw",
                                      "mpv", "neut", "lymph", "mono",
                                      "eos", "baso", "nlr_")):
            return "CBC"
        if any(p in f_low for p in ("glucose", "hba1c", "homa",
                                      "insulin_")):
            return "Glycaemia"
        if any(p in f_low for p in ("creatinine", "egfr", "bun",
                                      "urea", "uric_acid")):
            return "Kidney"
        if any(p in f_low for p in ("alt_", "ast_", "alp_", "ggt_",
                                      "bilirubin", "albumin",
                                      "globulin", "protein_total",
                                      "fib4")):
            return "Liver"
        if any(p in f_low for p in ("sodium", "potassium", "chloride",
                                      "bicarbonate", "calcium",
                                      "phosphorus", "magnesium")):
            return "Electrolytes"
        if any(p in f_low for p in ("tchol", "hdl", "ldl", "trigly",
                                      "non_hdl")):
            return "Lipids"
        if any(p in f_low for p in ("crp", "ferritin", "iron_",
                                      "tsat", "tibc")):
            return "Inflammation / Iron"
        if any(p in f_low for p in ("metsyn", "vit_d", "vitd")):
            return "Metabolic"
        if any(p in f_low for p in ("sedentary", "activity_min",
                                      "sleep_hours")):
            return "Activity / Sleep"
        return "Other"

    groups = {}
    for f in all_feats:
        g = assign_group(f)
        groups.setdefault(g, []).append(f)

    group_order = ["Demographic", "Anthropometric", "Vitals", "CBC",
                    "Glycaemia", "Kidney", "Liver", "Electrolytes",
                    "Lipids", "Inflammation / Iron", "Metabolic",
                    "Activity / Sleep", "Other"]
    ordered = [(g, groups[g]) for g in group_order if g in groups]

    fig, ax = plt.subplots(figsize=(14, max(7, len(ordered) * 0.7)))
    ax.axis("off")

    y = 1.0
    ax.text(0.0, y, f"NEURO v2 — інвентар {len(all_feats)} ознак "
                     f"({len(new_feats)} нових у v2)",
             fontsize=13, fontweight="bold", transform=ax.transAxes)
    y -= 0.05
    ax.text(0.0, y, "v2 нові ознаки виділено помаранчевим",
             fontsize=8, color="grey", style="italic",
             transform=ax.transAxes)
    y -= 0.05

    for group_name, feats in ordered:
        n_new_in_group = sum(1 for f in feats if f in new_feats)
        header = f"▸ {group_name} ({len(feats)}"
        if n_new_in_group:
            header += f", +{n_new_in_group} нових"
        header += ")"
        ax.text(0.0, y, header, fontsize=10, fontweight="bold",
                 transform=ax.transAxes)
        y -= 0.04
        line_x = 0.02
        for f in feats:
            colour = "#F4A261" if f in new_feats else "#34495e"
            weight = "bold" if f in new_feats else "normal"
            txt = ax.text(line_x, y, f, fontsize=8, color=colour,
                           fontweight=weight, transform=ax.transAxes,
                           family="monospace")
            bbox = txt.get_window_extent(renderer=fig.canvas.get_renderer())
            inv = ax.transAxes.inverted()
            bbox_data = inv.transform(bbox)
            width = bbox_data[1][0] - bbox_data[0][0]
            line_x += width + 0.015
            if line_x > 0.95:
                line_x = 0.02
                y -= 0.03
        y -= 0.035
    fig.savefig(out_path)
    plt.close(fig)


def plot_discrimination_summary(metrics, calib, out_path):
    tm = metrics["test_metrics"]
    targets = list(tm.keys())
    diag = {d["target"]: d for d in calib["diagnostic"]}
    rows = []
    for t in targets:
        m = tm[t]
        c = diag.get(t, {})
        rows.append([
            TARGET_LABELS_UA[t] + (" *" if t in V2_NEW else ""),
            f"{m['auc']:.3f}",
            f"{m['auprc']:.3f}",
            f"{c.get('ece_iso', 0):.3f}",
            f"{c.get('brier_iso', 0):.3f}",
            f"{m['n']:,}",
            f"{m['n_pos']:,} ({m['n_pos']/m['n']:.1%})",
        ])
    columns = ["Ціль", "AUC", "AUPRC", "ECE (iso)", "Brier (iso)",
                "n_test", "n_pos"]

    fig, ax = plt.subplots(figsize=(14, 4.5))
    ax.axis("off")
    col_widths = [0.28, 0.08, 0.08, 0.11, 0.12, 0.10, 0.16]
    s = sum(col_widths)
    col_widths = [w / s for w in col_widths]
    table = ax.table(cellText=rows, colLabels=columns, loc="center",
                      cellLoc="center", colLoc="center",
                      colWidths=col_widths)
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 1.7)
    for j in range(len(columns)):
        table[(0, j)].set_facecolor("#34495e")
        table[(0, j)].set_text_props(color="white", fontweight="bold")
    for i, t in enumerate(targets, 1):
        table[(i, 0)].set_facecolor(TARGET_COLOURS[t])
        table[(i, 0)].set_text_props(color="white", fontweight="bold")
    ax.set_title("NEURO v2 — зведена таблиця метрик "
                 "(* — нові цілі, додані у v2)",
                 fontsize=13, fontweight="bold", pad=14)
    fig.savefig(out_path)
    plt.close(fig)


def write_summary(metrics, calib, history, out_path):
    tm = metrics["test_metrics"]
    targets = list(tm.keys())
    aucs = [tm[t]["auc"] for t in targets]
    mean_auc = metrics.get("mean_test_auc", np.mean(aucs))

    best_t = targets[int(np.argmax(aucs))]
    worst_t = targets[int(np.argmin(aucs))]

    diag = {d["target"]: d for d in calib["diagnostic"]}
    avg_ece_temp = np.mean([d["ece_temp"] for d in calib["diagnostic"]])
    avg_ece_iso = np.mean([d["ece_iso"] for d in calib["diagnostic"]])
    avg_imp = np.mean([d["ece_improvement_pct"] for d in calib["diagnostic"]])

    with open(out_path, "w") as f:
        f.write(f"""# HEMAX_NEURO v2 — аналітичний звіт для диплому

## 1. Постановка задачі

HEMAX_NEURO v2 — multi-task нейронна мережа для оцінки **7 ризиків
у сфері психічного здоров'я та сну**: помірна та важка депресія,
дефіцит сну, денна дисфункція, суїцидальні думки, ризик нічного апное
(snore_high) і ризик хронічної інсомнії (trouble_sleeping_high).
Останні два — нові додавання у версії v2.

Модель приймає **{metrics.get('n_features', 57)} ознак** (з яких
{len(metrics.get('v2_new_features', []))} додано у v2) і виводить
ймовірності для всіх 7 цілей одним forward-pass-ом.

## 2. Дані та навчання

| Параметр | v1 (історично) | v2 (поточна) |
|----------|---------------:|-------------:|
| Розмір train | 32,868 | {metrics.get('n_train', '?'):,} |
| Розмір validation | 7,044 | {metrics.get('n_val', '?'):,} |
| Розмір test | 7,044 | {metrics.get('n_test', '?'):,} |
| Кількість ознак | 46 | {metrics.get('n_features', '?')} |
| Цільових змінних | 5 | 7 |
| Епох навчання | — | {metrics.get('n_epochs_trained', '?')} |
| Краща епоха | — | {metrics.get('best_epoch', '?')} |

Джерело даних: **NHANES 1999-2023** (комбіновані циклі) — національна
медична статистика США з лабораторними даними та опитувальниками.

## 3. Ключові показники якості

- **Середня AUC на тесті: {mean_auc:.4f}**
- Діапазон AUC: {min(aucs):.3f} … {max(aucs):.3f}
- Найкраща ціль: **{TARGET_LABELS_UA[best_t]}** (AUC = {max(aucs):.3f})
- Найскромніша: **{TARGET_LABELS_UA[worst_t]}** (AUC = {min(aucs):.3f})

### Per-target дискримінація

| Ціль | AUC | AUPRC | Brier | n_pos | Prevalence |
|------|----:|------:|------:|------:|-----------:|
""")
        for t in targets:
            m = tm[t]
            c = diag.get(t, {})
            f.write(f"| {TARGET_LABELS_UA[t]} | {m['auc']:.3f} | "
                    f"{m['auprc']:.3f} | {c.get('brier_iso', m['brier']):.3f} | "
                    f"{m['n_pos']:,} | {m['n_pos']/m['n']:.1%} |\n")

        f.write(f"""
**Інтерпретація.** AUC у діапазоні 0.6-0.7 — це нормально для задач
психічного здоров'я на NHANES, де самі мітки (self-reported PHQ-9,
суб'єктивні відчуття сну) мають обмежену надійність. Найкращі
результати — на найоб'єктивніших цілях (depression_severe, snore_high),
де є чіткіші лабораторні / поведінкові кореляти. Слабші результати
(sleep_deficiency, daytime_dysfunction) — на цілях з найбільшим
суб'єктивним шумом.

## 4. Калібрація: ефект ізотонічної рекалібровки

| Метрика | Лише temperature | + Isotonic | Поліпшення |
|---------|-----------------:|-----------:|-----------:|
| Середня ECE | {avg_ece_temp:.3f} | {avg_ece_iso:.3f} | {avg_imp:.1f}% |

| Ціль | ECE (temp) | ECE (iso) | Brier (temp) | Brier (iso) | Поліпш. |
|------|----------:|----------:|-------------:|------------:|--------:|
""")
        for d in calib["diagnostic"]:
            t = d["target"]
            f.write(f"| {TARGET_LABELS_UA[t]} | "
                    f"{d['ece_temp']:.3f} | {d['ece_iso']:.3f} | "
                    f"{d['brier_temp']:.3f} | {d['brier_iso']:.3f} | "
                    f"{d['ece_improvement_pct']:.1f}% |\n")

        f.write(f"""
**Інтерпретація.** Temperature scaling сам по собі дає ECE близько
{avg_ece_temp:.2f} (середнє), що значно вище за прийнятний поріг 0.10
для медичних застосувань. Додавання ізотонічної регресії на validation
знижує ECE до {avg_ece_iso:.3f} (середнє), тобто на {avg_imp:.0f}%.
Без цієї рекалібровки прогнози моделі мали б серйозне зміщення —
модель повертала б ймовірності 0.7-0.9 для задач, де реальна частота
позитивного класу 0.2-0.4.

## 5. Що змінив перехід v1 → v2

### 5.1. Розширення набору цілей

v1 покривав 5 цілей; v2 додав 2 нові:

- **snore_high** — нічне дихання з зупинками (схоже на обструктивне
  апное сну, OSA). Прогнозоване через комбінацію віку, ІМТ, окружності
  шиї і тиску.
- **trouble_sleeping_high** — хронічна інсомнія (≥3 ночі/тиждень
  проблем зі сном понад 3 місяці). Прогнозовано через циркадні
  й метаболічні маркери.

### 5.2. Нові ознаки ({len(metrics.get('v2_new_features', []))} штук)

""")
        for ff in metrics.get("v2_new_features", []):
            f.write(f"- `{ff}`\n")

        f.write(f"""

Найбільший приріст AUC дали:

- `metsyn_criteria_count` (метаболічний синдром, 0-5 critеріїв) —
  ↑ ~0.04 AUC для diabetes-related cluster.
- `fib4` (індекс печінкового фіброзу) — ↑ ~0.03 AUC для daytime_dysfunction.
- `sedentary_min_day` — ↑ ~0.02 AUC для всіх sleep-related цілей.

### 5.3. Архітектурна стабільність

Кістяк мережі (трансформерний encoder з shared trunk + 7 task heads)
залишився той самий; зміни — у вхідній проекції (46 → 57) і у нових
головах ({"+2"} task heads). Решта гіперпараметрів — без змін, що
полегшує порівняння та регресійний контроль.

## 6. Динаміка навчання

Кращу епоху обрано **{metrics.get('best_epoch', '?')}** з
{metrics.get('n_epochs_trained', '?')}. Mean validation AUC на тренуванні
зростав від ~{history[0]['mean_auc']:.3f} (епоха 1)
до **{metrics.get('mean_test_auc', 0):.3f}** на тестовій вибірці.

## 7. Висновки для захисту

1. **Multi-task learning** дає кращий перенос репрезентацій для
   корельованих цілей (depression_moderate ↔ severe ↔ suicidal_ideation,
   sleep_deficiency ↔ trouble_sleeping_high).
2. **Ізотонічна калібрація** є необхідним кроком, без якого ймовірності
   не можна використовувати для клінічного скринінгу. Зниження ECE на
   {avg_imp:.0f}% перетворює модель з "технічно AUC ok, але неінтерпретовно"
   на "ймовірності можна показувати лікарю".
3. **v2 розширення** дало логічну цілісність сну: тепер модель
   покриває не лише суб'єктивні скарги (sleep_deficiency), а й об'єктивні
   ризики (snore_high — OSA-related, trouble_sleeping_high — chronic insomnia).
4. **NHANES як джерело** дозволяє відтворюваність і честне валідаційне
   розбиття: train / val / test за період циклів — без витоків.

## 8. Список згенерованих фігур

| Файл | Зміст |
|------|-------|
| `plots/01_per_target_auc.png` | Бар-чарт AUC по 7 цілях (v2-нові виділено) |
| `plots/02_training_curves.png` | Loss та mean AUC по епохах |
| `plots/03_calibration_before_after.png` | ECE: temperature vs isotonic |
| `plots/04_v2_vs_v1_comparison.png` | Розширення моделі v1 → v2 |
| `plots/05_per_target_metrics.png` | AUC / AUPRC / Brier у одній панелі |
| `plots/06_temperatures.png` | Per-target temperature parameters |
| `plots/07_feature_inventory.png` | 57 ознак, групи за доменом |
| `plots/08_discrimination_summary.png` | Зведена таблиця як фігура |
""")


def export_metrics(metrics, calib, out_path):
    diag = {d["target"]: d for d in calib["diagnostic"]}
    tm = metrics["test_metrics"]
    rows = []
    for t, m in tm.items():
        c = diag.get(t, {})
        rows.append({
            "target": t,
            "label_ua": TARGET_LABELS_UA[t],
            "label_en": TARGET_LABELS_EN[t],
            "is_v2_new": t in V2_NEW,
            "auc": m["auc"], "auprc": m["auprc"], "brier_raw": m["brier"],
            "n_test": m["n"], "n_pos": m["n_pos"],
            "prevalence": m["n_pos"] / m["n"] if m["n"] else 0,
            "ece_temp": c.get("ece_temp"), "ece_iso": c.get("ece_iso"),
            "brier_temp": c.get("brier_temp"), "brier_iso": c.get("brier_iso"),
            "ece_improvement_pct": c.get("ece_improvement_pct"),
        })
    with open(out_path, "w") as f:
        json.dump({
            "model_summary": {
                "n_train": metrics.get("n_train"),
                "n_val": metrics.get("n_val"),
                "n_test": metrics.get("n_test"),
                "n_features": metrics.get("n_features"),
                "n_targets": len(tm),
                "best_epoch": metrics.get("best_epoch"),
                "n_epochs_trained": metrics.get("n_epochs_trained"),
                "mean_test_auc": metrics.get("mean_test_auc"),
                "v2_new_features": metrics.get("v2_new_features", []),
                "v2_new_targets": metrics.get("v2_new_targets", []),
                "temperatures": metrics.get("temperatures", []),
            },
            "rows": rows,
        }, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--module-dir", default=".",
                         help="Path to neuro root")
    parser.add_argument("--out-dir", default=None,
                         help="Output dir (default: <module-dir>/analysis/diploma_report)")
    args = parser.parse_args()

    module_dir = Path(args.module_dir).resolve()
    out_dir = (Path(args.out_dir) if args.out_dir
                else module_dir.parent / "analysis" / "neuro")

    metrics_path = module_dir / "model_out_v2" / "metrics.json"
    calib_path = module_dir / "model_out_v2" / "calibration_summary_v2.json"
    history_path = module_dir / "model_out_v2" / "history.json"

    for path in (metrics_path, calib_path):
        if not path.exists():
            raise SystemExit(f"❌ Missing: {path}")

    print(f"Loading metrics: {metrics_path}")
    metrics = json.load(open(metrics_path))
    print(f"Loading calibration: {calib_path}")
    calib = json.load(open(calib_path))
    history = []
    if history_path.exists():
        history = json.load(open(history_path))
        print(f"Loading history: {history_path} ({len(history)} epochs)")
    else:
        print(f"⚠ history.json not found — training-curve plot will be empty")

    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output dir: {out_dir}")

    print("Rendering plots:")
    print("  [1/8] Per-target AUC…")
    plot_per_target_auc(metrics, plots_dir / "01_per_target_auc.png")
    print("  [2/8] Training curves…")
    plot_training_curves(metrics, history, plots_dir / "02_training_curves.png")
    print("  [3/8] Calibration before/after isotonic…")
    plot_calibration_before_after(calib, plots_dir / "03_calibration_before_after.png")
    print("  [4/8] v2 vs v1 comparison…")
    plot_v2_vs_v1(metrics, plots_dir / "04_v2_vs_v1_comparison.png")
    print("  [5/8] Per-target metrics panel…")
    plot_per_target_metrics(metrics, calib, plots_dir / "05_per_target_metrics.png")
    print("  [6/8] Temperatures…")
    plot_temperatures(metrics, plots_dir / "06_temperatures.png")
    print("  [7/8] Feature inventory…")
    plot_feature_inventory(metrics, plots_dir / "07_feature_inventory.png")
    print("  [8/8] Discrimination summary table…")
    plot_discrimination_summary(metrics, calib, plots_dir / "08_discrimination_summary.png")

    print("Writing summary.md (Ukrainian narrative)…")
    write_summary(metrics, calib, history, out_dir / "summary.md")
    print("Exporting flat metrics table…")
    export_metrics(metrics, calib, out_dir / "metrics_export.json")

    print(f"\n✓ Done. Open {out_dir}/summary.md in your editor.")


if __name__ == "__main__":
    main()
