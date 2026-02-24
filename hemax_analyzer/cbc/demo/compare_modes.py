#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import os
import sys
from pathlib import Path

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)
sys.path.insert(0, os.path.abspath(os.path.join(_here, "..", "engine")))

import importlib.util
_mpt_path = Path(__file__).with_name("manual_patient_test.py")
_spec = importlib.util.spec_from_file_location("mpt", _mpt_path)
_mpt  = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mpt)
PATIENTS = _mpt.PATIENTS


GREEN  = "\033[32m"; RED    = "\033[31m"; YELLOW = "\033[33m"; BLUE = "\033[34m"
GREY   = "\033[90m"; BOLD   = "\033[1m";  DIM    = "\033[2m";  RESET = "\033[0m"

SEV_ORDER = {"low": 1, "medium": 2, "high": 3, "": 0}
SEV_SYMBOL = {"low": "⚠", "medium": "⚠⚠", "high": "🔴", "": " "}


def _run_all(patients: list) -> list[dict]:
    from cbc_api import analyze_cbc_payload  # type: ignore
    from cbc_api.rules import reload_empirical_config  # type: ignore
    reload_empirical_config()
    out = []
    for title, descr, payload in patients:
        res = analyze_cbc_payload(payload)
        non_q = [
            s for s in res.get("signals", [])
            if "quality" not in (s.get("tags") or [])
        ]
        signals = {s.get("id", "?"): s.get("severity", "") for s in non_q}
        out.append({"title": title, "descr": descr, "signals": signals, "full": res})
    return out


def _sig_line(sig_id: str, sev: str, color: str = "") -> str:
    mark = SEV_SYMBOL.get(sev, " ")
    return f"{color}{mark} {sig_id}[{sev}]{RESET}"


