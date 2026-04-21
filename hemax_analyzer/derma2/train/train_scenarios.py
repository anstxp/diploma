from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.optim as optim
from sklearn.metrics import f1_score, accuracy_score, roc_auc_score
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.dataset import (
    HAM10000Dataset, get_train_transform, get_eval_transform,
    make_balanced_sampler,
)
from engine.scenarios import (
    SCENARIOS, ScenarioConfig, build_model, build_loss,
)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("train_scenarios")

ROOT = Path(__file__).parent.parent
PROCESSED = ROOT / "data_processed"
SCEN_DIR = ROOT / "model_out" / "scenarios"
SCEN_DIR.mkdir(exist_ok=True, parents=True)
REP = ROOT / "analysis" / "reports"
FIG = ROOT / "analysis" / "figures"
REP.mkdir(exist_ok=True, parents=True)
FIG.mkdir(exist_ok=True, parents=True)


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
    macro_f1 = f1_score(labels_np, preds, average="macro", zero_division=0)
    weighted_f1 = f1_score(labels_np, preds, average="weighted", zero_division=0)

    aucs = {}
    for i, cls in enumerate(classes):
        try:
            y_true = (labels_np == i).astype(int)
            if 0 < y_true.sum() < len(y_true):
                aucs[cls] = float(roc_auc_score(y_true, probs[:, i]))
            else:
                aucs[cls] = float("nan")
        except Exception:
            aucs[cls] = float("nan")

    top3 = 0
    order = np.argsort(-probs, axis=1)
    for i in range(len(labels_np)):
        if labels_np[i] in order[i, :3]:
            top3 += 1
    top3_acc = top3 / len(labels_np)

    return {
        "accuracy": float(acc),
        "top3_accuracy": float(top3_acc),
        "macro_f1": float(macro_f1),
        "weighted_f1": float(weighted_f1),
        "macro_auc": float(np.nanmean(list(aucs.values()))),
        "per_class_auc": aucs,
    }


