from __future__ import annotations

import argparse
import json
import logging
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.optim as optim
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.multimodal_models import build_model, FocalLoss, MODEL_REGISTRY
from engine.multimodal_dataset import (
    HAM10000Multimodal, fit_metadata_stats, make_balanced_sampler,
    get_train_transform, get_eval_transform,
)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("train_multimodal")

ROOT = Path(__file__).parent.parent
PROCESSED = ROOT / "data_processed"
META_CSV = ROOT / "data" / "HAM10000_metadata.csv"
IMAGE_DIR = ROOT / "data" / "HAM10000_images"
OUT_DIR = ROOT / "model_out" / "multimodal"
OUT_DIR.mkdir(exist_ok=True, parents=True)
REP = ROOT / "analysis" / "reports"
FIG = ROOT / "analysis" / "figures"
REP.mkdir(exist_ok=True, parents=True)
FIG.mkdir(exist_ok=True, parents=True)


def merge_metadata(splits_dir: Path, meta_csv: Path):
    out = {}
    for name in ["train", "val", "test"]:
        df = pd.read_csv(splits_dir / f"{name}.csv")
        out[name] = df
        log.info(f"  {name}: {len(df)} rows, "
                 f"missing age={df['age'].isna().sum()}, "
                 f"missing sex={df['sex'].isna().sum()}, "
                 f"missing loc={df['localization'].isna().sum()}")
    return out


def evaluate(model, loader, criterion, device, classes):
    model.eval()
    all_probs, all_labels = [], []
    total_loss = 0.0
    with torch.no_grad():
        for images, metas, labels, _ in loader:
            images = images.to(device)
            metas = metas.to(device)
            labels = labels.to(device)
            logits = model(images, metas)
            loss = criterion(logits, labels)
            total_loss += loss.item() * images.size(0)
            probs = torch.softmax(logits, dim=1)
            all_probs.append(probs.cpu())
            all_labels.append(labels.cpu())

    probs = torch.cat(all_probs).numpy()
    labels = torch.cat(all_labels).numpy()
    preds = probs.argmax(axis=1)

    acc = accuracy_score(labels, preds)
    macro_f1 = f1_score(labels, preds, average="macro", zero_division=0)

    aucs = {}
    for i, cls in enumerate(classes):
        try:
            y_true = (labels == i).astype(int)
            if 0 < y_true.sum() < len(y_true):
                aucs[cls] = float(roc_auc_score(y_true, probs[:, i]))
            else:
                aucs[cls] = float("nan")
        except Exception:
            aucs[cls] = float("nan")

    order = np.argsort(-probs, axis=1)
    top3 = sum(labels[i] in order[i, :3] for i in range(len(labels)))
    top3_acc = top3 / len(labels)

    return {
        "loss": total_loss / max(len(labels), 1),
        "accuracy": float(acc),
        "top3_accuracy": float(top3_acc),
        "macro_f1": float(macro_f1),
        "macro_auc": float(np.nanmean(list(aucs.values()))),
        "per_class_auc": aucs,
    }


def build_optimizer(model, args, name):
    if name in ("late_fusion", "image_only"):
        backbone_params = []
        head_params = []
        for n, p in model.named_parameters():
            if not p.requires_grad:
                continue
            if "image_encoder.features" in n:
                backbone_params.append(p)
            else:
                head_params.append(p)
        log.info(f"  Backbone params: {sum(p.numel() for p in backbone_params):,} "
                 f"(LR × {args.backbone_lr_mult})")
        log.info(f"  Head/fusion params: {sum(p.numel() for p in head_params):,} "
                 f"(LR × 1.0)")
        return optim.AdamW([
            {"params": backbone_params, "lr": args.lr * args.backbone_lr_mult},
            {"params": head_params, "lr": args.lr},
        ], weight_decay=args.weight_decay)
    else:
        return optim.AdamW(model.parameters(), lr=args.lr,
                            weight_decay=args.weight_decay)


