from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as tv_models



class PretrainedBackbone(nn.Module):
    def __init__(self, backbone: str = "efficientnet_b3",
                 pretrained: bool = True, embed_dim: int = 256):
        super().__init__()
        self.backbone_name = backbone
        self.embed_dim = embed_dim

        if backbone == "efficientnet_b3":
            net = tv_models.efficientnet_b3(
                weights=tv_models.EfficientNet_B3_Weights.IMAGENET1K_V1
                if pretrained else None
            )
            self.features = net.features
            in_channels = 1536
        elif backbone == "efficientnet_b0":
            net = tv_models.efficientnet_b0(
                weights=tv_models.EfficientNet_B0_Weights.IMAGENET1K_V1
                if pretrained else None
            )
            self.features = net.features
            in_channels = 1280
        elif backbone == "resnet50":
            net = tv_models.resnet50(
                weights=tv_models.ResNet50_Weights.IMAGENET1K_V2
                if pretrained else None
            )
            self.features = nn.Sequential(
                net.conv1, net.bn1, net.relu, net.maxpool,
                net.layer1, net.layer2, net.layer3, net.layer4,
            )
            in_channels = 2048
        else:
            raise ValueError(f"Unsupported backbone: {backbone}")

        self.proj = nn.Sequential(
            nn.Conv2d(in_channels, embed_dim, kernel_size=1, bias=False),
            nn.BatchNorm2d(embed_dim),
            nn.ReLU(inplace=True),
        )
        self.gap = nn.AdaptiveAvgPool2d(1)

    def forward_features(self, x):
        x = self.features(x)
        x = self.proj(x)
        return x

    def forward(self, x):
        x = self.forward_features(x)
        return self.gap(x).flatten(1)

    @property
    def out_features(self):
        return self.embed_dim



class ResidualBlock(nn.Module):
    def __init__(self, channels: int):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(channels),
            nn.ReLU(),
            nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(channels),
        )
        self.relu = nn.ReLU()

    def forward(self, x):
        return self.relu(self.block(x) + x)


class LegacyImageEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(3, stride=2, padding=1),
        )
        self.layer1 = ResidualBlock(64)
        self.layer2 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(),
        )
        self.layer3 = ResidualBlock(128)
        self.gap = nn.AdaptiveAvgPool2d(1)

    def forward_features(self, x):
        x = self.stem(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        return x

    def forward(self, x):
        return self.gap(self.forward_features(x)).flatten(1)



class ImageOnlyModel(nn.Module):
    def __init__(self, num_classes: int = 7,
                 backbone: str = "efficientnet_b3", embed_dim: int = 256,
                 pretrained: bool = True):
        super().__init__()
        self.image_encoder = PretrainedBackbone(backbone=backbone,
                                                  embed_dim=embed_dim,
                                                  pretrained=pretrained)
        self.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(embed_dim, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(128, num_classes),
        )

    def forward(self, image, meta=None):
        return self.classifier(self.image_encoder(image))

    @property
    def last_conv_layer(self):
        return self.image_encoder.proj


class MetadataOnlyModel(nn.Module):
    def __init__(self, meta_dim: int, num_classes: int = 7):
        super().__init__()
        self.mlp = nn.Sequential(
            nn.Linear(meta_dim, 128), nn.ReLU(),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, num_classes),
        )

    def forward(self, image, meta):
        return self.mlp(meta)



class LateFusionModel(nn.Module):
    def __init__(self, meta_dim: int, num_classes: int = 7,
                 backbone: str = "efficientnet_b3", embed_dim: int = 256,
                 pretrained: bool = True):
        super().__init__()
        self.image_encoder = PretrainedBackbone(backbone=backbone,
                                                  embed_dim=embed_dim,
                                                  pretrained=pretrained)
        self.meta_encoder = nn.Sequential(
            nn.Linear(meta_dim, 64), nn.ReLU(),
            nn.Linear(64, 64), nn.ReLU(),
        )
        self.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(embed_dim + 64, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(128, num_classes),
        )

    def forward(self, image, meta):
        img_feat = self.image_encoder(image)
        meta_feat = self.meta_encoder(meta)
        combined = torch.cat([img_feat, meta_feat], dim=1)
        return self.classifier(combined)

    @property
    def last_conv_layer(self):
        return self.image_encoder.proj


class EarlyFusionModel(nn.Module):
    def __init__(self, meta_dim: int, num_classes: int = 7):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False),
            nn.BatchNorm2d(64), nn.ReLU(),
            nn.MaxPool2d(3, stride=2, padding=1),
        )
        self.meta_proj = nn.Sequential(nn.Linear(meta_dim, 64), nn.ReLU())
        self.layer1 = ResidualBlock(64)
        self.layer2 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(128), nn.ReLU(),
        )
        self.layer3 = ResidualBlock(128)
        self.gap = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, num_classes),
        )

    def forward(self, image, meta):
        x = self.stem(image)
        meta_vec = self.meta_proj(meta).unsqueeze(-1).unsqueeze(-1)
        x = x + meta_vec
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        return self.classifier(self.gap(x))

    @property
    def last_conv_layer(self):
        return self.layer3


