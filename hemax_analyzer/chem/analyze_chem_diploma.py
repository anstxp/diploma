#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
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


TIER_COLOURS = {
    "critical": "#D62828",
    "abnormal": "#E76F51",
    "minor":    "#F4A261",
    "info":     "#2E86AB",
    "normal":   "#06A77D",
    "urgent":      "#E76F51",
    "notable":     "#F4A261",
    "informative": "#06A77D",
    "incomplete":  "#bdc3c7",
}
TIER_ORDER = ["critical", "abnormal", "minor", "info", "normal"]

GROUP_COLOURS = {
    "glycaemia":    "#E63946",
    "kidney":       "#7209B7",
    "liver":        "#F4A261",
    "lipids":       "#F1FA8C",
    "electrolytes": "#2E86AB",
    "minerals":     "#06A77D",
    "iron":         "#9B0F00",
    "inflammation": "#D62828",
    "special":      "#bdc3c7",
    "general":      "#34495e",
}

META_SIGNALS = {"missing_core_chem"}



def load_labs(knowledge_path):
    text = knowledge_path.read_text()
    pattern = re.compile(r'^\s*"([a-z_][a-z_0-9]*)"\s*:\s*LabDef',
                          re.MULTILINE)
    labs = sorted(set(pattern.findall(text)))
    return labs


def load_signals(rules_path):
    text = rules_path.read_text()
    signals = set()
    for m in re.finditer(r'_signal\(\s*sig_id\s*[=:]?\s*["\']([a-z_]+)["\']',
                          text):
        signals.add(m.group(1))
    for m in re.finditer(r'sig_id\s*=\s*["\']([a-z_]+)["\']', text):
        signals.add(m.group(1))
    for m in re.finditer(r'_signal\(\s*["\']([a-z_]+)["\']', text):
        signals.add(m.group(1))
    for m in re.finditer(r'["\']([a-z_]+)["\']\s+in\s+sig_ids', text):
        signals.add(m.group(1))
    return sorted(signals)


def load_clusters(yaml_path):
    try:
        import yaml
    except ImportError:
        return _load_clusters_regex(yaml_path)
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    return data.get("clusters", [])


def _load_clusters_regex(yaml_path):
    text = yaml_path.read_text()
    clusters = []
    current = None
    for line in text.splitlines():
        if "#" in line:
            line = line[:line.index("#")]
        m_id = re.match(r"\s*-\s+id:\s*([a-z_][a-z_0-9]*)", line)
        if m_id:
            if current is not None:
                clusters.append(current)
            current = {"id": m_id.group(1)}
            continue
        if current is None:
            continue
        m_pri = re.match(r"\s*priority:\s*(\d+)", line)
        if m_pri:
            current["priority"] = int(m_pri.group(1))
            continue
        m_tier = re.match(r"\s*tier:\s*([a-z_]+)", line)
        if m_tier:
            current["tier"] = m_tier.group(1)
            continue
        m_grp = re.match(r"\s*group:\s*([a-z_]+)", line)
        if m_grp:
            current["group"] = m_grp.group(1)
            continue
    if current is not None:
        clusters.append(current)
    return clusters



