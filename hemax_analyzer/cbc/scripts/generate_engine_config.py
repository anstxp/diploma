#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger("engine_config")


MASTER_TO_ENGINE: dict[str, str] = {
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

DATA_DRIVEN_HIGH = {
    "wbc_high":     ("wbc",       "high", False),
    "anc_high":     ("neut_abs",  "high", False),
    "plt_high":     ("plt",       "high", True),
}
DATA_DRIVEN_LOW = {
    "wbc_low":      ("wbc",       "low",  False),
    "anc_low":      ("neut_abs",  "low",  False),
    "plt_low":      ("plt",       "low",  True),
}


def _pooled_minmax_lrl_url(bm_obj: dict, sex: str) -> tuple[float | None, float | None]:
    lrls, urls = [], []
    for label, part in bm_obj["partitions"].items():
        if not label.startswith(sex):
            continue
        if part["n_final"] < 20:
            continue
        if part.get("lrl") is not None and not np.isnan(part["lrl"]):
            lrls.append(part["lrl"])
        if part.get("url") is not None and not np.isnan(part["url"]):
            urls.append(part["url"])
    if not lrls or not urls:
        return None, None
    return min(lrls), max(urls)


PRESERVE_TEXTBOOK_LOW = {
    "hgb",
    "hct",
}

def build_reference_intervals(empirical: dict) -> dict:
    out: dict[str, dict] = {}
    for master_code, bm in empirical["biomarkers"].items():
        if master_code not in MASTER_TO_ENGINE:
            continue
        engine_code = MASTER_TO_ENGINE[master_code]

        f_lrl, f_url = _pooled_minmax_lrl_url(bm, "female")
        m_lrl, m_url = _pooled_minmax_lrl_url(bm, "male")

        if f_lrl is None or m_lrl is None:
            continue

        preserve_low = engine_code in PRESERVE_TEXTBOOK_LOW
        tb_f = bm.get("textbook_female") or [None, None]
        tb_m = bm.get("textbook_male") or [None, None]
        if preserve_low:
            if tb_f[0] is not None: f_lrl = tb_f[0]
            if tb_m[0] is not None: m_lrl = tb_m[0]

        partition = bm.get("recommended_partitioning", ["collapsed"])
        if "sex" in partition:
            out[engine_code] = {
                "partition_by":     "sex",
                "female":           [round(f_lrl, 2), round(f_url, 2)],
                "male":             [round(m_lrl, 2), round(m_url, 2)],
                "source":           "empirical+clinical_floor" if preserve_low else "empirical",
                "textbook_female":  bm.get("textbook_female"),
                "textbook_male":    bm.get("textbook_male"),
            }
        else:
            lrl = min(f_lrl, m_lrl)
            url = max(f_url, m_url)
            out[engine_code] = {
                "partition_by":    "none",
                "any":             [round(lrl, 2), round(url, 2)],
                "source":          "empirical+clinical_floor" if preserve_low else "empirical",
                "textbook_female": bm.get("textbook_female"),
                "textbook_male":   bm.get("textbook_male"),
            }
    return out


def compute_data_driven_severity(master: pd.DataFrame) -> dict:
    bands: dict[str, dict] = {}

    for band_name, (master_col, _, sex_partitioned) in DATA_DRIVEN_HIGH.items():
        if master_col not in master.columns:
            continue
        if sex_partitioned:
            bands[band_name] = {"partition_by": "sex"}
            for sex_code, sex_label in [(1, "male"), (2, "female")]:
                vals = master.loc[
                    master["sex"].eq(sex_code) & master[master_col].notna() &
                    master["age_years"].ge(18),
                    master_col,
                ].to_numpy(dtype=float)
                if len(vals) < 100:
                    continue
                mild      = float(np.percentile(vals, 97.5))
                moderate  = float(np.percentile(vals, 99.0))
                severe    = float(np.percentile(vals, 99.9))
                bands[band_name][sex_label] = {
                    "mild":     round(mild, 2),
                    "moderate": round(moderate, 2),
                    "severe":   round(severe, 2),
                    "n":        int(len(vals)),
                }
        else:
            vals = master.loc[
                master[master_col].notna() & master["age_years"].ge(18),
                master_col,
            ].to_numpy(dtype=float)
            if len(vals) < 100:
                continue
            bands[band_name] = {
                "partition_by": "none",
                "mild":     round(float(np.percentile(vals, 97.5)), 2),
                "moderate": round(float(np.percentile(vals, 99.0)), 2),
                "severe":   round(float(np.percentile(vals, 99.9)), 2),
                "n":        int(len(vals)),
            }

    for band_name, (master_col, _, sex_partitioned) in DATA_DRIVEN_LOW.items():
        if master_col not in master.columns:
            continue
        if sex_partitioned:
            bands[band_name] = {"partition_by": "sex"}
            for sex_code, sex_label in [(1, "male"), (2, "female")]:
                vals = master.loc[
                    master["sex"].eq(sex_code) & master[master_col].notna() &
                    master["age_years"].ge(18),
                    master_col,
                ].to_numpy(dtype=float)
                if len(vals) < 100:
                    continue
                mild      = float(np.percentile(vals,  2.5))
                moderate  = float(np.percentile(vals,  1.0))
                severe    = float(np.percentile(vals,  0.1))
                bands[band_name][sex_label] = {
                    "mild":     round(mild,     2),
                    "moderate": round(moderate, 2),
                    "severe":   round(severe,   2),
                    "n":        int(len(vals)),
                }
        else:
            vals = master.loc[
                master[master_col].notna() & master["age_years"].ge(18),
                master_col,
            ].to_numpy(dtype=float)
            if len(vals) < 100:
                continue
            bands[band_name] = {
                "partition_by": "none",
                "mild":     round(float(np.percentile(vals, 2.5)), 2),
                "moderate": round(float(np.percentile(vals, 1.0)), 2),
                "severe":   round(float(np.percentile(vals, 0.1)), 2),
                "n":        int(len(vals)),
            }

    return bands


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--empirical-refs", type=Path, required=True)
    p.add_argument("--master",         type=Path, required=True)
    p.add_argument("--out",            type=Path, required=True)
    p.add_argument("--log-level",      default="INFO")
    args = p.parse_args()

    logging.basicConfig(level=args.log_level,
                        format="%(asctime)s %(levelname)-7s %(message)s",
                        datefmt="%H:%M:%S")

    for f in [args.empirical_refs, args.master]:
        if not f.is_file():
            sys.exit(f"not found: {f}")

    log.info("loading %s", args.empirical_refs)
    with open(args.empirical_refs) as f:
        empirical = json.load(f)

    log.info("loading %s", args.master)
    master = pd.read_parquet(args.master)

    log.info("building reference intervals...")
    refs = build_reference_intervals(empirical)
    log.info("  → %d biomarkers", len(refs))

    log.info("computing data-driven severity bands from population percentiles...")
    bands = compute_data_driven_severity(master)
    log.info("  → %d bands", len(bands))

    cfg = {
        "metadata": {
            "version":           "1.0",
            "generated_from":    {
                "empirical_refs": str(args.empirical_refs.name),
                "master":         str(args.master.name),
                "master_n":       int(len(master)),
            },
            "method": {
                "reference_intervals": "non-parametric 2.5/97.5 percentiles on "
                                       "healthy cohort (CLSI EP28-A3c); pooled "
                                       "across age bands; sex partition only when "
                                       "Harris-Boyd justified",
                "severity_bands":      "percentiles on full master (adult) for "
                                       "counts-type markers only; WHO/clinical "
                                       "grading retained for hemoglobin",
            },
            "notes": [
                "This config is opt-in. The engine falls back to its textbook "
                "defaults when the file is not loaded.",
                "Pediatric reference ranges are NOT affected — they remain "
                "sourced from NHS paediatric haematology tables.",
                "Hemoglobin severity bands remain WHO-based (mild 10-12/10-13, "
                "moderate 7-10, severe <7) as these are clinical grading "
                "definitions, not statistical tail percentiles.",
            ],
        },
        "reference_intervals": refs,
        "severity_bands":      bands,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(cfg, f, indent=2)
    log.info("wrote %s", args.out)

    print()
    print("=" * 78)
    print(f"Engine config written to: {args.out}")
    print(f"  reference intervals:     {len(refs)} biomarkers")
    print(f"  data-driven severity:    {len(bands)} bands")
    print()
    print("Key severity-band changes vs textbook:")
    text_def = {
        "wbc_high":  {"mild": 11.1,  "moderate": 15.0,   "severe": 25.0},
        "wbc_low":   {"mild": 3.5,   "moderate": 2.0,    "severe": 1.0},
        "anc_high":  {"mild": 7.6,   "moderate": 12.0,   "severe": 20.0},
        "anc_low":   {"mild": 1.5,   "moderate": 1.0,    "severe": 0.5},
        "plt_high":  {"mild": 450.0, "moderate": 600.0,  "severe": 1000.0},
        "plt_low":   {"mild": 150.0, "moderate": 100.0,  "severe": 50.0},
    }
    for band_name, td in text_def.items():
        new = bands.get(band_name)
        if not new: continue
        if new.get("partition_by") == "sex":
            f_new = new.get("female", {}); m_new = new.get("male", {})
            if f_new and m_new:
                print(f"  {band_name:<12} textbook mild={td['mild']:>6.1f}  "
                      f"empirical ♀={f_new.get('mild'):>6.1f}  ♂={m_new.get('mild'):>6.1f}")
        else:
            print(f"  {band_name:<12} textbook mild={td['mild']:>6.1f}  "
                  f"empirical    ={new.get('mild'):>6.1f}")


if __name__ == "__main__":
    main()
