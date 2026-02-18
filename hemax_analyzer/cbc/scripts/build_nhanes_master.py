#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

log = logging.getLogger("nhanes_master")



@dataclass(frozen=True)
class CycleInfo:
    letter: str | None
    prefix: str | None
    overrides: dict

CYCLE_INFO: dict[str, CycleInfo] = {
    "1999-2000": CycleInfo(None, None, {
        "demo":     "DEMO",
        "cbc":      "LAB25",
        "chem":     "LAB18",
        "hba1c":    "LAB10",
        "glu":      "LAB10AM",
        "ins":      "LAB10AM",
        "ogtt":     None,
        "hdl":      "LAB13",
        "tchol":    "LAB13",
        "trigly":   "LAB13AM",
        "apob":     None,
        "hscrp":    "LAB11",
        "ferritin": None,
        "vid":      None,
        "tst":      None,
        "fastqx":   None,
        "bmx":      "BMX",
        "bpx":      "BPX",
        "bpxo":     None,
    }),
    "2001-2002": CycleInfo("B", None, {
        "demo":     "DEMO_B",
        "cbc":      "L25_B",
        "chem":     "L40_B",
        "hba1c":    "L10_B",
        "glu":      "L10_2_B",
        "ins":      "L10_2_B",
        "ogtt":     None,
        "hdl":      "L13_B",
        "tchol":    "L13_B",
        "trigly":   "L13AM_B",
        "apob":     None,
        "hscrp":    "L11_B",
        "ferritin": "L06_B",
        "vid":      None,
        "tst":      None,
        "fastqx":   None,
    }),
    "2003-2004": CycleInfo("C", None, {
        "demo":     "DEMO_C",
        "cbc":      "L25_C",
        "chem":     "L40_C",
        "hba1c":    "L10_C",
        "glu":      "L10AM_C",
        "ins":      "L10AM_C",
        "ogtt":     None,
        "hdl":      "L13_C",
        "tchol":    "L13_C",
        "trigly":   "L13AM_C",
        "apob":     None,
        "hscrp":    "L11_C",
        "ferritin": "L06TFR_C",
        "vid":      None,
        "tst":      None,
        "fastqx":   None,
    }),
    "2005-2006": CycleInfo("D", None, {"hscrp": "CRP_D", "vid": None}),
    "2007-2008": CycleInfo("E", None, {"hscrp": "CRP_E", "vid": None}),
    "2009-2010": CycleInfo("F", None, {"hscrp": "CRP_F", "vid": None}),
    "2011-2012": CycleInfo("G", None, {"hscrp": None}),
    "2013-2014": CycleInfo("H", None, {"hscrp": None}),
    "2015-2016": CycleInfo("I", None, {}),
    "2017-2020": CycleInfo(None, "P_", {
        "bpx":      None,
        "bpxo":     "P_BPXO",
        "ogtt":     None,
        "apob":     None,
        "vid":      None,
    }),
    "2021-2023": CycleInfo("L", None, {
        "bpx":      None,
        "apob":     None,
        "ogtt":     None,
        "hscrp":    None,
    }),
}


STEM_TO_MODERN_NAME = {
    "demo": "DEMO", "cbc": "CBC", "chem": "BIOPRO", "hba1c": "GHB",
    "glu": "GLU",   "ins": "INS", "ogtt": "OGTT",   "hdl": "HDL",
    "tchol": "TCHOL", "trigly": "TRIGLY", "apob": "APOB", "hscrp": "HSCRP",
    "ferritin": "FERTIN", "vid": "VID", "tst": "TST", "fastqx": "FASTQX",
    "bmx": "BMX", "bpx": "BPX", "bpxo": "BPXO",
    "dpq": "DPQ", "slq": "SLQ", "paq": "PAQ", "alq": "ALQ", "smq": "SMQ",
    "dbq": "DBQ", "diq": "DIQ", "bpq": "BPQ", "mcq": "MCQ", "kiq": "KIQ_U",
    "cdq": "CDQ", "whq": "WHQ",
}

STEM_TO_COMPONENT = {
    "demo": "demographics",
    **{s: "laboratory" for s in ["cbc","chem","hba1c","glu","ins","ogtt",
                                  "hdl","tchol","trigly","apob","hscrp",
                                  "ferritin","vid","tst","fastqx"]},
    **{s: "examination" for s in ["bmx","bpx","bpxo"]},
    **{s: "questionnaire" for s in ["dpq","slq","paq","alq","smq","dbq",
                                     "diq","bpq","mcq","kiq","cdq","whq"]},
}



