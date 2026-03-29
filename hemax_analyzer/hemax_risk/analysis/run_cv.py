import sys, time, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "analysis"))

from extra_rigor import run_kfold_cv, plot_22_kfold_stability, FIG, REP

if __name__ == "__main__":
    t0 = time.time()
    print("Starting 5-fold CV (3 epochs each)...", flush=True)
    fold_aucs = run_kfold_cv(K=5, epochs=3)
    print(f"Total CV time: {time.time()-t0:.0f}s", flush=True)
    plot_22_kfold_stability(fold_aucs, FIG / "22_kfold_stability.png")
    with open(REP / "kfold_aucs.json", "w") as f:
        json.dump(fold_aucs, f, indent=2)
    print("Done.", flush=True)
