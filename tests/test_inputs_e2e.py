"""Hostile inputs, robustness and security checks against the real running server (real model)."""
from __future__ import annotations

import concurrent.futures as cf
import io
import subprocess

import numpy as np
import pytest
from PIL import Image

from conftest import SAMPLES, QAServer

PNEU = SAMPLES / "pneumonia_01.jpeg"   # p = 0.9558, High
NORM = SAMPLES / "normal_01.jpeg"      # p = 0.0006, Low


def post(http, data: bytes, filename: str, mime: str = "application/octet-stream", **fields):
    return http.post("/api/predict", files={"file": (filename, data, mime)}, data=fields)


def enc(img: Image.Image, fmt: str, **kw) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=fmt, **kw)
    return buf.getvalue()


def ok_scan(r) -> dict:
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["rejected"] is False, body
    return body["scan"]


@pytest.fixture(scope="module")
def ref(http) -> dict:
    """Reference probabilities of the two demo X-rays as plain JPEG uploads."""
    return {p.name: ok_scan(post(http, p.read_bytes(), p.name, "image/jpeg"))["prob_pneumonia"] for p in (PNEU, NORM)}


def same_result(scan: dict, ref_p: float, tol: float = 0.02):
    assert scan["label"] == ("PNEUMONIA" if ref_p >= scan["threshold"] else "NORMAL")
    assert abs(scan["prob_pneumonia"] - ref_p) < tol, (scan["prob_pneumonia"], ref_p)


# ------------------------------------------------------------------ formats
def test_grayscale_and_rgb_give_same_result(http, ref):
    img = Image.open(PNEU)
    assert img.mode == "L"
    gray = ok_scan(post(http, enc(img, "PNG"), "gray.png", "image/png"))
    rgb = ok_scan(post(http, enc(img.convert("RGB"), "PNG"), "rgb.png", "image/png"))
    assert abs(gray["prob_pneumonia"] - rgb["prob_pneumonia"]) < 1e-6
    same_result(gray, ref["pneumonia_01.jpeg"], tol=1e-3)


def test_png16(http, ref):
    a = np.asarray(Image.open(PNEU), dtype=np.uint16) * 257  # full 16-bit range
    img = Image.fromarray(a)  # I;16
    assert img.mode.startswith("I;16")
    same_result(ok_scan(post(http, enc(img, "PNG"), "xray16.png", "image/png")), ref["pneumonia_01.jpeg"], tol=1e-3)


def test_png_with_alpha(http, ref):
    rgba = Image.open(NORM).convert("RGBA")
    rgba.putalpha(255)
    same_result(ok_scan(post(http, enc(rgba, "PNG"), "alpha.png", "image/png")), ref["normal_01.jpeg"], tol=1e-3)
    # partly transparent corner (composited on black) must not crash
    a = np.asarray(rgba).copy()
    a[:80, :80, 3] = 0
    ok_scan(post(http, enc(Image.fromarray(a), "PNG"), "alpha2.png", "image/png"))


def test_exif_rotated_jpeg_is_turned_upright(http, ref):
    img = Image.open(PNEU)
    stored = img.transpose(Image.Transpose.ROTATE_90)  # pixels stored sideways ...
    exif = Image.Exif()
    exif[0x0112] = 6  # ... and the tag says "rotate 90 CW to display": upright again
    scan = ok_scan(post(http, enc(stored, "JPEG", quality=95, exif=exif.tobytes()), "phone.jpg", "image/jpeg"))
    assert (scan["width"], scan["height"]) == img.size
    same_result(scan, ref["pneumonia_01.jpeg"], tol=0.02)


def test_cmyk_jpeg(http):
    img = Image.open(NORM).convert("CMYK")
    r = post(http, enc(img, "JPEG", quality=95), "cmyk.jpg", "image/jpeg")
    assert r.status_code == 200, r.text  # analysed or politely rejected, never a crash


def test_bmp_webp_tiff(http, ref):
    img = Image.open(PNEU)
    for fmt, name in (("BMP", "x.bmp"), ("WEBP", "x.webp"), ("TIFF", "x.tif")):
        kw = {"lossless": True} if fmt == "WEBP" else {}
        same_result(ok_scan(post(http, enc(img, fmt, **kw), name)), ref["pneumonia_01.jpeg"], tol=1e-3)