COL_MAP: dict[str, list[str]] = {
    "age_years":     ["RIDAGEYR"],
    "age_months":    ["RIDAGEMN"],
    "sex":           ["RIAGENDR"],
    "race_eth":      ["RIDRETH3", "RIDRETH1"],
    "income_ratio":  ["INDFMPIR"],
    "edu_level":     ["DMDEDUC2"],
    "marital":       ["DMDMARTL"],
    "pregnancy":     ["RIDEXPRG"],
    "birth_country": ["DMDBORN4", "DMDBORN2", "DMDBORN"],

    "wbc":        ["LBXWBCSI"],
    "rbc":        ["LBXRBCSI"],
    "hb_gdl":     ["LBXHGB"],
    "hct":        ["LBXHCT"],
    "mcv":        ["LBXMCVSI"],
    "mch":        ["LBXMCHSI"],
    "mchc":       ["LBXMC"],
    "rdw":        ["LBXRDW"],
    "plt":        ["LBXPLTSI"],
    "mpv":        ["LBXMPSI"],
    "neut_pct":   ["LBXNEPCT"],
    "lymph_pct":  ["LBXLYPCT"],
    "mono_pct":   ["LBXMOPCT"],
    "eos_pct":    ["LBXEOPCT"],
    "baso_pct":   ["LBXBAPCT"],
    "neut_abs":   ["LBDNENO"],
    "lymph_abs":  ["LBDLYMNO"],
    "mono_abs":   ["LBDMONO"],
    "eos_abs":    ["LBDEONO"],
    "baso_abs":   ["LBDBANO"],

    "albumin_gdl":        ["LBXSAL"],
    "alt_ul":             ["LBXSATSI"],
    "ast_ul":             ["LBXSASSI"],
    "alp_ul":             ["LBXSAPSI", "LBDSAPSI"],
    "ggt_ul":             ["LBXSGTSI"],
    "bilirubin_total":    ["LBXSTB"],
    "protein_total_gdl":  ["LBXSTP"],
    "globulin_gdl":       ["LBXSGB"],
    "bun_mgdl":           ["LBXSBU"],
    "creatinine_mgdl":    ["LBXSCR"],
    "glucose_random":     ["LBXSGL"],
    "uric_acid_mgdl":     ["LBXSUA"],
    "calcium_mgdl":       ["LBXSCA"],
    "phosphorus_mgdl":    ["LBXSPH"],
    "sodium_mmoll":       ["LBXSNASI"],
    "potassium_mmoll":    ["LBXSKSI"],
    "chloride_mmoll":     ["LBXSCLSI"],
    "bicarbonate_mmoll":  ["LBXSC3SI"],
    "ck_ul":              ["LBXSCK"],
    "ldh_ul":             ["LBXSLDSI"],
    "iron_chem_ugdl":     ["LBXSIR"],
    "tchol_chem":         ["LBXSCH"],
    "trigly_chem":        ["LBXSTR"],

    "hba1c_pct":          ["LBXGH",  "LB2GH"],
    "glucose_fasting":    ["LBXGLU", "LB2GLU"],
    "insulin_uuml":       ["LBXIN",  "LB2IN"],
    "c_peptide":          ["LBXCP",  "LB2CP", "LBXCPSI"],
    "glucose_2h":         ["LBXGLT"],
    "fasting_hours":      ["PHAFSTHR"],
    "fasting_minutes":    ["PHAFSTMN"],

    "hdl_mgdl":           ["LBDHDD", "LBXHDD", "LBDHDL"],
    "tchol_mgdl":         ["LBXTC"],
    "trigly_mgdl":        ["LBXTR"],
    "ldl_friedewald_src": ["LBDLDL"],
    "apob_mgdl":           ["LBXAPB"],

    "hs_crp":             ["LBXHSCRP", "LBXCRP"],

    "ferritin_ngml":      ["LBXFER", "LBDFER"],
    "vit_d_total":        ["LBXVIDMS", "LBDVIDMS", "LBXVIDSI"],

    "testosterone":       ["LBXTST"],
    "estradiol":          ["LBXEST"],
    "shbg":               ["LBXSHBG"],

    "weight_kg":          ["BMXWT"],
    "height_cm":          ["BMXHT"],
    "bmi":                ["BMXBMI"],
    "waist_cm":           ["BMXWAIST"],
    "hip_cm":             ["BMXHIP"],
    "arm_circ_cm":        ["BMXARMC"],

    "phq9_q1": ["DPQ010"], "phq9_q2": ["DPQ020"], "phq9_q3": ["DPQ030"],
    "phq9_q4": ["DPQ040"], "phq9_q5": ["DPQ050"], "phq9_q6": ["DPQ060"],
    "phq9_q7": ["DPQ070"], "phq9_q8": ["DPQ080"], "phq9_q9": ["DPQ090"],

    "sleep_hours_weekday": ["SLD012", "SLD010H"],
    "sleep_hours_weekend": ["SLD013"],
    "trouble_sleeping":    ["SLQ050"],
    "snore":               ["SLQ030"],
    "daytime_sleepy":      ["SLQ120"],

    "ever_smoked_100":     ["SMQ020"],
    "current_smoker":      ["SMQ040"],

    "drinks_per_day":      ["ALQ130"],
    "drinking_days_mo":    ["ALQ120Q"],

    "told_diabetes":       ["DIQ010"],
    "age_dx_diabetes":     ["DID040"],
    "on_insulin":          ["DIQ050"],
    "on_oral_diabetes_med":["DIQ070"],
    "told_prediabetes":    ["DIQ160"],

    "told_htn":            ["BPQ020"],
    "on_htn_med":          ["BPQ050A"],
    "told_high_chol":      ["BPQ080"],
    "on_chol_med":         ["BPQ100D", "BPQ090D"],

    "told_chf":            ["MCQ160B"],
    "told_chd":            ["MCQ160C"],
    "told_angina":         ["MCQ160D"],
    "told_mi":             ["MCQ160E"],
    "told_stroke":         ["MCQ160F"],
    "told_asthma":         ["MCQ010"],
    "told_cancer":         ["MCQ220"],
    "told_liver":          ["MCQ160L"],
    "told_thyroid":        ["MCQ160M"],

    "told_weak_kidney":    ["KIQ022"],
    "told_dialysis":       ["KIQ025"],

    "vigorous_work":       ["PAQ605"],
    "moderate_work":       ["PAQ620"],
    "vigorous_rec":        ["PAQ650"],
    "moderate_rec":        ["PAQ665"],
    "sedentary_min_day":   ["PAD680"],
}


