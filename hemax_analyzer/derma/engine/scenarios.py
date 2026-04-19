from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F



class NotebookCNN(nn.Module):

    def __init__(self, n_classes: int = 7, input_size: int = 71,
                 dropout: float = 0.5):
        super().__init__()
        self.input_size = input_size
        self.dropout_rate = dropout

        self.bn1 = nn.BatchNorm2d(3)
        self.conv1 = nn.Conv2d(3, 96, kernel_size=3)
        self.pool1 = nn.MaxPool2d(kernel_size=3, stride=2)

        self.bn2 = nn.BatchNorm2d(96)
        self.conv2 = nn.Conv2d(96, 512, kernel_size=3, padding=1)
        self.pool2 = nn.MaxPool2d(kernel_size=3, stride=2)

        self.bn3 = nn.BatchNorm2d(512)
        self.conv3 = nn.Conv2d(512, 1024, kernel_size=3, padding=1)
        self.pool3 = nn.MaxPool2d(kernel_size=3, stride=2)

        self.bn4 = nn.BatchNorm2d(1024)
        self.conv4 = nn.Conv2d(1024, 1024, kernel_size=3, padding=1)
        self.pool4 = nn.MaxPool2d(kernel_size=3, stride=2)

        with torch.no_grad():
            x = torch.zeros(1, 3, input_size, input_size)
            x = self.pool1(F.relu(self.conv1(self.bn1(x))))
            x = self.pool2(F.relu(self.conv2(self.bn2(x))))
            x = self.pool3(F.relu(self.conv3(self.bn3(x))))
            x = self.pool4(F.relu(self.conv4(self.bn4(x))))
            self._flat_size = x.numel()

        self.bn5 = nn.BatchNorm1d(self._flat_size)
        self.fc1 = nn.Linear(self._flat_size, 4096)
        self.drop1 = nn.Dropout(dropout)
        self.fc2 = nn.Linear(4096, 4096)
        self.drop2 = nn.Dropout(dropout)
        self.fc_out = nn.Linear(4096, n_classes)

    def features(self, x):
        x = self.pool1(F.relu(self.conv1(self.bn1(x))))
        x = self.pool2(F.relu(self.conv2(self.bn2(x))))
        x = self.pool3(F.relu(self.conv3(self.bn3(x))))
        x = self.pool4(F.relu(self.conv4(self.bn4(x))))
        return x

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        x = self.bn5(x)
        x = F.relu(self.fc1(x))
        x = self.drop1(x)
        x = F.relu(self.fc2(x))
        x = self.drop2(x)
        return self.fc_out(x)

    @property
    def last_conv_layer(self):
        return self.conv4



class SoftAttention(nn.Module):
    def __init__(self, in_channels: int):
        super().__init__()
        self.attention_conv = nn.Conv2d(in_channels, 1, kernel_size=1)

    def forward(self, x):
        scores = self.attention_conv(x)
        B, _, H, W = scores.shape
        weights = F.softmax(scores.view(B, 1, -1), dim=-1).view(B, 1, H, W)
        attended = (x * weights).sum(dim=(2, 3))
        return attended


class NotebookCNNWithAttention(nn.Module):

    def __init__(self, n_classes: int = 7, input_size: int = 71):
        super().__init__()
        self.backbone = NotebookCNN(n_classes=n_classes, input_size=input_size,
                                     dropout=0.0)
        self.attention = SoftAttention(in_channels=1024)
        self.dropout = nn.Dropout(0.2)
        self.fc_out = nn.Linear(1024, n_classes)
        self.input_size = input_size

    def forward(self, x):
        feat = self.backbone.features(x)
        attended = self.attention(feat)
        attended = self.dropout(attended)
        return self.fc_out(attended)

    @property
    def last_conv_layer(self):
        return self.backbone.conv4



class ResNetTransfer(nn.Module):
    def __init__(self, n_classes: int = 7, backbone: str = "resnet18",
                 pretrained: bool = True, dropout: float = 0.3,
                 use_attention: bool = False):
        super().__init__()
        import torchvision.models as M
        from torchvision.models import (
            ResNet18_Weights, ResNet34_Weights, ResNet50_Weights,
        )

        weight_map = {
            "resnet18": (M.resnet18, ResNet18_Weights.IMAGENET1K_V1),
            "resnet34": (M.resnet34, ResNet34_Weights.IMAGENET1K_V1),
            "resnet50": (M.resnet50, ResNet50_Weights.IMAGENET1K_V2),
        }
        if backbone not in weight_map:
            raise ValueError(f"Unknown backbone: {backbone}")
        ctor, weights = weight_map[backbone]

        if pretrained:
            try:
                self.backbone = ctor(weights=weights)
            except Exception:
                self.backbone = ctor(weights=None)
        else:
            self.backbone = ctor(weights=None)

        in_features = self.backbone.fc.in_features
        if use_attention:
            self.backbone.fc = nn.Identity()
            self.backbone.avgpool = nn.Identity()
            self._needs_attention = True
            self.attention = SoftAttention(in_channels=in_features)
            self.dropout = nn.Dropout(dropout)
            self.fc_out = nn.Linear(in_features, n_classes)
        else:
            self.backbone.fc = nn.Sequential(
                nn.Dropout(dropout),
                nn.Linear(in_features, n_classes),
            )
            self._needs_attention = False

    def forward(self, x):
        if self._needs_attention:
            x = self.backbone.conv1(x)
            x = self.backbone.bn1(x)
            x = self.backbone.relu(x)
            x = self.backbone.maxpool(x)
            x = self.backbone.layer1(x)
            x = self.backbone.layer2(x)
            x = self.backbone.layer3(x)
            x = self.backbone.layer4(x)
            x = self.attention(x)
            x = self.dropout(x)
            return self.fc_out(x)
        else:
            return self.backbone(x)

    @property
    def last_conv_layer(self):
        return self.backbone.layer4



