"""Loads the real ResNet model once (in a background thread), or falls back to the mock.

Real model: used when ml/inference.py and models/ensemble.json exist and load without error.
Mock model: used otherwise; health reports mode "mock" and the UI shows a DEMO MODE banner.
"""
from __future__ import annotations

import json
import logging
import sys
import threading
import time
import traceback
from typing import Any

from PIL import Image

from . import config
from .errors import AppError

log = logging.getLogger("pneumoscan.model")


def real_model_files_present() -> bool:
    return (config.ML_DIR / "inference.py").exists() and (config.MODELS_DIR / "ensemble.json").exists()


class ModelService:
    def __init__(self) -> None:
        self.model: Any = None
        self.mode: str | None = None  # "real" | "mock"
        self.state = "idle"  # idle | loading | ready | error
        self.error: str | None = None
        self.mock_reason: str | None = None
        self.device: str | None = None
        self.version: str | None = None
        self._lock = threading.Lock()  # one prediction at a time (GPU memory, thread safety)
        self._thread: threading.Thread | None = None
        self.loaded_at: float | None = None

    # ------------------------------------------------------------------ loading
    def start(self, background: bool = True) -> None:
        if self.state in ("loading", "ready"):
            return
        self.state = "loading"
        if background:
            self._thread = threading.Thread(target=self._load, name="model-loader", daemon=True)
            self._thread.start()
        else:
            self._load()

    def wait(self, timeout: float = 120.0) -> None:
        if self._thread is not None:
            self._thread.join(timeout)

    def _load_mock(self, reason: str) -> None:
        from .mock_inference import PneumoniaModel as MockModel

        self.model = MockModel(str(config.MODELS_DIR))
        self.mode = "mock"
        self.mock_reason = reason
        self.device = "cpu (mock)"
        self.version = self.model.version

    def _load(self) -> None:
        try:
            want = config.MODEL_MODE
            if want == "mock":
                self._load_mock("Mock model selected with PNEUMOSCAN_MODEL=mock.")
            elif real_model_files_present():
                try:
                    self._load_real()
                except Exception as exc:  # fall back, but say why
                    log.error("Real model failed to load:\n%s", traceback.format_exc())
                    if want == "real":
                        raise
                    self._load_mock(f"The trained model could not be loaded ({type(exc).__name__}: {exc}).")
            else:
                if want == "real":
                    raise RuntimeError("Trained model files were not found in the models folder.")
                self._load_mock("Trained model files were not found in the models folder.")
            self.loaded_at = time.time()
            self.state = "ready"
            log.info("Model ready: mode=%s device=%s version=%s", self.mode, self.device, self.version)
        except Exception as exc:
            self.state = "error"
            self.error = f"{type(exc).__name__}: {exc}"
            log.error("Model loading failed:\n%s", traceback.format_exc())

    def _load_real(self) -> None:
        root = str(config.ROOT)
        if root not in sys.path:
            sys.path.insert(0, root)
        from ml.inference import PneumoniaModel  # type: ignore[import-not-found]

        model = PneumoniaModel(str(config.MODELS_DIR))
        dev = getattr(model, "device", None)
        device = str(dev) if dev is not None else "cpu"
        try:
            import torch

            if device.startswith("cuda") and torch.cuda.is_available():
                device = f"cuda ({torch.cuda.get_device_name(0)})"
        except Exception:
            pass
        self.model = model
        self.mode = "real"
        self.mock_reason = None
        self.device = device
        self.version = getattr(model, "version", None) or self._version_from_metrics()
        if not config.SKIP_WARMUP:
            self._warm_up()

    def _version_from_metrics(self) -> str:
        try:
            return json.loads((config.MODELS_DIR / "metrics.json").read_text(encoding="utf-8")).get("model_version", "unknown")
        except Exception:
            return "unknown"

    def _warm_up(self) -> None:
        """Run one prediction so the first real scan in class is fast."""
        try:
            candidates = sorted(config.SAMPLES_DIR.glob("*.jp*g")) + sorted(config.SAMPLES_DIR.glob("*.png"))
            img = Image.open(candidates[0]) if candidates else Image.new("L", (512, 512), 90)
            img.load()
            with self._lock:
                self.model.predict(img, with_gradcam=True)
        except Exception:
            log.warning("Warm-up prediction failed (ignored):\n%s", traceback.format_exc())

    # ------------------------------------------------------------------ use
    def health(self) -> dict:
        status = {"ready": "ok", "error": "error"}.get(self.state, "warming_up")
        return {
            "status": status,
            "ready": self.state == "ready",
            "mode": self.mode,
            "device": self.device,
            "model_version": self.version,
            "mock_reason": self.mock_reason,
            "error": self.error,
            "app_version": config.APP_VERSION,
        }

    def require_ready(self) -> None:
        if self.state == "ready":
            return
        if self.state == "error":
            raise AppError(503, "model_error", "The model failed to load. Check the start.bat window for details.")
        raise AppError(503, "warming_up", "The model is still warming up. Try again in a few seconds.")

    def predict(self, img: Image.Image) -> dict:
        self.require_ready()
        try:
            with self._lock:
                return self.model.predict(img, with_gradcam=True)
        except AppError:
            raise
        except Exception as exc:
            log.error("Prediction failed:\n%s", traceback.format_exc())
            raise AppError(500, "inference_failed", "The model could not analyse this image. Try another X-ray.") from exc

    def info(self) -> dict:
        """metrics.json + model_card.json (read from disk so they are shown even in mock mode)."""
        out: dict = {"metrics": None, "model_card": None}
        for key, name in (("metrics", "metrics.json"), ("model_card", "model_card.json")):
            p = config.MODELS_DIR / name
            if p.exists():
                try:
                    out[key] = json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    log.warning("Could not read %s", p)
        return out


service = ModelService()
