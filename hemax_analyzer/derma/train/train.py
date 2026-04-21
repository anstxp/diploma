from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import f1_score, accuracy_score, roc_auc_score
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.dataset import (
    HAM10000Dataset, get_train_transform, get_eval_transform,
    make_balanced_sampler,
)
from engine.model import HemaxDermaNet, ModelConfig, save_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("train")

ROOT = Path(__file__).parent.parent
PROCESSED = ROOT / "data_processed"
OUT_DIR = ROOT / "model_out"
OUT_DIR.mkdir(exist_ok=True)


def evaluate(model, loader, device, classes):
    model.eval()
    all_logits, all_labels = [], []
    with torch.no_grad():
        for imgs, labels, _ in loader:
            imgs = imgs.to(device)
            logits = model(imgs)
            all_logits.append(logits.cpu())
            all_labels.append(labels)
    logits = torch.cat(all_logits)
    labels = torch.cat(all_labels)
    probs = torch.softmax(logits, dim=1).numpy()
    preds = logits.argmax(dim=1).numpy()
    labels_np = labels.numpy()

    acc = accuracy_score(labels_np, preds)
    macro_f1 = f1_score(labels_np, preds, average="macro")

    aucs = {}
    for i, cls in enumerate(classes):
        try:
            y_true = (labels_np == i).astype(int)
            if y_true.sum() > 0 and y_true.sum() < len(y_true):
                aucs[cls] = float(roc_auc_score(y_true, probs[:, i]))
            else:
                aucs[cls] = float("nan")
        except Exception:
            aucs[cls] = float("nan")
    macro_auc = float(np.nanmean(list(aucs.values())))

    return {
        "accuracy": float(acc),
        "macro_f1": float(macro_f1),
        "macro_auc": macro_auc,
        "per_class_auc": aucs,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--bs", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--patience", type=int, default=5,
                        help="early stopping patience")
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--no-pretrained", action="store_true",
                        help="train from scratch (much slower convergence)")
    parser.add_argument("--device", default=None,
                        help="cuda / mps / cpu (auto-detected)")
    args = parser.parse_args()

    if args.device is None:
        if torch.cuda.is_available():
            args.device = "cuda"
        elif torch.backends.mps.is_available():
            args.device = "mps"
        else:
            args.device = "cpu"
    device = torch.device(args.device)
    log.info(f"Device: {device}")

    log.info("=" * 70)
    log.info("HEMAX_DERMA — training")
    log.info("=" * 70)

    with open(PROCESSED / "metadata.json") as f:
        meta = json.load(f)
    classes = meta["classes"]
    log.info(f"Classes: {classes}")

    train_ds = HAM10000Dataset(
        PROCESSED / "train.csv", classes,
        transform=get_train_transform(meta["image_size"]),
        image_size=meta["image_size"],
    )
    val_ds = HAM10000Dataset(
        PROCESSED / "val.csv", classes,
        transform=get_eval_transform(meta["image_size"]),
        image_size=meta["image_size"],
    )
    test_ds = HAM10000Dataset(
        PROCESSED / "test.csv", classes,
        transform=get_eval_transform(meta["image_size"]),
        image_size=meta["image_size"],
    )
    log.info(f"Train: {len(train_ds):,}, Val: {len(val_ds):,}, Test: {len(test_ds):,}")

    sampler = make_balanced_sampler(train_ds, meta["class_weights"])
    train_loader = DataLoader(train_ds, batch_size=args.bs, sampler=sampler,
                              num_workers=args.num_workers, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=args.bs, shuffle=False,
                            num_workers=args.num_workers, pin_memory=True)
    test_loader = DataLoader(test_ds, batch_size=args.bs, shuffle=False,
                             num_workers=args.num_workers, pin_memory=True)

    config = ModelConfig(
        n_classes=len(classes),
        pretrained=not args.no_pretrained,
        dropout=0.3,
        image_size=meta["image_size"],
        classes=classes,
    )
    model = HemaxDermaNet(config).to(device)
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    log.info(f"Trainable parameters: {n_params:,}")

    class_weight_tensor = torch.tensor(
        [meta["class_weights"][c] for c in classes],
        dtype=torch.float32, device=device,
    )
    criterion = nn.CrossEntropyLoss(weight=class_weight_tensor)
    optimizer = optim.AdamW(model.parameters(), lr=args.lr,
                            weight_decay=args.weight_decay)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=args.epochs, eta_min=args.lr * 0.01,
    )

    history = []
    best_val_metric = -float("inf")
    best_epoch = 0
    epochs_no_improve = 0
    best_path = OUT_DIR / "model.pt"

    for epoch in range(1, args.epochs + 1):
        t_start = time.time()
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        for batch_idx, (imgs, labels, _) in enumerate(train_loader):
            imgs = imgs.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)

            optimizer.zero_grad()
            logits = model(imgs)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * imgs.size(0)
            train_correct += (logits.argmax(1) == labels).sum().item()
            train_total += imgs.size(0)

            if batch_idx % 50 == 0:
                log.info(f"  epoch {epoch} batch {batch_idx}/{len(train_loader)}  "
                         f"loss={loss.item():.4f}")

        train_loss /= train_total
        train_acc = train_correct / train_total

        val_metrics = evaluate(model, val_loader, device, classes)
        scheduler.step()

        elapsed = time.time() - t_start
        log.info(f"Epoch {epoch:>3}  ({elapsed:.0f}s)  "
                 f"train_loss={train_loss:.4f} train_acc={train_acc:.3f}  "
                 f"val_acc={val_metrics['accuracy']:.3f}  "
                 f"val_f1={val_metrics['macro_f1']:.3f}  "
                 f"val_auc={val_metrics['macro_auc']:.3f}")

        history.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "train_acc": train_acc,
            "val_acc": val_metrics["accuracy"],
            "val_f1": val_metrics["macro_f1"],
            "val_auc": val_metrics["macro_auc"],
            "per_class_auc": val_metrics["per_class_auc"],
            "lr": optimizer.param_groups[0]["lr"],
        })

        cur = val_metrics["macro_f1"]
        if cur > best_val_metric:
            best_val_metric = cur
            best_epoch = epoch
            epochs_no_improve = 0
            save_model(model, best_path, extras={
                "classes": classes,
                "class_names_en": meta["class_names_en"],
                "class_names_uk": meta["class_names_uk"],
                "class_severity": meta["class_severity"],
                "imagenet_mean": meta["imagenet_mean"],
                "imagenet_std": meta["imagenet_std"],
                "image_size": meta["image_size"],
                "best_epoch": epoch,
                "best_val_macro_f1": float(cur),
            })
            log.info(f"   ↑ saved best model (val_f1={cur:.3f})")
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= args.patience:
                log.info(f"   ! early stopping at epoch {epoch} "
                         f"(best={best_epoch}, val_f1={best_val_metric:.3f})")
                break

    log.info("=" * 70)
    log.info(f"Loading best model from epoch {best_epoch}, evaluating on test...")
    from engine.model import load_model
    model, _ = load_model(best_path, device=str(device))
    test_metrics = evaluate(model, test_loader, device, classes)
    log.info(f"TEST  acc={test_metrics['accuracy']:.4f}  "
             f"macro_f1={test_metrics['macro_f1']:.4f}  "
             f"macro_auc={test_metrics['macro_auc']:.4f}")
    log.info("Per-class AUC:")
    for cls, auc in test_metrics["per_class_auc"].items():
        log.info(f"  {cls}: {auc:.4f}")

    with open(OUT_DIR / "metrics.json", "w") as fp:
        json.dump({
            "best_epoch": best_epoch,
            "best_val_macro_f1": best_val_metric,
            "test_metrics": test_metrics,
            "history": history,
            "args": vars(args),
        }, fp, indent=2)
    log.info(f"Saved metrics to {OUT_DIR / 'metrics.json'}")
    log.info("=" * 70)
    log.info("Done!")


if __name__ == "__main__":
    main()
