"""Self-tests for the inference contract.  Run:  python -m pytest ml/test_inference.py -q"""
from __future__ import annotations

import base64
import io

import numpy as np
import pytest
from PIL import Image

from ml.common import ROOT
from ml.inference import PneumoniaModel

SAMPLES = ROOT / "sample_xrays"
KEYS = {"label": str, "prob_pneumonia": float, "confidence": float, "threshold": float, "risk_level": str,
        "gradcam_overlay_png": str, "gradcam_heatmap_png": str, "input_png": str, "xray_check": dict,
        "inference_ms": float, "model_version": str}


@pytest.fixture(scope="module")
def model():
    return PneumoniaModel("models")


@pytest.fixture(scope="module")
def xray():
    return Image.open(SAMPLES / "pneumonia_01.jpeg")


def png_size(b64: str) -> tuple[int, int]:
    return Image.open(io.BytesIO(base64.b64decode(b64))).size


def test_contract_keys_and_types(model, xray):
    r = model.predict(xray)
    for k, t in KEYS.items():
        assert isinstance(r[k], t), k
    assert r["label"] in ("NORMAL", "PNEUMONIA") and r["risk_level"] in ("Low", "Moderate", "High")
    assert 0 <= r["prob_pneumonia"] <= 1 and 0 <= r["confidence"] <= 1
    assert set(r["xray_check"]) == {"is_xray", "score", "reason"} and r["xray_check"]["is_xray"]


def test_pngs_decode_and_line_up(model, xray):
    r = model.predict(xray)
    sizes = {png_size(r[k]) for k in ("input_png", "gradcam_overlay_png", "gradcam_heatmap_png")}
    assert len(sizes) == 1
    (w, h), (W, H) = sizes.pop(), xray.size
    assert abs(w / h - W / H) < 0.01  # same aspect ratio as the upload


def to_mode(img: Image.Image, mode: str) -> Image.Image:
    g = np.asarray(img.convert("L"))
    if mode == "I;16":
        return Image.fromarray(g.astype(np.uint16) * 257)  # 16-bit, like a DICOM export
    if mode == "I":
        return Image.fromarray(g.astype(np.int32) * 1000)
    if mode == "F":
        return Image.fromarray(g.astype(np.float32) / 255.0)
    return img.convert(mode)


@pytest.mark.parametrize("mode", ["L", "RGB", "RGBA", "LA", "P", "I;16", "I", "F", "CMYK", "1"])
def test_every_pil_mode(model, xray, mode):
    r = model.predict(to_mode(xray, mode))
    if mode == "1":  # a 1-bit image may legitimately be rejected; it must not crash
        assert "xray_check" in r
        return
    assert not r.get("rejected"), (mode, r["xray_check"])
    ref = model.predict(xray, with_gradcam=False)
    assert abs(r["prob_pneumonia"] - ref["prob_pneumonia"]) < 0.05, mode


@pytest.mark.parametrize("size", [(16, 16), (70, 60), (4000, 3500)])
def test_tiny_and_huge(model, xray, size):
    r = model.predict(xray.resize(size))
    if min(size) < 64:
        assert r["rejected"] and "small" in r["xray_check"]["reason"]
    else:
        assert "xray_check" in r


@pytest.mark.parametrize("name", ["astronaut", "chelsea", "coffee", "text", "rocket"])
def test_rejects_non_xray(model, name):
    from skimage import data
    r = model.predict(Image.fromarray(getattr(data, name)()))
    assert r.get("rejected") is True and r["xray_check"]["is_xray"] is False
    assert "label" not in r


def test_rejects_blank_and_noise(model):
    for img in [Image.new("RGB", (512, 512), (0, 0, 0)), Image.new("L", (300, 300), 200),
                Image.fromarray(np.random.default_rng(0).integers(0, 256, (400, 400, 3), dtype=np.uint8))]:
        assert model.predict(img).get("rejected") is True


def test_answer_key_matches(model):
    import pandas as pd
    key = pd.read_csv(SAMPLES / "answer_key.csv")
    for row in key.itertuples():
        r = model.predict(Image.open(SAMPLES / row.filename), with_gradcam=False)
        assert r["label"] == row.model_prediction


def test_info(model):
    info = model.info()
    assert "test" in info["metrics"]["final"] and "intended_use" in info["model_card"]


def test_dicom_via_load_image(model, xray, tmp_path):
    """A 16-bit MONOCHROME2 DICOM written with pydicom goes through load_image() + predict()."""
    from pydicom.dataset import FileDataset, FileMetaDataset
    from pydicom.uid import ExplicitVRLittleEndian, generate_uid

    from ml.inference import load_image
    arr = np.asarray(xray.convert("L"), dtype=np.uint16) * 16  # 12-bit range
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.1"  # CR image storage
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    ds = FileDataset(str(tmp_path / "x.dcm"), {}, file_meta=meta, preamble=b"\0" * 128)
    ds.Rows, ds.Columns = arr.shape
    ds.SamplesPerPixel, ds.PhotometricInterpretation = 1, "MONOCHROME2"
    ds.BitsAllocated, ds.BitsStored, ds.HighBit, ds.PixelRepresentation = 16, 12, 11, 0
    ds.PixelData = arr.tobytes()
    ds.save_as(str(tmp_path / "x.dcm"), enforce_file_format=True)
    r = model.predict(load_image(tmp_path / "x.dcm"))
    ref = model.predict(xray, with_gradcam=False)
    assert not r.get("rejected") and r["label"] == ref["label"]
