from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import pandas as pd
import torch
from PIL import Image
from torch.utils.data import Dataset, WeightedRandomSampler
from torchvision import transforms


def get_train_transform(image_size: int = 224):
    return transforms.Compose([
        transforms.Resize((image_size + 32, image_size + 32)),
        transforms.RandomCrop(image_size),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.5),
        transforms.RandomRotation(degrees=20),
        transforms.ColorJitter(brightness=0.2, contrast=0.2,
                               saturation=0.2, hue=0.05),
        transforms.RandomAffine(degrees=0, translate=(0.05, 0.05),
                                scale=(0.9, 1.1)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ])


def get_eval_transform(image_size: int = 224):
    return transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ])


class HAM10000Dataset(Dataset):
    def __init__(self, csv_path: Path, classes: List[str],
                 transform=None, image_size: int = 224):
        self.df = pd.read_csv(csv_path)
        self.classes = classes
        self.class_to_idx = {c: i for i, c in enumerate(classes)}
        self.transform = transform or get_eval_transform(image_size)
        self.image_size = image_size

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_path = row["image_path"]
        try:
            img = Image.open(img_path).convert("RGB")
        except Exception as e:
            img = Image.new("RGB", (self.image_size, self.image_size), (128, 128, 128))
        if self.transform:
            img = self.transform(img)
        label = self.class_to_idx[row["dx"]]
        return img, label, row["image_id"]


def make_balanced_sampler(dataset: HAM10000Dataset,
                           class_weights: Optional[dict] = None) -> WeightedRandomSampler:
    if class_weights is None:
        counts = dataset.df["dx"].value_counts().to_dict()
        class_weights = {c: 1.0 / counts.get(c, 1) for c in dataset.classes}

    weights = [class_weights[row["dx"]] for _, row in dataset.df.iterrows()]
    return WeightedRandomSampler(weights, num_samples=len(weights), replacement=True)
