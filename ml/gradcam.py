"""Grad-CAM (Selvaraju et al., 2017) for torchvision ResNets.

The heatmap is taken from the last convolutional block (layer4): each of its 2048
(ResNet50) feature maps is weighted by the average gradient of the class score with
respect to it, the weighted maps are summed, and ReLU keeps only positive evidence.

For this 2-class model the score is the logit margin z = logit(PNEUMONIA) - logit(NORMAL).
The gradient of the NORMAL margin is simply -dz, so ONE backward pass serves both classes.
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn.functional as F


class GradCAM:
    def __init__(self, model: torch.nn.Module, layer: torch.nn.Module | None = None):
        self.model = model
        self._acts = None
        (layer if layer is not None else model.layer4).register_forward_hook(self._save)

    def _save(self, _module, _inp, out):
        self._acts = out

    def explain(self, x: torch.Tensor):
        """Forward + backward once. Returns (activations, d z / d activations, logits)."""
        self.model.eval()
        with torch.enable_grad():
            x = x.detach().requires_grad_(True)  # lets gradients flow even if weights are frozen
            logits = self.model(x)
            z = logits[:, 1] - logits[:, 0]
            grads = torch.autograd.grad(z.sum(), self._acts)[0]
        return self._acts.detach(), grads.detach(), logits.detach()

    @staticmethod
    def cam(acts: torch.Tensor, grads: torch.Tensor, class_idx: int, size: tuple[int, int]) -> np.ndarray:
        """Grad-CAM map in [0, 1] for class_idx (0 NORMAL, 1 PNEUMONIA) resized to size=(H, W)."""
        sign = 1.0 if class_idx == 1 else -1.0
        weights = sign * grads.float().mean(dim=(2, 3), keepdim=True)
        m = F.relu((weights * acts.float()).sum(1, keepdim=True))
        m = F.interpolate(m, size=size, mode="bilinear", align_corners=False)[0, 0].cpu().numpy()
        return m / m.max() if m.max() > 0 else m


def colorize(cam: np.ndarray) -> np.ndarray:
    """[0,1] map -> uint8 RGBA 'jet' heatmap (blue = low, red = high).

    Alpha grows with the map value (0.2 .. 1.0), so weak regions only lightly tint the
    X-ray while strong regions stand out. Drawn over the X-ray at 60 % opacity this
    PNG reproduces the overlay image exactly, so the app can offer an opacity slider.
    """
    import cv2

    c = np.clip(cam, 0, 1)
    rgb = cv2.cvtColor(cv2.applyColorMap(np.uint8(c * 255), cv2.COLORMAP_JET), cv2.COLOR_BGR2RGB)
    alpha = np.uint8(np.round((0.2 + 0.8 * c) * 255))
    return np.dstack([rgb, alpha])


def overlay(gray: np.ndarray, heat_rgba: np.ndarray, opacity: float = 0.6) -> np.ndarray:
    """Alpha-blend an RGBA heatmap (at the given overall opacity) onto a uint8 grayscale image."""
    a = heat_rgba[..., 3:4].astype(np.float32) / 255.0 * opacity
    base = np.repeat(gray[..., None], 3, axis=2).astype(np.float32)
    return np.uint8(np.clip((1 - a) * base + a * heat_rgba[..., :3].astype(np.float32), 0, 255))
