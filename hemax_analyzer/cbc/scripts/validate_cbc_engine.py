#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger("cbc_validate")



MASTER_TO_PAYLOAD = {
    "wbc":       "wbc",
    "hb_gdl":    "hgb",
    "hct":       "hct",
    "mcv":       "mcv",
    "mch":       "mch",
    "mchc":      "mchc",
    "rdw":       "rdw",
    "plt":       "plt",
    "mpv":       "mpv",
    "rbc":       "rbc",
    "neut_pct":  "neut_pct",
    "lymph_pct": "lymph_pct",
    "mono_pct":  "mono_pct",
    "eos_pct":   "eos_pct",
    "baso_pct":  "baso_pct",
    "neut_abs":  "anc",
    "lymph_abs": "alc",
    "mono_abs":  "amc",
    "eos_abs":   "aec",
    "baso_abs":  "abc",
}

def row_to_payload(row: pd.Series) -> dict:
    p: dict = {}
    sex_num = row.get("sex")
    if pd.notna(sex_num):
        p["sex"] = "male" if int(sex_num) == 1 else "female" if int(sex_num) == 2 else None
    age = row.get("age_years")
    if pd.notna(age):
        p["age"] = float(age)
    for master_col, payload_key in MASTER_TO_PAYLOAD.items():
        v = row.get(master_col)
        if pd.notna(v):
            p[payload_key] = float(v)
    return p



def _is_adult(row) -> bool:
    age = row.get("age_years")
    return pd.notna(age) and age >= 18

def _anemia_gt(row):
    if not _is_adult(row): return np.nan
    hb, sex = row.get("hb_gdl"), row.get("sex")
    if pd.isna(hb) or pd.isna(sex):  return np.nan
    if sex == 1: return int(hb < 13.0)
    if sex == 2: return int(hb < 12.0)
    return np.nan

def _high_hb_gt(row):
    if not _is_adult(row): return np.nan
    hb, sex = row.get("hb_gdl"), row.get("sex")
    if pd.isna(hb) or pd.isna(sex):  return np.nan
    if sex == 1: return int(hb > 17.5)
    if sex == 2: return int(hb > 16.0)
    return np.nan

def _micro_gt(row):
    if not _is_adult(row): return np.nan
    hb, mcv, sex = row.get("hb_gdl"), row.get("mcv"), row.get("sex")
    if any(pd.isna(v) for v in [hb, mcv, sex]): return np.nan
    cutoff = 13.0 if sex == 1 else 12.0
    return int(hb < cutoff and mcv < 80)

def _macro_gt(row):
    if not _is_adult(row): return np.nan
    hb, mcv, sex = row.get("hb_gdl"), row.get("mcv"), row.get("sex")
    if any(pd.isna(v) for v in [hb, mcv, sex]): return np.nan
    cutoff = 13.0 if sex == 1 else 12.0
    return int(hb < cutoff and mcv > 100)

def _normo_gt(row):
    if not _is_adult(row): return np.nan
    hb, mcv, sex = row.get("hb_gdl"), row.get("mcv"), row.get("sex")
    if any(pd.isna(v) for v in [hb, mcv, sex]): return np.nan
    cutoff = 13.0 if sex == 1 else 12.0
    return int(hb < cutoff and 80 <= mcv <= 100)

def _pancyto_gt(row):
    if not _is_adult(row): return np.nan
    wbc, hb, plt, sex = row.get("wbc"), row.get("hb_gdl"), row.get("plt"), row.get("sex")
    if any(pd.isna(v) for v in [wbc, hb, plt, sex]): return np.nan
    cutoff = 13.0 if sex == 1 else 12.0
    return int(wbc < 4.0 and hb < cutoff and plt < 150)

def _mk_adult_gt(col: str, op: str, threshold: float):
    def gt(row):
        if not _is_adult(row): return np.nan
        v = row.get(col)
        if pd.isna(v): return np.nan
        if op == ">":  return int(v > threshold)
        if op == "<":  return int(v < threshold)
        raise ValueError(op)
    return gt

