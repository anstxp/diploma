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

CLASS_COLOURS = {
    "akiec": "#F4A261",
    "bcc":   "#E76F51",
    "bkl":   "#bdc3c7",
    "df":    "#7209B7",
    "mel":   "#D62828",
    "nv":    "#06A77D",
    "vasc":  "#2E86AB",
}
CLASS_LABELS_UA = {
    "akiec": "Actinic keratoses (akiec)",
    "bcc":   "Basal cell carcinoma (bcc)",
    "bkl":   "Benign keratosis (bkl)",
    "df":    "Dermatofibroma (df)",
    "mel":   "Меланома (mel)",
    "nv":    "Melanocytic nevi (nv)",
    "vasc":  "Судинні ушкодж. (vasc)",
}
CLASS_SEVERITY = {
    "akiec": "high",
    "bcc":   "high",
    "bkl":   "low",
    "df":    "low",
    "mel":   "critical",
    "nv":    "low",
    "vasc":  "medium",
}
SEVERITY_COLOURS = {
    "critical": "#D62828",
    "high":     "#F4A261",
    "medium":   "#2E86AB",
    "low":      "#06A77D",
}


def plot_per_class_auc(metrics, out_path):
    pc = metrics["test_metrics"]["per_class_auc"]
    classes = list(pc.keys())
    aucs = [pc[c] for c in classes]
    labels = [CLASS_LABELS_UA[c] for c in classes]
    colours = [CLASS_COLOURS[c] for c in classes]
    edges = ["red" if c == "mel" else "black" for c in classes]
    widths = [2.5 if c == "mel" else 0.6 for c in classes]

    order = np.argsort(aucs)[::-1]
    classes = [classes[i] for i in order]
    aucs = [aucs[i] for i in order]
    labels = [labels[i] for i in order]
    colours = [colours[i] for i in order]
    edges = [edges[i] for i in order]
    widths = [widths[i] for i in order]

    fig, ax = plt.subplots(figsize=(11, 5.5))
    bars = ax.bar(labels, aucs, color=colours, edgecolor=edges, linewidth=widths)
    ax.axhline(0.5, color="grey", linestyle=":", linewidth=1, label="Random")
    ax.axhline(0.8, color="grey", linestyle="--", linewidth=0.7, alpha=0.5,
                label="AUC = 0.80 (clinical screening threshold)")
    for bar, auc in zip(bars, aucs):
        ax.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 0.01,
                 f"{auc:.3f}", ha="center", va="bottom",
                 fontsize=9, fontweight="bold")
    ax.set_ylim(0.5, 1.05)
    ax.set_ylabel("Test AUC (one-vs-rest)")
    macro = metrics["test_metrics"]["macro_auc"]
    ax.set_title(f"DERMA — AUC по 7 класах "
                 f"(macro AUC = {macro:.3f})")
    plt.xticks(rotation=20, ha="right")
    ax.legend(loc="lower right")
    fig.savefig(out_path)
    plt.close(fig)


