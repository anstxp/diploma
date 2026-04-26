from __future__ import annotations

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

from engine.model import HemaxDermaNet, ModelConfig
from engine.multimodal_models import build_model
from engine.multimodal_dataset import (
    HAM10000Multimodal, get_eval_transform, encode_metadata,
)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("comparison")

ROOT = Path(__file__).parent.parent
PROCESSED = ROOT / "data_processed"
META_CSV = ROOT / "data" / "HAM10000_metadata.csv"
IMAGE_DIR = ROOT / "data" / "HAM10000_images"
FIG = ROOT / "analysis" / "figures"
FIG.mkdir(exist_ok=True, parents=True)

CLASSES = ['akiec', 'bcc', 'bkl', 'df', 'mel', 'nv', 'vasc']


class GradCAM:
    def __init__(self, model, target_layer, multimodal=False):
        self.model = model
        self.multimodal = multimodal
        self.activations = None
        self.gradients = None
        target_layer.register_forward_hook(self._save_act)
        target_layer.register_full_backward_hook(self._save_grad)

    def _save_act(self, module, inp, out):
        self.activations = out.detach()

    def _save_grad(self, module, grad_in, grad_out):
        self.gradients = grad_out[0].detach()

    def generate(self, image, meta=None, class_idx=None):
        self.model.eval()
        image = image.unsqueeze(0)
        if self.multimodal:
            meta = meta.unsqueeze(0)
            logits = self.model(image, meta)
        else:
            logits = self.model(image)
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
        return cam.squeeze().cpu().numpy(), int(logits.argmax(1).item())


def overlay_heatmap(image_pil, heatmap, alpha=0.45):
    image_np = np.array(image_pil.resize((224, 224))) / 255.0
    cmap = plt.get_cmap("jet")
    colored = cmap(heatmap)[..., :3]
    return (1 - alpha) * image_np + alpha * colored


def load_v1_model(device):
    state = torch.load(ROOT / "model_out" / "model.pt", map_location=device,
                        weights_only=False)
    if "config" in state:
        config_dict = state["config"]
        if isinstance(config_dict, dict):
            config = ModelConfig(**config_dict)
        else:
            config = config_dict
    else:
        config = ModelConfig()

    model = HemaxDermaNet(config).to(device).eval()
    sd = state.get("model_state_dict") or state.get("state_dict") or state
    model.load_state_dict(sd)

    target_layer = model.backbone.layer4
    log.info(f"v1 ResNet-18 loaded, target layer: backbone.layer4")
    return model, target_layer


def load_v2_model(name, device):
    state = torch.load(ROOT / "model_out" / "multimodal" / name / "model.pt",
                        map_location=device, weights_only=False)
    classes = state["classes"]
    meta_stats = state["meta_stats"]
    image_size = state.get("args", {}).get("image_size", 224)

    model = build_model(name, meta_dim=meta_stats["meta_dim"],
                         num_classes=len(classes))
    model.load_state_dict(state["model_state_dict"])
    model = model.to(device).eval()

    log.info(f"v2 {name} loaded")
    return model, meta_stats, image_size


def get_attention_map(model, image, meta):
    model.eval()
    with torch.no_grad():
        _, attn_map = model(image.unsqueeze(0), meta.unsqueeze(0),
                             return_attention=True)
    attn_np = attn_map[0].cpu().numpy()
    attn_min, attn_max = attn_np.min(), attn_np.max()
    if attn_max > attn_min:
        attn_norm = (attn_np - attn_min) / (attn_max - attn_min)
    else:
        attn_norm = attn_np
    attn_up = np.array(
        Image.fromarray((attn_norm * 255).astype(np.uint8))
            .resize((224, 224), Image.BILINEAR)
    ) / 255.0
    return attn_up


def find_agreement_lesions(v1_model, v2_late, v2_cross, meta_stats,
                            image_size, classes, device, target_class="mel",
                            n=3):
    meta_df = pd.read_csv(META_CSV)
    test_df = pd.read_csv(PROCESSED / "test.csv")
    if "age" not in test_df.columns:
        test_df = test_df.merge(
            meta_df[["image_id", "age", "sex", "localization"]],
            on="image_id", how="left",
        )

    transform = get_eval_transform(image_size)
    target_idx = classes.index(target_class)

    candidates = []
    test_target = test_df[test_df["dx"] == target_class]
    log.info(f"Searching among {len(test_target)} {target_class} examples...")

    for _, row in test_target.iterrows():
        image_id = row["image_id"]
        if "image_path" in row and pd.notna(row.get("image_path")):
            img_path = Path(row["image_path"])
            if not img_path.is_absolute():
                img_path = IMAGE_DIR / img_path
        else:
            img_path = IMAGE_DIR / f"{image_id}.jpg"
        if not img_path.exists():
            continue

        try:
            img = Image.open(img_path).convert("RGB")
            tensor = transform(img).to(device)
            meta_tensor = encode_metadata(row, meta_stats).to(device)

            with torch.no_grad():
                v1_pred = v1_model(tensor.unsqueeze(0)).argmax(1).item()
                v2_late_pred = v2_late(tensor.unsqueeze(0),
                                          meta_tensor.unsqueeze(0)).argmax(1).item()
                v2_cross_pred = v2_cross(tensor.unsqueeze(0),
                                            meta_tensor.unsqueeze(0)).argmax(1).item()

            if (v1_pred == target_idx and v2_late_pred == target_idx
                    and v2_cross_pred == target_idx):
                candidates.append({"row": row, "image_id": image_id,
                                    "img_path": img_path})
                if len(candidates) >= n:
                    break
        except Exception:
            continue

    return candidates


