from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class C:
    R = "\033[0m"; B = "\033[1m"; D = "\033[2m"
    GRN = "\033[92m"; YEL = "\033[93m"; RED = "\033[91m"
    CYN = "\033[96m"; MAG = "\033[95m"


def banner(text: str, color: str = C.CYN):
    print()
    print(f"{color}{C.B}{'═' * 78}")
    print(f"  {text}")
    print(f"{'═' * 78}{C.R}")


def run_step(name: str, cmd: list) -> bool:
    print(f"\n{C.YEL}▶  {name}{C.R}")
    print(f"   {C.D}$ {' '.join(cmd)}{C.R}\n")
    t0 = time.time()
    try:
        subprocess.run(cmd, cwd=str(ROOT), check=True)
        elapsed = time.time() - t0
        print(f"\n{C.GRN}✓  {name} done in {elapsed:.0f}s{C.R}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n{C.RED}✗  {name} FAILED (exit {e.returncode}){C.R}")
        return False


def step_prepare() -> bool:
    banner("STEP 1 — Prepare HAM10000 splits")
    meta_path = ROOT / "data" / "HAM10000_metadata.csv"
    if not meta_path.exists():
        print(f"{C.RED}HAM10000_metadata.csv not found at {meta_path}{C.R}")
        print()
        print("Download options:")
        print("  Kaggle: kaggle datasets download -d kmader/skin-cancer-mnist-ham10000")
        print("  Harvard Dataverse: https://doi.org/10.7910/DVN/DBW86T")
        return False
    return run_step("prepare_data.py", [sys.executable, "train/prepare_data.py"])


def step_train() -> bool:
    banner("STEP 2 — Train ResNet-18 (20-60 min on Mac M1)")
    return run_step("train.py", [sys.executable, "train/train.py"])


def step_analysis() -> bool:
    banner("STEP 3 — Analysis pipeline (figures + Grad-CAM)")
    return run_step("analysis.run_all", [sys.executable, "-m", "analysis.run_all"])


def step_sync_weights() -> bool:
    banner("STEP 4 — Sync weights + calibration into derma_api/")
    src = ROOT / "model_out" / "model.pt"
    dst = ROOT / "derma_api" / "weights" / "model.pt"
    if not src.exists():
        print(f"{C.YEL}⚠  no model.pt at {src} — skipping{C.R}")
        return True
    dst.parent.mkdir(exist_ok=True, parents=True)
    shutil.copy(src, dst)
    print(f"{C.GRN}✓  copied {src.name} → derma_api/weights/{C.R}")

    calib_src = ROOT / "analysis" / "reports" / "calibration_params.json"
    calib_dst = ROOT / "derma_api" / "weights" / "calibration_params.json"
    if calib_src.exists():
        shutil.copy(calib_src, calib_dst)
        print(f"{C.GRN}✓  copied calibration_params.json → derma_api/weights/{C.R}")
    else:
        print(f"{C.YEL}⚠  no calibration_params.json yet — predictor will use raw softmax{C.R}")
    return True


def step_tests() -> bool:
    banner("STEP 5 — Tests")
    return run_step("pytest", [sys.executable, "-m", "pytest",
                                "derma_api/tests/", "-q"])


def step_demo() -> bool:
    banner("STEP 6 — Demo on 7 test cases (one per class)")
    return run_step("demo.py --test-set",
                    [sys.executable, "demo.py", "--test-set"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-prepare", action="store_true")
    parser.add_argument("--skip-train", action="store_true")
    parser.add_argument("--skip-analysis", action="store_true")
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--skip-demo", action="store_true")
    parser.add_argument("--quick", action="store_true",
                        help="--skip-prepare --skip-train")
    args = parser.parse_args()

    if args.quick:
        args.skip_prepare = True
        args.skip_train = True

    print(f"{C.B}{C.MAG}HEMAX_DERMA — full cycle{C.R}")

    t_start = time.time()
    results = []

    if not args.skip_prepare:
        ok = step_prepare()
        results.append(("prepare", ok))
        if not ok:
            sys.exit(1)
    if not args.skip_train:
        ok = step_train()
        results.append(("train", ok))
        if not ok:
            sys.exit(1)
    if not args.skip_analysis:
        ok = step_analysis()
        results.append(("analysis", ok))
    ok = step_sync_weights()
    results.append(("sync_weights", ok))
    if not args.skip_tests:
        ok = step_tests()
        results.append(("tests", ok))
    if not args.skip_demo:
        ok = step_demo()
        results.append(("demo", ok))

    total = time.time() - t_start
    banner("SUMMARY", color=C.MAG)
    for name, ok in results:
        marker = f"{C.GRN}✓{C.R}" if ok else f"{C.RED}✗{C.R}"
        print(f"  {marker}  {name}")
    print(f"\n  Total time: {total/60:.1f} min")

    if all(ok for _, ok in results):
        print(f"\n{C.GRN}{C.B}All steps succeeded ✨{C.R}")
    else:
        print(f"\n{C.RED}Some steps failed{C.R}")
        sys.exit(1)


if __name__ == "__main__":
    main()