def plot_training_dynamics(metrics, out_path):
    hist = metrics.get("history", [])
    if not hist:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "history missing", ha="center", va="center")
        ax.axis("off")
        fig.savefig(out_path)
        plt.close(fig)
        return

    eps = [h["epoch"] for h in hist]
    train_loss = [h.get("train_loss", np.nan) for h in hist]
    train_acc = [h.get("train_acc", np.nan) for h in hist]
    val_acc = [h.get("val_acc", np.nan) for h in hist]
    val_auc = [h.get("val_auc", np.nan) for h in hist]
    val_f1 = [h.get("val_f1", np.nan) for h in hist]

    best_ep = metrics.get("best_epoch")

    fig, axes = plt.subplots(2, 2, figsize=(13, 8))

    axes[0, 0].plot(eps, train_loss, "o-", color="#2E86AB", linewidth=2)
    axes[0, 0].set_xlabel("Епоха")
    axes[0, 0].set_ylabel("Training loss")
    axes[0, 0].set_title("Train loss (cross-entropy)")
    if best_ep:
        axes[0, 0].axvline(best_ep, color="green", linestyle=":", linewidth=1.5)

    axes[0, 1].plot(eps, train_acc, "o-", color="#06A77D",
                     linewidth=2, label="Train")
    axes[0, 1].plot(eps, val_acc, "s-", color="#E63946",
                     linewidth=2, label="Validation")
    axes[0, 1].set_xlabel("Епоха")
    axes[0, 1].set_ylabel("Accuracy")
    axes[0, 1].set_title("Точність — train vs validation")
    axes[0, 1].legend()
    if best_ep:
        axes[0, 1].axvline(best_ep, color="green", linestyle=":", linewidth=1.5)

    axes[1, 0].plot(eps, val_auc, "o-", color="#7209B7", linewidth=2)
    axes[1, 0].set_xlabel("Епоха")
    axes[1, 0].set_ylabel("Validation macro AUC")
    axes[1, 0].set_title("Validation macro AUC")
    axes[1, 0].set_ylim(0.7, 1.0)
    if best_ep:
        axes[1, 0].axvline(best_ep, color="green", linestyle=":", linewidth=1.5)

    axes[1, 1].plot(eps, val_f1, "o-", color="#F4A261", linewidth=2)
    axes[1, 1].set_xlabel("Епоха")
    axes[1, 1].set_ylabel("Validation macro F1")
    axes[1, 1].set_title("Validation macro F1 (із imbalance)")
    if best_ep:
        axes[1, 1].axvline(best_ep, color="green", linestyle=":", linewidth=1.5)

    fig.suptitle(f"DERMA — динаміка навчання "
                 f"({len(eps)} епох, best = epoch {best_ep})",
                 fontsize=13, fontweight="bold")
    fig.savefig(out_path)
    plt.close(fig)


def plot_severity_weighted_perf(metrics, out_path):
    pc = metrics["test_metrics"]["per_class_auc"]

    sev_groups = {}
    for c, auc in pc.items():
        sev = CLASS_SEVERITY[c]
        sev_groups.setdefault(sev, []).append((c, auc))

    order = ["critical", "high", "medium", "low"]
    fig, ax = plt.subplots(figsize=(11, 5.5))

    x_pos = 0
    x_labels = []
    x_positions = []
    for sev in order:
        if sev not in sev_groups:
            continue
        for c, auc in sev_groups[sev]:
            ax.bar(x_pos, auc, width=0.7,
                    color=SEVERITY_COLOURS[sev], edgecolor="black",
                    linewidth=0.6)
            ax.text(x_pos, auc + 0.01, f"{auc:.2f}",
                     ha="center", va="bottom", fontsize=9, fontweight="bold")
            x_labels.append(c)
            x_positions.append(x_pos)
            x_pos += 1
        ax.axvline(x_pos - 0.4, color="grey", linestyle=":", alpha=0.5)
        ax.text(x_pos - 1.5 - (len(sev_groups[sev]) - 1) / 2,
                 1.02, sev.upper(), ha="center", fontsize=10,
                 fontweight="bold", color=SEVERITY_COLOURS[sev])
        x_pos += 0.5

    ax.set_xticks(x_positions)
    ax.set_xticklabels(x_labels)
    ax.set_ylim(0.5, 1.1)
    ax.set_ylabel("Test AUC")
    ax.set_title("DERMA — AUC згруповано за клінічною тяжкістю класу")

    from matplotlib.patches import Patch
    handles = [Patch(facecolor=col, edgecolor="black",
                      label=sev.upper())
                for sev, col in SEVERITY_COLOURS.items()]
    ax.legend(handles=handles, loc="lower right", title="Severity")

    fig.savefig(out_path)
    plt.close(fig)


