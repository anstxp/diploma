from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def run(name: str, cmd: list):
    print(f"\n{'=' * 70}")
    print(f"  {name}")
    print(f"{'=' * 70}")
    result = subprocess.run(cmd, cwd=str(ROOT))
    return result.returncode == 0


def main():
    print("HEMAX_DERMA — analysis pipeline")
    if not run("Phase 1 — Evaluation",
               [sys.executable, "analysis/evaluate.py"]):
        print("Phase 1 failed — abort")
        sys.exit(1)
    if not run("Phase 2 — Grad-CAM gallery",
               [sys.executable, "analysis/gradcam_gallery.py"]):
        print("Phase 2 failed (continuing)")
    if not run("Phase 3 — Calibration",
               [sys.executable, "analysis/calibration.py"]):
        print("Phase 3 failed (continuing)")
    print(f"\n✅ Done. Figures: {ROOT / 'analysis/figures'}")
    print(f"   Reports: {ROOT / 'analysis/reports'}")


if __name__ == "__main__":
    main()