MISSING_CODES_SMALL = {7.0, 9.0}
MISSING_CODES_LARGE = {77.0, 99.0, 777.0, 999.0}

QN_COLS_SMALL_CODES = {
    "phq9_q1","phq9_q2","phq9_q3","phq9_q4","phq9_q5","phq9_q6","phq9_q7","phq9_q8","phq9_q9",
    "ever_smoked_100","current_smoker",
    "told_diabetes","on_insulin","on_oral_diabetes_med","told_prediabetes",
    "told_htn","on_htn_med","told_high_chol","on_chol_med",
    "told_chf","told_chd","told_angina","told_mi","told_stroke",
    "told_asthma","told_cancer","told_liver","told_thyroid",
    "told_weak_kidney","told_dialysis",
    "vigorous_work","moderate_work","vigorous_rec","moderate_rec",
    "trouble_sleeping","snore","daytime_sleepy","pregnancy","marital","edu_level","race_eth",
}
QN_COLS_LARGE_CODES = {
    "drinks_per_day","drinking_days_mo","age_dx_diabetes",
    "sleep_hours_weekday","sleep_hours_weekend","sedentary_min_day",
}



def resolve_path(csv_root: Path, cycle: str, stem: str) -> Path | None:
    info = CYCLE_INFO[cycle]
    comp = STEM_TO_COMPONENT[stem]
    comp_dir = csv_root / cycle / comp

    if stem in info.overrides:
        ov = info.overrides[stem]
        if ov is None:
            return None
        p = comp_dir / f"{ov}.csv"
        return p if p.exists() else None

    modern = STEM_TO_MODERN_NAME[stem]
    if info.prefix:
        p = comp_dir / f"{info.prefix}{modern}.csv"
    elif info.letter:
        p = comp_dir / f"{modern}_{info.letter}.csv"
    else:
        p = comp_dir / f"{modern}.csv"
    return p if p.exists() else None


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, low_memory=False)
        if "SEQN" in df.columns:
            df["SEQN"] = df["SEQN"].astype("Int64")
        return df
    except Exception as e:
        log.warning("failed to read %s: %s", path, e)
        return pd.DataFrame()