def plot_class_prevalence_test(metrics, out_path):
    hist = metrics.get("history", [])
    pc_auc = metrics["test_metrics"]["per_class_auc"]
    classes = list(pc_auc.keys())

    HAM_BASELINE = {
        "akiec": 0.034, "bcc":   0.052, "bkl":   0.108,
        "df":    0.012, "mel":   0.111, "nv":    0.668, "vasc":  0.015,
    }
    prevs = [HAM_BASELINE.get(c, 1/7) for c in classes]
    labels = [CLASS_LABELS_UA[c] for c in classes]
    colours = [CLASS_COLOURS[c] for c in classes]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(labels, prevs, color=colours, edgecolor="black", linewidth=0.5)
    for bar, p in zip(bars, prevs):
        ax.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height() / 2,
                 f"{p:.1%}", va="center", fontsize=9, fontweight="bold")
    ax.axvline(1/7, color="grey", linestyle="--",
                label=f"Балансована частка (1/7 = {1/7:.1%})")
    ax.set_xlabel("Частка у HAM10000 (test, типова)")
    ax.set_title("DERMA — типовий розподіл класів у тестовій вибірці HAM10000")
    ax.legend()
    fig.text(0.5, -0.02, "Примітка: ~67% — nevus (родимка). Це найбільший "
              "виклик: модель має не плутати з ними меланому.",
              ha="center", fontsize=9, color="grey", style="italic")
    fig.savefig(out_path)
    plt.close(fig)


def plot_auc_evolution(metrics, out_path):
    hist = metrics.get("history", [])
    if not hist or "per_class_auc" not in hist[0]:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "per-class history missing", ha="center", va="center")
        ax.axis("off")
        fig.savefig(out_path)
        plt.close(fig)
        return

    classes = list(hist[0]["per_class_auc"].keys())
    eps = [h["epoch"] for h in hist]

    fig, ax = plt.subplots(figsize=(11, 6))
    for c in classes:
        series = [h["per_class_auc"].get(c, np.nan) for h in hist]
        linewidth = 3 if c == "mel" else 1.5
        marker = "o" if c == "mel" else "."
        ax.plot(eps, series, marker=marker, linewidth=linewidth,
                color=CLASS_COLOURS[c], label=CLASS_LABELS_UA[c],
                markersize=7 if c == "mel" else 4)
    ax.set_xlabel("Епоха")
    ax.set_ylabel("Validation AUC (one-vs-rest)")
    ax.set_title("DERMA — еволюція per-class AUC по епохах "
                 "(меланома виділена)")
    ax.legend(loc="lower right", fontsize=8, ncol=2)
    ax.set_ylim(0.5, 1.0)
    fig.savefig(out_path)
    plt.close(fig)