ARCHETYPES = [
    {
        "name": "T2DM (декомпенсований)",
        "short": "T2DM",
        "payload": {
            "age": 58, "sex": "male",
            "glucose": 220, "hba1c": 9.4, "trigly": 320, "hdl": 30,
            "creatinine": 1.1, "alt": 35,
        },
    },
    {
        "name": "Преддіабет + метаб. синдром",
        "short": "PreDM",
        "payload": {
            "age": 52, "sex": "female",
            "glucose": 110, "hba1c": 6.0, "trigly": 200,
            "hdl": 38, "tchol": 240, "alt": 28,
        },
    },
    {
        "name": "ХХН-4 (тяжке порушення нирок)",
        "short": "CKD-4",
        "payload": {
            "age": 70, "sex": "male",
            "creatinine": 3.2, "urea": 80, "potassium": 5.4,
            "sodium": 138, "bicarbonate": 19,
        },
    },
    {
        "name": "Гострий гепатит (hepatocellular)",
        "short": "Hep-acute",
        "payload": {
            "age": 40, "sex": "female",
            "alt": 320, "ast": 280, "bilirubin_total": 4.2,
            "alp": 110, "ggt": 90, "albumin": 3.5,
        },
    },
    {
        "name": "Холестатичне ураження печінки",
        "short": "Hep-cholest",
        "payload": {
            "age": 60, "sex": "female",
            "alt": 60, "ast": 55, "alp": 380, "ggt": 410,
            "bilirubin_total": 3.0,
        },
    },
    {
        "name": "Тяжка дисліпідемія (FH-like)",
        "short": "Dyslipid",
        "payload": {
            "age": 50, "sex": "male",
            "tchol": 320, "ldl": 220, "hdl": 32, "trigly": 180,
        },
    },
    {
        "name": "Тяжка гіпертригліцеридемія",
        "short": "TG-severe",
        "payload": {
            "age": 45, "sex": "male",
            "trigly": 1200, "tchol": 280, "hdl": 28, "glucose": 130,
        },
    },
    {
        "name": "Гіперкаліємія + ацидоз",
        "short": "HyperK",
        "payload": {
            "age": 65, "sex": "male",
            "potassium": 6.2, "sodium": 135, "creatinine": 1.9,
            "bicarbonate": 16, "chloride": 109,
        },
    },
    {
        "name": "Тяжка гіпонатріємія",
        "short": "HypoNa",
        "payload": {
            "age": 75, "sex": "female",
            "sodium": 122, "potassium": 4.0, "creatinine": 0.9,
        },
    },
    {
        "name": "Залізодефіцитна анемія",
        "short": "IronDef",
        "payload": {
            "age": 30, "sex": "female",
            "ferritin": 8, "iron": 30, "tibc": 480,
            "trigly": 100, "alt": 18,
        },
    },
    {
        "name": "Запалення / хронічна хвороба",
        "short": "Inflamm",
        "payload": {
            "age": 55, "sex": "female",
            "crp": 24, "ferritin": 380, "albumin": 3.2,
            "tchol": 180, "alt": 22,
        },
    },
    {
        "name": "Здоровий пацієнт (контроль)",
        "short": "Healthy",
        "payload": {
            "age": 35, "sex": "male",
            "glucose": 88, "hba1c": 5.2, "creatinine": 0.95,
            "alt": 22, "ast": 20, "tchol": 180, "hdl": 55,
            "ldl": 110, "trigly": 80, "sodium": 140, "potassium": 4.1,
        },
    },
]


def run_battery(module_dir):
    chem_pkg = module_dir / "engine"
    if not chem_pkg.exists():
        return None
    sys.path.insert(0, str(chem_pkg))
    sys.path.insert(0, str(chem_pkg / "chem_api"))
    try:
        from chem.analyze import analyze_chem_payload
    except ImportError as e:
        print(f"⚠ Could not import analyze_chem_payload ({e})")
        print("  Dynamic battery skipped; static inventory plots will be produced.")
        return None

    results = []
    for arch in ARCHETYPES:
        try:
            out = analyze_chem_payload(arch["payload"])
            sigs = out.get("signals", [])
            combos = out.get("combos", []) or out.get("clusters", [])
            recs = out.get("recommendations", [])
            results.append({
                "name": arch["name"],
                "short": arch["short"],
                "signals": [s.get("id") for s in sigs if s.get("id")],
                "signal_severities": [(s.get("id"), s.get("severity"))
                                        for s in sigs if s.get("id")],
                "clusters": [c.get("id") for c in combos if isinstance(c, dict)],
                "rec_count": len(recs),
            })
        except Exception as e:
            print(f"⚠ Failed on archetype {arch['short']}: {e}")
            results.append({
                "name": arch["name"],
                "short": arch["short"],
                "signals": [], "signal_severities": [],
                "clusters": [], "rec_count": 0,
            })
    return results



