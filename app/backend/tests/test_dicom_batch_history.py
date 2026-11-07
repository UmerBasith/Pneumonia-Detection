"""DICOM decoding, batch triage, history CRUD and PDF reports."""
from __future__ import annotations

import io

import numpy as np
import pypdfium2 as pdfium
import pydicom
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, SecondaryCaptureImageStorage, generate_uid

from app.backend.imaging import decode_image
from conftest import colour_photo, encode, upload, xray_like


def make_dicom(arr: np.ndarray, photometric: str = "MONOCHROME2", window: tuple[int, int] | None = (1200, 2400),
               with_pixels: bool = True) -> bytes:
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    ds = FileDataset("synthetic.dcm", {}, file_meta=meta, preamble=b"\0" * 128)
    ds.SOPClassUID = SecondaryCaptureImageStorage
    ds.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    ds.Modality = "CR"
    ds.PatientName = "Test^Patient"
    if with_pixels:
        ds.Rows, ds.Columns = arr.shape
        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = photometric
        ds.BitsAllocated = 16
        ds.BitsStored = 12
        ds.HighBit = 11
        ds.PixelRepresentation = 0
        ds.RescaleSlope = 1
        ds.RescaleIntercept = 0
        if window:
            ds.WindowCenter, ds.WindowWidth = window
        ds.PixelData = arr.astype(np.uint16).tobytes()
    buf = io.BytesIO()
    pydicom.dcmwrite(buf, ds, enforce_file_format=True)
    return buf.getvalue()


def _twelve_bit() -> np.ndarray:
    return (xray_like(300, 360).astype(np.float32) / 255 * 4095).astype(np.uint16)


# ------------------------------------------------------------------ DICOM
def test_dicom_monochrome2_decodes_to_8bit():
    dec = decode_image(make_dicom(_twelve_bit()), "scan.dcm")
    assert dec.kind == "DICOM" and dec.image.mode == "L"
    assert (dec.width, dec.height) == (300, 360)
    arr = np.asarray(dec.image)
    assert arr.min() == 0 and arr.max() == 255


def test_dicom_monochrome1_is_inverted():
    src = _twelve_bit()
    a = np.asarray(decode_image(make_dicom(src, "MONOCHROME2"), "a.dcm").image).astype(int)
    b = np.asarray(decode_image(make_dicom(src, "MONOCHROME1"), "b.dcm").image).astype(int)
    assert np.abs((255 - a) - b).max() <= 1


def test_dicom_without_window_uses_percentiles():
    dec = decode_image(make_dicom(_twelve_bit(), window=None), "nowin.dcm")
    assert np.asarray(dec.image).std() > 10


def test_dicom_detected_by_magic_bytes_without_extension():
    assert decode_image(make_dicom(_twelve_bit()), "upload").kind == "DICOM"


def test_dicom_upload_endpoint(client):
    r = upload(client, make_dicom(_twelve_bit()), filename="chest.dcm", mime="application/dicom")
    assert r.status_code == 200, r.text
    assert r.json()["scan"]["width"] == 300


def test_bad_dicoms(client):
    r = upload(client, make_dicom(_twelve_bit(), with_pixels=False), filename="empty.dcm", mime="application/dicom")
    assert r.status_code == 422 and r.json()["error"]["code"] == "dicom_no_image"
    r = upload(client, b"\0" * 128 + b"DICM" + b"\x01\x02garbage" * 20, filename="broken.dcm", mime="application/dicom")
    assert r.status_code == 422


# ------------------------------------------------------------------ batch
def test_batch_mixed_files_sorted(client):
    files = [("files", (f"x{i}.png", encode(xray_like(seed=20 + i)), "image/png")) for i in range(4)]
    files.append(("files", ("photo.jpg", colour_photo(), "image/jpeg")))
    files.append(("files", ("broken.png", b"not an image", "image/png")))
    files.append(("files", ("empty.png", b"", "image/png")))
    r = client.post("/api/batch", files=files)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["count"] == 7
    items = body["items"]
    ok = [i for i in items if i["ok"]]
    assert len(ok) == 4
    probs = [i["scan"]["prob_pneumonia"] for i in ok]
    assert probs == sorted(probs, reverse=True)
    assert items[:4] == ok  # successful ones first
    assert items[4]["rejected"] is True and items[4]["error"]["code"] == "not_xray"
    assert {i["error"]["code"] for i in items[5:]} == {"corrupt_image", "empty_file"}
    assert all(i["scan"]["source"] == "triage" for i in ok)


def test_batch_limit(client):
    files = [("files", (f"x{i}.png", b"x", "image/png")) for i in range(51)]
    r = client.post("/api/batch", files=files)
    assert r.status_code == 413 and r.json()["error"]["code"] == "too_many_files"


