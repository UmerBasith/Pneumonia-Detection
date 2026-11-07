"""Endpoint tests: health, model info, predict, samples, figures, SPA serving, errors."""
from __future__ import annotations

import io

import numpy as np
from PIL import Image

from conftest import colour_photo, encode, upload, xray_like


def test_health_reports_mock_mode(client):
    h = client.get("/api/health").json()
    assert h["status"] == "ok" and h["ready"] is True
    assert h["mode"] == "mock"
    assert h["mock_reason"]
    assert "simulated" in h["model_version"]
    assert h["app_version"]


def test_model_info_without_metrics(client):
    r = client.get("/api/model-info")
    assert r.status_code == 200
    body = r.json()
    assert body["metrics"] is None and body["model_card"] is None
    names = {f["name"] for f in body["figures"]}
    assert names == {"confusion_matrix", "roc_curve"}
    assert client.get(body["figures"][0]["url"]).status_code == 200


def test_model_info_with_metrics(client, metrics_file):
    body = client.get("/api/model-info").json()
    assert body["metrics"]["final"]["test"]["accuracy"] == 0.95


def test_predict_png_with_patient_details(client):
    r = upload(client, encode(xray_like()), filename="chest.png", name="Priya Raman", age="58", sex="f",
               patient_id="OP-1", symptoms="Cough", notes="Review in 48 h")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["rejected"] is False and body["saved"] is True
    s = body["scan"]
    assert s["id"].startswith("PS-")
    assert s["label"] in ("NORMAL", "PNEUMONIA")
    assert 0 <= s["prob_pneumonia"] <= 1 and 0.5 <= s["confidence"] <= 1
    assert s["risk_level"] in ("Low", "Moderate", "High")
    assert s["mode"] == "mock"
    assert s["patient"] == {"name": "Priya Raman", "age": 58, "sex": "Female", "patient_id": "OP-1", "symptoms": "Cough"}
    assert s["doctor_notes"] == "Review in 48 h"
    assert (s["width"], s["height"]) == (512, 600)
    for kind in ("input", "overlay", "heatmap", "thumb"):
        img = client.get(s["images"][kind])
        assert img.status_code == 200
        Image.open(io.BytesIO(img.content)).verify()
    heat = Image.open(io.BytesIO(client.get(s["images"]["heatmap"]).content))
    assert heat.mode == "RGBA"  # softened heatmap with an alpha channel


def test_predict_is_deterministic_for_same_image(client):
    data = encode(xray_like(seed=3))
    a = upload(client, data).json()["scan"]["prob_pneumonia"]
    b = upload(client, data).json()["scan"]["prob_pneumonia"]
    assert a == b


def test_predict_accepts_many_formats(client):
    arr = xray_like(400, 400, seed=5)
    cases = [
        ("a.jpg", encode(arr, "JPEG"), "image/jpeg"),
        ("b.bmp", encode(arr, "BMP"), "image/bmp"),
        ("c.webp", encode(arr, "WEBP"), "image/webp"),
        ("d.tiff", encode(arr, "TIFF"), "image/tiff"),
        ("e.png", encode(Image.fromarray(arr).convert("RGBA")), "image/png"),
        ("f.png", encode(Image.fromarray((arr.astype(np.uint16) * 257))), "image/png"),  # 16-bit PNG
        ("g.png", encode(Image.fromarray(arr).convert("P")), "image/png"),
    ]
    for name, data, mime in cases:
        r = upload(client, data, filename=name, mime=mime)
        assert r.status_code == 200, (name, r.text)
        assert r.json()["rejected"] is False, name


def test_exif_orientation_is_applied(client):
    img = Image.fromarray(xray_like(300, 500))  # 300 wide, 500 tall
    exif = Image.Exif()
    exif[0x0112] = 6  # rotate 90 degrees on display
    data = encode(img, "JPEG", exif=exif.tobytes())
    s = upload(client, data, filename="phone.jpg", mime="image/jpeg").json()["scan"]
    assert (s["width"], s["height"]) == (500, 300)


def test_non_xray_is_rejected_and_not_saved(client):
    before = client.get("/api/history").json()["total"]
    r = upload(client, colour_photo(), filename="holiday.jpg", mime="image/jpeg")
    assert r.status_code == 200
    body = r.json()
    assert body["rejected"] is True and body["saved"] is False
    assert body["xray_check"]["is_xray"] is False and body["xray_check"]["reason"]
    assert "scan" not in body
    assert client.get("/api/history").json()["total"] == before