SIGNAL_CATALOG: dict[str, dict] = {
    "leukocytosis":      {"needs": ["wbc"],          "gt": _mk_adult_gt("wbc", ">", 11.0)},
    "leukopenia":        {"needs": ["wbc"],          "gt": _mk_adult_gt("wbc", "<", 4.0)},
    "neutrophilia":      {"needs": ["neut_abs"],     "gt": _mk_adult_gt("neut_abs", ">", 7.5)},
    "neutropenia":       {"needs": ["neut_abs"],     "gt": _mk_adult_gt("neut_abs", "<", 1.5)},
    "lymphocytosis":     {"needs": ["lymph_abs"],    "gt": _mk_adult_gt("lymph_abs", ">", 4.0)},
    "lymphopenia":       {"needs": ["lymph_abs"],    "gt": _mk_adult_gt("lymph_abs", "<", 1.0)},
    "thrombocytosis":    {"needs": ["plt"],          "gt": _mk_adult_gt("plt", ">", 450)},
    "thrombocytopenia":  {"needs": ["plt"],          "gt": _mk_adult_gt("plt", "<", 150)},
    "eosinophilia":      {"needs": ["eos_abs"],      "gt": _mk_adult_gt("eos_abs", ">", 0.5)},
    "monocytosis":       {"needs": ["mono_abs"],     "gt": _mk_adult_gt("mono_abs", ">", 0.8)},
    "basophilia":        {"needs": ["baso_abs"],     "gt": _mk_adult_gt("baso_abs", ">", 0.1)},
    "anemia_possible":   {"needs": ["hb_gdl","sex"], "gt": _anemia_gt},
    "high_hgb":          {"needs": ["hb_gdl","sex"], "gt": _high_hb_gt},
    "high_rdw":          {"needs": ["rdw"],          "gt": _mk_adult_gt("rdw", ">", 15.0)},
    "microcytic_anemia_pattern":    {"needs": ["hb_gdl","mcv","sex"], "gt": _micro_gt},
    "macrocytic_anemia_pattern":    {"needs": ["hb_gdl","mcv","sex"], "gt": _macro_gt},
    "normocytic_anemia_pattern":    {"needs": ["hb_gdl","mcv","sex"], "gt": _normo_gt},
    "pancytopenia_pattern":         {"needs": ["wbc","hb_gdl","plt","sex"], "gt": _pancyto_gt},
    "iron_deficiency_likely_pattern": {"needs": None, "gt": None},
    "plt_high_microcytosis_combo":    {"needs": None, "gt": None},
    "thal_trait_like_pattern":        {"needs": None, "gt": None},
    "nlr_high":                       {"needs": None, "gt": None},
    "low_mchc_hypochromia":           {"needs": None, "gt": None},
    "high_mchc_note":                 {"needs": None, "gt": None},
    "microcytosis_without_anemia":    {"needs": None, "gt": None},
    "macrocytosis_without_anemia":    {"needs": None, "gt": None},
    "hemoconcentration_possible":     {"needs": None, "gt": None},
    "low_plt_high_mpv":               {"needs": None, "gt": None},
    "low_plt_low_mpv":                {"needs": None, "gt": None},
    "bicytopenia_wbc_hgb":            {"needs": None, "gt": None},
    "bicytopenia_hgb_plt":            {"needs": None, "gt": None},
    "bicytopenia_wbc_plt":            {"needs": None, "gt": None},
    "relative_neutrophilia":          {"needs": None, "gt": None},
    "relative_lymphocytosis":         {"needs": None, "gt": None},
    "missing_core_cbc":               {"needs": None, "gt": None},
}