def _print_diff(tb: dict, emp: dict) -> None:
    print()
    print("═" * 96)
    print(f"{BOLD}{tb['title']}{RESET}")
    print(f"{DIM}{tb['descr']}{RESET}")

    tb_ids  = set(tb["signals"].keys())
    emp_ids = set(emp["signals"].keys())
    removed = tb_ids - emp_ids
    added   = emp_ids - tb_ids
    kept    = tb_ids & emp_ids
    sev_shifts = {
        s: (tb["signals"][s], emp["signals"][s])
        for s in kept if tb["signals"][s] != emp["signals"][s]
    }

    if not tb_ids and not emp_ids:
        print(f"  {GREY}no signals in either mode — clinically unremarkable{RESET}")
        return

    if not (added or removed or sev_shifts):
        print(f"  {GREY}identical signal set in both modes{RESET}")
    else:
        tags = []
        if added:      tags.append(f"{GREEN}+{len(added)} added{RESET}")
        if removed:    tags.append(f"{RED}-{len(removed)} removed{RESET}")
        if sev_shifts: tags.append(f"{YELLOW}~{len(sev_shifts)} severity shifts{RESET}")
        print(f"  {BOLD}Δ{RESET}  " + "   ".join(tags))

    max_rows = max(len(tb_ids), len(emp_ids))
    col_w = 44
    print()
    print(f"  {BOLD}{'TEXTBOOK mode'.ljust(col_w)}{'EMPIRICAL mode'.ljust(col_w)}{RESET}")
    print(f"  {'─' * (col_w - 2)} {'─' * (col_w - 2)}")

    tb_sorted = sorted(tb["signals"].items(),
                       key=lambda x: (-SEV_ORDER.get(x[1], 0), x[0]))
    emp_sorted = sorted(emp["signals"].items(),
                        key=lambda x: (-SEV_ORDER.get(x[1], 0), x[0]))

    def fmt_slot(sig, sev, role):
        color = ""
        if role == "tb" and sig in removed:
            color = RED
        elif role == "emp" and sig in added:
            color = GREEN
        elif sig in sev_shifts:
            color = YELLOW
        return _sig_line(sig, sev, color)

    for i in range(max_rows):
        left  = fmt_slot(*tb_sorted[i],  "tb")  if i < len(tb_sorted)  else ""
        right = fmt_slot(*emp_sorted[i], "emp") if i < len(emp_sorted) else ""
        def _vlen(s): return len(s.encode("utf-8").decode("utf-8") if not s else
                                 __import__("re").sub(r"\x1b\[[0-9;]*m", "", s))
        left_pad  = left  + " " * max(0, col_w - _vlen(left))
        print(f"  {left_pad}{right}")

    highlights = []
    for sig in added:
        highlights.append(f"{GREEN}ADDED{RESET} {sig} — empirical refs caught this")
    for sig in removed:
        highlights.append(f"{RED}REMOVED{RESET} {sig} — textbook flagged it, empirical did not")
    for sig, (old, new) in sev_shifts.items():
        if SEV_ORDER[new] > SEV_ORDER[old]:
            highlights.append(f"{YELLOW}ESCALATED{RESET} {sig}: {old} → {new}")
        else:
            highlights.append(f"{YELLOW}DE-ESCALATED{RESET} {sig}: {old} → {new}")
    if highlights:
        print()
        print(f"  {DIM}clinical impact:{RESET}")
        for h in highlights:
            print(f"    • {h}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True,
                    help="Path to engine_config.json from Phase 3.")
    args = ap.parse_args()

    cfg_path = os.path.abspath(args.config)
    if not os.path.isfile(cfg_path):
        sys.exit(f"not found: {cfg_path}")

    print()
    print("┏" + "━" * 94 + "┓")
    print(f"┃ CBC engine — textbook vs empirical side-by-side".ljust(95) + "┃")
    print(f"┃ cases: {len(PATIENTS)}".ljust(95) + "┃")
    print(f"┃ empirical config: {cfg_path}".ljust(95) + "┃")
    print("┗" + "━" * 94 + "┛")

    os.environ.pop("CBC_ENGINE_CONFIG", None)
    for mod_name in ("cbc_api", "cbc_api.rules", "cbc_api.config",
                     "cbc_api.empirical_refs_loader", "cbc_api.analyze"):
        if mod_name in sys.modules:
            importlib.reload(sys.modules[mod_name])
    tb_results = _run_all(PATIENTS)

    os.environ["CBC_ENGINE_CONFIG"] = cfg_path
    for mod_name in ("cbc_api", "cbc_api.rules", "cbc_api.config",
                     "cbc_api.empirical_refs_loader", "cbc_api.analyze"):
        if mod_name in sys.modules:
            importlib.reload(sys.modules[mod_name])
    emp_results = _run_all(PATIENTS)

    n_changed = 0
    n_added   = 0
    n_removed = 0
    n_escalated = 0
    for tb, emp in zip(tb_results, emp_results):
        _print_diff(tb, emp)
        tb_set = set(tb["signals"]); emp_set = set(emp["signals"])
        added   = emp_set - tb_set
        removed = tb_set - emp_set
        kept    = tb_set & emp_set
        esc = sum(1 for s in kept
                  if SEV_ORDER[emp["signals"][s]] > SEV_ORDER[tb["signals"][s]])
        if added or removed or esc:
            n_changed += 1
        n_added   += len(added)
        n_removed += len(removed)
        n_escalated += esc

    print()
    print("═" * 96)
    print(f"{BOLD}AGGREGATE — effect of switching to empirical mode{RESET}")
    print("═" * 96)
    print(f"  patients with any change:     {n_changed} / {len(PATIENTS)}")
    print(f"  {GREEN}total signals added:{RESET}         {n_added}")
    print(f"  {RED}total signals removed:{RESET}       {n_removed}")
    print(f"  {YELLOW}total severity escalations:{RESET}  {n_escalated}")
    print()
    if n_added > n_removed:
        print(f"  {BOLD}Net direction:{RESET} empirical surfaces MORE findings than textbook — ")
        print(f"  consistent with tighter population-derived reference intervals (especially")
        print(f"  for PLT where textbook upper bound of 450 is higher than the empirical p97.5).")
    elif n_removed > n_added:
        print(f"  {BOLD}Net direction:{RESET} empirical rejects MORE findings than textbook — ")
        print(f"  consistent with looser upper bounds on e.g. monocytes where textbook was")
        print(f"  under-bounded.")
    else:
        print(f"  {BOLD}Net direction:{RESET} balanced gains/losses; severity profile is the main change.")
    print()


if __name__ == "__main__":
    main()
