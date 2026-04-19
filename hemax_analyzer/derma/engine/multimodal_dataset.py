from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
import torch
from PIL import Image
from torch.utils.data import Dataset
import torchvision.transforms as T


SEX_CATEGORIES = ["male", "female", "unknown"]


def get_train_transform(image_size: int = 300, heavy: bool = True):
    if heavy:
        return T.Compose([
            T.Resize((image_size + 32, image_size + 32)),
            T.RandomCrop(image_size),
            T.RandomHorizontalFlip(),
            T.RandomVerticalFlip(),
            T.RandomRotation(30),
            T.RandAugment(num_ops=2, magnitude=9),
            T.ColorJitter(brightness=0.3, contrast=0.3,
                          saturation=0.3, hue=0.05),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225]),
            T.RandomErasing(p=0.25, scale=(0.02, 0.15)),
        ])
    else:
        return T.Compose([
            T.Resize((image_size, image_size)),
            T.RandomHorizontalFlip(),
            T.RandomVerticalFlip(),
            T.RandomRotation(20),
            T.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225]),
        ])


def get_eval_transform(image_size: int = 300):
    return T.Compose([
        T.Resize((image_size, image_size)),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]),
    ])


def get_tta_transforms(image_size: int = 300, n_aug: int = 4):
    base_norm = T.Normalize(mean=[0.485, 0.456, 0.406],
                            std=[0.229, 0.224, 0.225])
    return [
        T.Compose([T.Resize((image_size, image_size)),
                   T.ToTensor(), base_norm]),
        T.Compose([T.Resize((image_size, image_size)),
                   T.RandomHorizontalFlip(p=1.0),
                   T.ToTensor(), base_norm]),
        T.Compose([T.Resize((image_size, image_size)),
                   T.RandomVerticalFlip(p=1.0),
                   T.ToTensor(), base_norm]),
        T.Compose([T.Resize((image_size, image_size)),
                   T.RandomRotation((90, 90)),
                   T.ToTensor(), base_norm]),
    ][:n_aug]


def fit_metadata_stats(train_df: pd.DataFrame) -> dict:
    loc_categories = sorted(train_df["localization"].dropna().unique().tolist())
    age_mean = float(train_df["age"].mean())
    age_std = float(train_df["age"].std())
    if age_std < 1e-6:
        age_std = 1.0

    return {
        "loc_categories": loc_categories,
        "age_mean": age_mean,
        "age_std": age_std,
        "sex_categories": SEX_CATEGORIES,
        "meta_dim": 1 + len(SEX_CATEGORIES) + len(loc_categories),
    }


def encode_metadata(row: pd.Series, stats: dict) -> torch.Tensor:
    parts = []

    age = row.get("age")
    if pd.isna(age):
        parts.append(0.0)
    else:
        parts.append((float(age) - stats["age_mean"]) / stats["age_std"])

    sex = str(row.get("sex", "unknown")).lower()
    if sex not in SEX_CATEGORIES:
        sex = "unknown"
    for cat in SEX_CATEGORIES:
        parts.append(1.0 if sex == cat else 0.0)

    loc = row.get("localization")
    loc = str(loc).lower() if not pd.isna(loc) else None
    for cat in stats["loc_categories"]:
        parts.append(1.0 if loc == cat else 0.0)

    return torch.tensor(parts, dtype=torch.float32)


class HAM10000Multimodal(Dataset):
    def __init__(self, csv_path, image_dir, classes, meta_stats,
                 transform=None, image_size: int = 300):
        self.df = pd.read_csv(csv_path) if not isinstance(csv_path, pd.DataFrame) \
                  else csv_path.copy()
        self.image_dir = Path(image_dir)
        self.classes = classes
        self.class_to_idx = {c: i for i, c in enumerate(classes)}
        self.meta_stats = meta_stats
        self.transform = transform or get_eval_transform(image_size)
        self.image_size = image_size

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        image_id = row["image_id"]
        if "image_path" in row and pd.notna(row.get("image_path")):
            img_path = Path(row["image_path"])
            if not img_path.is_absolute():
                img_path = self.image_dir / img_path
        else:
            img_path = self.image_dir / f"{image_id}.jpg"
        image = Image.open(img_path).convert("RGB")
        image = self.transform(image)

        meta = encode_metadata(row, self.meta_stats)

        dx = row["dx"]
        label = self.class_to_idx[dx]

        return image, meta, label, image_id


def make_balanced_sampler(dataset: HAM10000Multimodal,
                           class_weights: dict) -> torch.utils.data.WeightedRandomSampler:
    weights = []
    for _, row in dataset.df.iterrows():
        weights.append(class_weights[row["dx"]])
    return torch.utils.data.WeightedRandomSampler(
        weights=torch.tensor(weights, dtype=torch.float32),
        num_samples=len(weights),
        replacement=True,
    )
