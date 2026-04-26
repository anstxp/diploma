from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.multimodal_models import build_model, CrossAttentionFusionModel
from engine.multimodal_dataset import (
    HAM10000Multimodal, get_eval_transform, encode_metadata,
)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("mm_gradcam")

ROOT = Path(__file__).parent.parent
PROCESSED = ROOT / "data_processed"
META_CSV = ROOT / "data" / "HAM10000_metadata.csv"
IMAGE_DIR = ROOT / "data" / "HAM10000_images"
FIG = ROOT / "analysis" / "figures"
FIG.mkdir(exist_ok=True, parents=True)


class MultimodalGradCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self.activations = None
        self.gradients = None
        target_layer.register_forward_hook(self._save_act)
        target_layer.register_full_backward_hook(self._save_grad)

    def _save_act(self, module, inp, out):
        self.activations = out.detach()

    def _save_grad(self, module, grad_in, grad_out):
        self.gradients = grad_out[0].detach()

    def generate(self, image: torch.Tensor, meta: torch.Tensor,
                  class_idx: int = None) -> np.ndarray:
        self.model.eval()
        image = image.unsqueeze(0)
        meta = meta.unsqueeze(0)
        logits = self.model(image, meta)
        if class_idx is None:
            class_idx = int(logits.argmax(1).item())

        self.model.zero_grad()
        target = logits[0, class_idx]
        target.backward()

        acts = self.activations[0]
        grads = self.gradients[0]
        weights = grads.mean(dim=(1, 2))
        cam = (weights[:, None, None] * acts).sum(0)
        cam = F.relu(cam)
        cam_min, cam_max = cam.min(), cam.max()
        if cam_max > cam_min:
            cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam = torch.zeros_like(cam)
        cam = cam.unsqueeze(0).unsqueeze(0)
        cam = F.interpolate(cam, size=(224, 224), mode="bilinear",
                              align_corners=False)
        return cam.squeeze().cpu().numpy()


def overlay_heatmap(image_pil, heatmap, alpha=0.45):
    image_np = np.array(image_pil.resize((224, 224))) / 255.0
    cmap = plt.get_cmap("jet")
    colored = cmap(heatmap)[..., :3]
    return (1 - alpha) * image_np + alpha * colored


