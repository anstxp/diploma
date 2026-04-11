from __future__ import annotations

import argparse
import datetime
import json
import logging
import shutil
import sys
from pathlib import Path

import torch

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("promote")

ROOT = Path(__file__).parent.parent.parent
V2_MODEL_DIR = ROOT / "model_out_v2"
V2_DATA_DIR = ROOT / "data_processed_v2"
WEIGHTS_DIR = ROOT / "neuro_api" / "weights"


def repackage_v2_model(src_model: Path, target_stats: dict, dst_model: Path) -> None:
    log.info(f"Reading v2 model: {src_model}")
    payload = torch.load(src_model, map_location="cpu", weights_only=False)

    needed = {"feature_names", "target_names", "feature_stats"}
    have = set(payload.keys())
    missing = needed - have
    if missing:
        raise RuntimeError(f"v2 model.pt missing required keys: {missing}")

    if "target_stats" in payload and payload["target_stats"]:
        log.info("  target_stats already in payload — keeping existing")
    else:
        log.info("  injecting target_stats from prepare_data_v2 output")
        payload["target_stats"] = target_stats

    tn = set(payload["target_names"])
    ts_keys = set(payload["target_stats"].keys())
    if not tn.issubset(ts_keys):
        miss = tn - ts_keys
        raise RuntimeError(
            f"target_stats missing entries for: {miss}. "
            f"Re-run prepare_data_v2 first."
        )

    payload["promoted_at"] = datetime.datetime.now().isoformat()
    payload.setdefault("model_version", "2.0")

    dst_model.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, dst_model)
    size_mb = dst_model.stat().st_size / (1024 * 1024)
    log.info(f"✓ Wrote {dst_model} ({size_mb:.1f} MB)")


def promote() -> int:
    if not (V2_MODEL_DIR / "model.pt").exists():
        log.error(f"  ✗ v2 model not found: {V2_MODEL_DIR / 'model.pt'}")
        log.error(f"     Run: python -m train.v2.train_v2 first")
        return 1
    if not (V2_DATA_DIR / "target_stats.json").exists():
        log.error(f"  ✗ v2 target_stats not found: {V2_DATA_DIR / 'target_stats.json'}")
        log.error(f"     Run: python -m train.v2.prepare_data_v2 first")
        return 1

    log.info("=" * 70)
    log.info("  HEMAX_NEURO v2 — promotion to production")
    log.info("=" * 70)

    with open(V2_DATA_DIR / "target_stats.json") as f:
        target_stats = json.load(f)
    log.info(f"  target_stats keys: {sorted(target_stats.keys())}")

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = WEIGHTS_DIR.parent / f"weights.v1.{ts}"
    if WEIGHTS_DIR.exists() and any(WEIGHTS_DIR.iterdir()):
        log.info(f"Backing up current weights → {backup}")
        shutil.copytree(WEIGHTS_DIR, backup)
        log.info(f"  ✓ Backup contains: {sorted(p.name for p in backup.iterdir())}")
    else:
        log.warning("  No existing weights/ to back up — first install?")

    for stale in ("isotonic_params.json", "isotonic_params.json.bak"):
        p = WEIGHTS_DIR / stale
        if p.exists():
            log.info(f"Removing v1-specific {p.name} (v2 uses temperature only)")
            p.unlink()

    repackage_v2_model(
        V2_MODEL_DIR / "model.pt",
        target_stats,
        WEIGHTS_DIR / "model.pt",
    )

    marker = WEIGHTS_DIR / "MODEL_VERSION.txt"
    marker.write_text(
        f"v2 — promoted {datetime.datetime.now().isoformat()}\n"
        f"source: {V2_MODEL_DIR / 'model.pt'}\n"
        f"features: 57 (46 v1 base + 11 v2 new)\n"
        f"targets: 7 (5 v1 + 2 new: snore_high, trouble_sleeping_high)\n"
        f"backup of previous weights: {backup if WEIGHTS_DIR else 'n/a'}\n"
    )
    log.info(f"✓ Wrote marker: {marker.name}")

    log.info("=" * 70)
    log.info("✅ v2 PROMOTED TO PRODUCTION")
    log.info("=" * 70)
    log.info("")
    log.info("Next: restart the neuro-api container so it loads the new weights")
    log.info("")
    log.info("  cd ..   # back to hemax_analyzer/")
    log.info("  docker compose up -d --build --force-recreate neuro-api")
    log.info("")
    log.info("Verify with:")
    log.info("  docker logs hemax-neuro 2>&1 | grep -E 'Loading|target_names|features'")
    log.info("  curl http://127.0.0.1:8003/neuro/healthz")
    log.info("")
    log.info("Rollback if needed:")
    log.info(f"  python -m train.v2.promote_to_production --rollback")
    return 0


def rollback() -> int:
    log.info("=" * 70)
    log.info("  ROLLBACK to v1 weights")
    log.info("=" * 70)

    backups = sorted(WEIGHTS_DIR.parent.glob("weights.v1.*"))
    if not backups:
        log.error("  ✗ No backup found in neuro_api/weights.v1.*")
        return 1
    latest = backups[-1]
    log.info(f"Most recent backup: {latest}")

    if WEIGHTS_DIR.exists():
        shutil.rmtree(WEIGHTS_DIR)
    shutil.copytree(latest, WEIGHTS_DIR)
    log.info(f"✓ Restored from {latest}")
    log.info("")
    log.info("Now restart container:")
    log.info("  docker compose up -d --force-recreate neuro-api")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rollback", action="store_true",
                    help="Restore the most recent v1 backup instead of promoting v2")
    args = ap.parse_args()
    if args.rollback:
        return rollback()
    return promote()


if __name__ == "__main__":
    sys.exit(main())