class FocalLoss(nn.Module):
    def __init__(self, gamma: float = 2.0,
                 alpha: Optional[torch.Tensor] = None):
        super().__init__()
        self.gamma = gamma
        self.alpha = alpha

    def forward(self, logits, targets):
        log_probs = F.log_softmax(logits, dim=1)
        probs = log_probs.exp()
        target_log_p = log_probs.gather(1, targets.unsqueeze(1)).squeeze(1)
        target_p = probs.gather(1, targets.unsqueeze(1)).squeeze(1)
        focal_weight = (1 - target_p).pow(self.gamma)
        loss = -focal_weight * target_log_p
        if self.alpha is not None:
            alpha_t = self.alpha[targets]
            loss = alpha_t * loss
        return loss.mean()



@dataclass
class ScenarioConfig:
    name: str
    description: str
    architecture: str
    backbone: str = "resnet18"
    dropout: float = 0.0
    augmentation: bool = False
    class_weights: bool = False
    loss: str = "ce"
    focal_gamma: float = 2.0
    use_attention: bool = False


SCENARIOS = {
    "1_cnn_baseline": ScenarioConfig(
        name="1_cnn_baseline",
        description="Plain 4-block CNN, no regularization (notebook cell 90)",
        architecture="notebook_cnn",
        dropout=0.0, augmentation=False, class_weights=False, loss="ce",
    ),
    "2_cnn_dropout": ScenarioConfig(
        name="2_cnn_dropout",
        description="+ Dropout(0.5) after each dense (notebook cell 111)",
        architecture="notebook_cnn",
        dropout=0.5, augmentation=False, class_weights=False, loss="ce",
    ),
    "3_cnn_aug": ScenarioConfig(
        name="3_cnn_aug",
        description="+ Data augmentation (notebook cell 134)",
        architecture="notebook_cnn",
        dropout=0.5, augmentation=True, class_weights=False, loss="ce",
    ),
    "4_cnn_classweight": ScenarioConfig(
        name="4_cnn_classweight",
        description="+ Class weights in loss (notebook cell 150)",
        architecture="notebook_cnn",
        dropout=0.5, augmentation=True, class_weights=True, loss="ce",
    ),
    "5_cnn_focal": ScenarioConfig(
        name="5_cnn_focal",
        description="+ Focal loss replaces CE (notebook cell 172)",
        architecture="notebook_cnn",
        dropout=0.5, augmentation=True, class_weights=True, loss="focal",
    ),
    "6_cnn_attention": ScenarioConfig(
        name="6_cnn_attention",
        description="+ Attention layer before output (notebook cell 195)",
        architecture="notebook_cnn_attn",
        dropout=0.2, augmentation=True, class_weights=True, loss="ce",
    ),
    "7_resnet_transfer": ScenarioConfig(
        name="7_resnet_transfer",
        description="ResNet-18 ImageNet transfer (PyTorch equivalent of "
                    "notebook Xception, cell 214). HEMAX_DERMA v1 baseline.",
        architecture="resnet",
        backbone="resnet18",
        dropout=0.3, augmentation=True, class_weights=True, loss="ce",
    ),
    "8_resnet_focal_attn": ScenarioConfig(
        name="8_resnet_focal_attn",
        description="ResNet-18 + Attention + Focal (PyTorch equivalent of "
                    "notebook Xception+attention+focal, cell 261 — best in study)",
        architecture="resnet",
        backbone="resnet18",
        dropout=0.3, augmentation=True, class_weights=True, loss="focal",
        use_attention=True,
    ),
}


def build_model(config: ScenarioConfig, n_classes: int, input_size: int):
    if config.architecture == "notebook_cnn":
        return NotebookCNN(n_classes=n_classes, input_size=input_size,
                           dropout=config.dropout)
    elif config.architecture == "notebook_cnn_attn":
        return NotebookCNNWithAttention(n_classes=n_classes,
                                         input_size=input_size)
    elif config.architecture == "resnet":
        return ResNetTransfer(n_classes=n_classes, backbone=config.backbone,
                               pretrained=True, dropout=config.dropout,
                               use_attention=config.use_attention)
    raise ValueError(f"Unknown architecture: {config.architecture}")


def build_loss(config: ScenarioConfig, class_weights: torch.Tensor):
    alpha = class_weights if config.class_weights else None
    if config.loss == "focal":
        return FocalLoss(gamma=config.focal_gamma, alpha=alpha)
    elif config.loss == "ce":
        if alpha is not None:
            return nn.CrossEntropyLoss(weight=alpha)
        return nn.CrossEntropyLoss()
    raise ValueError(f"Unknown loss: {config.loss}")
