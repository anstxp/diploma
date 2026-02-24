#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from typing import Any

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)
sys.path.insert(0, os.path.abspath(os.path.join(_here, "..", "engine")))

from cbc_api import analyze_cbc_payload
from cbc_api.rules import reload_empirical_config, empirical_active



PATIENTS: list[tuple[str, str, dict[str, Any]]] = [
    ("Healthy young woman",
     "28-year-old, baseline metrics — engine should be silent",
     {
        "sex": "female", "age": 28,
        "wbc": 6.2, "hgb": 13.4, "hct": 40.5, "rbc": 4.55,
        "mcv": 89, "mch": 29.5, "mchc": 33.1, "rdw": 12.8,
        "plt": 265, "mpv": 9.8,
        "neut_pct": 58, "lymph_pct": 32, "mono_pct": 7, "eos_pct": 2.5, "baso_pct": 0.5,
        "anc": 3.6, "alc": 2.0, "amc": 0.43, "aec": 0.16, "abc": 0.03,
     }),

    ("Iron-deficiency anaemia — young woman with heavy menses",
     "Classic IDA pattern: low Hb, low MCV, high RDW",
     {
        "sex": "female", "age": 30,
        "wbc": 6.8, "hgb": 9.5, "hct": 31.2, "rbc": 4.2,
        "mcv": 72, "mch": 22.6, "mchc": 30.4, "rdw": 17.1,
        "plt": 410, "mpv": 10.5,
        "neut_pct": 55, "lymph_pct": 35, "mono_pct": 7, "eos_pct": 2.5, "baso_pct": 0.5,
        "anc": 3.74, "alc": 2.38, "amc": 0.48, "aec": 0.17, "abc": 0.03,
     }),

    ("Macrocytic anaemia — suspected B12 / folate deficiency",
     "Low Hb with elevated MCV (B12/folate def, or alcohol, or MDS)",
     {
        "sex": "male", "age": 55,
        "wbc": 5.1, "hgb": 11.8, "hct": 36.0, "rbc": 3.3,
        "mcv": 108, "mch": 35.8, "mchc": 32.8, "rdw": 16.5,
        "plt": 185, "mpv": 10.2,
        "neut_pct": 60, "lymph_pct": 30, "mono_pct": 7, "eos_pct": 2.5, "baso_pct": 0.5,
        "anc": 3.06, "alc": 1.53, "amc": 0.36, "aec": 0.13, "abc": 0.03,
     }),

    ("Acute bacterial infection — pneumonia",
     "Leukocytosis with left shift: high WBC + high neutrophils",
     {
        "sex": "female", "age": 42,
        "wbc": 16.2, "hgb": 13.1, "hct": 40.0, "rbc": 4.4,
        "mcv": 91, "mch": 29.8, "mchc": 32.7, "rdw": 13.0,
        "plt": 380, "mpv": 9.6,
        "neut_pct": 82, "lymph_pct": 10, "mono_pct": 6, "eos_pct": 1.5, "baso_pct": 0.5,
        "anc": 13.28, "alc": 1.62, "amc": 0.97, "aec": 0.24, "abc": 0.08,
     }),

    ("Elderly male with CKD",
     "Normocytic anaemia typical of renal EPO deficiency",
     {
        "sex": "male", "age": 72,
        "wbc": 7.1, "hgb": 10.8, "hct": 33.5, "rbc": 3.6,
        "mcv": 93, "mch": 30.0, "mchc": 32.2, "rdw": 14.2,
        "plt": 230, "mpv": 10.1,
        "neut_pct": 62, "lymph_pct": 25, "mono_pct": 9, "eos_pct": 3, "baso_pct": 1,
        "anc": 4.4, "alc": 1.78, "amc": 0.64, "aec": 0.21, "abc": 0.07,
     }),

    ("Paediatric case — 4-year-old with mild anaemia",
     "Child — engine must use paediatric refs, not adult WHO cutoffs",
     {
        "sex": "female", "age": 4,
        "wbc": 8.5, "hgb": 11.0, "hct": 34.0, "rbc": 4.2,
        "mcv": 81, "mch": 26.2, "mchc": 32.4, "rdw": 14.0,
        "plt": 310, "mpv": 9.0,
        "neut_pct": 40, "lymph_pct": 50, "mono_pct": 7, "eos_pct": 2.5, "baso_pct": 0.5,
        "anc": 3.4, "alc": 4.25, "amc": 0.6, "aec": 0.21, "abc": 0.04,
     }),

    ("Pancytopenia — haematology red flag",
     "All three lineages low — must trigger pancytopenia_pattern at high severity",
     {
        "sex": "male", "age": 60,
        "wbc": 3.2, "hgb": 9.8, "hct": 30.5, "rbc": 3.3,
        "mcv": 92, "mch": 29.7, "mchc": 32.1, "rdw": 14.8,
        "plt": 110, "mpv": 10.8,
        "neut_pct": 45, "lymph_pct": 42, "mono_pct": 10, "eos_pct": 2.5, "baso_pct": 0.5,
        "anc": 1.44, "alc": 1.34, "amc": 0.32, "aec": 0.08, "abc": 0.02,
     }),

    ("Beta-thalassemia minor (trait)",
     "Microcytic w/o anaemia: low MCV + high RBC + normal RDW — classic trait signature",
     {
        "sex": "female", "age": 35,
        "wbc": 6.5, "hgb": 12.2, "hct": 37.5, "rbc": 5.85,
        "mcv": 65, "mch": 20.8, "mchc": 32.5, "rdw": 13.2,
        "plt": 260, "mpv": 9.4,
        "neut_pct": 58, "lymph_pct": 32, "mono_pct": 7, "eos_pct": 2.5, "baso_pct": 0.5,
        "anc": 3.77, "alc": 2.08, "amc": 0.46, "aec": 0.16, "abc": 0.03,
     }),

    ("Polycythemia vera — suspected JAK2+",
     "Elevated RBC/Hb/Hct in a male non-smoker; also high WBC and PLT typical of PV",
     {
        "sex": "male", "age": 58,
        "wbc": 12.8, "hgb": 18.9, "hct": 56.8, "rbc": 6.52,
        "mcv": 87, "mch": 29.0, "mchc": 33.3, "rdw": 14.5,
        "plt": 520, "mpv": 10.6,
        "neut_pct": 68, "lymph_pct": 22, "mono_pct": 7, "eos_pct": 2.5, "baso_pct": 0.5,
        "anc": 8.7, "alc": 2.82, "amc": 0.90, "aec": 0.32, "abc": 0.06,
     }),

    ("Chronic lymphocytic leukemia — CLL suspected",
     "Marked lymphocytosis in an older adult; isolated ALC ≫ upper",
     {
        "sex": "male", "age": 68,
        "wbc": 28.5, "hgb": 12.8, "hct": 39.0, "rbc": 4.30,
        "mcv": 90, "mch": 29.8, "mchc": 32.8, "rdw": 13.5,
        "plt": 180, "mpv": 9.9,
        "neut_pct": 20, "lymph_pct": 74, "mono_pct": 4, "eos_pct": 1.5, "baso_pct": 0.5,
        "anc": 5.70, "alc": 21.09, "amc": 1.14, "aec": 0.43, "abc": 0.14,
     }),

    ("Eosinophilia — asthmatic with parasite risk",
     "Elevated eosinophils with reasonable normal rest of CBC",
     {
        "sex": "female", "age": 34,
        "wbc": 8.9, "hgb": 13.6, "hct": 41.0, "rbc": 4.55,
        "mcv": 90, "mch": 29.9, "mchc": 33.2, "rdw": 12.8,
        "plt": 290, "mpv": 9.5,
        "neut_pct": 48, "lymph_pct": 28, "mono_pct": 7, "eos_pct": 16, "baso_pct": 1,
        "anc": 4.27, "alc": 2.49, "amc": 0.62, "aec": 1.42, "abc": 0.09,
     }),

    ("Post-splenectomy reactive state",
     "Marked thrombocytosis + leukocytosis; classic post-splenectomy blood picture",
     {
        "sex": "male", "age": 45,
        "wbc": 13.5, "hgb": 14.2, "hct": 43.0, "rbc": 4.80,
        "mcv": 89, "mch": 29.6, "mchc": 33.0, "rdw": 13.8,
        "plt": 720, "mpv": 11.2,
        "neut_pct": 62, "lymph_pct": 28, "mono_pct": 7, "eos_pct": 2.5, "baso_pct": 0.5,
        "anc": 8.37, "alc": 3.78, "amc": 0.95, "aec": 0.34, "abc": 0.07,
     }),

    ("Hemoconcentration (dehydration)",
     "Hct and Hgb elevated due to volume depletion — RBC/MCV normal",
     {
        "sex": "female", "age": 40,
        "wbc": 7.2, "hgb": 16.4, "hct": 49.5, "rbc": 5.10,
        "mcv": 92, "mch": 30.2, "mchc": 33.1, "rdw": 13.0,
        "plt": 270, "mpv": 9.7,
        "neut_pct": 60, "lymph_pct": 30, "mono_pct": 7, "eos_pct": 2.5, "baso_pct": 0.5,
        "anc": 4.32, "alc": 2.16, "amc": 0.50, "aec": 0.18, "abc": 0.04,
     }),

    ("Severe sepsis with ITP-like picture",
     "Critical combo: low neutrophils + severely low platelets — meets several bicytopenia patterns",
     {
        "sex": "female", "age": 55,
        "wbc": 2.8, "hgb": 11.5, "hct": 35.0, "rbc": 3.85,
        "mcv": 91, "mch": 29.9, "mchc": 32.8, "rdw": 14.0,
        "plt": 38, "mpv": 12.1,
        "neut_pct": 40, "lymph_pct": 50, "mono_pct": 8, "eos_pct": 1.5, "baso_pct": 0.5,
        "anc": 1.12, "alc": 1.40, "amc": 0.22, "aec": 0.04, "abc": 0.01,
     }),
]