# ------------------------------------------------------------------ history
def _scan(client, **fields) -> dict:
    return upload(client, encode(xray_like(seed=np.random.randint(1000))), **fields).json()["scan"]


def test_history_crud(client):
    a = _scan(client, name="Asha Kumar", patient_id="P-100")
    b = _scan(client, name="Ravi Shankar", notes="needs follow-up")
    _scan(client)

    page = client.get("/api/history").json()
    assert page["total"] == 3 and page["items"][0]["id"] != a["id"]  # newest first
    assert client.get("/api/history", params={"q": "asha"}).json()["total"] == 1
    assert client.get("/api/history", params={"q": "follow"}).json()["items"][0]["id"] == b["id"]
    assert client.get("/api/history", params={"q": a["id"]}).json()["total"] == 1
    assert client.get("/api/history", params={"q": "100%_"}).json()["total"] == 0  # wildcards escaped
    lab = a["label"]
    assert all(i["label"] == lab for i in client.get("/api/history", params={"label": lab}).json()["items"])

    p1 = client.get("/api/history", params={"page_size": 2, "page": 1}).json()
    p2 = client.get("/api/history", params={"page_size": 2, "page": 2}).json()
    assert p1["pages"] == 2 and len(p1["items"]) == 2 and len(p2["items"]) == 1

    assert client.get(f"/api/history/{a['id']}").json()["patient"]["name"] == "Asha Kumar"
    r = client.patch(f"/api/history/{a['id']}", json={"doctor_notes": "Reviewed ✓", "age": "61", "sex": "male"})
    assert r.status_code == 200
    assert r.json()["doctor_notes"] == "Reviewed ✓" and r.json()["patient"]["age"] == 61
    assert r.json()["patient"]["sex"] == "Male" and r.json()["patient"]["name"] == "Asha Kumar"
    r = client.patch(f"/api/history/{a['id']}", json={"age": None, "name": ""})
    assert r.json()["patient"]["age"] is None and r.json()["patient"]["name"] == ""
    assert client.patch(f"/api/history/{a['id']}", json={"age": -3}).status_code == 422
    assert client.patch(f"/api/history/{a['id']}", json={"doctor_notes": "x" * 5001}).status_code == 422

    assert client.delete(f"/api/history/{a['id']}").json() == {"deleted": 1}
    assert client.get(f"/api/history/{a['id']}").status_code == 404
    assert client.get(f"/api/history/{a['id']}/image/input").status_code == 404
    assert client.delete(f"/api/history/{a['id']}").status_code == 404

    assert client.delete("/api/history").json() == {"deleted": 2}
    assert client.get("/api/history").json()["total"] == 0


def test_history_bad_ids_and_params(client):
    for bad in ("nope", "PS-20260101-ABCDEF", "..%2F..%2Fpneumoscan.db"):
        assert client.get(f"/api/history/{bad}").status_code == 404
    assert client.get("/api/history", params={"label": "maybe"}).status_code == 422
    assert client.get("/api/history", params={"page": 0}).status_code == 422
    s = _scan(client)
    assert client.get(f"/api/history/{s['id']}/image/secret").status_code == 404


# ------------------------------------------------------------------ PDF
def _pdf_text(data: bytes) -> tuple[int, str]:
    doc = pdfium.PdfDocument(data)
    text = "".join(doc[i].get_textpage().get_text_range() for i in range(len(doc)))
    return len(doc), text


def test_pdf_report(client, metrics_file):
    s = _scan(client, name="Priya Raman", age="58", sex="Female", symptoms="Cough, fever")
    r = client.get(s["report_url"])
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert f"PneumoScan_Report_{s['id']}.pdf" in r.headers["content-disposition"]
    assert r.content.startswith(b"%PDF")
    pages, text = _pdf_text(r.content)
    assert pages >= 1
    for needle in ("Priya Raman", s["id"], "DEMO MODE", "Disclaimer", "95.0%", "Signature"):
        assert needle in text, needle


def test_pdf_long_and_unicode_text(client):
    name = "Dr. Ünal “Quote” O’Brien – ₹ 500 & <Sons> " + "Long" * 18
    notes = ("Line one with ₹, “smart quotes”, em — dash, and <tags> & ampersands.\n" * 60)[:5000]
    s = _scan(client, name=name[:120], symptoms="Fever\x07 with control char", notes=notes)
    r = client.get(s["report_url"])
    assert r.status_code == 200
    pages, text = _pdf_text(r.content)
    assert pages >= 2  # long notes flow onto more pages
    assert "₹" in text and "“smart quotes”" in text and "<Sons>" in text


def test_pdf_missing_scan(client):
    assert client.get("/api/report/PS-20260101-ABCDEF.pdf").status_code == 404