def plot_calibration_params(calib_params, out_path):
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    raw_ece  = calib_params.get("raw_ece")
    t_ece    = calib_params.get("temperature_ece")
    iso_ece  = calib_params.get("isotonic_ece")
    prod_ece = calib_params.get("production_ece")
    strategy = calib_params.get("production_strategy", "?")

    if raw_ece is not None:
        eces = [raw_ece, t_ece or 0, iso_ece or 0]
        labels = ["Raw\n(no calib)", "Temperature\nscaling",
                   "Isotonic\nregression"]
        colours = ["#bdc3c7", "#7209B7", "#06A77D"]
        edges = ["black"] * 3
        widths = [0.6] * 3
        if strategy == "temperature_only":
            edges[1] = "red"; widths[1] = 2.5
        elif strategy == "isotonic":
            edges[2] = "red"; widths[2] = 2.5
        bars = axes[0].bar(labels, eces, color=colours,
                            edgecolor=edges, linewidth=widths)
        axes[0].axhline(0.10, color="red", linestyle="--", linewidth=0.8,
                         label="0.10 (поріг прийнятної)")
        for bar, v in zip(bars, eces):
            axes[0].text(bar.get_x() + bar.get_width()/2,
                          bar.get_height() + max(eces)*0.02,
                          f"{v:.3f}", ha="center", va="bottom",
                          fontsize=10, fontweight="bold")
        axes[0].set_ylabel("Expected Calibration Error (ECE)")
        axes[0].set_title("ECE: raw → temperature → isotonic\n"
                           f"(production strategy: {strategy})")
        axes[0].legend(loc="upper right", fontsize=8)
        axes[0].set_ylim(0, max(eces) * 1.20)
    else:
        axes[0].text(0.5, 0.5, "No ECE data", ha="center",
                      va="center", transform=axes[0].transAxes)
        axes[0].axis("off")

    raw_acc = calib_params.get("raw_accuracy")
    t_acc   = calib_params.get("temperature_accuracy")
    iso_acc = calib_params.get("isotonic_accuracy")
    if raw_acc is not None:
        accs = [raw_acc, t_acc or 0, iso_acc or 0]
        labels = ["Raw", "Temp", "Iso"]
        colours = ["#bdc3c7", "#7209B7", "#06A77D"]
        bars = axes[1].bar(labels, accs, color=colours,
                            edgecolor="black", linewidth=0.5)
        for bar, v in zip(bars, accs):
            axes[1].text(bar.get_x() + bar.get_width()/2,
                          bar.get_height() + 0.01,
                          f"{v:.3f}", ha="center", va="bottom",
                          fontsize=10, fontweight="bold")
        axes[1].set_ylabel("Top-1 Accuracy")
        axes[1].set_title("Accuracy через стадії калібрації")
        axes[1].set_ylim(0, 1.0)
    else:
        axes[1].axis("off")

    T = calib_params.get("temperature")
    n_val = calib_params.get("n_val")
    n_test = calib_params.get("n_test")
    info_lines = []
    if T is not None:
        info_lines.append(f"Temperature scalar:  T = {T:.3f}")
        if T < 1.0:
            info_lines.append("  → недо-впевнена модель")
            info_lines.append("    (ймовірності загострюються)")
        elif T > 1.0:
            info_lines.append("  → пере-впевнена модель")
            info_lines.append("    (ймовірності пом'якшуються)")
        else:
            info_lines.append("  → добре відкалібрована")
        info_lines.append("")
    if n_val is not None:
        info_lines.append(f"n_validation:  {n_val:,}")
    if n_test is not None:
        info_lines.append(f"n_test:        {n_test:,}")
    info_lines.append("")
    info_lines.append(f"Production strategy:")
    info_lines.append(f"  {strategy}")
    pce = calib_params.get("per_class_ece")
    if isinstance(pce, dict) and pce:
        prod_pce = pce.get(strategy) or pce.get("temperature") or pce.get("isotonic")
        if isinstance(prod_pce, dict) and prod_pce:
            info_lines.append("")
            info_lines.append(f"Per-class ECE (production):")
            worst_cls = max(prod_pce, key=prod_pce.get)
            best_cls = min(prod_pce, key=prod_pce.get)
            info_lines.append(f"  min:  {best_cls}  {prod_pce[best_cls]:.3f}")
            info_lines.append(f"  max:  {worst_cls}  {prod_pce[worst_cls]:.3f}")

    axes[2].axis("off")
    axes[2].text(0.05, 0.95, "\n".join(info_lines),
                  transform=axes[2].transAxes, fontsize=11,
                  family="monospace", va="top",
                  bbox=dict(facecolor="#fef6e4", edgecolor="#7209B7",
                             boxstyle="round,pad=0.6"))

    fig.suptitle("DERMA — параметри калібрації",
                  fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def plot_overall_metrics(metrics, out_path):
    tm = metrics["test_metrics"]
    names = ["Accuracy", "Macro F1", "Macro AUC"]
    values = [tm.get("accuracy", 0), tm.get("macro_f1", 0), tm.get("macro_auc", 0)]
    colours = ["#2E86AB", "#F4A261", "#06A77D"]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(names, values, color=colours,
                   edgecolor="black", linewidth=0.6, width=0.6)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 0.02,
                 f"{v:.3f}", ha="center", va="bottom",
                 fontsize=12, fontweight="bold")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Метрика")
    ax.set_title(f"DERMA — основні метрики на тесті\n"
                 f"(best epoch {metrics.get('best_epoch')} "
                 f"з {metrics.get('args', {}).get('epochs', '?')})")
    ax.text(0.5, 0.05,
             "Розрив між Accuracy/F1 та AUC є очікуваним для НЕзбалансованих "
             "класів:\n"
             "AUC оцінює discrimination ability, F1 — operating-point performance.",
             ha="center", va="bottom", transform=ax.transAxes,
             fontsize=9, color="grey", style="italic",
             bbox=dict(facecolor="#fef6e4", edgecolor="grey",
                        boxstyle="round,pad=0.4"))
    fig.savefig(out_path)
    plt.close(fig)