def make_lr_lambda(warmup_epochs: int, total_epochs: int):
    def lr_lambda(epoch):
        if epoch < warmup_epochs:
            return (epoch + 1) / warmup_epochs
        progress = (epoch - warmup_epochs) / max(total_epochs - warmup_epochs, 1)
        return 0.01 + 0.99 * 0.5 * (1 + math.cos(math.pi * progress))
    return lr_lambda


def train_one_model(name: str, splits, meta_stats, classes, args, device):
    log.info("=" * 70)
    log.info(f"MODEL: {name}")
    log.info(f"  meta_dim: {meta_stats['meta_dim']}")
    log.info(f"  backbone: {args.backbone if name in ('late_fusion','image_only') else 'legacy CNN-B'}")
    log.info(f"  image_size: {args.image_size}")
    log.info("=" * 70)

    out_dir = OUT_DIR / name
    out_dir.mkdir(exist_ok=True, parents=True)

    train_ds = HAM10000Multimodal(
        splits["train"], IMAGE_DIR, classes, meta_stats,
        transform=get_train_transform(args.image_size, heavy=args.heavy_aug),
        image_size=args.image_size,
    )
    val_ds = HAM10000Multimodal(
        splits["val"], IMAGE_DIR, classes, meta_stats,
        transform=get_eval_transform(args.image_size),
        image_size=args.image_size,
    )
    test_ds = HAM10000Multimodal(
        splits["test"], IMAGE_DIR, classes, meta_stats,
        transform=get_eval_transform(args.image_size),
        image_size=args.image_size,
    )

    counts = train_ds.df["dx"].value_counts().to_dict()
    total = sum(counts.values())
    cw = {c: total / (len(classes) * counts.get(c, 1)) for c in classes}

    sampler = make_balanced_sampler(train_ds, cw) if args.balanced_sampler else None
    train_loader = DataLoader(train_ds, batch_size=args.bs,
                               sampler=sampler, shuffle=(sampler is None),
                               num_workers=args.num_workers, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=args.bs, shuffle=False,
                             num_workers=args.num_workers, pin_memory=True)
    test_loader = DataLoader(test_ds, batch_size=args.bs, shuffle=False,
                              num_workers=args.num_workers, pin_memory=True)

    model = build_model(name,
                          meta_dim=meta_stats["meta_dim"],
                          num_classes=len(classes),
                          backbone=args.backbone,
                          embed_dim=args.embed_dim).to(device)
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    log.info(f"  total trainable params: {n_params:,}")

    cw_tensor = torch.tensor([cw[c] for c in classes],
                              dtype=torch.float32, device=device)
    if args.loss == "focal":
        criterion = FocalLoss(gamma=2.0,
                                weight=cw_tensor if args.use_class_weights else None)
    else:
        criterion = torch.nn.CrossEntropyLoss(
            weight=cw_tensor if args.use_class_weights else None
        )

    optimizer = build_optimizer(model, args, name)

    scheduler = optim.lr_scheduler.LambdaLR(
        optimizer, lr_lambda=make_lr_lambda(args.warmup_epochs, args.epochs)
    )

    history = []
    best_val_auc = -float("inf")
    best_epoch = 0
    epochs_no_improve = 0

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0

        for images, metas, labels, _ in train_loader:
            images = images.to(device, non_blocking=True)
            metas = metas.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)
            optimizer.zero_grad()
            logits = model(images, metas)
            loss = criterion(logits, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            train_loss += loss.item() * images.size(0)
            train_correct += (logits.argmax(1) == labels).sum().item()
            train_total += labels.size(0)

        train_loss /= max(train_total, 1)
        train_acc = train_correct / max(train_total, 1)
        scheduler.step()

        val_metrics = evaluate(model, val_loader, criterion, device, classes)
        elapsed = time.time() - t0
        current_lrs = [g["lr"] for g in optimizer.param_groups]
        lr_str = " / ".join(f"{lr:.2e}" for lr in current_lrs)

        log.info(f"  Epoch {epoch:2d}/{args.epochs}  "
                 f"({elapsed:.1f}s, lr={lr_str})  "
                 f"train_loss={train_loss:.4f}  "
                 f"train_acc={train_acc:.3f}  "
                 f"val_acc={val_metrics['accuracy']:.3f}  "
                 f"val_f1={val_metrics['macro_f1']:.3f}  "
                 f"val_auc={val_metrics['macro_auc']:.3f}")

        history.append({
            "epoch": epoch,
            "train_loss": train_loss, "train_acc": train_acc,
            "val_loss": val_metrics["loss"],
            "val_acc": val_metrics["accuracy"],
            "val_f1": val_metrics["macro_f1"],
            "val_auc": val_metrics["macro_auc"],
            "lr": current_lrs[0] if len(current_lrs) == 1 else current_lrs,
        })

        if val_metrics["macro_auc"] > best_val_auc:
            best_val_auc = val_metrics["macro_auc"]
            best_epoch = epoch
            epochs_no_improve = 0
            torch.save({
                "model_state_dict": model.state_dict(),
                "model_name": name,
                "epoch": epoch,
                "best_val_auc": best_val_auc,
                "meta_stats": meta_stats,
                "classes": classes,
                "args": vars(args),
            }, out_dir / "model.pt")
            log.info(f"    ↑ new best (val_auc={best_val_auc:.4f}) — saved")
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= args.patience:
                log.info(f"  early stopping at epoch {epoch} "
                         f"(best={best_epoch}, val_auc={best_val_auc:.4f})")
                break

    log.info(f"  Loading best model from epoch {best_epoch}, evaluating on test...")
    state = torch.load(out_dir / "model.pt", map_location=device, weights_only=False)
    model.load_state_dict(state["model_state_dict"])
    test_metrics = evaluate(model, test_loader, criterion, device, classes)
    log.info(f"  TEST  acc={test_metrics['accuracy']:.4f}  "
             f"top3={test_metrics['top3_accuracy']:.4f}  "
             f"macro_f1={test_metrics['macro_f1']:.4f}  "
             f"macro_auc={test_metrics['macro_auc']:.4f}")

    summary = {
        "model_name": name,
        "best_epoch": best_epoch,
        "best_val_auc": best_val_auc,
        "n_params": n_params,
        "test_metrics": test_metrics,
        "history": history,
    }
    with open(out_dir / "metrics.json", "w") as f:
        json.dump(summary, f, indent=2)
    return summary


def make_comparison(summaries, classes):
    rows = []
    for s in summaries:
        tm = s["test_metrics"]
        rows.append({
            "model": s["model_name"],
            "params": s["n_params"],
            "best_epoch": s["best_epoch"],
            "test_acc": tm["accuracy"],
            "top3_acc": tm["top3_accuracy"],
            "macro_f1": tm["macro_f1"],
            "macro_auc": tm["macro_auc"],
            **{f"auc_{c}": tm["per_class_auc"][c] for c in classes},
        })
    df = pd.DataFrame(rows)
    df.to_csv(REP / "multimodal_comparison.csv", index=False)

    md = [
        "# HEMAX_DERMA — Multimodal Architecture Comparison (v3)",
        "",
        "All models trained on identical lesion-aware HAM10000 split.",
        "image_only and late_fusion use pretrained EfficientNet-B3 backbone.",
        "",
        "## Headline metrics",
        "",
        "| Model | Params | Best ep | Test Acc | Top-3 Acc | Macro F1 | Macro AUROC |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        md.append(f"| {r['model']} | {r['params']:,} | {r['best_epoch']} "
                  f"| {r['test_acc']:.3f} | {r['top3_acc']:.3f} "
                  f"| {r['macro_f1']:.3f} | **{r['macro_auc']:.3f}** |")

    md.extend([
        "",
        "## Per-class AUROC",
        "",
        "| Model | " + " | ".join(classes) + " |",
        "|---|" + "---|" * len(classes),
    ])
    for r in rows:
        cells = [r["model"]] + [f"{r[f'auc_{c}']:.3f}" for c in classes]
        md.append("| " + " | ".join(cells) + " |")

    (REP / "multimodal_comparison.md").write_text("\n".join(md))
    log.info(f"Saved {(REP / 'multimodal_comparison.md').relative_to(ROOT)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--bs", type=int, default=24,
                          help="Batch size (24 for EffNet-B3 @ 300, 32 for B0 @ 224)")
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--backbone-lr-mult", type=float, default=0.1,
                          help="Multiplier for pretrained backbone LR (0.1 = 10x lower)")
    parser.add_argument("--warmup-epochs", type=int, default=2)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--patience", type=int, default=5)
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--image-size", type=int, default=300,
                          help="300 for EfficientNet-B3, 224 for B0/legacy")
    parser.add_argument("--backbone", default="efficientnet_b3",
                          choices=["efficientnet_b3", "efficientnet_b0", "resnet50"])
    parser.add_argument("--embed-dim", type=int, default=256)
    parser.add_argument("--device", default=None)
    parser.add_argument("--loss", default="ce", choices=["ce", "focal"])
    parser.add_argument("--use-class-weights", action="store_true",
                        help="Use inverse-frequency class weights in loss")
    parser.add_argument("--balanced-sampler", action="store_true", default=True)
    parser.add_argument("--no-balanced-sampler", dest="balanced_sampler",
                        action="store_false")
    parser.add_argument("--heavy-aug", action="store_true", default=True,
                          help="Use RandAugment + heavy color jitter (default on)")
    parser.add_argument("--no-heavy-aug", dest="heavy_aug", action="store_false")
    parser.add_argument("--models", nargs="+", default=None,
                        help="Models to train. Default: all 6")
    args = parser.parse_args()

    if args.device is None:
        args.device = ("cuda" if torch.cuda.is_available()
                       else ("mps" if torch.backends.mps.is_available()
                             else "cpu"))
    device = torch.device(args.device)
    log.info(f"Device: {device}")
    log.info(f"Backbone: {args.backbone}, image_size: {args.image_size}, "
             f"heavy_aug: {args.heavy_aug}")

    with open(PROCESSED / "metadata.json") as f:
        meta = json.load(f)
    classes = meta["classes"]
    log.info(f"Classes: {classes}")

    log.info("Merging HAM10000 metadata into splits...")
    splits = merge_metadata(PROCESSED, META_CSV)

    meta_stats = fit_metadata_stats(splits["train"])
    log.info(f"Metadata: meta_dim={meta_stats['meta_dim']}, "
             f"age_mean={meta_stats['age_mean']:.1f}, "
             f"age_std={meta_stats['age_std']:.1f}")

    with open(OUT_DIR / "meta_stats.json", "w") as f:
        json.dump(meta_stats, f, indent=2)

    if args.models is None:
        names = list(MODEL_REGISTRY.keys())
    else:
        names = args.models
    log.info(f"Will train {len(names)} models: {names}")

    summaries = []
    for name in names:
        if name not in MODEL_REGISTRY:
            log.warning(f"Unknown model {name}, skipping")
            continue
        try:
            summary = train_one_model(name, splits, meta_stats, classes, args, device)
            summaries.append(summary)
        except Exception as e:
            log.error(f"Model {name} FAILED: {e}", exc_info=True)
            continue

    if summaries:
        log.info("\n" + "=" * 70)
        log.info("FINAL COMPARISON")
        log.info("=" * 70)
        log.info(f"{'Model':<20}  {'Acc':>6}  {'Top3':>6}  {'F1':>6}  {'AUC':>6}")
        for s in summaries:
            tm = s["test_metrics"]
            log.info(f"{s['model_name']:<20}  "
                     f"{tm['accuracy']:>6.3f}  "
                     f"{tm['top3_accuracy']:>6.3f}  "
                     f"{tm['macro_f1']:>6.3f}  "
                     f"{tm['macro_auc']:>6.3f}")
        make_comparison(summaries, classes)


if __name__ == "__main__":
    main()