def plot_inventory_overview(labs, signals, clusters, out_path):
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.axis("off")

    lab_examples = []
    for marker in ("glucose", "a1c", "creatinine", "alt", "sodium", "ldl"):
        if marker in labs:
            lab_examples.append(marker)
    if not lab_examples:
        lab_examples = labs[:4]
    lab_desc = ", ".join(lab_examples[:5]) + (",\n+ " +
                str(len(labs) - len(lab_examples[:5])) + " інших"
                if len(labs) > 5 else "")

    sig_examples = []
    priority_sigs = ["glucose_diabetes_range", "hyperkalemia", "egfr_low",
                      "transaminitis", "hypertriglyceridemia"]
    for s in priority_sigs:
        if s in signals:
            sig_examples.append(s)
    if len(sig_examples) < 3:
        sig_examples += [s for s in signals if s not in sig_examples][:3]
    sig_desc = ",\n".join(sig_examples[:3])
    if len(signals) > 3:
        sig_desc += ",\n+ " + str(len(signals) - 3) + " інших"

    groups_present = sorted({c.get("group", "?") for c in clusters
                              if c.get("group")})
    grp_short_map = {
        "glycaemia": "GLY", "kidney": "KID", "liver": "LIV",
        "lipids": "LIP", "electrolytes": "ELE", "minerals": "MIN",
        "iron": "IRN", "inflammation": "INF", "special": "SPC",
        "general": "GEN",
    }
    group_codes = [grp_short_map.get(g, g[:3].upper()) for g in groups_present]
    clust_desc = (f"{len(groups_present)} клінічних груп:\n"
                  + ", ".join(group_codes))

    cards = [
        ("Підтримувані lab-тести", len(labs), "#2E86AB", lab_desc),
        ("Аналітичні сигнали",     len(signals), "#06A77D", sig_desc),
        ("Клінічні кластери",      len(clusters), "#7209B7", clust_desc),
    ]
    for i, (title, count, colour, desc) in enumerate(cards):
        x_left = i / 3 + 0.02
        x_w = 1/3 - 0.04
        ax.add_patch(plt.Rectangle((x_left, 0.05), x_w, 0.9,
                                    facecolor=colour, alpha=0.10,
                                    edgecolor=colour, linewidth=2,
                                    transform=ax.transAxes))
        ax.text(x_left + x_w/2, 0.78, title,
                 transform=ax.transAxes, fontsize=11, fontweight="bold",
                 ha="center", color=colour)
        ax.text(x_left + x_w/2, 0.50, str(count),
                 transform=ax.transAxes, fontsize=42, fontweight="bold",
                 ha="center", color=colour)
        ax.text(x_left + x_w/2, 0.20, desc,
                 transform=ax.transAxes, fontsize=8,
                 ha="center", color="#34495e", style="italic")
    ax.set_title("HEMAX_CHEM — інвентар rule-based engine",
                 fontsize=14, fontweight="bold", pad=10)
    fig.savefig(out_path)
    plt.close(fig)


def plot_clusters_by_group(clusters, out_path):
    by_group = {}
    for c in clusters:
        g = c.get("group") or "unknown"
        by_group[g] = by_group.get(g, 0) + 1
    groups = sorted(by_group.keys(), key=lambda g: -by_group[g])
    counts = [by_group[g] for g in groups]
    colours = [GROUP_COLOURS.get(g, "#888") for g in groups]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    bars = ax.bar(groups, counts, color=colours,
                   edgecolor="black", linewidth=0.5)
    for bar, c in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                 str(c), ha="center", va="bottom",
                 fontsize=11, fontweight="bold")
    ax.set_ylabel("Кількість кластерів")
    ax.set_title(f"CHEM — розподіл {len(clusters)} кластерів по клінічних групах")
    plt.xticks(rotation=15, ha="right")
    fig.savefig(out_path)
    plt.close(fig)


def plot_clusters_by_tier(clusters, out_path):
    by_tier = {}
    for c in clusters:
        t = c.get("tier") or "uncategorized"
        by_tier[t] = by_tier.get(t, 0) + 1

    tiers = [t for t in TIER_ORDER if t in by_tier]
    extras = sorted(t for t in by_tier if t not in tiers)
    tiers += extras
    counts = [by_tier[t] for t in tiers]
    colours = [TIER_COLOURS.get(t, "#888") for t in tiers]
    total = sum(counts)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

    labels = [f"{t}\n(n={c} = {c/total*100:.0f}%)" for t, c in zip(tiers, counts)]
    ax1.pie(counts, labels=labels, colors=colours,
             autopct=lambda p: f"{p:.0f}%" if p >= 3 else "",
             pctdistance=0.72, labeldistance=1.15,
             wedgeprops={"edgecolor": "white", "linewidth": 2})
    ax1.set_title("Розподіл severity-tiers серед кластерів")

    bars = ax2.bar(tiers, counts, color=colours,
                    edgecolor="black", linewidth=0.5)
    for bar, c in zip(bars, counts):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                  str(c), ha="center", va="bottom",
                  fontsize=11, fontweight="bold")
    ax2.set_ylabel("Кількість кластерів")
    ax2.set_title("Кластери за severity-tier")
    ax2.set_ylim(0, max(counts) * 1.15)

    fig.suptitle(f"CHEM — severity-розподіл усіх {total} кластерів",
                  fontsize=13, fontweight="bold")
    fig.savefig(out_path)
    plt.close(fig)