def _assert_error(r, status, code):
    assert r.status_code == status, r.text
    err = r.json()["error"]
    assert err["code"] == code and err["message"]


def test_bad_inputs_give_friendly_errors(client):
    _assert_error(upload(client, b"", filename="empty.png"), 400, "empty_file")
    _assert_error(upload(client, b"hello world, not an image", filename="notes.txt", mime="text/plain"), 415, "unsupported_type")
    _assert_error(upload(client, b"hello world, not an image", filename="fake.png"), 422, "corrupt_image")
    jpeg = encode(xray_like(), "JPEG")
    _assert_error(upload(client, jpeg[: len(jpeg) // 3], filename="cut.jpg", mime="image/jpeg"), 422, "corrupt_image")
    gif = encode(Image.fromarray(xray_like()).convert("P"), "GIF")
    _assert_error(upload(client, gif, filename="anim.gif", mime="image/gif"), 415, "unsupported_type")
    _assert_error(upload(client, encode(xray_like(40, 40)), filename="tiny.png"), 422, "image_too_small")
    _assert_error(client.post("/api/predict"), 400, "no_file")


def test_huge_file_is_rejected(client):
    data = b"\xff\xd8\xff" + b"0" * (25 * 1024 * 1024 + 10)
    _assert_error(upload(client, data, filename="huge.jpg", mime="image/jpeg"), 413, "file_too_large")


def test_invalid_patient_fields(client):
    png = encode(xray_like())
    _assert_error(upload(client, png, age="abc"), 422, "invalid_field")
    _assert_error(upload(client, png, age="200"), 422, "invalid_field")
    _assert_error(upload(client, png, sex="banana"), 422, "invalid_field")
    _assert_error(upload(client, png, name="x" * 121), 422, "invalid_field")


def test_samples_list_thumbs_and_files(client):
    items = client.get("/api/samples").json()["items"]
    assert len(items) == 5
    cats = {i["filename"]: (i["category"], i["ground_truth"]) for i in items}
    assert cats["normal_01.jpeg"] == ("normal", "NORMAL")
    assert cats["pneumonia_02.jpeg"] == ("pneumonia", "PNEUMONIA")
    assert cats["photo.jpg"] == ("not_xray", None)
    for it in items:
        assert client.get(it["url"]).status_code == 200
        t = client.get(it["thumb_url"])
        assert t.status_code == 200 and t.headers["content-type"] == "image/jpeg"
    _assert_error(client.get("/api/samples/thumb/../../config.py"), 404, "not_found")
    _assert_error(client.get("/api/samples/thumb/nope.jpeg"), 404, "not_found")


def test_spa_and_unknown_routes(client):
    for path in ("/", "/history", "/history/PS-20260101-ABCDEF", "/curb-65"):
        r = client.get(path)
        assert r.status_code == 200 and "PneumoScan AI" in r.text
    assert client.get("/assets/app.js").status_code == 200
    _assert_error(client.get("/assets/missing.js"), 404, "not_found")
    _assert_error(client.get("/api/does-not-exist"), 404, "not_found")
    _assert_error(client.post("/api/health"), 405, "method_not_allowed")


def test_warming_up_returns_503(env):
    from fastapi.testclient import TestClient

    from app.backend.main import create_app

    app = create_app()
    app.state.model.state = "loading"  # pretend the weights are still loading
    with TestClient(app) as c:  # lifespan start() is a no-op while "loading"
        assert c.get("/api/health").json()["status"] == "warming_up"
        _assert_error(upload(c, encode(xray_like())), 503, "warming_up")


def test_heatmap_alpha_handling():
    from app.backend.storage import soft_heatmap

    rgba = np.zeros((20, 20, 4), np.uint8)
    rgba[..., 0] = 255
    rgba[..., 3] = 128
    data = encode(rgba)
    assert soft_heatmap(data) == data  # model's own alpha is kept exactly
    rgb = np.zeros((20, 20, 3), np.uint8)
    rgb[:10] = (255, 0, 0)  # red = high influence
    rgb[10:] = (0, 0, 128)  # dark blue = low influence
    out = np.asarray(Image.open(io.BytesIO(soft_heatmap(encode(rgb)))))
    assert out.shape[-1] == 4 and out[0, 0, 3] > 200 and out[-1, -1, 3] == 0