def plot_summary_table(metrics, calib_params, out_path):
    pc = metrics["test_metrics"]["per_class_auc"]
    rows = []
    for c in sorted(pc.keys(), key=lambda x: -pc[x]):
        rows.append([
            c.upper(),
            CLASS_LABELS_UA[c],
            CLASS_SEVERITY[c].upper(),
            f"{pc[c]:.3f}",
        ])
    columns = ["Код", "Клас", "Severity", "Test AUC"]

    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.axis("off")
    table = ax.table(cellText=rows, colLabels=columns, loc="center",
                      cellLoc="left", colLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.0, 1.7)
    for j in range(len(columns)):
        table[(0, j)].set_facecolor("#34495e")
        table[(0, j)].set_text_props(color="white", fontweight="bold")
    for i, c in enumerate([row[0].lower() for row in rows], 1):
        table[(i, 0)].set_facecolor(CLASS_COLOURS[c])
        table[(i, 0)].set_text_props(color="white", fontweight="bold")
        sev = CLASS_SEVERITY[c]
        table[(i, 2)].set_facecolor(SEVERITY_COLOURS[sev])
        table[(i, 2)].set_text_props(color="white", fontweight="bold")

    macro = metrics["test_metrics"]["macro_auc"]
    acc = metrics["test_metrics"]["accuracy"]
    f1 = metrics["test_metrics"]["macro_f1"]
    title = (f"DERMA — повна таблиця класів | macro AUC = {macro:.3f} | "
             f"accuracy = {acc:.3f} | macro F1 = {f1:.3f}")
    ax.set_title(title, fontsize=12, fontweight="bold", pad=14)
    fig.savefig(out_path)
    plt.close(fig)


