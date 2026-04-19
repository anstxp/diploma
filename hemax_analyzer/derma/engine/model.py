from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import torch
import torch.nn as nn
import torchvision
from torchvision.models import resnet18, ResNet18_Weights

log = logging.getLogger("model")


@dataclass
class ModelConfig:
    n_classes: int = 7
    pretrained: bool = True
    dropout: float = 0.3
    image_size: int = 224
    classes: List[str] = None


class HemaxDermaNet(nn.Module):

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config

        if config.pretrained:
            try:
                self.backbone = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
                log.info("Using ImageNet pretrained weights")
            except Exception as e:
                log.warning(f"Pretrained weights unavailable ({e}); training from scratch")
                self.backbone = resnet18(weights=None)
        else:
            self.backbone = resnet18(weights=None)

        in_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Sequential(
            nn.Dropout(config.dropout),
            nn.Linear(in_features, config.n_classes),
        )

    def forward(self, x):
        return self.backbone(x)

    @property
    def feature_extractor(self):
        return nn.Sequential(*list(self.backbone.children())[:-2])

    @property
    def last_conv_layer(self):
        return self.backbone.layer4


def save_model(model: HemaxDermaNet, path: Path,
               extras: Optional[Dict] = None) -> None:
    state = {
        "model_state_dict": model.state_dict(),
        "config": {
            "n_classes": model.config.n_classes,
            "pretrained": model.config.pretrained,
            "dropout": model.config.dropout,
            "image_size": model.config.image_size,
            "classes": model.config.classes,
        },
        "extras": extras or {},
    }
    torch.save(state, path)
    log.info(f"Saved model to {path}")


def load_model(path: Path, device: str = "cpu"):
    state = torch.load(path, map_location=device, weights_only=False)
    config = ModelConfig(**state["config"])
    config.pretrained = False
    model = HemaxDermaNet(config)
    model.load_state_dict(state["model_state_dict"])
    model.to(device)
    model.eval()
    return model, state.get("extras", {})