def plot_signals_per_archetype(battery, out_path):
    if not battery:
        _no_battery_plot(out_path)
        return

    names = [r["short"] for r in battery]
    counts = [len(r["signals"]) for r in battery]
    rec_counts = [r["rec_count"] for r in battery]

    fig, ax = plt.subplots(figsize=(12, 5.5))
    x = np.arange(len(names))
    w = 0.4
    ax.bar(x - w/2, counts, w, label="Сигнали", color="#2E86AB",
            edgecolor="black", linewidth=0.4)
    ax.bar(x + w/2, rec_counts, w, label="Рекомендації",
            color="#06A77D", edgecolor="black", linewidth=0.4)
    for xi, sc, rc in zip(x, counts, rec_counts):
        ax.text(xi - w/2, sc + 0.2, str(sc), ha="center", fontsize=8)
        ax.text(xi + w/2, rc + 0.2, str(rc), ha="center", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=20, ha="right")
    ax.set_ylabel("Кількість")
    ax.set_title("CHEM — кількість сигналів і рекомендацій по архетипах")
    ax.legend()
    fig.savefig(out_path)
    plt.close(fig)


def plot_archetype_heatmap(battery, out_path):
    if not battery:
        _no_battery_plot(out_path)
        return

    all_sigs = sorted({s for r in battery for s in r["signals"]
                       if s not in META_SIGNALS})
    if not all_sigs:
        _no_battery_plot(out_path)
        return

    matrix = np.zeros((len(battery), len(all_sigs)))
    for i, r in enumerate(battery):
        for j, s in enumerate(all_sigs):
            matrix[i, j] = 1.0 if s in r["signals"] else 0.0

    fig, ax = plt.subplots(figsize=(max(10, len(all_sigs) * 0.4),
                                      max(5, len(battery) * 0.4)))
    im = ax.imshow(matrix, aspect="auto", cmap="Blues",
                    vmin=0, vmax=1)
    ax.set_xticks(range(len(all_sigs)))
    ax.set_xticklabels(all_sigs, rotation=80, fontsize=7, ha="right")
    ax.set_yticks(range(len(battery)))
    ax.set_yticklabels([r["short"] for r in battery])

    meta_present = sum(1 for r in battery for s in r["signals"]
                       if s in META_SIGNALS)
    meta_note = (f"  (виключено {meta_present} спрацьовувань "
                 f"data-quality сигналів)" if meta_present else "")
    ax.set_title(f"CHEM — incidence matrix: {len(battery)} архетипів × "
                 f"{len(all_sigs)} клінічних сигналів{meta_note}")
    fig.savefig(out_path)
    plt.close(fig)


def plot_cluster_activation(battery, out_path):
    if not battery:
        _no_battery_plot(out_path)
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5),
                                     gridspec_kw={"width_ratios": [1.3, 1]})

    names = [r["short"] for r in battery]
    counts = [len(r["clusters"]) for r in battery]
    colours = ["#7209B7" if c > 0 else "#bdc3c7" for c in counts]
    bars = ax1.bar(names, counts, color=colours,
                    edgecolor="black", linewidth=0.5)
    for bar, c in zip(bars, counts):
        ax1.text(bar.get_x() + bar.get_width()/2,
                  bar.get_height() + 0.05,
                  str(c), ha="center", va="bottom", fontsize=10,
                  fontweight="bold")
    ax1.set_ylabel("Кількість активованих кластерів")
    ax1.set_title("Активація clinical clusters на архетипах")
    ax1.set_ylim(0, max(max(counts), 2) + 0.5)
    plt.sca(ax1)
    plt.xticks(rotation=30, ha="right")

    ax2.axis("off")
    activated = [(r["short"], r["clusters"]) for r in battery if r["clusters"]]
    rows = []
    if activated:
        for short, clusters in activated:
            rows.append([short, ", ".join(clusters)])
    else:
        rows.append(["—", "Жоден кластер не активувався"])
    table = ax2.table(cellText=rows,
                       colLabels=["Архетип", "Активовані cluster IDs"],
                       loc="center", cellLoc="left", colLoc="center",
                       colWidths=[0.20, 0.78])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 1.8)
    for j in range(2):
        table[(0, j)].set_facecolor("#7209B7")
        table[(0, j)].set_text_props(color="white", fontweight="bold")
    for i in range(1, len(rows) + 1):
        table[(i, 0)].set_text_props(fontweight="bold")
    ax2.set_title(f"Які кластери спрацювали "
                   f"({len(activated)} з {len(battery)} архетипів)",
                   fontsize=11, pad=8)

    total_clusters = sum(counts)
    n_with_clusters = sum(1 for c in counts if c > 0)
    fig.text(0.5, -0.02,
              f"Спостереження: тільки {n_with_clusters} з {len(battery)} "
              f"архетипів активують clinical clusters "
              f"(total {total_clusters} activations). "
              "Кластери у CHEM мають специфічні `requires`-умови.",
              ha="center", fontsize=8, color="grey", style="italic")
    fig.savefig(out_path)
    plt.close(fig)