def _dicom(arr: np.ndarray, photometric: str = "MONOCHROME2", window: bool = True) -> bytes:
    from pydicom.dataset import FileDataset, FileMetaDataset
    from pydicom.uid import ExplicitVRLittleEndian, generate_uid

    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.1.1"
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    ds = FileDataset("x.dcm", {}, file_meta=meta, preamble=b"\0" * 128)
    ds.SOPClassUID = meta.MediaStorageSOPClassUID
    ds.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    ds.Modality = "DX"
    ds.PatientName = "QA^Synthetic"
    ds.Rows, ds.Columns = arr.shape
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = photometric
    ds.BitsAllocated, ds.BitsStored, ds.HighBit, ds.PixelRepresentation = 16, 12, 11, 0
    if window:
        ds.WindowCenter, ds.WindowWidth = 2048, 4096
    ds.PixelData = arr.astype(np.uint16).tobytes()
    buf = io.BytesIO()
    ds.save_as(buf, enforce_file_format=True)
    return buf.getvalue()


def test_dicom_mono2_and_mono1(http, ref):
    a = np.asarray(Image.open(PNEU), dtype=np.float32)
    a12 = np.round(a / 255 * 4095).astype(np.uint16)
    same_result(ok_scan(post(http, _dicom(a12), "chest.dcm", "application/dicom")), ref["pneumonia_01.jpeg"], tol=0.01)
    inv = (4095 - a12).astype(np.uint16)  # MONOCHROME1 stores bone dark
    same_result(ok_scan(post(http, _dicom(inv, "MONOCHROME1", window=False), "chest_m1.dcm")), ref["pneumonia_01.jpeg"], tol=0.03)


def test_large_20mb_image_ok_and_over_25mb_refused(http, ref):
    img = Image.open(NORM).resize((3600, 3000), Image.Resampling.BICUBIC)
    a = np.asarray(img, dtype=np.float32) * 257 + np.random.default_rng(0).normal(0, 400, (3000, 3600))
    big = enc(Image.fromarray(np.clip(a, 0, 65535).astype(np.uint16)), "PNG")
    assert 15e6 < len(big) < 25 * 1024 * 1024, len(big)
    same_result(ok_scan(post(http, big, "huge_scanner_export.png", "image/png")), ref["normal_01.jpeg"], tol=0.05)
    r = post(http, big + b"\0" * (26 * 1024 * 1024 - len(big)), "too_big.png", "image/png")
    assert r.status_code == 413 and r.json()["error"]["code"] == "file_too_large"


def test_tiny_and_empty_and_fake_files(http):
    r = post(http, enc(Image.new("L", (40, 40), 100), "PNG"), "tiny.png")
    assert r.status_code == 422 and r.json()["error"]["code"] == "image_too_small"
    assert "too small" in r.json()["error"]["message"]
    r = post(http, b"", "empty.png")
    assert r.status_code == 400 and r.json()["error"]["code"] == "empty_file"
    r = post(http, b"hello, I am a text file\n" * 10, "notes.txt.png", "image/png")
    assert r.status_code == 422 and r.json()["error"]["code"] == "corrupt_image"
    r = post(http, b"hello", "notes.txt", "text/plain")
    assert r.status_code == 415
    r = post(http, PNEU.read_bytes()[:5000], "truncated.jpeg", "image/jpeg")
    assert r.status_code == 422
    r = http.post("/api/predict", data={"name": "x"})
    assert r.status_code == 400 and r.json()["error"]["code"] == "no_file"
    # 64x64 is the smallest accepted size: analysed or rejected, never a crash
    assert post(http, enc(Image.open(PNEU).resize((64, 64)), "PNG"), "s64.png").status_code == 200


@pytest.mark.parametrize("name", [
    "நெஞ்சு எக்ஸ்ரே.jpeg",            # Tamil
    "chest 🫁 x-ray (1).jpeg",        # emoji + spaces
    'a<b>c:d"e|f?g*h.jpeg',            # Windows-reserved characters
    "CON.jpeg",
    "..\\..\\windows\\evil.jpeg",
    "../../etc/passwd.jpeg",
])
def test_unusual_filenames(http, name):
    r = post(http, PNEU.read_bytes(), name, "image/jpeg")
    scan = ok_scan(r)
    assert "/" not in scan["filename"]
    sid = scan["id"]
    got = http.get(f"/api/history/{sid}").json()
    assert got["filename"] == scan["filename"]
    pdf = http.get(f"/api/report/{sid}.pdf")
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"
    found = http.get("/api/history", params={"q": scan["filename"][:6]}).json()
    assert any(it["id"] == sid for it in found["items"])