def train_scenario(config: ScenarioConfig, args, meta, classes,
                   train_csv, val_csv, test_csv) -> dict:
    out_dir = SCEN_DIR / config.name
    out_dir.mkdir(exist_ok=True, parents=True)

    log.info("=" * 70)
    log.info(f"SCENARIO: {config.name}")
    log.info(f"  {config.description}")
    log.info(f"  arch={config.architecture}  dropout={config.dropout}  "
             f"aug={config.augmentation}  cw={config.class_weights}  "
             f"loss={config.loss}  attn={config.use_attention}")
    log.info("=" * 70)

    device = torch.device(args.device)
    image_size = args.image_size

    train_tf = get_train_transform(image_size) if config.augmentation \
                else get_eval_transform(image_size)
    train_ds = HAM10000Dataset(train_csv, classes, transform=train_tf,
                                image_size=image_size)
    val_ds = HAM10000Dataset(val_csv, classes,
                              transform=get_eval_transform(image_size),
                              image_size=image_size)
    test_ds = HAM10000Dataset(test_csv, classes,
                               transform=get_eval_transform(image_size),
                               image_size=image_size)

    sampler = (make_balanced_sampler(train_ds, meta["class_weights"])
               if config.class_weights else None)
    shuffle = sampler is None
    train_loader = DataLoader(train_ds, batch_size=args.bs,
                               sampler=sampler, shuffle=shuffle,
                               num_workers=args.num_workers, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=args.bs, shuffle=False,
                             num_workers=args.num_workers, pin_memory=True)
    test_loader = DataLoader(test_ds, batch_size=args.bs, shuffle=False,
                              num_workers=args.num_workers, pin_memory=True)

    model = build_model(config, n_classes=len(classes),
                        input_size=image_size).to(device)
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    log.info(f"  trainable params: {n_params:,}")

    cw_tensor = torch.tensor([meta["class_weights"][c] for c in classes],
                              dtype=torch.float32, device=device)
    criterion = build_loss(config, cw_tensor).to(device)

    optimizer = optim.AdamW(model.parameters(), lr=args.lr,
                             weight_decay=args.weight_decay)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=args.epochs, eta_min=args.lr * 0.01,
    )

    history = []
    best_val_f1 = -float("inf")
    best_epoch = 0
    epochs_no_improve = 0
    best_path = out_dir / "model.pt"

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0

        for imgs, labels, _ in train_loader:
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

        train_loss /= max(train_total, 1)
        train_acc = train_correct / max(train_total, 1)
        val_metrics = evaluate(model, val_loader, device, classes)
        scheduler.step()

        elapsed = time.time() - t0
        log.info(f"  epoch {epoch:>2}/{args.epochs}  ({elapsed:.0f}s)  "
                 f"train_loss={train_loss:.4f} train_acc={train_acc:.3f}  "
                 f"val_acc={val_metrics['accuracy']:.3f}  "
                 f"val_f1={val_metrics['macro_f1']:.3f}  "
                 f"val_auc={val_metrics['macro_auc']:.3f}")

        history.append({
            "epoch": epoch,
            "train_loss": train_loss, "train_acc": train_acc,
            "val_acc": val_metrics["accuracy"],
            "val_f1": val_metrics["macro_f1"],
            "val_auc": val_metrics["macro_auc"],
            "lr": optimizer.param_groups[0]["lr"],
        })

        if val_metrics["macro_f1"] > best_val_f1:
            best_val_f1 = val_metrics["macro_f1"]
            best_epoch = epoch
            epochs_no_improve = 0
            torch.save({
                "model_state_dict": model.state_dict(),
                "scenario": config.__dict__,
                "epoch": epoch,
                "best_val_f1": best_val_f1,
            }, best_path)
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= args.patience:
                log.info(f"  early stopping at epoch {epoch} "
                         f"(best={best_epoch}, val_f1={best_val_f1:.3f})")
                break

    log.info(f"  Loading best model from epoch {best_epoch}, evaluating on test...")
    state = torch.load(best_path, map_location=device, weights_only=False)
    model.load_state_dict(state["model_state_dict"])
    test_metrics = evaluate(model, test_loader, device, classes)
    log.info(f"  TEST  acc={test_metrics['accuracy']:.4f}  "
             f"top3={test_metrics['top3_accuracy']:.4f}  "
             f"macro_f1={test_metrics['macro_f1']:.4f}  "
             f"macro_auc={test_metrics['macro_auc']:.4f}")

    summary = {
        "scenario": config.name,
        "description": config.description,
        "best_epoch": best_epoch,
        "best_val_f1": best_val_f1,
        "n_params": n_params,
        "image_size": image_size,
        "test_metrics": test_metrics,
        "history": history,
        "config": {
            "architecture": config.architecture,
            "backbone": config.backbone,
            "dropout": config.dropout,
            "augmentation": config.augmentation,
            "class_weights": config.class_weights,
            "loss": config.loss,
            "use_attention": config.use_attention,
        },
    }
    with open(out_dir / "metrics.json", "w") as f:
        json.dump(summary, f, indent=2)
    return summary