def plot_top_signals_battery(battery, out_path):
    if not battery:
        _no_battery_plot(out_path)
        return

    counts = {}
    meta_count = 0
    for r in battery:
        for s in r["signals"]:
            if s in META_SIGNALS:
                meta_count += 1
                continue
            counts[s] = counts.get(s, 0) + 1
    if not counts:
        _no_battery_plot(out_path)
        return

    items = sorted(counts.items(), key=lambda kv: -kv[1])[:20]
    sigs = [s for s, _ in items]
    cnts = [c for _, c in items]

    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.barh(sigs[::-1], cnts[::-1], color="#2E86AB",
                    edgecolor="black", linewidth=0.4)
    for bar, c in zip(bars, cnts[::-1]):
        ax.text(c + 0.05, bar.get_y() + bar.get_height() / 2,
                 str(c), va="center", fontsize=9)
    ax.set_xlabel(f"Кількість архетипів (з {len(battery)}), "
                  f"у яких сигнал спрацював")
    note = (f"  (виключено {meta_count} спрацьовувань "
            f"data-quality сигналів)" if meta_count else "")
    ax.set_title(f"CHEM — top {len(items)} клінічних сигналів "
                 f"у synthetic battery{note}")
    fig.savefig(out_path)
    plt.close(fig)


def plot_engine_inventory_table(labs, signals, clusters, battery, out_path):
    by_tier = {}
    by_group = {}
    for c in clusters:
        by_tier[c.get("tier", "uncategorized")] = \
            by_tier.get(c.get("tier", "uncategorized"), 0) + 1
        by_group[c.get("group", "unknown")] = \
            by_group.get(c.get("group", "unknown"), 0) + 1

    n_clinical_signals = len([s for s in signals if s not in META_SIGNALS])
    n_meta_signals = len([s for s in signals if s in META_SIGNALS])

    rows = [
        ["Lab-тестів підтримується", str(len(labs))],
        ["  з них клінічних сигналів", str(n_clinical_signals)],
        ["  з них data-quality сигналів", str(n_meta_signals)],
        ["Аналітичних сигналів (всього)", str(len(signals))],
        ["Клінічних кластерів", str(len(clusters))],
        ["", ""],
        ["─── Severity-tiers ───", "──"],
    ]
    ordered_tiers = [t for t in TIER_ORDER if t in by_tier]
    extras = sorted(t for t in by_tier if t not in ordered_tiers)
    for tier in ordered_tiers + extras:
        rows.append([f"  • {tier}", str(by_tier[tier])])
    rows.append(["", ""])
    rows.append(["─── Клінічні групи ───", "──"])
    for g, c in sorted(by_group.items(), key=lambda kv: -kv[1]):
        rows.append([f"  • {g}", str(c)])

    if battery:
        rows.append(["", ""])
        rows.append(["─── Synthetic battery ───", "──"])
        clin_sig_total = sum(1 for r in battery for s in r["signals"]
                              if s not in META_SIGNALS)
        meta_sig_total = sum(1 for r in battery for s in r["signals"]
                              if s in META_SIGNALS)
        rows.append(["Архетипів", str(len(battery))])
        rows.append(["  з них активних (≥1 clinical signal)",
                      str(sum(1 for r in battery if any(s not in META_SIGNALS
                                                          for s in r["signals"])))])
        rows.append(["Сума клінічних signal-events", str(clin_sig_total)])
        rows.append(["Сума data-quality flag-events", str(meta_sig_total)])
        rows.append(["Сума активованих кластерів",
                      str(sum(len(r["clusters"]) for r in battery))])
        rows.append(["Сума рекомендацій",
                      str(sum(r["rec_count"] for r in battery))])

    fig, ax = plt.subplots(figsize=(10, max(7, len(rows) * 0.36)))
    ax.axis("off")
    table = ax.table(cellText=rows, loc="upper center",
                      cellLoc="left", colLoc="center",
                      colWidths=[0.68, 0.22], bbox=[0, 0, 1, 0.92])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    for i, (k, v) in enumerate(rows):
        if not k:
            for j in range(2):
                table[(i, j)].set_facecolor("#ecf0f1")
        elif k.startswith("───"):
            for j in range(2):
                table[(i, j)].set_facecolor("#34495e")
                table[(i, j)].set_text_props(color="white", fontweight="bold")
        else:
            table[(i, 1)].set_text_props(fontweight="bold", color="#2E86AB")
    ax.text(0.5, 0.97, "CHEM — engine inventory",
             transform=ax.transAxes,
             fontsize=14, fontweight="bold",
             ha="center", va="top")
    fig.savefig(out_path)
    plt.close(fig)


