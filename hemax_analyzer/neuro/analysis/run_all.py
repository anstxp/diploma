
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"

PHASES = [
    ("evaluate.py",
     "Phase 1 — initial evaluation (figures 01-10, metrics.json, operating_table.csv)"),
    ("calibration_analysis.py",
     "Phase 2 — calibration deep dive (figures 11-12, isotonic_params.json)"),
    ("advanced_analyses.py",
     "Phase 3 — advanced metrics (figures 13-19, decision curves, Brier decomp, "
     "permutation importance, learning curves, multi-task correlation)"),
    ("extra_rigor.py",
     "Phase 4 — formal statistical rigor (figures 20-24, DeLong, HL, NRI/IDI, "
     "subgroup calibration, confusion matrices)"),
    ("regen_extra_rigor.py",
     "Phase 5 — regenerate extra_rigor.md from JSON (single source of truth)"),
]


def run_phase(script: str, description: str, env: dict) -> bool:
    path = ANALYSIS / script
    if not path.exists():
        print(f"  [SKIP] {script} not found")
        return True

    print(f"\n{'=' * 76}")
    print(description)
    print(f"  Running: python3 {path.relative_to(ROOT)}")
    print(f"{'=' * 76}")
    t0 = time.time()
    try:
        subprocess.run(
            [sys.executable, str(path)],
            cwd=str(ROOT), env=env, check=True,
        )
        elapsed = time.time() - t0
        print(f"  ✓ Done in {elapsed:.1f}s")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed (exit {e.returncode})")
        return False


def main():
    parser = argparse.ArgumentParser(description="HEMAX_RISK — full analysis pipeline")
    parser.add_argument("--phase", type=int, default=None,
                        help="Run only the given phase (1-5)")
    parser.add_argument("--skip-cv", action="store_true",
                        help="Skip 5-fold CV in extra_rigor (much faster)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    args = parser.parse_args()

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    env["SEED"] = str(args.seed)
    if args.skip_cv:
        env["SKIP_CV"] = "1"

    print(f"HEMAX_RISK analysis runner")
    print(f"  Root:    {ROOT}")
    print(f"  Seed:    {args.seed}")
    print(f"  Skip CV: {args.skip_cv}")

    phases_to_run = PHASES if args.phase is None else [PHASES[args.phase - 1]]
    results = []
    t_start = time.time()
    for script, desc in phases_to_run:
        ok = run_phase(script, desc, env)
        results.append((script, ok))

    total = time.time() - t_start
    print(f"\n{'=' * 76}")
    print("Summary")
    print(f"{'=' * 76}")
    for script, ok in results:
        status = "✓" if ok else "✗"
        print(f"  {status}  {script}")
    print(f"\nTotal time: {total:.1f}s")
    print(f"\nFigures:  {ROOT / 'analysis' / 'figures'}")
    print(f"Reports:  {ROOT / 'analysis' / 'reports'}")

    if not all(ok for _, ok in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
