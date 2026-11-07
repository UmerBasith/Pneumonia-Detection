"""Mock PneumoniaModel with the exact API of ml/inference.py (see docs/PROJECT_PLAN.md).

Used only when the trained model is not available. Its outputs are FAKE: the probability
comes from a hash of the pixels, and the "Grad-CAM" is two blurred blobs over the lungs.
The app shows a "DEMO MODE - mock model" banner whenever this class is active.
"""
from __future__ import annotations

import base64
import hashlib
import io
import threading
import time

import numpy as np
from PIL import Image, ImageOps

MOCK_VERSION = "mock-model-0.1 (simulated)"
DISPLAY_LONG_SIDE = 768
OVERLAY_OPACITY = 0.6  # same as ml/inference.py


def _gray(img: Image.Image) -> np.ndarray:
    img = ImageOps.exif_transpose(img) or img
    if img.mode in ("I;16", "I;16B", "I;16L", "I;16N", "I", "F"):
        arr = np.asarray(img, dtype=np.float32)
        lo, hi = float(arr.min()), float(arr.max())
        if hi - lo < 1e-6:
            return np.zeros(arr.shape, dtype=np.uint8)
        return ((arr - lo) / (hi - lo) * 255).round().astype(np.uint8)
    if img.mode in ("RGBA", "LA", "PA"):
        rgba = img.convert("RGBA")
        img = Image.alpha_composite(Image.new("RGBA", rgba.size, (0, 0, 0, 255)), rgba)
    return np.asarray(img.convert("RGB").convert("L"), dtype=np.uint8)


def _png_b64(arr: np.ndarray) -> str:
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _jet(v: np.ndarray) -> np.ndarray:
    """Simple jet-like colour map for values in 0..1 -> uint8 RGB."""
    v = np.clip(v, 0, 1)
    r = np.clip(1.5 - np.abs(4 * v - 3), 0, 1)
    g = np.clip(1.5 - np.abs(4 * v - 2), 0, 1)
    b = np.clip(1.5 - np.abs(4 * v - 1), 0, 1)
    return (np.stack([r, g, b], axis=-1) * 255).astype(np.uint8)


class PneumoniaModel:
    """Fake model. Same constructor, methods and output keys as the real one."""

    def __init__(self, models_dir: str = "models", device: str | None = None):
        self.models_dir = models_dir
        self.device = "cpu"
        self.version = MOCK_VERSION
        self.threshold = 0.5
        self._lock = threading.Lock()

    def check_image(self, img: Image.Image) -> dict:
        w, h = img.size
        if min(w, h) < 64:
            return {"is_xray": False, "score": 0.0, "reason": "The image is too small to be a chest X-ray."}
        aspect = max(w, h) / max(1, min(w, h))
        if aspect > 2.6:
            return {"is_xray": False, "score": 0.05, "reason": "The image shape does not look like a chest X-ray."}
        if img.mode in ("RGB", "RGBA", "P", "CMYK", "YCbCr"):
            hsv = np.asarray(img.convert("RGB").resize((128, 128)).convert("HSV"), dtype=np.float32)
            sat = float(hsv[..., 1].mean() / 255.0)
            if sat > 0.16:
                score = max(0.0, 0.5 - sat)
                return {
                    "is_xray": False,
                    "score": round(score, 3),
                    "reason": "This looks like a colour photo, not a chest X-ray.",
                }
        return {"is_xray": True, "score": 0.93, "reason": "Grayscale image with X-ray-like contrast (mock check)."}

    def predict(self, img: Image.Image, with_gradcam: bool = True) -> dict:
        t0 = time.perf_counter()
        check = self.check_image(img)
        if not check["is_xray"]:
            return {"rejected": True, "xray_check": check, "inference_ms": (time.perf_counter() - t0) * 1000,
                    "model_version": self.version}
        with self._lock:
            gray = _gray(img)
            digest = hashlib.sha256(gray[::4, ::4].tobytes()).digest()
            rng = np.random.default_rng(int.from_bytes(digest[:8], "little"))
            # Skewed so that both outcomes appear in a demo.
            prob = float(np.clip(rng.beta(0.7, 0.7), 0.02, 0.98))
            label = "PNEUMONIA" if prob >= self.threshold else "NORMAL"
            thr = self.threshold
            risk = "Low" if prob < thr / 2 else ("Moderate" if prob < (1 + thr) / 2 else "High")

            h, w = gray.shape
            s = DISPLAY_LONG_SIDE / max(h, w)
            dw, dh = max(1, round(w * s)), max(1, round(h * s))
            disp = np.asarray(Image.fromarray(gray).resize((dw, dh), Image.Resampling.LANCZOS))
            out = {
                "label": label,
                "prob_pneumonia": prob,
                "confidence": prob if label == "PNEUMONIA" else 1 - prob,
                "threshold": thr,
                "risk_level": risk,
                "input_png": _png_b64(disp),
                "xray_check": check,
            }
            if with_gradcam:
                yy, xx = np.mgrid[0:dh, 0:dw].astype(np.float32)
                cam = np.zeros((dh, dw), np.float32)
                for cx, cy, amp in ((0.32, 0.52, 1.0), (0.68, 0.56, 0.75)):
                    cx += rng.uniform(-0.05, 0.05)
                    cy += rng.uniform(-0.08, 0.08)
                    sx, sy = dw * rng.uniform(0.09, 0.14), dh * rng.uniform(0.10, 0.16)
                    cam += amp * np.exp(-(((xx - cx * dw) / sx) ** 2 + ((yy - cy * dh) / sy) ** 2) / 2)
                cam = cam / cam.max()
                heat = _jet(cam)
                alpha = 0.2 + 0.8 * cam  # like ml/gradcam.colorize: RGBA, alpha 0.2..1.0 by importance
                a = (alpha * OVERLAY_OPACITY)[..., None]
                base = np.repeat(disp[..., None], 3, axis=-1).astype(np.float32)
                over = (base * (1 - a) + heat.astype(np.float32) * a).astype(np.uint8)
                rgba = np.dstack([heat, np.round(alpha * 255).astype(np.uint8)])
                out["gradcam_overlay_png"] = _png_b64(over)
                out["gradcam_heatmap_png"] = _png_b64(rgba)
            else:
                out["gradcam_overlay_png"] = out["gradcam_heatmap_png"] = ""
        out["inference_ms"] = (time.perf_counter() - t0) * 1000
        out["model_version"] = self.version
        return out

    def info(self) -> dict:
        return {"metrics": {}, "model_card": {}}
