from __future__ import annotations

import json
import logging
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import (
    average_precision_score, brier_score_loss, roc_auc_score
)
from torch.utils.data import DataLoader, Dataset

sys.path.insert(0, str(Path(__file__).parent.parent / "engine"))
from model import HemaxRiskNet, MaskedMultiTaskBCELoss, ModelConfig, save_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("train")

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data_processed"
OUT_DIR = ROOT / "model_out"
OUT_DIR.mkdir(exist_ok=True)



class RiskDataset(Dataset):
    def __init__(self, split_path: Path, feature_names: List[str],
                 target_names: List[str], feature_stats: Dict[str, Dict]):
        df = pd.read_parquet(split_path)
        self.feature_names = feature_names
        self.target_names = target_names

        self.means = np.array([feature_stats[f]["mean"] for f in feature_names], dtype=np.float32)
        self.stds  = np.array([feature_stats[f]["std"]  for f in feature_names], dtype=np.float32)
        self.stds = np.where(self.stds < 1e-6, 1.0, self.stds)

        feat_raw = df[feature_names].values.astype(np.float32)
        self.missing = np.isnan(feat_raw).astype(np.float32)

        feat_filled = np.where(np.isnan(feat_raw), self.means, feat_raw)
        self.features = (feat_filled - self.means) / self.stds
        self.features = np.clip(self.features, -5.0, 5.0)

        targets_raw = df[target_names].values.astype(np.float32)
        self.target_mask = (~np.isnan(targets_raw)).astype(np.float32)
        self.targets = np.where(np.isnan(targets_raw), 0.0, targets_raw)

    def __len__(self) -> int:
        return len(self.features)

    def __getitem__(self, idx: int):
        return (
            torch.from_numpy(self.features[idx]),
            torch.from_numpy(self.missing[idx]),
            torch.from_numpy(self.targets[idx]),
            torch.from_numpy(self.target_mask[idx]),
        )



def train_one_epoch(model, loader, loss_fn, optimizer, device, log_every=50):
    model.train()
    total_loss = 0.0
    n_batches = 0
    for batch_idx, (feat, mask, tgt, tmask) in enumerate(loader):
        feat, mask, tgt, tmask = feat.to(device), mask.to(device), tgt.to(device), tmask.to(device)
        optimizer.zero_grad()
        logits_dict = model(feat, mask)
        loss, _ = loss_fn(logits_dict, tgt, tmask)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        total_loss += loss.item()
        n_batches += 1
    return total_loss / max(n_batches, 1)


@torch.no_grad()
def evaluate(model, loader, loss_fn, device, target_names):
    model.eval()
    all_logits = {t: [] for t in target_names}
    all_targets = {t: [] for t in target_names}
    all_masks = {t: [] for t in target_names}
    total_loss = 0.0
    per_task_losses = {t: [] for t in target_names}
    n_batches = 0

    for feat, mask, tgt, tmask in loader:
        feat, mask, tgt, tmask = feat.to(device), mask.to(device), tgt.to(device), tmask.to(device)
        logits_dict = model(feat, mask)
        loss, ptl = loss_fn(logits_dict, tgt, tmask)
        total_loss += loss.item()
        n_batches += 1
        for i, t in enumerate(target_names):
            all_logits[t].append(logits_dict[t].cpu().numpy())
            all_targets[t].append(tgt[:, i].cpu().numpy())
            all_masks[t].append(tmask[:, i].cpu().numpy())
            if not np.isnan(ptl[t]):
                per_task_losses[t].append(ptl[t])

    metrics = {}
    for t in target_names:
        logits = np.concatenate(all_logits[t])
        targets = np.concatenate(all_targets[t])
        masks = np.concatenate(all_masks[t]).astype(bool)
        if masks.sum() < 2 or targets[masks].sum() == 0:
            metrics[t] = {"auc": float("nan"), "auprc": float("nan"),
                          "brier": float("nan"), "n": int(masks.sum())}
            continue
        probs = 1.0 / (1.0 + np.exp(-logits))
        try:
            auc = roc_auc_score(targets[masks], probs[masks])
        except ValueError:
            auc = float("nan")
        try:
            auprc = average_precision_score(targets[masks], probs[masks])
        except ValueError:
            auprc = float("nan")
        brier = brier_score_loss(targets[masks], probs[masks])
        metrics[t] = {
            "auc": float(auc), "auprc": float(auprc),
            "brier": float(brier), "n": int(masks.sum()),
            "n_pos": int(targets[masks].sum())
        }

    avg_loss = total_loss / max(n_batches, 1)
    avg_per_task = {t: (np.mean(v) if v else float("nan"))
                    for t, v in per_task_losses.items()}
    return avg_loss, avg_per_task, metrics, all_logits, all_targets, all_masks


def calibrate_temperatures(model, val_loader, device, target_names) -> torch.Tensor:
    log.info("Calibrating temperatures on val set...")
    model.eval()
    all_logits = {t: [] for t in target_names}
    all_targets = {t: [] for t in target_names}
    all_masks = {t: [] for t in target_names}

    with torch.no_grad():
        for feat, mask, tgt, tmask in val_loader:
            feat, mask, tgt, tmask = feat.to(device), mask.to(device), tgt.to(device), tmask.to(device)
            logits_dict = model(feat, mask, apply_temperature=False)
            for i, t in enumerate(target_names):
                all_logits[t].append(logits_dict[t].cpu())
                all_targets[t].append(tgt[:, i].cpu())
                all_masks[t].append(tmask[:, i].cpu())

    temperatures = torch.ones(len(target_names))
    for i, t in enumerate(target_names):
        logits = torch.cat(all_logits[t])
        targets = torch.cat(all_targets[t])
        masks = torch.cat(all_masks[t]).bool()

        if masks.sum() < 100 or targets[masks].sum() == 0:
            continue

        T = torch.ones(1, requires_grad=True)
        opt = torch.optim.LBFGS([T], lr=0.01, max_iter=50)
        valid_logits = logits[masks]
        valid_targets = targets[masks]

        def closure():
            opt.zero_grad()
            scaled = valid_logits / T.clamp(min=0.1)
            loss = nn.functional.binary_cross_entropy_with_logits(scaled, valid_targets)
            loss.backward()
            return loss

        opt.step(closure)
        T_val = max(0.1, float(T.detach().item()))
        temperatures[i] = T_val
        log.info(f"   {t}: T = {T_val:.3f}")

    return temperatures