def _take_first_available(df: pd.DataFrame, candidates: Iterable[str]) -> pd.Series:
    for c in candidates:
        if c in df.columns:
            return df[c]
    return pd.Series(np.nan, index=df.index, dtype="float64")


def rename_to_canonical(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    cols: dict[str, pd.Series] = {}
    if "SEQN" in df.columns:
        cols["SEQN"] = df["SEQN"]
    for canonical, sources in COL_MAP.items():
        cols[canonical] = _take_first_available(df, sources)
    return pd.DataFrame(cols)


def _apply_missing_codes(df: pd.DataFrame) -> pd.DataFrame:
    for col in QN_COLS_SMALL_CODES & set(df.columns):
        df.loc[df[col].isin(MISSING_CODES_SMALL), col] = np.nan
    for col in QN_COLS_LARGE_CODES & set(df.columns):
        df.loc[df[col].isin(MISSING_CODES_LARGE), col] = np.nan
    return df



def aggregate_bp(csv_root: Path, cycle: str) -> pd.DataFrame:
    rows = []
    bpx_path = resolve_path(csv_root, cycle, "bpx")
    if bpx_path:
        df = _read_csv(bpx_path)
        if not df.empty:
            sbp_cols = [c for c in ["BPXSY1","BPXSY2","BPXSY3","BPXSY4"] if c in df.columns]
            dbp_cols = [c for c in ["BPXDI1","BPXDI2","BPXDI3","BPXDI4"] if c in df.columns]
            out = pd.DataFrame({"SEQN": df["SEQN"].astype("Int64")})
            out["sbp"]   = df[sbp_cols].mean(axis=1, skipna=True) if sbp_cols else np.nan
            out["dbp"]   = df[dbp_cols].mean(axis=1, skipna=True) if dbp_cols else np.nan
            out["pulse"] = df["BPXPLS"] if "BPXPLS" in df else np.nan
            out["bp_is_oscillometric"] = False
            rows.append(out)

    bpxo_path = resolve_path(csv_root, cycle, "bpxo")
    if bpxo_path:
        df = _read_csv(bpxo_path)
        if not df.empty:
            sbp_cols = [c for c in ["BPXOSY1","BPXOSY2","BPXOSY3"] if c in df.columns]
            dbp_cols = [c for c in ["BPXODI1","BPXODI2","BPXODI3"] if c in df.columns]
            pls_cols = [c for c in ["BPXOPLS1","BPXOPLS2","BPXOPLS3"] if c in df.columns]
            out = pd.DataFrame({"SEQN": df["SEQN"].astype("Int64")})
            sbp = df[sbp_cols].mean(axis=1, skipna=True) if sbp_cols else np.nan
            dbp = df[dbp_cols].mean(axis=1, skipna=True) if dbp_cols else np.nan
            out["sbp"]   = sbp + 1.5 if sbp_cols else np.nan
            out["dbp"]   = dbp - 1.3 if dbp_cols else np.nan
            out["pulse"] = df[pls_cols].mean(axis=1, skipna=True) if pls_cols else np.nan
            out["bp_is_oscillometric"] = True
            rows.append(out)

    if not rows:
        return pd.DataFrame(columns=["SEQN","sbp","dbp","pulse","bp_is_oscillometric"])

    combined = pd.concat(rows, ignore_index=True)
    combined = combined.sort_values(["SEQN","bp_is_oscillometric"]).drop_duplicates("SEQN", keep="last")
    return combined


_STEMS_TO_LOAD = [
    "cbc","chem","hba1c","glu","ins","ogtt","hdl","tchol","trigly","apob",
    "hscrp","ferritin","vid","tst","fastqx",
    "bmx",
    "dpq","slq","paq","alq","smq","dbq","diq","bpq","mcq","kiq","cdq","whq",
]

def build_cycle(csv_root: Path, cycle: str) -> pd.DataFrame:
    log.info("=== %s ===", cycle)

    demo_path = resolve_path(csv_root, cycle, "demo")
    if not demo_path:
        log.warning("no demographics for %s — skipping", cycle)
        return pd.DataFrame()

    demo = rename_to_canonical(_read_csv(demo_path))
    demo["cycle"] = cycle
    log.info("  demo: %d participants", len(demo))

    out = demo

    for stem in _STEMS_TO_LOAD:
        p = resolve_path(csv_root, cycle, stem)
        if not p:
            log.debug("  skip %s (not available)", stem)
            continue
        raw = _read_csv(p)
        if raw.empty:
            continue
        canon = rename_to_canonical(raw)
        keep = ["SEQN"] + [c for c in canon.columns if c != "SEQN" and canon[c].notna().any()]
        canon = canon[keep]
        canon = canon.drop_duplicates("SEQN", keep="first")
        before_cols = set(out.columns)
        out = out.merge(canon, on="SEQN", how="left", suffixes=("", f"__{stem}"))
        for col in canon.columns:
            if col == "SEQN": continue
            dup = f"{col}__{stem}"
            if dup in out.columns and col in before_cols:
                out[col] = out[col].combine_first(out[dup])
                out = out.drop(columns=[dup])
        n_new = len([c for c in canon.columns if c not in before_cols and c != "SEQN"])
        log.info("  %-8s %5d records, +%d new canonical cols", stem, len(canon), n_new)

    bp = aggregate_bp(csv_root, cycle)
    if not bp.empty:
        out = out.merge(bp, on="SEQN", how="left")
        log.info("  bp       %5d records", len(bp))

    out = _apply_missing_codes(out)

    return out



def compute_derived(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    phq_items = [f"phq9_q{i}" for i in range(1, 10)]
    if all(c in df.columns for c in phq_items):
        items = df[phq_items]
        valid_count = items.notna().sum(axis=1)
        phq_total = items.sum(axis=1, skipna=True)
        phq_total = phq_total.where(valid_count >= 7)
        df["phq9_total"] = phq_total
        df["phq9_positive"] = (phq_total >= 10).astype("Int8")
        bins = [-0.01, 4, 9, 14, 19, 27]
        labels = ["minimal", "mild", "moderate", "moderately_severe", "severe"]
        df["phq9_severity"] = pd.cut(phq_total, bins=bins, labels=labels)

    if "weight_kg" in df.columns and "height_cm" in df.columns:
        h_m = df["height_cm"] / 100.0
        df["bmi_calc"] = df["weight_kg"] / (h_m ** 2)
        df["bmi"] = df["bmi"].combine_first(df["bmi_calc"])

    need = {"tchol_mgdl","hdl_mgdl","trigly_mgdl"}
    if need <= set(df.columns):
        ldl_f = df["tchol_mgdl"] - df["hdl_mgdl"] - df["trigly_mgdl"] / 5.0
        ldl_f = ldl_f.where(df["trigly_mgdl"] < 400)
        df["ldl_friedewald"] = ldl_f
        df["ldl_mgdl"] = df.get("ldl_friedewald_src", pd.Series(np.nan, index=df.index)) \
                              .combine_first(ldl_f)
        df["non_hdl_mgdl"] = df["tchol_mgdl"] - df["hdl_mgdl"]

    if {"creatinine_mgdl","sex","age_years"} <= set(df.columns):
        scr = df["creatinine_mgdl"].astype(float)
        age = df["age_years"].astype(float)
        sex = df["sex"].astype(float)
        is_female = (sex == 2)
        K     = np.where(is_female, 0.7, 0.9)
        alpha = np.where(is_female, -0.241, -0.302)
        minr  = np.minimum(scr / K, 1.0)
        maxr  = np.maximum(scr / K, 1.0)
        egfr  = 142.0 * (minr ** alpha) * (maxr ** -1.200) * (0.9938 ** age)
        egfr  = np.where(is_female, egfr * 1.012, egfr)
        df["egfr_ckd_epi_2021"] = np.where(scr.notna() & age.notna() & sex.notna(), egfr, np.nan)

    need = {"age_years","ast_ul","plt","alt_ul"}
    if need <= set(df.columns):
        denom = df["plt"] * np.sqrt(df["alt_ul"])
        df["fib4"] = (df["age_years"] * df["ast_ul"]) / denom.replace(0, np.nan)

    if {"glucose_fasting","insulin_uuml"} <= set(df.columns):
        df["homa_ir"] = df["glucose_fasting"] * df["insulin_uuml"] / 405.0

    if {"waist_cm","sex","trigly_mgdl","hdl_mgdl","sbp","dbp",
        "glucose_fasting","on_htn_med","on_insulin","on_oral_diabetes_med"} <= set(df.columns):
        female = df["sex"] == 2
        crit_waist = (df["waist_cm"] > np.where(female, 88, 102))
        crit_tg    = (df["trigly_mgdl"] >= 150)
        crit_hdl   = (df["hdl_mgdl"] < np.where(female, 50, 40))
        crit_bp    = ((df["sbp"] >= 130) | (df["dbp"] >= 85) | (df["on_htn_med"] == 1))
        on_dm_rx   = ((df["on_insulin"] == 1) | (df["on_oral_diabetes_med"] == 1))
        crit_glu   = ((df["glucose_fasting"] >= 100) | on_dm_rx)
        score = (crit_waist.astype(int) + crit_tg.astype(int) + crit_hdl.astype(int) +
                 crit_bp.astype(int) + crit_glu.astype(int))
        df["metsyn_criteria_count"] = score
        df["metsyn_flag"] = (score >= 3).astype("Int8")

    if "age_years" in df.columns:
        df["is_pediatric"] = (df["age_years"] < 18).astype("Int8")
        df["is_adult"]     = (df["age_years"] >= 18).astype("Int8")
        df["age_group"]    = pd.cut(df["age_years"],
                                    bins=[-0.01, 1, 5, 12, 18, 40, 60, 80, 200],
                                    labels=["infant","early_child","child","teen",
                                            "young_adult","middle_age","senior","elderly"])

    return df



def build_manifest(df: pd.DataFrame) -> dict:
    col_cov = {c: float(df[c].notna().mean()) for c in df.columns}
    by_cycle = {}
    for cyc, sub in df.groupby("cycle", observed=True):
        by_cycle[str(cyc)] = {
            "n_rows": int(len(sub)),
            "coverage": {c: float(sub[c].notna().mean()) for c in sub.columns
                         if sub[c].notna().any()},
        }
    return {
        "n_rows_total": int(len(df)),
        "n_columns":    int(df.shape[1]),
        "cycles":       sorted(df["cycle"].dropna().unique().tolist()),
        "column_coverage_all": col_cov,
        "per_cycle": by_cycle,
    }


def main():
    p = argparse.ArgumentParser(description="Build NHANES master joined dataset.")
    p.add_argument("--csv-root", type=Path, required=True,
                   help="Root of local NHANES CSV mirror.")
    p.add_argument("--out-dir",  type=Path, required=True,
                   help="Output directory for the parquet + manifest.")
    p.add_argument("--cycles", nargs="*", default=None,
                   help="Subset of cycles to build (default: all).")
    p.add_argument("--log-level", default="INFO")
    args = p.parse_args()

    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )

    if not args.csv_root.is_dir():
        sys.exit(f"--csv-root does not exist: {args.csv_root}")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    cycles = args.cycles or list(CYCLE_INFO.keys())
    unknown = [c for c in cycles if c not in CYCLE_INFO]
    if unknown:
        sys.exit(f"unknown cycles requested: {unknown}")

    frames = []
    for cyc in cycles:
        df = build_cycle(args.csv_root, cyc)
        if not df.empty:
            frames.append(df)

    if not frames:
        sys.exit("no cycles produced any data")

    master = pd.concat(frames, ignore_index=True, sort=False)
    log.info("stacking %d cycles → master %d rows × %d cols",
             len(frames), len(master), master.shape[1])

    master = compute_derived(master)
    log.info("derived markers added → final shape %d × %d",
             len(master), master.shape[1])

    parquet_path  = args.out_dir / "nhanes_master.parquet"
    manifest_path = args.out_dir / "nhanes_master_manifest.json"
    master.to_parquet(parquet_path, index=False)
    log.info("wrote %s (%.1f MB)", parquet_path,
             parquet_path.stat().st_size / 1024 / 1024)

    manifest = build_manifest(master)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, default=str)
    log.info("wrote %s", manifest_path)

    print()
    print("=" * 72)
    print(f"NHANES master dataset: {len(master):,} rows × {master.shape[1]} columns")
    print(f"  parquet:  {parquet_path}")
    print(f"  manifest: {manifest_path}")
    print()
    print("Rows per cycle:")
    print(master["cycle"].value_counts().sort_index().to_string())
    print()
    headline = ["age_years","sex","hb_gdl","creatinine_mgdl","hba1c_pct",
                "hdl_mgdl","tchol_mgdl","sbp","dbp","bmi","phq9_total",
                "told_diabetes","told_mi","egfr_ckd_epi_2021","metsyn_flag"]
    print("Non-null counts for headline columns:")
    for c in headline:
        if c in master.columns:
            print(f"  {c:<28} {master[c].notna().sum():>7,}"
                  f"  ({master[c].notna().mean()*100:.1f}%)")


if __name__ == "__main__":
    main()
