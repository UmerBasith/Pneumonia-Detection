"""Shared fixtures: every test app gets its own temporary storage, samples, figures and frontend."""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Must be set before app.backend.main is imported (it builds a default app at import time).
os.environ.setdefault("PNEUMOSCAN_STORAGE", os.path.join(tempfile.gettempdir(), "pneumoscan_pytest_import"))
os.environ["PNEUMOSCAN_SKIP_WARMUP"] = "1"

from fastapi.testclient import TestClient  # noqa: E402

from app.backend import config  # noqa: E402


def xray_like(w: int = 512, h: int = 600, seed: int = 0) -> np.ndarray:
    """Grayscale image that looks vaguely like a chest film (dark lungs, bright mediastinum)."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    img = 60 + 40 * np.exp(-(((xx - w / 2) / (w * 0.12)) ** 2))
    for cx in (0.3, 0.7):
        img -= 25 * np.exp(-(((xx - cx * w) / (w * 0.14)) ** 2 + ((yy - h * 0.5) / (h * 0.25)) ** 2))
    img += rng.normal(0, 6, (h, w))
    return np.clip(img * 1.6, 0, 255).astype(np.uint8)


def encode(arr_or_img, fmt: str = "PNG", **kw) -> bytes:
    img = arr_or_img if isinstance(arr_or_img, Image.Image) else Image.fromarray(arr_or_img)
    buf = io.BytesIO()
    img.save(buf, format=fmt, **kw)
    return buf.getvalue()


def colour_photo(w: int = 400, h: int = 300) -> bytes:
    yy, xx = np.mgrid[0:h, 0:w]
    rgb = np.stack([xx / w * 255, yy / h * 255, 255 - xx / w * 255], -1).astype(np.uint8)
    return encode(rgb, "JPEG")


@pytest.fixture()
def env(tmp_path, monkeypatch):
    """Temporary folders for one app instance."""
    storage = tmp_path / "storage"
    samples = tmp_path / "samples"
    (samples / "not_xray").mkdir(parents=True)
    for i in range(2):
        Image.fromarray(xray_like(seed=i)).save(samples / f"normal_0{i + 1}.jpeg")
        Image.fromarray(xray_like(seed=10 + i)).save(samples / f"pneumonia_0{i + 1}.jpeg")
    (samples / "not_xray" / "photo.jpg").write_bytes(colour_photo())
    (samples / "answer_key.csv").write_text(
        "filename,label\nnormal_01.jpeg,NORMAL\nnormal_02.jpeg,NORMAL\npneumonia_01.jpeg,PNEUMONIA\n"
        "pneumonia_02.jpeg,PNEUMONIA\nnot_xray/photo.jpg,NOT_XRAY\n",
        encoding="utf-8",
    )
    figures = tmp_path / "figures"
    figures.mkdir()
    Image.fromarray(xray_like(80, 60)).save(figures / "confusion_matrix.png")
    Image.fromarray(xray_like(80, 60)).save(figures / "roc_curve.png")
    models = tmp_path / "models"
    models.mkdir()
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><title>PneumoScan AI</title><div id=root></div>", encoding="utf-8")
    (dist / "assets" / "app.js").write_text("console.log('ok')", encoding="utf-8")

    monkeypatch.setattr(config, "STORAGE_DIR", storage)
    monkeypatch.setattr(config, "SAMPLES_DIR", samples)
    monkeypatch.setattr(config, "FIGURES_DIR", figures)
    monkeypatch.setattr(config, "MODELS_DIR", models)
    monkeypatch.setattr(config, "FRONTEND_DIST", dist)
    monkeypatch.setattr(config, "MODEL_MODE", "mock")
    monkeypatch.setattr(config, "SKIP_WARMUP", True)
    return {"storage": storage, "samples": samples, "figures": figures, "models": models, "dist": dist, "tmp": tmp_path}


def wait_ready(client: TestClient, timeout: float = 30.0) -> dict:
    t0 = time.time()
    while time.time() - t0 < timeout:
        h = client.get("/api/health").json()
        if h["status"] != "warming_up":
            return h
        time.sleep(0.05)
    raise AssertionError("model never became ready")


@pytest.fixture()
def client(env):
    from app.backend.main import create_app

    app = create_app()
    with TestClient(app) as c:
        wait_ready(c)
        yield c


@pytest.fixture()
def metrics_file(env):
    m = {
        "model_version": "pneumoscan-resnet-ensemble-v1",
        "final": {
            "members": ["resnet50_a"],
            "threshold": 0.42,
            "test": {
                "n": 624, "accuracy": 0.95, "recall_sensitivity": 0.97, "specificity": 0.92, "precision": 0.95,
                "f1": 0.96, "roc_auc": 0.985, "confusion_matrix": {"tn": 215, "fp": 19, "fn": 12, "tp": 378},
            },
        },
    }
    (env["models"] / "metrics.json").write_text(json.dumps(m), encoding="utf-8")
    return m


def upload(client, data: bytes, filename: str = "xray.png", mime: str = "image/png", **fields):
    return client.post("/api/predict", files={"file": (filename, data, mime)}, data=fields)