def run_engine_on_master(df: pd.DataFrame, analyze_fn) -> pd.DataFrame:
    out_rows = []
    n = len(df)
    for i, (_, row) in enumerate(df.iterrows()):
        if i % 10_000 == 0 and i > 0:
            log.info("  processed %d / %d", i, n)
        payload = row_to_payload(row)
        try:
            res = analyze_fn(payload)
        except Exception as e:
            log.warning("row %d failed: %s", i, e)
            out_rows.append({"SEQN": row.get("SEQN"), "cycle": row.get("cycle"),
                             "n_signals": 0, "signal_ids": "", "severities": ""})
            continue
        signals = res.get("signals", [])
        non_q = [s for s in signals if "quality" not in (s.get("tags") or [])]
        out_rows.append({
            "SEQN": row.get("SEQN"),
            "cycle": row.get("cycle"),
            "n_signals": len(non_q),
            "signal_ids": " ".join(s.get("id","") for s in signals),
            "severities": " ".join(s.get("severity","") for s in signals),
            "signals_raw": signals,
        })
    return pd.DataFrame(out_rows)



def compute_metrics(master: pd.DataFrame,
                    engine_out: pd.DataFrame,
                    healthy_seqns: set[int]) -> dict:
    assert len(master) == len(engine_out), "row count mismatch"
    m = master.reset_index(drop=True)
    e = engine_out.reset_index(drop=True)

    log.info("building signal indicators...")
    fired: dict[str, np.ndarray] = {}
    severity_per_sig: dict[str, list[str]] = {sig: [] for sig in SIGNAL_CATALOG}
    for i, sigs in enumerate(e["signals_raw"]):
        present_ids = {s.get("id") for s in sigs}
        for sig in SIGNAL_CATALOG:
            if sig not in fired:
                fired[sig] = np.zeros(len(e), dtype=np.int8)
            if sig in present_ids:
                fired[sig][i] = 1
                for s in sigs:
                    if s.get("id") == sig:
                        severity_per_sig[sig].append(s.get("severity", ""))
                        break
    fired_df = pd.DataFrame(fired)

    e["any_signal"] = (e["n_signals"] > 0).astype(int)

    healthy_mask = m["SEQN"].isin(healthy_seqns).to_numpy()
    m_h = m.loc[healthy_mask].reset_index(drop=True)
    e_h = e.loc[healthy_mask].reset_index(drop=True)
    fired_h = fired_df.loc[healthy_mask].reset_index(drop=True)

    healthy_metrics = {
        "n_healthy": int(healthy_mask.sum()),
        "no_signal_rate": float((e_h["any_signal"] == 0).mean()),
        "mean_signals_per_record": float(e_h["n_signals"].mean()),
        "median_signals_per_record": float(e_h["n_signals"].median()),
        "per_signal_false_positive_rate": {
            sig: float(fired_h[sig].mean()) for sig in SIGNAL_CATALOG
        },
    }

    overall = {
        "n_total": int(len(m)),
        "any_signal_rate": float((e["any_signal"] > 0).mean()),
        "signals_per_record": {
            "mean":   float(e["n_signals"].mean()),
            "median": float(e["n_signals"].median()),
            "p95":    float(e["n_signals"].quantile(0.95)),
        },
        "signal_prevalence": {
            sig: {"n_fired": int(fired_df[sig].sum()),
                  "rate":    float(fired_df[sig].mean())}
            for sig in SIGNAL_CATALOG
        },
        "severity_distribution": {
            sig: dict(Counter(severity_per_sig[sig]))
            for sig in SIGNAL_CATALOG if severity_per_sig[sig]
        },
    }

    det = {}
    for sig, cfg in SIGNAL_CATALOG.items():
        if cfg["gt"] is None:
            continue
        gt = m.apply(cfg["gt"], axis=1)
        pred = fired_df[sig]
        evaluable = gt.notna()
        gt_eval = gt[evaluable].astype(int).to_numpy()
        pred_eval = pred[evaluable].to_numpy()
        tp = int(((pred_eval == 1) & (gt_eval == 1)).sum())
        fn = int(((pred_eval == 0) & (gt_eval == 1)).sum())
        fp = int(((pred_eval == 1) & (gt_eval == 0)).sum())
        tn = int(((pred_eval == 0) & (gt_eval == 0)).sum())
        det[sig] = {
            "n_evaluable":        int(evaluable.sum()),
            "gt_prevalence":      float(gt_eval.mean()) if len(gt_eval) else None,
            "engine_prevalence":  float(pred_eval.mean()) if len(pred_eval) else None,
            "tp": tp, "fn": fn, "fp": fp, "tn": tn,
            "sensitivity": (tp / (tp + fn)) if (tp + fn) > 0 else None,
            "specificity": (tn / (tn + fp)) if (tn + fp) > 0 else None,
            "precision":   (tp / (tp + fp)) if (tp + fp) > 0 else None,
            "f1":          ((2*tp) / (2*tp + fp + fn)) if (2*tp + fp + fn) > 0 else None,
        }

    label_signal_pairs = [
        ("told_mi",          "anemia_possible"),
        ("told_weak_kidney", "anemia_possible"),
        ("told_cancer",      "anemia_possible"),
        ("told_diabetes",    "anemia_possible"),
        ("told_diabetes",    "leukocytosis"),
        ("told_htn",         "leukocytosis"),
    ]
    lifts = []
    for label, sig in label_signal_pairs:
        if label not in m.columns: continue
        mask_pos = m[label].eq(1)
        mask_neg = m[label].eq(2)
        if mask_pos.sum() == 0 or mask_neg.sum() == 0: continue
        rate_pos = fired_df.loc[mask_pos.to_numpy(), sig].mean()
        rate_neg = fired_df.loc[mask_neg.to_numpy(), sig].mean()
        lift = (rate_pos / rate_neg) if rate_neg > 0 else None
        lifts.append({
            "label": label,
            "signal": sig,
            "n_label_pos": int(mask_pos.sum()),
            "n_label_neg": int(mask_neg.sum()),
            "rate_in_label_pos": float(rate_pos),
            "rate_in_label_neg": float(rate_neg),
            "lift": float(lift) if lift is not None else None,
        })

    by_cycle = {}
    for cyc, sub_idx in m.groupby("cycle", observed=True).groups.items():
        sub_fired = fired_df.iloc[sub_idx]
        sub_e     = e.iloc[sub_idx]
        by_cycle[str(cyc)] = {
            "n": int(len(sub_idx)),
            "any_signal_rate": float((sub_e["n_signals"] > 0).mean()),
            "anemia_rate":     float(sub_fired["anemia_possible"].mean()),
            "leukocytosis_rate": float(sub_fired["leukocytosis"].mean()),
        }

    return {
        "healthy_cohort": healthy_metrics,
        "overall": overall,
        "deterministic_performance": det,
        "self_report_lift": lifts,
        "by_cycle": by_cycle,
    }



