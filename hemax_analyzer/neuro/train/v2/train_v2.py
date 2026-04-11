from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import torch
import torch.optim as optim
from torch.utils.data import DataLoader

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT))
                                                # `import train.train`

# noqa imports happen after sys.path mutation
from model import HemaxRiskNet, MaskedMultiTaskBCELoss, ModelConfig, save_model  # noqa: E402

from train import train as v1_train  # noqa: E402

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("train_v2")

DATA_DIR = ROOT / "data_processed_v2"
OUT_DIR = ROOT / "model_out_v2"
OUT_DIR.mkdir(exist_ok=True)


def main():
    log.info("=" * 70)
    log.info("HEMAX_NEURO v2 — training (extended features + new heads)")
    log.info(f"  Data:   {DATA_DIR}")
    log.info(f"  Output: {OUT_DIR}")
    log.info("=" * 70)

    if not (DATA_DIR / "metadata.json").exists():
        log.error(f"  ✗ {DATA_DIR} not prepared yet.")
        log.error(f"  Run first:  python -m train.v2.prepare_data_v2")
        return 1

    with open(DATA_DIR / "metadata.json") as f:
        meta = json.load(f)
    with open(DATA_DIR / "feature_stats.json") as f:
        feature_stats = json.load(f)
    with open(DATA_DIR / "target_stats.json") as f:
        target_stats = json.load(f)

    feature_names = meta["feature_names"]
    target_names = meta["target_names"]
    log.info(f"v2 cohort: {meta['n_train']:,} train / "
             f"{meta['n_val']:,} val / {meta['n_test']:,} test")
    log.info(f"v2 features: {len(feature_names)} "
             f"({meta['n_features_v1']} v1 base + "
             f"{meta['n_features_v2_new']} v2 new)")
    log.info(f"v2 targets:  {len(target_names)}  "
             f"({len(meta['v2_new_targets'])} new heads)")
    log.info(f"  new features: {meta['v2_new_features']}")
    log.info(f"  new targets:  {meta['v2_new_targets']}")

    train_ds = v1_train.RiskDataset(
        DATA_DIR / "train.parquet", feature_names, target_names, feature_stats)
    val_ds = v1_train.RiskDataset(
        DATA_DIR / "val.parquet",   feature_names, target_names, feature_stats)
    test_ds = v1_train.RiskDataset(
        DATA_DIR / "test.parquet",  feature_names, target_names, feature_stats)
    BATCH = 256
    train_loader = DataLoader(train_ds, batch_size=BATCH, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=BATCH, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=BATCH, shuffle=False, num_workers=0)

    config = ModelConfig(
        n_features=len(feature_names),
        target_names=target_names,
        encoder_dim=256,
        encoder_depth=4,
        head_dim=64,
        dropout=0.2,
        use_missingness=True,
    )
    device = "cuda" if torch.cuda.is_available() else "cpu"
    log.info(f"Device: {device}")
    model = HemaxRiskNet(config).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    log.info(f"Model: {n_params:,} parameters")

    pos_weights = {t: target_stats[t]["pos_weight"] for t in target_names}
    log.info(f"Pos weights: {pos_weights}")
    loss_fn = MaskedMultiTaskBCELoss(target_names, pos_weights).to(device)

    optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=30, eta_min=1e-5)

    N_EPOCHS = 30
    PATIENCE = 5
    best_val_auc = 0.0
    best_epoch = 0
    history = []
    no_improve = 0

    log.info(f"\nTraining for up to {N_EPOCHS} epochs...")
    best_state_dict = None
    for epoch in range(1, N_EPOCHS + 1):
        tr_loss = v1_train.train_one_epoch(
            model, train_loader, loss_fn, optimizer, device)
        val_loss, _val_ptl, val_metrics, *_ = v1_train.evaluate(
            model, val_loader, loss_fn, device, target_names)
        scheduler.step()

        val_aucs = [m["auc"] for m in val_metrics.values()
                    if not np.isnan(m["auc"])]
        mean_auc = float(np.mean(val_aucs)) if val_aucs else 0.0

        log.info(f"Epoch {epoch:2d}/{N_EPOCHS}  "
                 f"train_loss={tr_loss:.4f}  val_loss={val_loss:.4f}  "
                 f"mean_AUC={mean_auc:.4f}")
        for t in target_names:
            m = val_metrics[t]
            tag = "★" if t in meta["v2_new_targets"] else " "
            log.info(f"           {tag} {t:<22}  "
                     f"AUC={m['auc']:.4f}  AUPRC={m['auprc']:.4f}")

        history.append({
            "epoch": epoch,
            "train_loss": tr_loss,
            "val_loss": val_loss,
            "val_metrics": val_metrics,
            "mean_auc": mean_auc,
            "lr": optimizer.param_groups[0]["lr"],
            "n_train": meta["n_train"], "n_val": meta["n_val"],
        })

        if mean_auc > best_val_auc:
            best_val_auc = mean_auc
            best_epoch = epoch
            no_improve = 0
            best_state_dict = {k: v.clone() for k, v in model.state_dict().items()}
        else:
            no_improve += 1
            if no_improve >= PATIENCE:
                log.info(f"  Early-stopping at epoch {epoch} "
                         f"(no improvement in {PATIENCE} epochs)")
                break

    if best_state_dict is not None:
        model.load_state_dict(best_state_dict)
    log.info(f"\nBest epoch: {best_epoch} (mean val AUC = {best_val_auc:.4f})")

    temperatures = v1_train.calibrate_temperatures(
        model, val_loader, device, target_names)
    log.info(f"Calibrated temperatures: {temperatures.tolist()}")

    if hasattr(model, "set_temperature"):
        model.set_temperature(temperatures)
        log.info("✓ Wrote calibrated temperatures back into model parameters.")
    else:
        log.warning("Model has no set_temperature(); temperatures NOT saved "
                    "with checkpoint. Inference will be uncalibrated.")

    log.info("\nFinal evaluation on TEST set...")
    test_loss, _ptl, test_metrics, *_ = v1_train.evaluate(
        model, test_loader, loss_fn, device, target_names)
    log.info(f"Test loss: {test_loss:.4f}")
    log.info(f"  {'Target':<24} {'AUC':>8} {'AUPRC':>8} {'Brier':>8} {'n':>6} {'n_pos':>6}")
    log.info(f"  {'-'*24} {'-'*8} {'-'*8} {'-'*8} {'-'*6} {'-'*6}")
    for t in target_names:
        m = test_metrics[t]
        tag = "★" if t in meta["v2_new_targets"] else " "
        log.info(f"  {tag}{t:<23} {m['auc']:>8.4f} {m['auprc']:>8.4f} "
                 f"{m['brier']:>8.4f} {m['n']:>6,} {m.get('n_pos', 0):>6,}")
    mean_test_auc = float(np.mean([m["auc"] for m in test_metrics.values()
                                    if not np.isnan(m["auc"])]))
    log.info(f"  {'MEAN':<24} {mean_test_auc:>8.4f}")

    save_model(
        model, OUT_DIR / "model.pt",
        feature_names=feature_names,
        target_names=target_names,
        feature_stats=feature_stats,
        test_metrics=test_metrics,
        model_version="2.0",
        history=history,
    )
    with open(OUT_DIR / "metrics.json", "w") as f:
        json.dump({
            "test_metrics": test_metrics,
            "test_loss": test_loss,
            "mean_test_auc": mean_test_auc,
            "best_epoch": best_epoch,
            "n_epochs_trained": len(history),
            "temperatures": temperatures.tolist(),
            "target_names": target_names,
            "feature_names": feature_names,
            "n_features": len(feature_names),
            "v2_new_features": meta["v2_new_features"],
            "v2_new_targets": meta["v2_new_targets"],
            "n_train": meta["n_train"],
            "n_val": meta["n_val"],
            "n_test": meta["n_test"],
        }, f, indent=2)
    with open(OUT_DIR / "history.json", "w") as f:
        json.dump(history, f, indent=2)
    log.info(f"\n✓ Saved {OUT_DIR / 'model.pt'}")
    log.info(f"✓ Saved {OUT_DIR / 'metrics.json'}")
    log.info(f"\nNext: python -m train.v2.compare_v1_v2")
    log.info("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