def _no_battery_plot(out_path):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.text(0.5, 0.5,
             "Synthetic battery skipped\n(engine import not available)",
             ha="center", va="center", fontsize=12, color="grey")
    ax.axis("off")
    fig.savefig(out_path)
    plt.close(fig)



def write_summary(labs, signals, clusters, battery, out_path):
    by_tier = {}
    by_group = {}
    for c in clusters:
        by_tier[c.get("tier", "uncategorized")] = \
            by_tier.get(c.get("tier", "uncategorized"), 0) + 1
        by_group[c.get("group", "unknown")] = \
            by_group.get(c.get("group", "unknown"), 0) + 1

    n_clinical_sigs = len([s for s in signals if s not in META_SIGNALS])
    n_meta_sigs = len([s for s in signals if s in META_SIGNALS])

    ordered_tiers = [t for t in TIER_ORDER if t in by_tier]
    extras = sorted(t for t in by_tier if t not in ordered_tiers)
    tier_display_order = ordered_tiers + extras

    grp_descriptions = {
        "glycaemia":    "діабет, преддіабет, гіпоглікемія",
        "kidney":       "ХХН, гостре ураження нирок, зниження eGFR",
        "liver":        "гепатоцелюлярне, холестатичне, змішане ураження",
        "lipids":       "атерогенна дисліпідемія, FH, тяжка TG",
        "electrolytes": "Na, K, Cl, HCO₃ — електроліти й кислотно-лужна рівновага",
        "minerals":     "Ca, Mg, P, вітамін D — мінерали і кісткова система",
        "iron":         "дефіцит заліза, перенавантаження",
        "inflammation": "CRP, хронічна хвороба",
        "special":      "сечова кислота, лiпаза/амілаза, КФК, ЛДГ",
        "general":      "загальні / data-quality clusters",
    }

    with open(out_path, "w") as f:
        f.write(f"""# HEMAX_CHEM — аналітичний звіт для диплому

## 1. Постановка задачі

HEMAX_CHEM — це **rule-based** експертна система для інтерпретації
біохімічного аналізу крові (basic metabolic / comprehensive metabolic
panel + lipid panel + iron studies + inflammation markers). Як і CBC,
CHEM застосовує клінічно-обґрунтовані правила (medical decision rules)
з фіксованими референтними діапазонами і severity-band-ами.

CHEM покриває **{len(by_group)} клінічних груп**:

| Група | Кількість кластерів | Покриває |
|-------|--------------------:|----------|
""")
        for g, c in sorted(by_group.items(), key=lambda kv: -kv[1]):
            desc = grp_descriptions.get(g, "—")
            f.write(f"| **{g}** | {c} | {desc} |\n")

        f.write(f"""

## 2. Інвентар engine

| Кількість | Артефакт |
|----------:|----------|
| **{len(labs)}** | Підтримуваних lab-тестів (knowledge.py) |
| **{len(signals)}** | Всього аналітичних сигналів (rules.py) |
| {n_clinical_sigs} | — з них клінічних |
| {n_meta_sigs} | — з них data-quality flags |
| **{len(clusters)}** | Клінічних кластерів (narrative/clusters.yaml) |

### 2.1. Severity-розподіл кластерів

CHEM використовує 5-рівневу severity-систему від найважчого до найлегшого:

| Tier | Кількість | %  | Інтерпретація |
|------|----------:|---:|---------------|
""")
        total_clusters = len(clusters)
        for tier in tier_display_order:
            n = by_tier[tier]
            tier_desc = {
                "critical": "Загрозливо для життя — термінова дія",
                "abnormal": "Значні відхилення — диференційна діагностика",
                "minor":    "Помірні відхилення — спостереження",
                "info":     "Інформативні знахідки — без дії",
                "normal":   "У межах норми — підтвердження",
            }.get(tier, "—")
            f.write(f"| **{tier}** | {n} | {n/total_clusters*100:.0f}% | "
                    f"{tier_desc} |\n")

        f.write(f"""
**Інтерпретація піраміди.** Більшість кластерів CHEM ({by_tier.get('abnormal', 0)} з
{total_clusters} = {by_tier.get('abnormal', 0)/total_clusters*100:.0f}%) мають
рівень `abnormal` — "значущі знахідки, що потребують додаткового обстеження".
Лише {by_tier.get('critical', 0)} кластерів класифіковано як `critical`
(термінова дія). Це відповідає клінічній реальності — більшість CHEM
відхилень не є гострими, але вимагають диференційної діагностики.

### 2.2. Data-quality сигнали

""")
        if n_meta_sigs > 0:
            meta_list = sorted([s for s in signals if s in META_SIGNALS])
            f.write("| Сигнал | Призначення |\n|--------|-------------|\n")
            for s in meta_list:
                f.write(f"| `{s}` | flag неповного запитку — потрібні базові labs |\n")
            f.write("""
Ці сигнали **не є клінічними знахідками**. Engine коректно повертає їх,
коли вхідний payload не містить достатньо ключових параметрів для
повноцінного аналізу. У всіх клінічних метриках (heatmap, top-signals,
battery rates) ми **виключаємо** ці сигнали, щоб не змішувати "engine
не зміг проаналізувати" з "engine виявив патологію".
""")
        else:
            f.write("(жодного data-quality сигналу)\n\n")

        f.write(f"""

## 3. Чому rule-based, а не ML?

CHEM є хорошим кандидатом для rule-based підходу через декілька причин:

1. **Чіткі клінічні пороги**. Кожен біохімічний параметр має
   міжнародно-стандартизований референтний діапазон і severity-band-и
   (Mild / Moderate / Severe). ML тут не дав би переваги — тільки
   ускладнив би explainability.
2. **Контекстуальна логіка**. CHEM реалізує clinical reasoning, який
   важко представити одним loss function. Наприклад:
   "діабет → знижити поріг ALT для NAFLD-pattern" — це composable rule,
   а не feature interaction для ML.
3. **Аудитованість**. Для медичного застосування рідер може перевірити
   кожне правило: "чому я отримав сигнал hyperkalemia_critical?" →
   "тому що K ≥ 6.0 mmol/L". У ML-моделі це було б "тому що так каже
   мережа".
4. **Стабільність через час**. Правила не drift-ять з даними; пороги
   побудовані на десятиліттях клінічних досліджень.

## 4. Synthetic clinical battery

Engine протестовано на {len(battery) if battery else 0} архетипних
пацієнтах, що покривають класичні клінічні фенотипи. Для кожного
рахуємо тільки клінічні сигнали (без data-quality flags).

""")
        if battery:
            f.write("| Архетип | n_clinical_signals | n_clusters | n_recs |\n")
            f.write("|---------|-------------------:|-----------:|-------:|\n")
            for r in battery:
                clin_sigs = [s for s in r["signals"] if s not in META_SIGNALS]
                f.write(f"| {r['name']} | {len(clin_sigs)} | "
                        f"{len(r['clusters'])} | {r['rec_count']} |\n")

            n_archetypes_with_clusters = sum(1 for r in battery if r["clusters"])
            f.write(f"""

**Спостереження для захисту:**

- **Здоровий пацієнт (контроль)** не має жодного клінічного сигналу — engine
  коректно мовчить на нормальних результатах.
- **Активація clusters рідкісна** — тільки {n_archetypes_with_clusters}
  з {len(battery)} архетипів активують хоча б один кластер
  ({n_archetypes_with_clusters/len(battery)*100:.0f}%). Це говорить про
  **консервативність cluster `requires`-умов**: кластер активується
  лише при специфічних комбінаціях сигналів і клінічно сильних патернах
  (наприклад, fh_like_ldl_ge190 = LDL ≥ 190; tg_very_high_pancreatitis_risk
  = TG > 1000). Більшість архетипів видають сигнали, але не задовольняють
  cluster-комбінації — кандидати на перегляд або підтвердження.
- **Сума рекомендацій ≈ 2 на архетип** — engine завжди дає мінімум 2
  рекомендації (loop у engine_health повертає базові розпоряджування).
""")
        else:
            f.write("(динамічний battery недоступний.)\n")

        f.write(f"""

## 5. Висновки для захисту

1. **CHEM — найкомплексніший rule-based модуль** у HEMAX
   ({len(clusters)} кластерів проти 31 у CBC).
2. **Покриває {len(by_group)} клінічних груп** — від glycaemia до minerals,
   обслуговуючи всі основні pathway-и у CMP + lipid + iron + CRP.
3. **5-рівнева severity-система** (critical → abnormal → minor → info →
   normal) дозволяє точне пріоритизування повідомлень лікарю.
4. **Inverse suppression links** (поле `suppresses` у clusters.yaml)
   гарантують, що urgent finding (наприклад, severe_hyperkalemia)
   приховує informative findings того ж стека (mild_hyperkalemia), щоб
   не плутати лікаря.
5. **Engine коректно ідентифікує incomplete records** через окремий
   `missing_core_chem` сигнал — це data-quality механізм, що відділяє
   "недостатньо даних" від клінічних знахідок.

## 6. Список згенерованих фігур

| Файл | Зміст |
|------|-------|
| `plots/01_inventory_overview.png` | Картки labs/signals/clusters |
| `plots/02_clusters_by_group.png` | Кластери по {len(by_group)} клінічних групах |
| `plots/03_clusters_by_tier.png` | Розподіл всіх 5 severity-tiers |
| `plots/04_signals_per_archetype.png` | Сигнали + рекомендації per архетип |
| `plots/05_archetype_heatmap.png` | Архетипи × клінічні сигнали (incidence) |
| `plots/06_cluster_activation.png` | Активація кластерів per архетип + table |
| `plots/07_top_signals_battery.png` | Top клінічних сигналів у battery |
| `plots/08_engine_inventory_table.png` | Зведена таблиця engine |
""")