# ------------------------------------------------------------------ robustness
def test_five_parallel_predictions(http, base, ref):
    import httpx

    def one(i):
        p = PNEU if i % 2 == 0 else NORM
        with httpx.Client(base_url=base, timeout=120) as c:
            return p.name, c.post("/api/predict", files={"file": (p.name, p.read_bytes(), "image/jpeg")})

    with cf.ThreadPoolExecutor(5) as ex:
        results = list(ex.map(one, range(5)))
    for name, r in results:
        assert abs(ok_scan(r)["prob_pneumonia"] - ref[name]) < 1e-4


def test_batch_of_50_and_51(http):
    files = [("files", (f"x{i:02d}.jpeg", (PNEU if i % 3 else NORM).read_bytes(), "image/jpeg")) for i in range(48)]
    files.append(("files", ("photo.png", (SAMPLES / "not_xray" / "coffee.png").read_bytes(), "image/png")))
    files.append(("files", ("bad.png", b"not an image", "image/png")))
    r = http.post("/api/batch", files=files, timeout=600)
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    assert len(items) == 50
    probs = [it["scan"]["prob_pneumonia"] for it in items if it["ok"]]
    assert len(probs) == 48 and probs == sorted(probs, reverse=True)
    assert items[-2]["rejected"] is True and items[-1]["error"]["code"] == "corrupt_image"
    files.append(("files", ("one_more.jpeg", PNEU.read_bytes(), "image/jpeg")))
    r = http.post("/api/batch", files=files, timeout=600)
    assert r.status_code == 413 and r.json()["error"]["code"] == "too_many_files"


def _gpu_used_mb() -> int | None:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=20)
        return int(out.stdout.strip().splitlines()[0])
    except Exception:
        return None


def test_memory_stable_over_100_predictions(http, server):
    import psutil

    # .venv\Scripts\python.exe is a small launcher; the real server is its (largest) child process
    root = psutil.Process(server.proc.pid)
    proc = max([root, *root.children(recursive=True)], key=lambda q: q.memory_info().rss)
    data = PNEU.read_bytes()
    for _ in range(10):  # settle allocator caches first
        ok_scan(post(http, data, "warm.jpeg", "image/jpeg"))
    rss0, gpu0 = proc.memory_info().rss, _gpu_used_mb()
    for i in range(100):
        ok_scan(post(http, data if i % 2 else NORM.read_bytes(), f"m{i}.jpeg", "image/jpeg"))
    rss1, gpu1 = proc.memory_info().rss, _gpu_used_mb()
    print(f"QA memory: RSS {rss0 / 2**20:.0f} -> {rss1 / 2**20:.0f} MB, GPU {gpu0} -> {gpu1} MB")
    assert rss1 - rss0 < 150 * 2**20
    if gpu0 is not None and gpu1 is not None:
        assert gpu1 - gpu0 < 200


# ------------------------------------------------------------------ security / privacy
@pytest.mark.parametrize("path", [
    "/api/history/..%2F..%2Fpneumoscan.db",
    "/api/history/PS-20260101-ABCDEF/image/..%2F..%2F..%2Fpneumoscan.db",
    "/api/history/..%5C..%5Cpneumoscan.db/image/input",
    "/api/report/..%2F..%2Fpneumoscan.db.pdf",
    "/api/samples/thumb/..%2F..%2Fmodels%2Fmetrics.json",
    "/api/samples/thumb/../../README.md",
    "/api/samples/thumb/..%5C..%5Cstart.bat",
    "/api/samples/thumb/C:%5CWindows%5Cwin.ini",
    "/samples/..%2F..%2Fstart.bat",
    "/samples/..%5C..%5Cstart.bat",
    "/figures/..%2F..%2F..%2Fmodels%2Fmetrics.json",
    "/figures/..%5C..%5C..%5Cstart.bat",
    "/assets/..%2F..%2F..%2F..%2Fstart.bat",
    "/..%2F..%2F..%2Fstart.bat",
    "/..%5C..%5C..%5Cstart.bat",
    "/%2e%2e/%2e%2e/%2e%2e/start.bat",
])
def test_path_traversal_blocked(http, path):
    r = http.get(path)
    body = r.content
    assert b"@echo off" not in body and b"SQLite format" not in body and b"[fonts]" not in body.lower()
    assert b'"model_version"' not in body and b"PneumoScan AI - Pneumonia Detection using ResNet\n=" not in body
    assert r.status_code in (200, 400, 404, 422), r.status_code
    if r.status_code == 200:  # only the SPA index may come back
        assert b"<div id=\"root\">" in body or b"id=\"root\"" in body