def main():
    device = torch.device("cuda" if torch.cuda.is_available()
                            else ("mps" if torch.backends.mps.is_available()
                                  else "cpu"))
    log.info(f"Device: {device}")

    log.info("Loading v1 ResNet-18...")
    v1_model, v1_target = load_v1_model(device)

    log.info("Loading v2 late_fusion...")
    v2_late, meta_stats, image_size = load_v2_model("late_fusion", device)
    v2_late_target = v2_late.image_encoder.layer3

    log.info("Loading v2 cross_attention...")
    v2_cross, _, _ = load_v2_model("cross_attention", device)
    v2_cross_target = v2_cross.layer3

    log.info("Finding 3 melanomas where all 3 models predict correctly...")
    candidates = find_agreement_lesions(
        v1_model, v2_late, v2_cross, meta_stats, image_size,
        CLASSES, device, target_class="mel", n=3,
    )

    if len(candidates) < 3:
        needed = 3 - len(candidates)
        log.warning(f"Only found {len(candidates)} agreement melanomas, "
                     f"supplementing with {needed} BCC examples...")
        extra = find_agreement_lesions(
            v1_model, v2_late, v2_cross, meta_stats, image_size,
            CLASSES, device, target_class="bcc", n=needed,
        )
        candidates.extend(extra)

    if len(candidates) == 0:
        log.error("No agreement examples found. Falling back to AKIEC...")
        candidates = find_agreement_lesions(
            v1_model, v2_late, v2_cross, meta_stats, image_size,
            CLASSES, device, target_class="akiec", n=3,
        )
        if len(candidates) == 0:
            log.error("Still none. Aborting.")
            return

    log.info(f"Selected: {[(c['image_id'], c['row']['dx']) for c in candidates]}")

    n_rows = len(candidates)
    fig, axes = plt.subplots(n_rows, 4, figsize=(14, 3.5 * n_rows))
    if n_rows == 1:
        axes = axes.reshape(1, -1)

    transform = get_eval_transform(image_size)

    column_titles = [
        "Original",
        "v1 ResNet-18 Grad-CAM\n(image-only, 11M params)",
        "v2 late_fusion Grad-CAM\n(multimodal, 471K params)",
        "v2 cross-attention map\n(metadata-conditioned, 530K)",
    ]

    v1_gradcam = GradCAM(v1_model, v1_target, multimodal=False)
    v2_late_gradcam = GradCAM(v2_late, v2_late_target, multimodal=True)

    for i, c in enumerate(candidates):
        row = c["row"]
        img = Image.open(c["img_path"]).convert("RGB")
        tensor = transform(img).to(device)
        meta_tensor = encode_metadata(row, meta_stats).to(device)

        ax = axes[i, 0]
        ax.imshow(np.array(img.resize((224, 224))))
        true_dx = row["dx"]
        age_str = f"{row['age']:.0f}" if not pd.isna(row.get("age")) else "?"
        sex_str = row.get("sex", "?")
        loc_str = row.get("localization", "?")
        info = f"{c['image_id']}\n{true_dx.upper()} | age={age_str} | {sex_str}\n{loc_str}"
        ax.set_title(info, fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])

        ax = axes[i, 1]
        cam_v1, pred_v1 = v1_gradcam.generate(tensor,
                                                 class_idx=CLASSES.index(true_dx))
        ax.imshow(overlay_heatmap(img, cam_v1))
        ax.set_title(f"pred: {CLASSES[pred_v1].upper()}", fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])

        ax = axes[i, 2]
        cam_late, pred_late = v2_late_gradcam.generate(
            tensor, meta_tensor, class_idx=CLASSES.index(true_dx))
        ax.imshow(overlay_heatmap(img, cam_late))
        ax.set_title(f"pred: {CLASSES[pred_late].upper()}", fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])

        ax = axes[i, 3]
        attn_map = get_attention_map(v2_cross, tensor, meta_tensor)
        ax.imshow(overlay_heatmap(img, attn_map))
        with torch.no_grad():
            logits = v2_cross(tensor.unsqueeze(0), meta_tensor.unsqueeze(0))
            pred_cross = logits.argmax(1).item()
        ax.set_title(f"pred: {CLASSES[pred_cross].upper()}", fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])

    for j, title in enumerate(column_titles):
        axes[0, j].annotate(
            title, xy=(0.5, 1.25), xycoords="axes fraction",
            ha="center", va="bottom", fontsize=11, fontweight="bold",
        )

    fig.suptitle(
        "DERMA model interpretability evolution — same lesion, three approaches",
        fontsize=13, y=1.02,
    )
    plt.tight_layout()
    out_path = FIG / "17_v1_vs_multimodal_comparison.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    log.info(f"Saved {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
