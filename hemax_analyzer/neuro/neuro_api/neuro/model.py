from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F



@dataclass
class ModelConfig:
    n_features: int
    target_names: List[str]
    encoder_dim: int = 256
    encoder_depth: int = 4
    head_dim: int = 64
    dropout: float = 0.2
    use_missingness: bool = True

    @property
    def n_targets(self) -> int:
        return len(self.target_names)

    @property
    def input_dim(self) -> int:
        return self.n_features * (2 if self.use_missingness else 1)



class ResidualBlock(nn.Module):
    def __init__(self, dim: int, dropout: float = 0.2):
        super().__init__()
        self.norm = nn.LayerNorm(dim)
        self.fc1 = nn.Linear(dim, dim * 2)
        self.fc2 = nn.Linear(dim * 2, dim)
        self.drop = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.norm(x)
        h = F.gelu(self.fc1(h))
        h = self.drop(h)
        h = self.fc2(h)
        return x + h


class TaskHead(nn.Module):
    def __init__(self, in_dim: int, hidden_dim: int, dropout: float):
        super().__init__()
        self.fc1 = nn.Linear(in_dim, hidden_dim)
        self.norm = nn.LayerNorm(hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, 1)
        self.drop = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = F.gelu(self.fc1(x))
        h = self.norm(h)
        h = self.drop(h)
        return self.fc2(h).squeeze(-1)



class HemaxRiskNet(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config

        self.input_proj = nn.Linear(config.input_dim, config.encoder_dim)
        self.input_norm = nn.LayerNorm(config.encoder_dim)

        self.blocks = nn.ModuleList([
            ResidualBlock(config.encoder_dim, dropout=config.dropout)
            for _ in range(config.encoder_depth)
        ])
        self.final_norm = nn.LayerNorm(config.encoder_dim)

        self.heads = nn.ModuleDict({
            t: TaskHead(config.encoder_dim, config.head_dim, config.dropout)
            for t in config.target_names
        })

        self.register_buffer("temperature", torch.ones(config.n_targets))

    def encode(self, features: torch.Tensor, missing_mask: torch.Tensor) -> torch.Tensor:
        if self.config.use_missingness:
            x = torch.cat([features, missing_mask], dim=-1)
        else:
            x = features
        x = self.input_proj(x)
        x = self.input_norm(x)
        for block in self.blocks:
            x = block(x)
        return self.final_norm(x)

    def forward(self, features: torch.Tensor, missing_mask: torch.Tensor,
                apply_temperature: bool = False) -> Dict[str, torch.Tensor]:
        embedding = self.encode(features, missing_mask)
        outputs = {}
        for i, t in enumerate(self.config.target_names):
            logits = self.heads[t](embedding)
            if apply_temperature:
                logits = logits / self.temperature[i].clamp(min=0.1)
            outputs[t] = logits
        return outputs

    def predict_proba(self, features: torch.Tensor,
                      missing_mask: torch.Tensor,
                      apply_temperature: bool = True) -> Dict[str, torch.Tensor]:
        with torch.no_grad():
            self.eval()
            logits_dict = self.forward(features, missing_mask, apply_temperature=apply_temperature)
            return {t: torch.sigmoid(l) for t, l in logits_dict.items()}

    def set_temperature(self, temperatures: torch.Tensor):
        assert temperatures.shape == self.temperature.shape
        self.temperature.copy_(temperatures)



class MaskedMultiTaskBCELoss(nn.Module):
    def __init__(self, target_names: List[str], pos_weights: Dict[str, float]):
        super().__init__()
        self.target_names = target_names
        weights = torch.tensor([pos_weights[t] for t in target_names], dtype=torch.float32)
        self.register_buffer("pos_weights", weights)

    def forward(self, logits_dict: Dict[str, torch.Tensor],
                targets: torch.Tensor,
                target_mask: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, float]]:
        per_task_losses = {}
        total = 0.0
        n_active_tasks = 0
        for i, t in enumerate(self.target_names):
            logits = logits_dict[t]
            tgt    = targets[:, i]
            mask   = target_mask[:, i]
            n_known = mask.sum()
            if n_known < 1:
                per_task_losses[t] = float("nan")
                continue
            pw = self.pos_weights[i]
            loss_per_sample = F.binary_cross_entropy_with_logits(
                logits, tgt,
                pos_weight=pw,
                reduction="none"
            )
            task_loss = (loss_per_sample * mask).sum() / n_known
            per_task_losses[t] = task_loss.item()
            total = total + task_loss
            n_active_tasks += 1

        if n_active_tasks == 0:
            total = torch.tensor(0.0, requires_grad=True)
        else:
            total = total / n_active_tasks

        return total, per_task_losses



def save_model(model: HemaxRiskNet, path: Path, **extras):
    payload = {
        "config": {
            "n_features": model.config.n_features,
            "target_names": model.config.target_names,
            "encoder_dim": model.config.encoder_dim,
            "encoder_depth": model.config.encoder_depth,
            "head_dim": model.config.head_dim,
            "dropout": model.config.dropout,
            "use_missingness": model.config.use_missingness,
        },
        "state_dict": model.state_dict(),
        **extras,
    }
    torch.save(payload, path)


def load_model(path: Path, device: str = "cpu") -> Tuple[HemaxRiskNet, Dict]:
    payload = torch.load(path, map_location=device, weights_only=False)
    config = ModelConfig(**payload["config"])
    model = HemaxRiskNet(config)
    model.load_state_dict(payload["state_dict"])
    model.eval()
    extras = {k: v for k, v in payload.items() if k not in ("config", "state_dict")}
    return model, extras



if __name__ == "__main__":
    config = ModelConfig(
        n_features=46,
        target_names=["depression_moderate", "depression_severe", "sleep_deficiency",
                      "daytime_dysfunction", "suicidal_ideation", "suicidal_ideation"],
    )
    model = HemaxRiskNet(config)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"Model: HemaxRiskNet")
    print(f"  Total parameters: {n_params:,}")
    print(f"  Input dim: {config.input_dim} (with missingness)")
    print(f"  Encoder dim: {config.encoder_dim}")
    print(f"  Encoder depth: {config.encoder_depth}")
    print(f"  Heads: {config.n_targets}")

    B = 4
    features = torch.randn(B, config.n_features)
    mask = torch.zeros(B, config.n_features)
    mask[0, :5] = 1

    out = model(features, mask)
    print("\nForward pass:")
    for t, logits in out.items():
        print(f"  {t}: shape={tuple(logits.shape)}, sample={logits[0].item():+.3f}")

    targets = torch.randint(0, 2, (B, config.n_targets)).float()
    target_mask = torch.ones(B, config.n_targets)
    target_mask[0, 0] = 0

    pos_weights = {t: 5.0 for t in config.target_names}
    loss_fn = MaskedMultiTaskBCELoss(config.target_names, pos_weights)
    loss, per_task = loss_fn(out, targets, target_mask)
    print(f"\nLoss: {loss.item():.4f}")
    for t, l in per_task.items():
        print(f"  {t}: {l:.4f}")
