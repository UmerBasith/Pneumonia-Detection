"""Real-vs-mock model selection, and the real model end to end when its files exist."""
from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest
from PIL import Image

from app.backend import config
from app.backend.mock_inference import PneumoniaModel as MockModel
from app.backend.model_service import ModelService
from conftest import xray_like


@pytest.fixture()
def fake_real(env, monkeypatch):
    """Pretend the ML agent shipped ml/inference.py + models/ensemble.json."""
    ml_dir = env["tmp"] / "ml"
    ml_dir.mkdir()
    (ml_dir / "inference.py").write_text("# fake", encoding="utf-8")
    (env["models"] / "ensemble.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(config, "ML_DIR", ml_dir)
    monkeypatch.setattr(config, "MODEL_MODE", "auto")

    class FakeReal(MockModel):
        def __init__(self, models_dir="models", device=None):
            super().__init__(models_dir, device)
            self.version = "fake-real-v1"
            self.device = "cpu"

    mod = types.ModuleType("ml.inference")
    mod.PneumoniaModel = FakeReal
    pkg = types.ModuleType("ml")
    pkg.inference = mod
    monkeypatch.setitem(sys.modules, "ml", pkg)
    monkeypatch.setitem(sys.modules, "ml.inference", mod)
    return mod


def test_auto_uses_mock_when_no_model_files(env, monkeypatch):
    monkeypatch.setattr(config, "MODEL_MODE", "auto")
    monkeypatch.setattr(config, "ML_DIR", env["tmp"] / "no-ml")
    s = ModelService()
    s.start(background=False)
    h = s.health()
    assert h["ready"] and h["mode"] == "mock" and "not found" in h["mock_reason"]


def test_auto_uses_real_when_files_exist(fake_real):
    s = ModelService()
    s.start(background=False)
    h = s.health()
    assert h["mode"] == "real" and h["model_version"] == "fake-real-v1" and h["mock_reason"] is None
    out = s.predict(Image.fromarray(xray_like()))
    assert out["model_version"] == "fake-real-v1"


def test_real_load_failure_falls_back_to_mock(fake_real):
    def boom(*a, **k):
        raise RuntimeError("weights corrupted")

    fake_real.PneumoniaModel = boom
    s = ModelService()
    s.start(background=False)
    h = s.health()
    assert h["mode"] == "mock" and "weights corrupted" in h["mock_reason"]


def test_forced_mock_overrides_real(fake_real, monkeypatch):
    monkeypatch.setattr(config, "MODEL_MODE", "mock")
    s = ModelService()
    s.start(background=False)
    assert s.health()["mode"] == "mock"


def test_forced_real_without_files_is_an_error(env, monkeypatch):
    monkeypatch.setattr(config, "MODEL_MODE", "real")
    monkeypatch.setattr(config, "ML_DIR", env["tmp"] / "no-ml")
    s = ModelService()
    s.start(background=False)
    h = s.health()
    assert h["status"] == "error" and not h["ready"]


def test_mock_matches_contract():
    m = MockModel()
    out = m.predict(Image.fromarray(xray_like()))
    for key in ("label", "prob_pneumonia", "confidence", "threshold", "risk_level", "gradcam_overlay_png",
                "gradcam_heatmap_png", "input_png", "xray_check", "inference_ms", "model_version"):
        assert key in out
    for mode in ("L", "RGB", "RGBA", "I;16", "F"):
        img = Image.fromarray(xray_like()).convert(mode)
        assert "label" in m.predict(img), mode


REAL_FILES = (config.ROOT / "ml" / "inference.py").exists() and (config.ROOT / "models" / "ensemble.json").exists()


@pytest.mark.skipif(not REAL_FILES, reason="trained model not available yet")
def test_real_model_end_to_end(monkeypatch):
    monkeypatch.setattr(config, "MODELS_DIR", config.ROOT / "models")
    monkeypatch.setattr(config, "MODEL_MODE", "real")
    s = ModelService()
    s.start(background=False)
    h = s.health()
    assert h["mode"] == "real", h
    samples = sorted(Path(config.ROOT / "sample_xrays").glob("*.jp*g"))
    img = Image.open(samples[0]) if samples else Image.fromarray(xray_like())
    out = s.predict(img)
    assert out.get("rejected") or out["label"] in ("NORMAL", "PNEUMONIA")