def make_comparison_table(summaries):
    rows = []
    for s in summaries:
        tm = s["test_metrics"]
        rows.append({
            "scenario": s["scenario"],
            "params": s["n_params"],
            "best_epoch": s["best_epoch"],
            "test_acc": tm["accuracy"],
            "top3_acc": tm["top3_accuracy"],
            "macro_f1": tm["macro_f1"],
            "macro_auc": tm["macro_auc"],
            "mel_auc": tm["per_class_auc"].get("mel", float("nan")),
            "bcc_auc": tm["per_class_auc"].get("bcc", float("nan")),
            "nv_auc": tm["per_class_auc"].get("nv", float("nan")),
        })
    df = pd.DataFrame(rows)
    df.to_csv(REP / "scenarios_comparison.csv", index=False)

    md = ["# HEMAX_DERMA — Scenario Comparison", "",
          "Adapted from Chinothebuilder (2023), *Human Against Machine with "
          "10000 Training Images: Dermatoscopic Image Analysis using CNNs* "
          "(SSID 2183141 Neural Computing dissertation, "
          "https://github.com/Chinothebuilder/HAM10000).",
          "",
          "Eight training scenarios reproduced in PyTorch within the HEMAX "
          "framework, on identical lesion-aware HAM10000 split (70/15/15 by "
          "lesion_id, n_test=1520).",
          ""]
    md.append("| Scenario | Params | Best ep | Test Acc | Top-3 Acc | Macro F1 | Macro AUC | MEL AUC | BCC AUC | NV AUC |")
    md.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        md.append(f"| {r['scenario']} | {r['params']:,} | {r['best_epoch']} "
                  f"| {r['test_acc']:.3f} | {r['top3_acc']:.3f} "
                  f"| {r['macro_f1']:.3f} | {r['macro_auc']:.3f} "
                  f"| {r['mel_auc']:.3f} | {r['bcc_auc']:.3f} | {r['nv_auc']:.3f} |")
    md.append("")
    md.append("## Description per scenario")
    md.append("")
    for s in summaries:
        md.append(f"**{s['scenario']}** — {s['description']}")
        md.append("")

    (REP / "scenarios_comparison.md").write_text("\n".join(md))

    try:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(12, 6))
        x = np.arange(len(rows))
        w = 0.27
        ax.bar(x - w, [r["test_acc"] for r in rows], w, label="Top-1 Acc")
        ax.bar(x, [r["top3_acc"] for r in rows], w, label="Top-3 Acc")
        ax.bar(x + w, [r["macro_auc"] for r in rows], w, label="Macro AUC")
        ax.set_xticks(x)
        ax.set_xticklabels([r["scenario"] for r in rows],
                            rotation=30, ha="right")
        ax.set_ylim(0, 1)
        ax.set_ylabel("Score")
        ax.set_title("HEMAX_DERMA — scenario comparison\n"
                     "(adapted from Chinothebuilder 2023 SSID 2183141)")
        ax.legend()
        ax.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        plt.savefig(FIG / "16_scenarios_comparison.png", dpi=150)
        plt.close()
    except Exception as e:
        log.warning(f"Could not save plot: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--bs", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--patience", type=int, default=5)
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--image-size", type=int, default=71,
                        help="71 matches notebook; 224 uses standard ResNet input")
    parser.add_argument("--device", default=None)
    parser.add_argument("--scenario", default=None,
                        help="Run only one scenario by name")
    parser.add_argument("--scenarios", nargs="*", default=None,
                        help="Run subset by number prefix, e.g. --scenarios 1 2 7 8")
    args = parser.parse_args()

    if args.device is None:
        args.device = ("cuda" if torch.cuda.is_available()
                       else ("mps" if torch.backends.mps.is_available()
                             else "cpu"))
    log.info(f"Device: {args.device}")
    log.info(f"Image size: {args.image_size}")

    with open(PROCESSED / "metadata.json") as f:
        meta = json.load(f)
    classes = meta["classes"]

    train_csv = PROCESSED / "train.csv"
    val_csv = PROCESSED / "val.csv"
    test_csv = PROCESSED / "test.csv"

    if args.scenario:
        names = [args.scenario]
    elif args.scenarios:
        names = []
        for token in args.scenarios:
            matches = [n for n in SCENARIOS if n.startswith(token + "_")
                       or n == token]
            if not matches:
                log.warning(f"  No scenario matches '{token}'")
            names.extend(matches)
    else:
        names = list(SCENARIOS.keys())

    log.info(f"Will train {len(names)} scenarios: {names}")

    summaries = []
    for name in names:
        if name not in SCENARIOS:
            log.warning(f"Unknown scenario {name}, skipping")
            continue
        config = SCENARIOS[name]
        try:
            summary = train_scenario(config, args, meta, classes,
                                      train_csv, val_csv, test_csv)
            summary["description"] = config.description
            summaries.append(summary)
        except Exception as e:
            log.error(f"  Scenario {name} FAILED: {e}", exc_info=True)
            continue

    if summaries:
        log.info("\n" + "=" * 70)
        log.info("FINAL COMPARISON")
        log.info("=" * 70)
        log.info(f"{'Scenario':<25}  {'Acc':>6}  {'Top3':>6}  {'F1':>6}  {'AUC':>6}")
        for s in summaries:
            tm = s["test_metrics"]
            log.info(f"{s['scenario']:<25}  "
                     f"{tm['accuracy']:>6.3f}  "
                     f"{tm['top3_accuracy']:>6.3f}  "
                     f"{tm['macro_f1']:>6.3f}  "
                     f"{tm['macro_auc']:>6.3f}")
        make_comparison_table(summaries)
        log.info(f"\nReports saved to {REP}")


if __name__ == "__main__":
    main()
