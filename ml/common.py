"""Shared constants and helpers used by every ML script.

Keeping image preprocessing and model construction in ONE place guarantees
that training, evaluation and the app's inference all see images the same way.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw" / "chest_xray"      # extracted Kermany et al. 2018 dataset
CACHE_DIR = DATA_DIR / "processed"             # 512x512 grayscale PNG cache
SPLIT_CSV = DATA_DIR / "splits.csv"
MODELS_DIR = ROOT / "models"
CKPT_DIR = MODELS_DIR / "checkpoints"
LOGS_DIR = ROOT / "logs"
FIG_DIR = ROOT / "docs" / "figures"

CLASSES = ["NORMAL", "PNEUMONIA"]              # index 1 = positive class
CANON_SIZE = 512                               # canonical square view (cache + inference)
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def to_gray_uint8(img: Image.Image) -> np.ndarray:
    """Convert a PIL image of ANY mode (L, RGB, RGBA, P, I;16, I, F, CMYK...) to uint8 grayscale.

    16-bit / 32-bit images (e.g. PNG16 exported from DICOM) are min-max scaled to 0..255.
    Transparent pixels are composited onto black (X-ray backgrounds are dark).
    """
    img = ImageOps.exif_transpose(img)  # respect phone-camera orientation tags
    mode = img.mode
    if mode in ("I;16", "I;16B", "I;16L", "I;16N", "I", "F"):
        arr = np.asarray(img, dtype=np.float32)
        lo, hi = float(arr.min()), float(arr.max())
        if hi - lo < 1e-6:
            return np.zeros(arr.shape, dtype=np.uint8)
        return ((arr - lo) / (hi - lo) * 255.0).round().astype(np.uint8)
    if mode in ("RGBA", "LA", "PA") or (mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        black = Image.new("RGBA", rgba.size, (0, 0, 0, 255))
        img = Image.alpha_composite(black, rgba)
    if mode == "1":
        img = img.convert("L")
    return np.asarray(img.convert("RGB").convert("L"), dtype=np.uint8)


def canonical_view(img: Image.Image) -> Image.Image:
    """Grayscale image squashed to CANON_SIZE x CANON_SIZE (the network's square view).

    Squashing (not cropping) keeps the whole chest visible, so a heatmap computed on the
    square view can be stretched back onto the original aspect ratio pixel-exactly.
    """
    gray = Image.fromarray(to_gray_uint8(img))
    return gray.resize((CANON_SIZE, CANON_SIZE), Image.Resampling.LANCZOS)


def build_model(arch: str, pretrained: bool = True):
    """torchvision ResNet with a 2-class head (NORMAL, PNEUMONIA)."""
    import torch.nn as nn
    import torchvision.models as tvm

    weights = {
        "resnet18": tvm.ResNet18_Weights.IMAGENET1K_V1,
        "resnet34": tvm.ResNet34_Weights.IMAGENET1K_V1,
        "resnet50": tvm.ResNet50_Weights.IMAGENET1K_V2,
    }[arch] if pretrained else None
    model = getattr(tvm, arch)(weights=weights)
    model.fc = nn.Sequential(nn.Dropout(0.2), nn.Linear(model.fc.in_features, len(CLASSES)))
    return model


def binary_metrics(y_true, prob, threshold: float) -> dict:
    """All headline metrics for a binary classifier at a given threshold."""
    from sklearn.metrics import average_precision_score, confusion_matrix, roc_auc_score

    y_true = np.asarray(y_true).astype(int)
    pred = (np.asarray(prob) >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    sens = tp / max(tp + fn, 1)
    spec = tn / max(tn + fp, 1)
    prec = tp / max(tp + fp, 1)
    return {
        "n": int(len(y_true)),
        "accuracy": float((tp + tn) / len(y_true)),
        "balanced_accuracy": float((sens + spec) / 2),
        "precision": float(prec),
        "recall_sensitivity": float(sens),
        "specificity": float(spec),
        "f1": float(2 * prec * sens / max(prec + sens, 1e-12)),
        "roc_auc": float(roc_auc_score(y_true, prob)),
        "pr_auc": float(average_precision_score(y_true, prob)),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "threshold": float(threshold),
    }