def main():
    log.info("=" * 70)
    log.info("HEMAX_RISK — training")
    log.info("=" * 70)

    with open(DATA_DIR / "metadata.json") as f:
        meta = json.load(f)
    with open(DATA_DIR / "feature_stats.json") as f:
        feature_stats = json.load(f)
    with open(DATA_DIR / "target_stats.json") as f:
        target_stats = json.load(f)

    feature_names = meta["feature_names"]
    target_names = meta["target_names"]
    log.info(f"Features: {len(feature_names)}, Targets: {len(target_names)}")
    log.info(f"Train: {meta['n_train']:,}, Val: {meta['n_val']:,}, Test: {meta['n_test']:,}")

    train_ds = RiskDataset(DATA_DIR / "train.parquet", feature_names, target_names, feature_stats)
    val_ds   = RiskDataset(DATA_DIR / "val.parquet",   feature_names, target_names, feature_stats)
    test_ds  = RiskDataset(DATA_DIR / "test.parquet",  feature_names, target_names, feature_stats)

    BATCH_SIZE = 256
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    test_loader  = DataLoader(test_ds,  batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

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
    best_val_auc_mean = 0.0
    best_epoch = 0
    history = []
    no_improve = 0

    log.info(f"\nTraining for up to {N_EPOCHS} epochs...")
    for epoch in range(1, N_EPOCHS + 1):
        train_loss = train_one_epoch(model, train_loader, loss_fn, optimizer, device)
        val_loss, val_ptl, val_metrics, *_ = evaluate(model, val_loader, loss_fn, device, target_names)
        scheduler.step()

        val_aucs = [m["auc"] for m in val_metrics.values() if not np.isnan(m["auc"])]
        mean_auc = np.mean(val_aucs)

        log.info(f"Epoch {epoch:2d}/{N_EPOCHS}  "
                 f"train_loss={train_loss:.4f}  "
                 f"val_loss={val_loss:.4f}  "
                 f"mean_AUC={mean_auc:.4f}")
        for t in target_names:
            m = val_metrics[t]
            log.info(f"             {t:<20}  AUC={m['auc']:.4f}  AUPRC={m['auprc']:.4f}")

        history.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "val_loss": val_loss,
            "val_metrics": val_metrics,
            "mean_auc": mean_auc,
            "lr": optimizer.param_groups[0]["lr"],
        })

        if mean_auc > best_val_auc_mean:
            best_val_auc_mean = mean_auc
            best_epoch = epoch
            no_improve = 0
            torch.save(model.state_dict(), OUT_DIR / "best_model_state.pt")
            log.info(f"             ↑ new best!")
        else:
            no_improve += 1
            if no_improve >= PATIENCE:
                log.info(f"\nEarly stopping at epoch {epoch} (no improvement for {PATIENCE} epochs)")
                break

    log.info(f"\nLoading best model from epoch {best_epoch}...")
    model.load_state_dict(torch.load(OUT_DIR / "best_model_state.pt"))

    temperatures = calibrate_temperatures(model, val_loader, device, target_names)
    model.set_temperature(temperatures)

    log.info("\nFinal test set evaluation (with calibration)...")
    test_loss, _, test_metrics, *_ = evaluate(model, test_loader, loss_fn, device, target_names)

    log.info(f"Test loss: {test_loss:.4f}")
    log.info(f"{'Target':<20}  {'AUC':>7}  {'AUPRC':>7}  {'Brier':>7}  {'n':>7}  {'n_pos':>7}")
    log.info("-" * 70)
    for t in target_names:
        m = test_metrics[t]
        log.info(f"{t:<20}  {m['auc']:.4f}  {m['auprc']:.4f}  {m['brier']:.4f}  "
                 f"{m['n']:>7}  {m['n_pos']:>7}")

    test_aucs = [m["auc"] for m in test_metrics.values() if not np.isnan(m["auc"])]
    log.info(f"\nMean test AUC: {np.mean(test_aucs):.4f}")

    save_model(
        model, OUT_DIR / "model.pt",
        feature_stats=feature_stats,
        feature_names=feature_names,
        target_names=target_names,
        target_stats=target_stats,
        temperature=temperatures.tolist(),
        test_metrics=test_metrics,
        best_epoch=best_epoch,
        history=history,
    )
    log.info(f"\nModel saved to {OUT_DIR / 'model.pt'}")

    with open(OUT_DIR / "metrics.json", "w") as f:
        json.dump({
            "test_metrics": test_metrics,
            "test_loss": test_loss,
            "mean_test_auc": float(np.mean(test_aucs)),
            "best_epoch": best_epoch,
            "n_epochs_trained": len(history),
            "temperatures": temperatures.tolist(),
            "target_names": target_names,
            "n_train": len(train_ds),
            "n_val": len(val_ds),
            "n_test": len(test_ds),
            "n_features": len(feature_names),
        }, f, indent=2)
    log.info(f"Metrics summary saved to {OUT_DIR / 'metrics.json'}")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