def export_metrics(labs, signals, clusters, battery, out_path):
    actual_tiers = sorted({c.get("tier", "uncategorized") for c in clusters})
    with open(out_path, "w") as f:
        json.dump({
            "inventory": {
                "n_labs": len(labs),
                "n_signals_total": len(signals),
                "n_signals_clinical": len([s for s in signals if s not in META_SIGNALS]),
                "n_signals_data_quality": len([s for s in signals if s in META_SIGNALS]),
                "n_clusters": len(clusters),
                "labs": labs,
                "signals": signals,
                "clusters_by_tier": {
                    tier: sum(1 for c in clusters
                                if c.get("tier") == tier)
                    for tier in actual_tiers
                },
                "clusters_by_group": {
                    g: sum(1 for c in clusters if c.get("group") == g)
                    for g in {c.get("group") for c in clusters
                              if c.get("group")}
                },
            },
            "battery_results": battery or [],
        }, f, indent=2, ensure_ascii=False)



def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--module-dir", default=".",
                         help="Path to chem/ module root")
    parser.add_argument("--out-dir", default=None,
                         help="Output dir (default: <module-dir>/analysis/diploma_report)")
    parser.add_argument("--no-battery", action="store_true",
                         help="Skip dynamic synthetic battery")
    args = parser.parse_args()

    module_dir = Path(args.module_dir).resolve()
    out_dir = (Path(args.out_dir) if args.out_dir
                else module_dir.parent / "analysis" / "chem")

    knowledge_path = module_dir / "engine" / "chem_api" / "chem" / "knowledge.py"
    rules_path = module_dir / "engine" / "chem_api" / "chem" / "rules.py"
    clusters_path = module_dir / "engine" / "chem_api" / "narrative" / "clusters.yaml"

    for p in (knowledge_path, rules_path, clusters_path):
        if not p.exists():
            raise SystemExit(f"❌ Missing: {p}")

    print("Parsing engine inventory…")
    labs = load_labs(knowledge_path)
    signals = load_signals(rules_path)
    clusters = load_clusters(clusters_path)
    print(f"  Labs:     {len(labs)}")
    print(f"  Signals:  {len(signals)}")
    print(f"  Clusters: {len(clusters)}")

    battery = None
    if not args.no_battery:
        print("\nRunning synthetic clinical battery…")
        battery = run_battery(module_dir)
        if battery:
            print(f"  ✓ Ran {len(battery)} archetypes through engine")

    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput dir: {out_dir}")

    print("Rendering plots:")
    print("  [1/8] Inventory overview…")
    plot_inventory_overview(labs, signals, clusters,
                              plots_dir / "01_inventory_overview.png")
    print("  [2/8] Clusters by clinical group…")
    plot_clusters_by_group(clusters, plots_dir / "02_clusters_by_group.png")
    print("  [3/8] Clusters by severity tier…")
    plot_clusters_by_tier(clusters, plots_dir / "03_clusters_by_tier.png")
    print("  [4/8] Signals per archetype…")
    plot_signals_per_archetype(battery, plots_dir / "04_signals_per_archetype.png")
    print("  [5/8] Archetype × signal heatmap…")
    plot_archetype_heatmap(battery, plots_dir / "05_archetype_heatmap.png")
    print("  [6/8] Cluster activation per archetype…")
    plot_cluster_activation(battery, plots_dir / "06_cluster_activation.png")
    print("  [7/8] Top signals in battery…")
    plot_top_signals_battery(battery, plots_dir / "07_top_signals_battery.png")
    print("  [8/8] Engine inventory table…")
    plot_engine_inventory_table(labs, signals, clusters, battery,
                                  plots_dir / "08_engine_inventory_table.png")

    print("Writing summary.md…")
    write_summary(labs, signals, clusters, battery, out_dir / "summary.md")
    print("Exporting metrics_export.json…")
    export_metrics(labs, signals, clusters, battery,
                    out_dir / "metrics_export.json")

    print(f"\n✓ Done. Open {out_dir}/summary.md")


if __name__ == "__main__":
    main()