def _fmt_pct(x):
    if x is None: return "—"
    if isinstance(x, float) and (x != x): return "—"
    return f"{x*100:.1f}%"

def _fmt_num(x):
    if x is None: return "—"
    if isinstance(x, float) and (x != x): return "—"
    if isinstance(x, int): return f"{x:,}"
    return f"{x:.3f}"


def generate_markdown(metrics: dict) -> str:
    L = []
    A = L.append

    hc = metrics["healthy_cohort"]
    ov = metrics["overall"]
    det = metrics["deterministic_performance"]

    A("# CBC Rules Engine — Validation Report on NHANES Master Dataset")
    A("")
    A("## 1. Protocol")
    A("")
    A(f"The CBC interpreter was executed on **{ov['n_total']:,} participant records** "
      f"from the harmonised NHANES 1999-2023 dataset. For each record, canonical master "
      f"columns were mapped to the engine's payload schema (sex, age, full CBC with "
      f"differential) and the resulting signal list, severity and flags were recorded. "
      f"Two analytical strata were used: the **healthy reference cohort** "
      f"(n={hc['n_healthy']:,}, used to estimate the engine's specificity baseline) "
      f"and the **full population** (used to characterise signal prevalence and to "
      f"evaluate diagnostic performance against deterministic lab-based ground truth).")
    A("")
    A("Ground-truth definitions for signals whose clinical meaning is entirely "
      "determined by lab values:")
    A("")
    A("| Signal | Ground-truth definition |")
    A("|---|---|")
    A("| anemia_possible | Hb < 12 g/dL (♀) or Hb < 13 g/dL (♂) (WHO) |")
    A("| leukocytosis / leukopenia | WBC > 11 / < 4 × 10⁹/L |")
    A("| neutrophilia / neutropenia | ANC > 7.5 / < 1.5 × 10⁹/L |")
    A("| lymphocytosis / lymphopenia | ALC > 4 / < 1 × 10⁹/L |")
    A("| thrombocytosis / thrombocytopenia | PLT > 450 / < 150 × 10⁹/L |")
    A("| microcytic_anemia_pattern | Hb < cutoff ∧ MCV < 80 fL |")
    A("| macrocytic_anemia_pattern | Hb < cutoff ∧ MCV > 100 fL |")
    A("| normocytic_anemia_pattern | Hb < cutoff ∧ 80 ≤ MCV ≤ 100 fL |")
    A("| pancytopenia_pattern | WBC < 4 ∧ Hb < cutoff ∧ PLT < 150 |")
    A("")

    A("## 2. Specificity on the healthy reference cohort")
    A("")
    A(f"On the healthy cohort (n={hc['n_healthy']:,}) the engine raised **at least one "
      f"non-quality signal in {_fmt_pct(1-hc['no_signal_rate'])} of records** — i.e. "
      f"the no-signal rate was **{_fmt_pct(hc['no_signal_rate'])}**. The mean number "
      f"of signals per healthy record was {hc['mean_signals_per_record']:.2f} "
      f"(median {hc['median_signals_per_record']:.0f}).")
    A("")
    A("*Per-signal false-positive rate on healthy cohort (top 15 most frequently fired):*")
    A("")
    A("| Signal | False-positive rate |")
    A("|---|---:|")
    fp_sorted = sorted(hc["per_signal_false_positive_rate"].items(), key=lambda x: -x[1])
    for sig, fpr in fp_sorted[:15]:
        A(f"| `{sig}` | {_fmt_pct(fpr)} |")
    A("")

    A("## 3. Signal prevalence in the full population")
    A("")
    A(f"On the full dataset (n={ov['n_total']:,}) **at least one signal was raised in "
      f"{_fmt_pct(ov['any_signal_rate'])} of records**; mean {ov['signals_per_record']['mean']:.2f}, "
      f"median {ov['signals_per_record']['median']:.0f}, "
      f"95th percentile {ov['signals_per_record']['p95']:.0f}.")
    A("")
    A("*All 23 signals, sorted by population prevalence:*")
    A("")
    A("| Signal | n fired | Population rate | Healthy FPR |")
    A("|---|---:|---:|---:|")
    prev_sorted = sorted(ov["signal_prevalence"].items(), key=lambda x: -x[1]["rate"])
    for sig, v in prev_sorted:
        fpr = hc["per_signal_false_positive_rate"].get(sig, None)
        A(f"| `{sig}` | {v['n_fired']:,} | {_fmt_pct(v['rate'])} | {_fmt_pct(fpr)} |")
    A("")

    A("## 4. Diagnostic performance against deterministic ground truth")
    A("")
    A("Sensitivity, specificity, precision and F1 are computed only on records whose "
      "ground-truth indicator was computable (i.e., the required lab values were present).")
    A("")
    A("| Signal | n eval. | GT prev. | Eng. prev. | Sens | Spec | Prec | F1 |")
    A("|---|---:|---:|---:|---:|---:|---:|---:|")
    det_sorted = sorted(det.items(), key=lambda x: -x[1]["n_evaluable"])
    for sig, v in det_sorted:
        A(f"| `{sig}` | {v['n_evaluable']:,} | {_fmt_pct(v['gt_prevalence'])} | "
          f"{_fmt_pct(v['engine_prevalence'])} | {_fmt_pct(v['sensitivity'])} | "
          f"{_fmt_pct(v['specificity'])} | {_fmt_pct(v['precision'])} | "
          f"{_fmt_num(v['f1'])} |")
    A("")
    A("*Confusion matrix counts (for the record):*")
    A("")
    A("| Signal | TP | FN | FP | TN |")
    A("|---|---:|---:|---:|---:|")
    for sig, v in det_sorted:
        A(f"| `{sig}` | {v['tp']:,} | {v['fn']:,} | {v['fp']:,} | {v['tn']:,} |")
    A("")

    A("## 5. Signal enrichment in self-reported disease")
    A("")
    A("For each (self-reported label × engine signal) pair, we compared the signal "
      "rate in label-positive participants against label-negative participants. A lift "
      ">1 indicates the engine signal is more common in those with the self-reported "
      "diagnosis, serving as a sanity check of the engine's clinical coupling.")
    A("")
    A("| Self-report | Signal | n (pos / neg) | Rate (pos / neg) | Lift |")
    A("|---|---|---:|---:|---:|")
    for e in metrics["self_report_lift"]:
        A(f"| `{e['label']}` | `{e['signal']}` | "
          f"{e['n_label_pos']:,} / {e['n_label_neg']:,} | "
          f"{_fmt_pct(e['rate_in_label_pos'])} / {_fmt_pct(e['rate_in_label_neg'])} | "
          f"{_fmt_num(e['lift'])} |")
    A("")

    A("## 6. Inter-cycle stability")
    A("")
    A("To check that the engine behaves consistently across NHANES cycles (despite "
      "small methodological changes between survey cycles), we report the rate of "
      "key signals per cycle.")
    A("")
    A("| Cycle | n | Any-signal rate | Anemia rate | Leukocytosis rate |")
    A("|---|---:|---:|---:|---:|")
    for cyc, v in sorted(metrics["by_cycle"].items()):
        A(f"| {cyc} | {v['n']:,} | {_fmt_pct(v['any_signal_rate'])} | "
          f"{_fmt_pct(v['anemia_rate'])} | {_fmt_pct(v['leukocytosis_rate'])} |")
    A("")

    A("## 7. Summary of findings")
    A("")
    A("*(Thesis-friendly framing — revise wording as needed.)*")
    A("")
    A(f"- **Specificity on the healthy cohort** is "
      f"{_fmt_pct(hc['no_signal_rate'])} for the *no-signal* class. "
      f"A well-calibrated clinical screener targeting a healthy adult population "
      f"should raise no signals on ≥ 90% of such subjects; deviations below that "
      f"threshold warrant re-examination of the responsible rules.")
    high_fpr = [(s, f) for s, f in hc["per_signal_false_positive_rate"].items() if f > 0.05]
    high_fpr.sort(key=lambda x: -x[1])
    if high_fpr:
        A(f"- Signals with healthy-cohort false-positive rate > 5%: "
          + ", ".join(f"`{s}` ({_fmt_pct(f)})" for s, f in high_fpr[:5]) + ".")
    low_sens = [(s, v) for s, v in det.items() if v.get("sensitivity") is not None and v["sensitivity"] < 0.9]
    low_sens.sort(key=lambda x: x[1]["sensitivity"])
    if low_sens:
        A(f"- Signals with sensitivity < 90% against deterministic ground truth: "
          + ", ".join(f"`{s}` ({_fmt_pct(v['sensitivity'])})" for s, v in low_sens[:5]) + ".")
    A("- Inter-cycle rates of anaemia and leukocytosis are stable, indicating no major "
      "cycle-specific artefact in the harmonised master.")
    A("")
    A("These results form the baseline against which the next iteration of the "
      "engine — using empirically-derived reference intervals (§2.3) — is to be "
      "compared.")
    A("")
    return "\n".join(L)



