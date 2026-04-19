from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

from .model import HemaxDermaNet, load_model

log = logging.getLogger("derma_inference")


@dataclass
class Prediction:
    top_class: str
    top_prob: float
    top_class_name_uk: str
    top_class_name_en: str
    severity: str
    all_probs: Dict[str, float]
    top_k: List[Tuple[str, float]]
    image_id: Optional[str] = None


class DermaPredictor:

    def __init__(self, model_path: Path, device: str = "cpu",
                 calibration_path: Optional[Path] = None):
        self.device = torch.device(device)
        log.info(f"Loading derma model from {model_path}")
        self.model, self.extras = load_model(model_path, device=str(self.device))
        self.classes: List[str] = self.extras["classes"]
        self.class_names_en: Dict[str, str] = self.extras["class_names_en"]
        self.class_names_uk: Dict[str, str] = self.extras["class_names_uk"]
        self.class_severity: Dict[str, str] = self.extras["class_severity"]
        self.image_size: int = self.extras.get("image_size", 224)
        self.mean = self.extras.get("imagenet_mean", [0.485, 0.456, 0.406])
        self.std = self.extras.get("imagenet_std", [0.229, 0.224, 0.225])

        self.preprocess = transforms.Compose([
            transforms.Resize((self.image_size, self.image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=self.mean, std=self.std),
        ])

        self.calibration: Optional[Dict] = None
        if calibration_path is None:
            candidates = [
                Path(model_path).parent / "calibration_params.json",
                Path(model_path).parent.parent / "analysis" / "reports" /
                    "calibration_params.json",
            ]
        else:
            candidates = [Path(calibration_path)]
        for p in candidates:
            if p.exists():
                with open(p) as f:
                    self.calibration = json.load(f)
                log.info(f"Loaded calibration from {p} "
                         f"(T={self.calibration.get('temperature', 1.0):.3f}, "
                         f"isotonic_classes={list(self.calibration.get('isotonic', {}).keys())})")
                break
        if self.calibration is None:
            log.warning("No calibration_params.json found — using raw softmax. "
                        "Run analysis/calibration.py to enable calibration.")

    def _calibrate_probs(self, logits: np.ndarray) -> np.ndarray:
        if self.calibration is None:
            scaled = logits
        else:
            T = self.calibration.get("temperature", 1.0)
            scaled = logits / max(T, 1e-3)

        e = np.exp(scaled - scaled.max(axis=-1, keepdims=True))
        probs = e / e.sum(axis=-1, keepdims=True)

        if self.calibration is None or not self.calibration.get("isotonic"):
            return probs

        out = np.zeros_like(probs)
        iso = self.calibration["isotonic"]
        for i, cls in enumerate(self.classes):
            if cls not in iso:
                out[..., i] = probs[..., i]
                continue
            p = iso[cls]
            out[..., i] = np.interp(probs[..., i],
                                     p["x_thresholds"], p["y_thresholds"])
        sums = out.sum(axis=-1, keepdims=True)
        sums = np.maximum(sums, 1e-9)
        return out / sums


    def _load_image(self, src: Union[str, Path, Image.Image]) -> Image.Image:
        if isinstance(src, Image.Image):
            return src.convert("RGB")
        return Image.open(src).convert("RGB")

    def predict(self, image: Union[str, Path, Image.Image],
                top_k: int = 3, image_id: Optional[str] = None) -> Prediction:
        img = self._load_image(image)
        x = self.preprocess(img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(x).cpu().numpy()
        probs = self._calibrate_probs(logits)[0]

        all_probs = {c: float(probs[i]) for i, c in enumerate(self.classes)}
        sorted_classes = sorted(all_probs.items(), key=lambda kv: -kv[1])
        top = sorted_classes[0]
        return Prediction(
            top_class=top[0],
            top_prob=top[1],
            top_class_name_uk=self.class_names_uk.get(top[0], top[0]),
            top_class_name_en=self.class_names_en.get(top[0], top[0]),
            severity=self.class_severity.get(top[0], "low"),
            all_probs=all_probs,
            top_k=sorted_classes[:top_k],
            image_id=image_id,
        )


    def gradcam(self, image: Union[str, Path, Image.Image],
                target_class: Optional[str] = None) -> Tuple[Prediction, np.ndarray]:
        img = self._load_image(image)
        x = self.preprocess(img).unsqueeze(0).to(self.device)
        x.requires_grad_(False)

        target_layer = self.model.last_conv_layer
        activations = {}
        gradients = {}

        def fwd_hook(module, inp, out):
            activations["a"] = out

        def bwd_hook(module, grad_in, grad_out):
            gradients["g"] = grad_out[0]

        h_fwd = target_layer.register_forward_hook(fwd_hook)
        h_bwd = target_layer.register_full_backward_hook(bwd_hook)

        self.model.eval()
        logits = self.model(x)
        probs = F.softmax(logits, dim=1)

        if target_class is not None and target_class in self.classes:
            target_idx = self.classes.index(target_class)
        else:
            target_idx = int(logits.argmax(dim=1).item())

        self.model.zero_grad()
        score = logits[0, target_idx]
        score.backward()

        h_fwd.remove()
        h_bwd.remove()

        feats = activations["a"][0].detach().cpu().numpy()
        grads = gradients["g"][0].detach().cpu().numpy()
        weights = grads.mean(axis=(1, 2))
        cam = np.einsum("c,chw->hw", weights, feats)
        cam = np.maximum(cam, 0)
        if cam.max() > 0:
            cam = cam / cam.max()

        cam_resized = np.array(
            Image.fromarray((cam * 255).astype(np.uint8))
                 .resize((self.image_size, self.image_size), Image.BILINEAR)
        ).astype(np.float32) / 255.0

        heatmap = self._apply_jet_colormap(cam_resized)
        img_resized = img.resize((self.image_size, self.image_size))
        img_np = np.array(img_resized).astype(np.float32) / 255.0
        overlay = (img_np * 0.55 + heatmap * 0.45)
        overlay = np.clip(overlay * 255, 0, 255).astype(np.uint8)

        logits_np = logits.detach().cpu().numpy()
        probs_arr = self._calibrate_probs(logits_np)[0]
        all_probs = {c: float(probs_arr[i]) for i, c in enumerate(self.classes)}
        sorted_classes = sorted(all_probs.items(), key=lambda kv: -kv[1])
        top = sorted_classes[0]
        prediction = Prediction(
            top_class=top[0],
            top_prob=top[1],
            top_class_name_uk=self.class_names_uk.get(top[0], top[0]),
            top_class_name_en=self.class_names_en.get(top[0], top[0]),
            severity=self.class_severity.get(top[0], "low"),
            all_probs=all_probs,
            top_k=sorted_classes[:3],
        )
        return prediction, overlay

    @staticmethod
    def _apply_jet_colormap(gray: np.ndarray) -> np.ndarray:
        r = np.clip(1.5 - np.abs(4 * gray - 3), 0, 1)
        g = np.clip(1.5 - np.abs(4 * gray - 2), 0, 1)
        b = np.clip(1.5 - np.abs(4 * gray - 1), 0, 1)
        return np.stack([r, g, b], axis=-1)