class FiLMLayer(nn.Module):
    def __init__(self, meta_dim: int, num_channels: int):
        super().__init__()
        self.film_generator = nn.Sequential(
            nn.Linear(meta_dim, 128), nn.ReLU(),
            nn.Linear(128, num_channels * 2),
        )

    def forward(self, x, meta):
        params = self.film_generator(meta)
        gamma, beta = params.chunk(2, dim=1)
        gamma = gamma.unsqueeze(-1).unsqueeze(-1)
        beta = beta.unsqueeze(-1).unsqueeze(-1)
        return gamma * x + beta


class FiLMFusionModel(nn.Module):
    def __init__(self, meta_dim: int, num_classes: int = 7):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False),
            nn.BatchNorm2d(64), nn.ReLU(),
            nn.MaxPool2d(3, stride=2, padding=1),
        )
        self.layer1 = ResidualBlock(64)
        self.film1 = FiLMLayer(meta_dim, num_channels=64)
        self.layer2 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(128), nn.ReLU(),
        )
        self.layer3 = ResidualBlock(128)
        self.film2 = FiLMLayer(meta_dim, num_channels=128)
        self.gap = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, num_classes),
        )

    def forward(self, image, meta):
        x = self.stem(image)
        x = self.layer1(x)
        x = self.film1(x, meta)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.film2(x, meta)
        return self.classifier(self.gap(x))

    @property
    def last_conv_layer(self):
        return self.layer3


class CrossAttentionFusion(nn.Module):
    def __init__(self, meta_dim: int, embed_dim: int = 128, num_heads: int = 4):
        super().__init__()
        self.meta_proj = nn.Linear(meta_dim, embed_dim)
        self.attention = nn.MultiheadAttention(
            embed_dim=embed_dim, num_heads=num_heads, batch_first=True,
        )
        self.norm = nn.LayerNorm(embed_dim)

    def forward(self, image_features, meta, return_attention=False):
        B, C, H, W = image_features.shape
        tokens = image_features.flatten(2).transpose(1, 2)
        query = self.meta_proj(meta).unsqueeze(1)
        attended, attn_weights = self.attention(
            query, tokens, tokens, need_weights=return_attention
        )
        attended = attended.squeeze(1)
        out = self.norm(attended)
        if return_attention:
            attn_map = attn_weights.squeeze(1).reshape(B, H, W)
            return out, attn_map
        return out


class CrossAttentionFusionModel(nn.Module):
    def __init__(self, meta_dim: int, num_classes: int = 7):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False),
            nn.BatchNorm2d(64), nn.ReLU(),
            nn.MaxPool2d(3, stride=2, padding=1),
        )
        self.layer1 = ResidualBlock(64)
        self.layer2 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(128), nn.ReLU(),
        )
        self.layer3 = ResidualBlock(128)
        self.cross_attention = CrossAttentionFusion(meta_dim, embed_dim=128,
                                                     num_heads=4)
        self.classifier = nn.Sequential(
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, num_classes),
        )

    def forward(self, image, meta, return_attention=False):
        x = self.stem(image)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        if return_attention:
            x, attn_map = self.cross_attention(x, meta, return_attention=True)
            return self.classifier(x), attn_map
        x = self.cross_attention(x, meta)
        return self.classifier(x)

    @property
    def last_conv_layer(self):
        return self.layer3



class FocalLoss(nn.Module):
    def __init__(self, gamma: float = 2.0, weight=None):
        super().__init__()
        self.gamma = gamma
        self.weight = weight

    def forward(self, inputs, targets):
        ce_loss = F.cross_entropy(inputs, targets, weight=self.weight,
                                    reduction="none")
        p_t = torch.exp(-ce_loss)
        focal_loss = (1 - p_t) ** self.gamma * ce_loss
        return focal_loss.mean()



MODEL_REGISTRY = {
    "image_only":      ImageOnlyModel,
    "metadata_only":   MetadataOnlyModel,
    "late_fusion":     LateFusionModel,
    "early_fusion":    EarlyFusionModel,
    "film_fusion":     FiLMFusionModel,
    "cross_attention": CrossAttentionFusionModel,
}


def build_model(name: str, meta_dim: int, num_classes: int = 7,
                backbone: str = "efficientnet_b3", embed_dim: int = 256,
                pretrained: bool = True):
    if name == "image_only":
        return ImageOnlyModel(num_classes=num_classes,
                                backbone=backbone, embed_dim=embed_dim,
                                pretrained=pretrained)
    elif name == "metadata_only":
        return MetadataOnlyModel(meta_dim=meta_dim, num_classes=num_classes)
    elif name == "late_fusion":
        return LateFusionModel(meta_dim=meta_dim, num_classes=num_classes,
                                 backbone=backbone, embed_dim=embed_dim,
                                 pretrained=pretrained)
    elif name in MODEL_REGISTRY:
        return MODEL_REGISTRY[name](meta_dim=meta_dim, num_classes=num_classes)
    raise ValueError(f"Unknown model: {name}. Choose from {list(MODEL_REGISTRY)}")