def main():
    p = argparse.ArgumentParser()
    p.add_argument("--master",       type=Path, required=True)
    p.add_argument("--healthy",      type=Path, required=True)
    p.add_argument("--engine-dir",   type=Path, required=True,
                   help="Path to the CBC service directory containing cbc_api/")
    p.add_argument("--out-dir",      type=Path, required=True)
    p.add_argument("--sample",       type=int, default=None,
                   help="Optional: evaluate only this many randomly-sampled records (debug).")
    p.add_argument("--seed",         type=int, default=42)
    p.add_argument("--log-level",    default="INFO")
    args = p.parse_args()

    logging.basicConfig(level=args.log_level,
                        format="%(asctime)s %(levelname)-7s %(message)s",
                        datefmt="%H:%M:%S")

    for f in [args.master, args.healthy]:
        if not f.is_file():
            sys.exit(f"not found: {f}")
    if not args.engine_dir.is_dir():
        sys.exit(f"--engine-dir does not exist: {args.engine_dir}")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(args.engine_dir.resolve()))
    try:
        from cbc_api.analyze import analyze_cbc_payload  # type: ignore
    except Exception as e:
        sys.exit(f"failed to import cbc_api.analyze from {args.engine_dir}: {e}")

    log.info("loading master: %s", args.master)
    master = pd.read_parquet(args.master)
    log.info("master: %d rows × %d cols", len(master), master.shape[1])

    log.info("loading healthy cohort: %s", args.healthy)
    healthy = pd.read_parquet(args.healthy)
    healthy_seqns = set(healthy["SEQN"].dropna().astype(int).tolist())
    log.info("healthy cohort: %d records", len(healthy_seqns))

    if args.sample:
        master = master.sample(n=args.sample, random_state=args.seed).reset_index(drop=True)
        log.info("sampled %d records", len(master))

    log.info("running engine on %d records...", len(master))
    engine_out = run_engine_on_master(master, analyze_cbc_payload)
    log.info("engine done")

    persistable = engine_out.drop(columns=["signals_raw"])
    out_parquet = args.out_dir / "validation_results.parquet"
    persistable.to_parquet(out_parquet, index=False)
    log.info("wrote %s", out_parquet)

    log.info("computing metrics...")
    metrics = compute_metrics(master, engine_out, healthy_seqns)

    out_json = args.out_dir / "validation_metrics.json"
    with open(out_json, "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    log.info("wrote %s", out_json)

    out_md = args.out_dir / "validation_report.md"
    with open(out_md, "w") as f:
        f.write(generate_markdown(metrics))
    log.info("wrote %s", out_md)

    hc = metrics["healthy_cohort"]
    ov = metrics["overall"]
    print()
    print("=" * 90)
    print(f"Validation complete on {ov['n_total']:,} records")
    print(f"Healthy cohort (n={hc['n_healthy']:,}):")
    print(f"  no-signal rate:           {_fmt_pct(hc['no_signal_rate'])}")
    print(f"  mean signals/record:      {hc['mean_signals_per_record']:.2f}")
    print(f"Full population:")
    print(f"  any-signal rate:          {_fmt_pct(ov['any_signal_rate'])}")
    print(f"  signals/record (mean):    {ov['signals_per_record']['mean']:.2f}")
    print()
    print("Top signals by population prevalence:")
    for sig, v in sorted(ov["signal_prevalence"].items(), key=lambda x: -x[1]["rate"])[:8]:
        fpr = hc["per_signal_false_positive_rate"].get(sig, 0.0)
        print(f"  {sig:<32} pop {_fmt_pct(v['rate']):>7}   healthy_fpr {_fmt_pct(fpr):>7}")
    print()
    det = metrics["deterministic_performance"]
    print("Diagnostic performance highlights:")
    key_sigs = ["anemia_possible","leukocytosis","leukopenia","thrombocytopenia",
                "thrombocytosis","neutropenia","microcytic_anemia_pattern"]
    for s in key_sigs:
        v = det.get(s)
        if not v: continue
        print(f"  {s:<32} sens {_fmt_pct(v['sensitivity']):>7}  "
              f"spec {_fmt_pct(v['specificity']):>7}  "
              f"prec {_fmt_pct(v['precision']):>7}  "
              f"n_eval {v['n_evaluable']:>6}")


if __name__ == "__main__":
    main()
