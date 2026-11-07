"""Predictions through the running app must equal the ML evaluation exactly.

* the 12 demo X-rays: app API == answer_key.csv == `python -m ml.inference` CLI (label, probability to 3 decimals)
* the 3 non-X-ray images are rejected and nothing is saved
* 40 random official TEST images: app API == direct PneumoniaModel.predict == models/checkpoints/final_preds.npz
  (proves there is no preprocessing mismatch between the app and the evaluation: EXIF, colour mode, resize)
"""
from __future__ import annotations

import json
import random
import re
import subprocess

import numpy as np
import pytest

from conftest import PY, ROOT, SAMPLES, sample_files

TEST_DIR = ROOT / "data" / "raw" / "chest_xray" / "test"


def predict(http, path, **fields):
    with open(path, "rb") as f:
        r = http.post("/api/predict", files={"file": (path.name, f.read(), "image/jpeg")}, data=fields)
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture(scope="module")
def cli_results() -> dict[str, dict]:
    files = [str(p.relative_to(ROOT)) for p in sample_files()]
    out = subprocess.run([str(PY), "-X", "utf8", "-m", "ml.inference", *files], cwd=str(ROOT),
                         capture_output=True, text=True, timeout=600)
    assert out.returncode == 0, out.stderr[-2000:]
    res = {}
    for m in re.finditer(r"^(\S+\.jpeg) (\{.*?^\})", out.stdout, flags=re.S | re.M):
        res[m.group(1)] = json.loads(m.group(2))
    assert len(res) == 12, out.stdout[:2000]
    return res


@pytest.mark.parametrize("path", sample_files(), ids=lambda p: p.name)
def test_sample_matches_answer_key_and_cli(http, path, answer_key, cli_results):
    res = predict(http, path)
    assert res["rejected"] is False and res["saved"] is True
    scan = res["scan"]
    key = answer_key[path.name]
    cli = cli_results[path.name]
    assert scan["label"] == key["model_prediction"] == cli["label"]
    assert scan["risk_level"] == key["risk_level"] == cli["risk_level"]
    # answer_key.csv stores 4 decimals (e.g. 0.96348 -> "0.9635"), so compare at that precision
    # (rounding the key again to 3 decimals would double-round 0.9635 -> 0.964).
    assert abs(scan["prob_pneumonia"] - float(key["prob_pneumonia"])) <= 0.5e-4 + 1e-5
    assert round(scan["prob_pneumonia"], 3) == round(cli["prob_pneumonia"], 3)
    assert abs(scan["prob_pneumonia"] - cli["prob_pneumonia"]) < 5e-4
    assert scan["mode"] == "real"
    assert abs(scan["threshold"] - 0.0742560438811779) < 1e-12
    # the saved images exist and line up (same size)
    from PIL import Image
    import io

    sizes = set()
    for kind in ("input", "overlay", "heatmap"):
        r = http.get(scan["images"][kind])
        assert r.status_code == 200
        sizes.add(Image.open(io.BytesIO(r.content)).size)
    assert len(sizes) == 1


@pytest.mark.parametrize("path", sorted((SAMPLES / "not_xray").glob("*")), ids=lambda p: p.name)
def test_not_xray_rejected_and_not_saved(http, path):
    before = http.get("/api/history", params={"page_size": 1}).json()["total"]
    with open(path, "rb") as f:
        r = http.post("/api/predict", files={"file": (path.name, f.read(), "image/png")})
    assert r.status_code == 200
    body = r.json()
    assert body["rejected"] is True and body["saved"] is False
    assert body["xray_check"]["is_xray"] is False
    assert body["xray_check"]["reason"]
    assert "scan" not in body
    assert http.get("/api/history", params={"page_size": 1}).json()["total"] == before


@pytest.fixture(scope="module")
def direct_model():
    from ml.inference import PneumoniaModel

    return PneumoniaModel("models")


def _test_rows():
    import pandas as pd

    df = pd.read_csv(ROOT / "data" / "splits.csv")
    return df[df.split == "test"].reset_index(drop=True)


@pytest.mark.skipif(not TEST_DIR.exists(), reason="dataset not downloaded")
def test_random_test_images_match_evaluation(http, direct_model):
    from ml.inference import load_image

    rows = _test_rows()
    preds = np.load(ROOT / "models" / "checkpoints" / "final_preds.npz")["ensemble_test"]
    y = np.load(ROOT / "models" / "checkpoints" / "final_preds.npz")["y_test"]
    assert len(rows) == len(preds) == 624
    assert (y == (rows.label == "PNEUMONIA").astype(int).to_numpy()).all()
    rng = random.Random(2026)
    idx = rng.sample(range(624), 40)
    # make sure the RGB-encoded JPEGs (283 in the dataset) are represented
    rgb = [i for i in range(624) if rows.orig_mode[i] != "L"]
    idx += [i for i in rgb[:5] if i not in idx]
    thr = 0.0742560438811779
    worst_eval, worst_direct, checked, refused = 0.0, 0.0, 0, 0
    for i in idx:
        p = ROOT / "data" / "raw" / "chest_xray" / rows.raw_path[i]
        res = predict(http, p)
        direct = direct_model.predict(load_image(p), with_gradcam=False)
        if direct.get("rejected"):
            assert res["rejected"] is True  # the gate must agree too
            refused += 1
            continue
        assert res["rejected"] is False, f"{p.name} refused by app but accepted directly"
        app_p = res["scan"]["prob_pneumonia"]
        assert res["scan"]["label"] == direct["label"] == ("PNEUMONIA" if preds[i] >= thr else "NORMAL"), p.name
        worst_direct = max(worst_direct, abs(app_p - direct["prob_pneumonia"]))
        worst_eval = max(worst_eval, abs(app_p - float(preds[i])))
        checked += 1
    print(f"QA: checked={checked} refused_by_gate={refused} max|app-direct|={worst_direct:.2e} max|app-eval|={worst_eval:.2e}")
    assert checked >= 38
    assert worst_direct < 5e-4, worst_direct     # app == direct call (only GPU fp16 noise)
    assert worst_eval < 2e-3, worst_eval         # app == evaluation run (ML report: max diff 0.00047)
