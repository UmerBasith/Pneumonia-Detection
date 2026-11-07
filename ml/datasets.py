"""PyTorch dataset + augmentation pipelines for chest X-rays.

Images come from the 512x512 grayscale cache made by prepare_data.py. The network
gets the gray image replicated to 3 channels with ImageNet normalisation, because
the ResNet backbones were pretrained on colour ImageNet photos.
"""
from __future__ import annotations

import pandas as pd
import torch
from PIL import Image
from torch.utils.data import Dataset
from torchvision.transforms import v2 as T

from ml.common import CACHE_DIR, CLASSES, IMAGENET_MEAN, IMAGENET_STD, SPLIT_CSV


class AddGaussianNoise(torch.nn.Module):
    """Light sensor-like noise on a [0,1] tensor."""

    def __init__(self, sigma: float = 0.02):
        super().__init__()
        self.sigma = sigma

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return (x + torch.randn_like(x) * self.sigma).clamp(0, 1)


class GrayTo3(torch.nn.Module):
    """Replicate the single gray channel to RGB (a class, not a lambda, so Windows
    DataLoader workers can pickle it)."""

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x.expand(3, -1, -1).contiguous()


def to_network_input() -> list:
    """Shared tail of every pipeline: [0,1] gray tensor -> normalised 3-channel tensor."""
    return [GrayTo3(), T.Normalize(IMAGENET_MEAN, IMAGENET_STD)]


def train_transform(res: int) -> T.Compose:
    """Realistic X-ray augmentations: small crops, tilts, exposure changes, blur, noise."""
    return T.Compose([
        T.ToImage(), T.ToDtype(torch.float32, scale=True),
        T.RandomResizedCrop(res, scale=(0.75, 1.0), ratio=(0.9, 1.1), antialias=True),
        T.RandomHorizontalFlip(p=0.5),
        T.RandomAffine(degrees=10, translate=(0.05, 0.05), scale=(0.95, 1.05)),
        T.ColorJitter(brightness=0.2, contrast=0.2),
        T.RandomApply([T.GaussianBlur(kernel_size=5, sigma=(0.1, 1.2))], p=0.2),
        T.RandomApply([AddGaussianNoise(0.02)], p=0.2),
        *to_network_input(),
    ])


def eval_transform(res: int) -> T.Compose:
    """Deterministic resize used for validation, test and the app."""
    return T.Compose([
        T.ToImage(), T.ToDtype(torch.float32, scale=True),
        T.Resize((res, res), antialias=True),
        *to_network_input(),
    ])


class XrayDataset(Dataset):
    """Rows of data/splits.csv for one split ('train', 'val' or 'test')."""

    def __init__(self, split: str, transform, csv=SPLIT_CSV):
        df = pd.read_csv(csv)
        self.df = df[df.split == split].reset_index(drop=True)
        self.labels = [CLASSES.index(lbl) for lbl in self.df.label]
        self.transform = transform

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, i: int):
        with Image.open(CACHE_DIR / self.df.path[i]) as im:
            img = im.convert("L")
        return self.transform(img), self.labels[i]
