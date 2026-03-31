#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent

class C:
    R = "\033[0m"
    B = "\033[1m"
    D = "\033[2m"
    GRN = "\033[92m"
    YEL = "\033[93m"
    RED = "\033[91m"
    CYN = "\033[96m"
    MAG = "\033[95m"


def banner(text: str, color: str = C.CYN):
    line = "═" * 78
    print()
    print(f"{color}{C.B}{line}")
    print(f"  {text}")
    print(f"{line}{C.R}")


def run_step(name: str, cmd: list[str], cwd: Path = ROOT, env: dict | None = None) -> bool:
    print(f"\n{C.YEL}▶  {name}{C.R}")
    print(f"   {C.D}$ {' '.join(cmd)}{C.R}\n")
    t0 = time.time()
    try:
        subprocess.run(cmd, cwd=str(cwd), env=env, check=True)
        elapsed = time.time() - t0
        print(f"\n{C.GRN}✓  {name} done in {elapsed:.1f}s{C.R}")
        return True
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - t0
        print(f"\n{C.RED}✗  {name} FAILED (exit {e.returncode}, after {elapsed:.1f}s){C.R}")
        return False


def step_prepare_data() -> bool:
    banner("STEP 1 — Prepare data (raw NHANES → train/val/test parquet)")

    nhanes_path = ROOT / "data" / "nhanes_master.parquet"
    if not nhanes_path.exists():
        print(f"{C.RED}✗  Raw NHANES not found at {nhanes_path}{C.R}")
        print()
        print("Place nhanes_master.parquet in data/. Common location:")
        print(f"  cp /Users/nstxp/Desktop/hemax_analyzer/joined/nhanes_master.parquet data/")
        return False

    return run_step("prepare_data.py", [sys.executable, "train/prepare_data.py"])


def step_train() -> bool:
    banner("STEP 2 — Train multi-task model (∼20s on Mac M1)")

    data_dir = ROOT / "data_processed"
    if not (data_dir / "train.parquet").exists():
        print(f"{C.RED}✗  data_processed/train.parquet missing — run --skip-prepare? Then need prepare first{C.R}")
        return False

    return run_step("train.py", [sys.executable, "train/train.py"])


def step_tests() -> bool:
    banner("STEP 3 — Unit tests (33 expected)")
    return run_step("pytest", [sys.executable, "-m", "pytest", "risk_api/tests/", "-q"])


def step_analysis(skip_cv: bool) -> bool:
    banner("STEP 4 — Scientific analysis (24+ figures, 11 reports)")

    cmd = [sys.executable, "-m", "analysis.run_all"]
    if skip_cv:
        cmd.append("--skip-cv")
    return run_step("analysis.run_all", cmd)


def step_update_isotonic() -> bool:
    banner("STEP 5 — Sync isotonic calibration into production weights")

    src = ROOT / "analysis" / "reports" / "isotonic_params.json"
    dst = ROOT / "risk_api" / "weights" / "isotonic_params.json"

    if not src.exists():
        print(f"{C.YEL}⚠  {src} not found — skipping (analysis didn't generate it){C.R}")
        return True

    shutil.copy(src, dst)
    size_kb = dst.stat().st_size / 1024
    print(f"{C.GRN}✓  Copied isotonic_params.json ({size_kb:.1f} KB){C.R}")
    print(f"   {C.D}{src} → {dst}{C.R}")
    return True


def step_demo() -> bool:
    banner("STEP 6 — Narrative demo (9 curated patients)")
    return run_step("narrative_demo.py", [sys.executable, "narrative_demo.py"])


def main():
    parser = argparse.ArgumentParser(
        description="Full HEMAX_RISK cycle: prepare → train → test → analysis → demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--skip-prepare", action="store_true",
                        help="skip data preparation (data_processed/ already populated)")
    parser.add_argument("--skip-train", action="store_true",
                        help="skip model training (model.pt already exists)")
    parser.add_argument("--skip-tests", action="store_true",
                        help="skip pytest")
    parser.add_argument("--skip-cv", action="store_true",
                        help="skip 5-fold cross-validation in analysis (~6 min faster)")
    parser.add_argument("--skip-demo", action="store_true",
                        help="don't run narrative demo at the end")
    parser.add_argument("--quick", action="store_true",
                        help="convenience: --skip-prepare --skip-train --skip-cv")
    args = parser.parse_args()

    if args.quick:
        args.skip_prepare = True
        args.skip_train = True
        args.skip_cv = True

    print()
    print(f"{C.B}{C.MAG}HEMAX_RISK — full cycle runner{C.R}")
    print(f"  Working dir: {ROOT}")
    print(f"  Skip prepare: {args.skip_prepare}")
    print(f"  Skip train:   {args.skip_train}")
    print(f"  Skip tests:   {args.skip_tests}")
    print(f"  Skip CV:      {args.skip_cv}")
    print(f"  Skip demo:    {args.skip_demo}")

    t_start = time.time()
    results: list[tuple[str, bool]] = []

    if not args.skip_prepare:
        ok = step_prepare_data()
        results.append(("prepare_data", ok))
        if not ok:
            sys.exit(1)
    else:
        print(f"\n{C.D}⤿  Skipping prepare_data{C.R}")

    if not args.skip_train:
        ok = step_train()
        results.append(("train", ok))
        if not ok:
            sys.exit(1)
    else:
        print(f"\n{C.D}⤿  Skipping train{C.R}")

    if not args.skip_tests:
        ok = step_tests()
        results.append(("tests", ok))
    else:
        print(f"\n{C.D}⤿  Skipping tests{C.R}")

    ok = step_analysis(skip_cv=args.skip_cv)
    results.append(("analysis", ok))

    ok = step_update_isotonic()
    results.append(("isotonic_sync", ok))

    if not args.skip_demo:
        ok = step_demo()
        results.append(("demo", ok))
    else:
        print(f"\n{C.D}⤿  Skipping demo{C.R}")

    total = time.time() - t_start
    banner("SUMMARY", color=C.MAG)
    for name, ok in results:
        mark = f"{C.GRN}✓{C.R}" if ok else f"{C.RED}✗{C.R}"
        print(f"  {mark}  {name}")
    print()
    print(f"  Total time: {C.B}{total:.1f}s{C.R} ({total/60:.1f} min)")
    print()
    print(f"  Figures:  {ROOT / 'analysis/figures'}")
    print(f"  Reports:  {ROOT / 'analysis/reports'}")
    print(f"  Model:    {ROOT / 'model_out/model.pt'}")
    print()

    failed = [n for n, ok in results if not ok]
    if failed:
        print(f"{C.RED}{C.B}Failed steps: {', '.join(failed)}{C.R}")
        sys.exit(1)
    else:
        print(f"{C.GRN}{C.B}All steps succeeded ✨{C.R}")


if __name__ == "__main__":
    main()