SEV_SYMBOL = {"low": "⚠", "medium": "⚠⚠", "high": "🔴"}
FLAG_SYMBOL = {"low": "↓", "high": "↑", "normal": " ", "na": "·"}
FLAG_COLOR  = {"low": "\033[34m", "high": "\033[31m", "normal": "", "na": "\033[90m"}
RESET       = "\033[0m"
BOLD        = "\033[1m"
DIM         = "\033[2m"


def print_lab_row(lab: dict) -> None:
    code = lab["code"]
    val = lab.get("value")
    unit = lab.get("unit", "")
    flag = lab.get("flag", "na")
    ref = lab.get("ref", {})
    lo = ref.get("low")
    hi = ref.get("high")
    ref_str = ""
    if lo is not None or hi is not None:
        ref_str = f"[{lo if lo is not None else '—'}–{hi if hi is not None else '—'}]"
    source = ref.get("source", "")
    source_tag = f" ({source})" if source and source != "default" else ""

    color = FLAG_COLOR.get(flag, "")
    symbol = FLAG_SYMBOL.get(flag, " ")
    val_str = f"{val:7.2f} {unit:<10}" if val is not None else " " * 18
    print(f"  {color}{symbol} {code:<8}{RESET} {val_str} {DIM}{ref_str}{source_tag}{RESET}")