def test_cors_not_open(http):
    r = http.get("/api/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in {k.lower() for k in r.headers}
    r = http.options("/api/predict", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in {k.lower() for k in r.headers}


def test_oversized_multipart_and_fields(http):
    r = post(http, b"\xff" * (40 * 1024 * 1024), "huge.jpg", "image/jpeg")
    assert r.status_code == 413
    r = post(http, PNEU.read_bytes(), "x.jpeg", "image/jpeg", name="A" * 121)
    assert r.status_code == 422 and "too long" in r.json()["error"]["message"]
    r = post(http, PNEU.read_bytes(), "x.jpeg", "image/jpeg", age="abc")
    assert r.status_code == 422
    r = post(http, PNEU.read_bytes(), "x.jpeg", "image/jpeg", age="200")
    assert r.status_code == 422


XSS = '<img src=x onerror="alert(1)"><script>alert(2)</script> & =cmd|calc'


def test_xss_text_is_stored_verbatim_and_pdf_shows_it_as_text(http):
    scan = ok_scan(post(http, PNEU.read_bytes(), "x.jpeg", "image/jpeg", name=XSS, symptoms=XSS, notes=XSS))
    assert scan["patient"]["name"] == XSS
    r = http.patch(f"/api/history/{scan['id']}", json={"doctor_notes": XSS + "\nline 2"})
    assert r.status_code == 200
    pdf = http.get(f"/api/report/{scan['id']}.pdf")
    assert pdf.status_code == 200
    import pymupdf as fitz

    text = "".join(page.get_text() for page in fitz.open(stream=pdf.content, filetype="pdf"))
    assert 'onerror="alert(1)"' in text and "<script>" in text and "line 2" in text


def test_server_binds_localhost_only():
    from pathlib import Path

    src = (Path(__file__).resolve().parents[1] / "app" / "backend" / "launcher.py").read_text(encoding="utf-8")
    assert 'host="127.0.0.1"' in src and "0.0.0.0" not in src


def test_history_survives_restart(qa_dir):
    storage = qa_dir / "restart_storage"
    s1 = QAServer(storage, qa_dir / "restart1.log").start()
    try:
        import httpx

        with httpx.Client(base_url=s1.base, timeout=120) as c:
            sid = ok_scan(c.post("/api/predict", files={"file": ("p.jpeg", PNEU.read_bytes(), "image/jpeg")},
                                 data={"name": "Restart Test"}))["id"]
            c.patch(f"/api/history/{sid}", json={"doctor_notes": "kept after restart"})
    finally:
        s1.stop()
    s2 = QAServer(storage, qa_dir / "restart2.log").start()
    try:
        import httpx

        with httpx.Client(base_url=s2.base, timeout=120) as c:
            got = c.get(f"/api/history/{sid}").json()
            assert got["patient"]["name"] == "Restart Test" and got["doctor_notes"] == "kept after restart"
            assert c.get(got["images"]["overlay"]).status_code == 200
            assert c.get(got["report_url"]).status_code == 200
    finally:
        s2.stop()


def test_pdf_prints_tamil_and_hindi_names(http):
    """Indian-language patient names must print as real letters in the PDF, not as empty boxes."""
    import pymupdf

    name = "முகமது உமர் கொண்டை राम"
    scan = ok_scan(post(http, PNEU.read_bytes(), "x.jpeg", "image/jpeg", name=name, symptoms="காய்ச்சல் fever"))
    pdf = http.get(scan["report_url"])
    doc = pymupdf.open(stream=pdf.content, filetype="pdf")
    fonts = {f[3].split("+")[-1] for f in doc[0].get_fonts()}
    assert any(f.startswith("NirmalaUI") for f in fonts), fonts
    text = doc[0].get_text()
    assert "fever" in text and "most influenced" in text   # ordinary English text is untouched (no ligatures)