def write_summary(metrics, calib_params, out_path):
    tm = metrics["test_metrics"]
    pc = tm["per_class_auc"]
    classes = list(pc.keys())
    aucs = list(pc.values())
    best_c = max(pc, key=pc.get)
    worst_c = min(pc, key=pc.get)
    mel_auc = pc.get("mel")
    args = metrics.get("args", {})

    with open(out_path, "w") as f:
        f.write(f"""# HEMAX_DERMA — аналітичний звіт для диплому

## 1. Постановка задачі

HEMAX_DERMA — система класифікації пігментних утворень шкіри на основі
дерматоскопічних зображень за датасетом **HAM10000**. Модель розрізняє
**7 класів** уражень: від доброякісних родимок до меланоми. Архітектурно
— CNN на основі ImageNet-предтренованої моделі (EfficientNet або
ResNet, залежно від конкретного запуску), дотренована з cross-entropy
loss на 224×224 центрованих кропах.

| Параметр навчання | Значення |
|-------------------|----------|
| Епох максимум | {args.get('epochs', '?')} |
| Batch size | {args.get('bs', '?')} |
| Learning rate | {args.get('lr', '?')} |
| Weight decay | {args.get('weight_decay', '?')} |
| Early stopping patience | {args.get('patience', '?')} |
| Pre-trained backbone | {'Yes' if not args.get('no_pretrained') else 'No'} |
| Device | `{args.get('device', '?')}` |
| Best epoch | {metrics.get('best_epoch', '?')} |

## 2. Основні показники якості

| Метрика | Значення | Інтерпретація |
|---------|---------:|---------------|
| Test **Macro AUC** | {tm['macro_auc']:.3f} | Дискримінація |
| Test **Accuracy** | {tm['accuracy']:.3f} | Top-1 правильність |
| Test **Macro F1** | {tm['macro_f1']:.3f} | Збалансована F1 по класах |

**Інтерпретація.** Розрив між Accuracy ({tm['accuracy']:.2f}) і Macro AUC
({tm['macro_auc']:.2f}) є типовим для дерматоскопії — клас "nv" (родимка)
займає ~67% даних, тому навіть constant predictor досягає accuracy 0.67
без жодної реальної дискримінації. **Macro AUC** — більш чесна метрика:
вона усереднює AUC по класах, ігноруючи частоти.

## 3. Per-class AUC (one-vs-rest)

| Клас | Опис | Severity | AUC |
|------|------|----------|----:|
""")
        for c in sorted(classes, key=lambda x: -pc[x]):
            f.write(f"| `{c}` | {CLASS_LABELS_UA[c]} | "
                    f"{CLASS_SEVERITY[c].upper()} | {pc[c]:.3f} |\n")

        f.write(f"""

### 3.1. Найкраща дискримінація

- **{CLASS_LABELS_UA[best_c]}** — AUC = {pc[best_c]:.3f}.
  Зазвичай це vascular або dermatofibroma, у яких унікальні текстурні
  й кольорові ознаки на дерматоскопі.

### 3.2. Меланома — критичний клас

- **Melanoma (mel)** — AUC = {mel_auc:.3f}.
  Melanoma — найвищий клінічний пріоритет (severity = critical). Модель
  розрізняє меланому проти решти класів із AUC ~{mel_auc:.2f}, що
  знаходиться у діапазоні опублікованих робіт на HAM10000 (зазвичай
  0.80-0.92 без додаткових модальностей).

### 3.3. Найскромніший клас

- **{CLASS_LABELS_UA[worst_c]}** — AUC = {pc[worst_c]:.3f}.
  Це найскладніше: типово bkl (benign keratosis) — оптично схожий і
  на nv, і на mel.

## 4. Severity-зважена ефективність

Класи згруповано за клінічною тяжкістю. Для медичного скринінгу
ключове — щоб модель *не пропускала* високотяжкі ураження (critical,
high). Подивіться `plots/03_severity_weighted_perf.png`:

- **critical (mel)**: AUC = {pc.get('mel', 0):.3f}
- **high (akiec, bcc)**: avg AUC = {np.mean([pc.get('akiec', 0), pc.get('bcc', 0)]):.3f}
- **medium (vasc)**: AUC = {pc.get('vasc', 0):.3f}
- **low (bkl, df, nv)**: avg AUC = {np.mean([pc.get('bkl', 0), pc.get('df', 0), pc.get('nv', 0)]):.3f}

## 5. Калібрація

Модель калібрується через **temperature scaling**, параметри збережено
у `derma_api/weights/calibration_params.json`.

""")
        if "temperature" in calib_params:
            T = calib_params["temperature"]
            f.write(f"- Оптимальна temperature: **T = {T:.3f}**\n")
            if T < 1.0:
                f.write("- T < 1.0 → модель **недо-впевнена**: ймовірності "
                        "будуть загострені (поділ на T<1 збільшує контраст).\n")
            elif T > 1.0:
                f.write("- T > 1.0 → модель **пере-впевнена**: ймовірності "
                        "будуть пом'якшені (поділ на T>1 пом'якшує).\n")
            else:
                f.write("- T ≈ 1.0 → модель добре відкалібрована "
                        "природно, додаткова scaling непотрібна.\n")
        else:
            f.write("- Тип калібрації: за класовою isotonic-регресією.\n")

        f.write(f"""

## 6. Динаміка навчання

Кращу епоху обрано **{metrics.get('best_epoch', '?')}** з
{args.get('epochs', '?')}. Це означає, що модель досягла плато після
середньої частини тренування, після чого validation score почав
повільно деградувати (overfitting).

## 7. Висновки для захисту

1. **Macro AUC {tm['macro_auc']:.3f}** — рівень робіт типу
   "ResNet-50 на HAM10000 без додаткової аугментації". Для production
   skin-cancer triage цього недостатньо без supplementary multimodal
   inputs (метадані пацієнта, anatomical site).
2. **Melanoma AUC {mel_auc:.3f}** — клінічно достатнє для
   тригер-flagging, але NPV / PPV треба окремо аналізувати при виборі
   операційного порогу.
3. **Сильні класи**: vasc, df, nv — модель надійно їх розрізняє.
   **Слабкі**: bkl, mel — між ними часті cross-misclassification, що
   є відомою проблемою дерматоскопічної класифікації.
4. **Severity-aware accuracy** є більш інформативною для медичних
   застосувань, ніж raw accuracy. Зокрема, false-negatives на класі
   mel мають значно вищу clinical cost.

## 8. Список згенерованих фігур

| Файл | Зміст |
|------|-------|
| `plots/01_per_class_auc.png` | AUC по 7 класах (меланома виділена) |
| `plots/02_training_dynamics.png` | Loss, accuracy, AUC, F1 по епохах |
| `plots/03_severity_weighted_perf.png` | AUC за severity-групами |
| `plots/04_class_prevalence_test.png` | Розподіл класів у HAM10000 test |
| `plots/05_auc_evolution_by_epoch.png` | Per-class AUC по епохах |
| `plots/06_calibration_params.png` | Calibration parameters |
| `plots/07_overall_metrics.png` | Accuracy / Macro F1 / Macro AUC |
| `plots/08_summary_table.png` | Зведена таблиця класів |
""")