def main(model_dir: Path = None, n_correct=7, n_errors=6, n_mel=6):
    if model_dir is None:
        mm_dir = ROOT / "model_out" / "multimodal"
        candidates = []
        for d in mm_dir.iterdir():
            if d.is_dir():
                metrics_path = d / "metrics.json"
                if metrics_path.exists():
                    with open(metrics_path) as f:
                        m = json.load(f)
                    candidates.append((m["best_val_auc"], d, m["model_name"]))
        if not candidates:
            log.error("No trained models found")
            return
        candidates.sort(reverse=True)
        _, model_dir, model_name = candidates[0]
        log.info(f"Using best model: {model_name}")

    state = torch.load(model_dir / "model.pt", map_location="cpu",
                        weights_only=False)
    model_name = state["model_name"]
    classes = state["classes"]
    meta_stats = state["meta_stats"]
    image_size = state.get("args", {}).get("image_size", 224)

    device = torch.device("cuda" if torch.cuda.is_available()
                            else ("mps" if torch.backends.mps.is_available()
                                  else "cpu"))
    log.info(f"Loading {model_name} on {device}")
    model = build_model(model_name, meta_dim=meta_stats["meta_dim"],
                         num_classes=len(classes))
    model.load_state_dict(state["model_state_dict"])
    model = model.to(device).eval()

    target_layer = model.last_conv_layer
    log.info(f"Target layer for Grad-CAM: {type(target_layer).__name__}")

    gradcam = MultimodalGradCAM(model, target_layer)

    meta_df = pd.read_csv(META_CSV)
    test_df = pd.read_csv(PROCESSED / "test.csv").merge(
        meta_df[["image_id", "age", "sex", "localization"]],
        on="image_id", how="left",
    )

    transform = get_eval_transform(image_size)

    log.info("Running inference on test for sample selection...")
    predictions = []
    for _, row in test_df.iterrows():
        try:
            img_path = IMAGE_DIR / f"{row['image_id']}.jpg"
            img = Image.open(img_path).convert("RGB")
            tensor = transform(img).unsqueeze(0).to(device)
            meta_tensor = encode_metadata(row, meta_stats).unsqueeze(0).to(device)
            with torch.no_grad():
                logits = model(tensor, meta_tensor)
                probs = torch.softmax(logits, 1).squeeze(0).cpu().numpy()
            pred_idx = int(probs.argmax())
            true_idx = classes.index(row["dx"])
            predictions.append({
                "image_id": row["image_id"],
                "dx": row["dx"],
                "pred": classes[pred_idx],
                "correct": pred_idx == true_idx,
                "confidence": float(probs.max()),
                "true_idx": true_idx,
                "pred_idx": pred_idx,
                "row": row,
            })
        except FileNotFoundError:
            continue

    log.info(f"Predictions: {len(predictions)}")

    log.info(f"[1/3] Correct gallery ({n_correct} classes)...")
    fig, axes = plt.subplots(1, n_correct, figsize=(n_correct * 3, 3.5))
    correct_per_class = {}
    for p in predictions:
        if p["correct"] and p["dx"] not in correct_per_class:
            correct_per_class[p["dx"]] = p
    for i, cls in enumerate(classes[:n_correct]):
        ax = axes[i]
        if cls in correct_per_class:
            p = correct_per_class[cls]
            img = Image.open(IMAGE_DIR / f"{p['image_id']}.jpg").convert("RGB")
            tensor = transform(img).to(device)
            meta_tensor = encode_metadata(p["row"], meta_stats).to(device)
            heatmap = gradcam.generate(tensor, meta_tensor, p["true_idx"])
            ax.imshow(overlay_heatmap(img, heatmap))
            for spine in ax.spines.values():
                spine.set_color("green")
                spine.set_linewidth(3)
            ax.set_title(f"{cls.upper()}\n{p['confidence']:.0%}", fontsize=10)
        else:
            ax.text(0.5, 0.5, f"no correct\n{cls}",
                    ha="center", va="center", transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle(f"Multimodal Grad-CAM — correct predictions [{model_name}]",
                  fontsize=12)
    plt.tight_layout()
    plt.savefig(FIG / "09_mm_gradcam_correct.png", dpi=150, bbox_inches="tight")
    plt.close()
    log.info("  09_mm_gradcam_correct.png")

    log.info(f"[2/3] Errors gallery ({n_errors})...")
    errors = sorted([p for p in predictions if not p["correct"]],
                     key=lambda p: -p["confidence"])[:n_errors]
    fig, axes = plt.subplots(2, 3, figsize=(11, 7.5))
    for i, p in enumerate(errors):
        ax = axes[i // 3, i % 3]
        img = Image.open(IMAGE_DIR / f"{p['image_id']}.jpg").convert("RGB")
        tensor = transform(img).to(device)
        meta_tensor = encode_metadata(p["row"], meta_stats).to(device)
        heatmap = gradcam.generate(tensor, meta_tensor, p["pred_idx"])
        ax.imshow(overlay_heatmap(img, heatmap))
        for spine in ax.spines.values():
            spine.set_color("red")
            spine.set_linewidth(3)
        ax.set_title(f"True: {p['dx']}, Pred: {p['pred']}\n"
                      f"conf={p['confidence']:.0%}", fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle(f"Multimodal Grad-CAM — errors [{model_name}]", fontsize=12)
    plt.tight_layout()
    plt.savefig(FIG / "10_mm_gradcam_errors.png", dpi=150, bbox_inches="tight")
    plt.close()
    log.info("  10_mm_gradcam_errors.png")

    log.info(f"[3/3] Melanoma gallery ({n_mel})...")
    mel_correct = [p for p in predictions if p["dx"] == "mel" and p["correct"]][:n_mel // 2]
    mel_missed = [p for p in predictions if p["dx"] == "mel" and not p["correct"]][:n_mel // 2]
    fig, axes = plt.subplots(2, n_mel // 2, figsize=(11, 7.5))
    if axes.ndim == 1:
        axes = axes.reshape(2, -1)
    for i, p in enumerate(mel_correct):
        ax = axes[0, i]
        img = Image.open(IMAGE_DIR / f"{p['image_id']}.jpg").convert("RGB")
        tensor = transform(img).to(device)
        meta_tensor = encode_metadata(p["row"], meta_stats).to(device)
        heatmap = gradcam.generate(tensor, meta_tensor, classes.index("mel"))
        ax.imshow(overlay_heatmap(img, heatmap))
        for spine in ax.spines.values():
            spine.set_color("green")
            spine.set_linewidth(3)
        ax.set_title(f"Caught: conf={p['confidence']:.0%}", fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])
    for i, p in enumerate(mel_missed):
        ax = axes[1, i]
        img = Image.open(IMAGE_DIR / f"{p['image_id']}.jpg").convert("RGB")
        tensor = transform(img).to(device)
        meta_tensor = encode_metadata(p["row"], meta_stats).to(device)
        heatmap = gradcam.generate(tensor, meta_tensor, classes.index("mel"))
        ax.imshow(overlay_heatmap(img, heatmap))
        for spine in ax.spines.values():
            spine.set_color("red")
            spine.set_linewidth(3)
        ax.set_title(f"Missed: pred={p['pred']}", fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle(f"Multimodal — melanoma focus [{model_name}]", fontsize=12)
    plt.tight_layout()
    plt.savefig(FIG / "11_mm_gradcam_melanoma.png", dpi=150, bbox_inches="tight")
    plt.close()
    log.info("  11_mm_gradcam_melanoma.png")

    if isinstance(model, CrossAttentionFusionModel):
        log.info("[bonus] Cross-attention map...")
        attn_examples = correct_per_class
        n = min(7, len(attn_examples))
        fig, axes = plt.subplots(2, n, figsize=(n * 3, 6))
        for i, cls in enumerate(list(attn_examples.keys())[:n]):
            p = attn_examples[cls]
            img = Image.open(IMAGE_DIR / f"{p['image_id']}.jpg").convert("RGB")
            tensor = transform(img).unsqueeze(0).to(device)
            meta_tensor = encode_metadata(p["row"], meta_stats).unsqueeze(0).to(device)
            with torch.no_grad():
                _, attn_map = model(tensor, meta_tensor, return_attention=True)
            attn_np = attn_map[0].cpu().numpy()
            attn_norm = (attn_np - attn_np.min()) / max(attn_np.max() - attn_np.min(), 1e-6)
            attn_up = np.array(Image.fromarray((attn_norm * 255).astype(np.uint8))
                                .resize((224, 224), Image.BILINEAR)) / 255.0

            axes[0, i].imshow(np.array(img.resize((224, 224))))
            axes[0, i].set_title(f"{cls.upper()}", fontsize=10)
            axes[0, i].set_xticks([]); axes[0, i].set_yticks([])

            axes[1, i].imshow(overlay_heatmap(img, attn_up))
            axes[1, i].set_xticks([]); axes[1, i].set_yticks([])
        fig.suptitle("Cross-attention — metadata queries select spatial regions",
                      fontsize=12)
        plt.tight_layout()
        plt.savefig(FIG / "12_mm_attention_map.png", dpi=150, bbox_inches="tight")
        plt.close()
        log.info("  12_mm_attention_map.png")

    log.info("Done.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, default=None)
    args = parser.parse_args()
    main(args.model_dir)
