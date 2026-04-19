from __future__ import annotations

import io
import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import torch
from PIL import Image, UnidentifiedImageError

from engine.multimodal_models import build_model
from engine.multimodal_dataset import (
    encode_metadata, get_eval_transform, SEX_CATEGORIES,
)

log = logging.getLogger(__name__)


class InvalidImageError(ValueError):
    pass


CLASS_NAMES_FULL = {
    "akiec": "Actinic keratosis / intraepithelial carcinoma",
    "bcc":   "Basal cell carcinoma",
    "bkl":   "Benign keratosis",
    "df":    "Dermatofibroma",
    "mel":   "Melanoma",
    "nv":    "Melanocytic nevus",
    "vasc":  "Vascular lesion",
}

SEVERITY = {
    "akiec": "medium",
    "bcc":   "high",
    "bkl":   "low",
    "df":    "low",
    "mel":   "critical",
    "nv":    "low",
    "vasc":  "low",
}


class MultimodalDermaPredictor:
    def __init__(self, weights_dir: Path, device: Optional[str] = None):
        self.weights_dir = Path(weights_dir)
        if device is None:
            device = ("cuda" if torch.cuda.is_available()
                      else ("mps" if torch.backends.mps.is_available()
                            else "cpu"))
        self.device = torch.device(device)

        model_path = self.weights_dir / "model.pt"
        if not model_path.exists():
            raise FileNotFoundError(f"model.pt not found in {self.weights_dir}")

        state = torch.load(model_path, map_location=self.device,
                            weights_only=False)
        self.model_name = state["model_name"]
        self.classes = state["classes"]
        self.meta_stats = state["meta_stats"]
        saved_args = state.get("args", {})
        self.image_size = saved_args.get("image_size", 224)
        self.backbone = saved_args.get("backbone", "efficientnet_b3")
        self.embed_dim = saved_args.get("embed_dim", 256)

        log.info(f"Loaded multimodal model: {self.model_name}")
        log.info(f"  classes: {self.classes}")
        log.info(f"  meta_dim: {self.meta_stats['meta_dim']}")
        log.info(f"  image_size: {self.image_size}")
        if self.model_name in ("late_fusion", "image_only"):
            log.info(f"  backbone: {self.backbone}, embed_dim: {self.embed_dim}")

        self.model = build_model(self.model_name,
                                  meta_dim=self.meta_stats["meta_dim"],
                                  num_classes=len(self.classes),
                                  backbone=self.backbone,
                                  embed_dim=self.embed_dim,
                                  pretrained=False)
        self.model.load_state_dict(state["model_state_dict"])
        self.model = self.model.to(self.device).eval()

        cal_path = self.weights_dir / "calibration_params.json"
        if cal_path.exists():
            with open(cal_path) as f:
                self.calibration = json.load(f)
            log.info(f"  calibration: T={self.calibration.get('temperature', 1.0):.3f}, "
                     f"strategy={self.calibration.get('production_strategy', 'unknown')}")
        else:
            self.calibration = None

        self.transform = get_eval_transform(self.image_size)

    def _encode_meta(self, age, sex, localization) -> torch.Tensor:
        sex_norm = "unknown"
        if sex is not None:
            s = str(sex).strip().lower()
            if s in ("m", "male", "ч", "чоловік", "1"):
                sex_norm = "male"
            elif s in ("f", "female", "ж", "жінка", "2"):
                sex_norm = "female"
            elif s in SEX_CATEGORIES:
                sex_norm = s
        loc_norm = "unknown"
        if localization is not None:
            loc = str(localization).strip().lower()
            known = set(self.meta_stats.get("loc_categories", []))
            if loc in known:
                loc_norm = loc
            elif "unknown" in known:
                loc_norm = "unknown"

        row = pd.Series({
            "age": age,
            "sex": sex_norm,
            "localization": loc_norm,
        })
        return encode_metadata(row, self.meta_stats)

    def predict(self, image_bytes: bytes,
                 age: Optional[float] = None,
                 sex: Optional[str] = None,
                 localization: Optional[str] = None,
                 top_k: int = 3) -> dict:
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except (UnidentifiedImageError, ValueError, OSError, Image.DecompressionBombError) as exc:
            raise InvalidImageError(
                f"Could not decode image bytes ({type(exc).__name__}). "
                "Make sure you're uploading a valid JPG/PNG file."
            ) from exc
        image_tensor = self.transform(image).unsqueeze(0).to(self.device)

        meta_tensor = self._encode_meta(age, sex, localization)
        meta_tensor = meta_tensor.unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(image_tensor, meta_tensor)

            if self.calibration:
                T = float(self.calibration.get("temperature", 1.0))
                if T > 0 and abs(T - 1.0) > 1e-6:
                    logits = logits / T

            probs = torch.softmax(logits, dim=1).squeeze(0).cpu().numpy()

        order = np.argsort(-probs)
        top_k_list = []
        for i in order[:top_k]:
            cls = self.classes[i]
            top_k_list.append({
                "class_code": cls,
                "class_name": CLASS_NAMES_FULL.get(cls, cls),
                "probability": float(probs[i]),
            })

        top_idx = int(order[0])
        top_cls = self.classes[top_idx]

        return {
            "top_class": top_cls,
            "top_class_name": CLASS_NAMES_FULL.get(top_cls, top_cls),
            "confidence": float(probs[top_idx]),
            "severity": SEVERITY.get(top_cls, "low"),
            "top_k": top_k_list,
            "all_probabilities": {c: float(probs[i])
                                    for i, c in enumerate(self.classes)},
            "meta_used": {
                "age": age,
                "sex": sex if sex in SEX_CATEGORIES else "unknown",
                "localization": localization,
                "model_arch": self.model_name,
                "backbone": self.backbone if self.model_name in ("late_fusion", "image_only") else "cnn_b",
            },
        }