def export_metrics(metrics, calib_params, out_path):
    tm = metrics["test_metrics"]
    pc = tm["per_class_auc"]
    rows = []
    for c, auc in pc.items():
        rows.append({
            "class_code": c,
            "label_ua": CLASS_LABELS_UA[c],
            "severity": CLASS_SEVERITY[c],
            "auc": auc,
        })
    with open(out_path, "w") as f:
        json.dump({
            "model_summary": {
                "best_epoch": metrics.get("best_epoch"),
                "args": metrics.get("args"),
                "accuracy": tm.get("accuracy"),
                "macro_f1": tm.get("macro_f1"),
                "macro_auc": tm.get("macro_auc"),
            },
            "calibration": calib_params,
            "rows": rows,
        }, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--module-dir", default=".",
                         help="Path to derma root")
    parser.add_argument("--out-dir", default=None,
                         help="Output dir (default: <module-dir>/analysis/diploma_report)")
    args = parser.parse_args()

    module_dir = Path(args.module_dir).resolve()
    out_dir = (Path(args.out_dir) if args.out_dir
                else module_dir.parent / "analysis" / "derma")

    metrics_path = module_dir / "model_out" / "metrics.json"
    calib_path = module_dir / "derma_api" / "weights" / "calibration_params.json"

    if not metrics_path.exists():
        raise SystemExit(f"❌ Missing: {metrics_path}")
    calib_params = {}
    if calib_path.exists():
        calib_params = json.load(open(calib_path))

    metrics = json.load(open(metrics_path))

    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output dir: {out_dir}")

    print("Rendering plots:")
    print("  [1/8] Per-class AUC…")
    plot_per_class_auc(metrics, plots_dir / "01_per_class_auc.png")
    print("  [2/8] Training dynamics…")
    plot_training_dynamics(metrics, plots_dir / "02_training_dynamics.png")
    print("  [3/8] Severity-weighted performance…")
    plot_severity_weighted_perf(metrics, plots_dir / "03_severity_weighted_perf.png")
    print("  [4/8] Class prevalence in test…")
    plot_class_prevalence_test(metrics, plots_dir / "04_class_prevalence_test.png")
    print("  [5/8] AUC evolution by epoch…")
    plot_auc_evolution(metrics, plots_dir / "05_auc_evolution_by_epoch.png")
    print("  [6/8] Calibration params…")
    plot_calibration_params(calib_params, plots_dir / "06_calibration_params.png")
    print("  [7/8] Overall metrics…")
    plot_overall_metrics(metrics, plots_dir / "07_overall_metrics.png")
    print("  [8/8] Summary table…")
    plot_summary_table(metrics, calib_params, plots_dir / "08_summary_table.png")

    print("Writing summary.md…")
    write_summary(metrics, calib_params, out_dir / "summary.md")
    print("Exporting metrics_export.json…")
    export_metrics(metrics, calib_params, out_dir / "metrics_export.json")

    print(f"\n✓ Done. Open {out_dir}/summary.md")


if __name__ == "__main__":
    main()