def print_signal(sig: dict) -> None:
    name = sig.get("id", "?")
    severity = sig.get("severity", "")
    sev_mark = SEV_SYMBOL.get(severity, "")
    title = sig.get("title") or sig.get("name") or ""
    print(f"    {sev_mark} {BOLD}{name:<36}{RESET} [{severity}] {DIM}{title}{RESET}")


def analyse_patient(title: str, descr: str, payload: dict, mode_label: str) -> dict:
    print()
    print("═" * 88)
    print(f"{BOLD}{title}{RESET}   {DIM}— {descr}{RESET}")
    print(f"  mode: {mode_label}")
    result = analyze_cbc_payload(payload)
    profile = result.get("profile", {})
    print(f"  profile: sex={profile.get('sex')} age={profile.get('age')} "
          f"(category: {profile.get('age_category', '—')})")

    print(f"\n  {BOLD}Labs:{RESET}")
    for lab in result.get("labs", [])[:12]:
        print_lab_row(lab)
    if len(result.get("labs", [])) > 12:
        print(f"  {DIM}... {len(result['labs'])-12} more labs{RESET}")

    signals = result.get("signals", [])
    non_quality = [s for s in signals if "quality" not in (s.get("tags") or [])]
    print(f"\n  {BOLD}Signals raised ({len(non_quality)}):{RESET}")
    if not non_quality:
        print(f"    {DIM}(none — clinically unremarkable){RESET}")
    else:
        severity_order = {"high": 0, "medium": 1, "low": 2, "": 3}
        for sig in sorted(non_quality, key=lambda s: severity_order.get(s.get("severity", ""), 99)):
            print_signal(sig)

    return result



if __name__ == "__main__":
    mode = "TEXTBOOK (default refs from knowledge.py)"
    if empirical_active():
        mode = f"EMPIRICAL (refs from {os.environ.get('CBC_ENGINE_CONFIG')})"

    print()
    print("┏" + "━" * 86 + "┓")
    print(f"┃ CBC engine — manual patient sanity check".ljust(87) + "┃")
    print(f"┃ mode: {mode}".ljust(87) + "┃")
    print("┗" + "━" * 86 + "┛")

    for title, descr, payload in PATIENTS:
        analyse_patient(title, descr, payload, mode.split(" (")[0])

    print()
    print("═" * 88)
    print("Done.")
