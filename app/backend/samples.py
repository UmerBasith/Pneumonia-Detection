"""Demo X-rays from sample_xrays/ (test split only) with their ground truth from answer_key.csv."""
from __future__ import annotations

import csv
import io
import threading
from pathlib import Path

from PIL import Image, ImageOps

from . import config

EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff", ".dcm"}
_thumb_cache: dict[tuple[str, float], bytes] = {}
_lock = threading.Lock()


def _norm_label(v: str) -> str | None:
    v = (v or "").strip().upper()
    if v in ("PNEUMONIA", "1", "POSITIVE", "BACTERIA", "VIRUS", "BACTERIAL", "VIRAL"):
        return "PNEUMONIA"
    if v in ("NORMAL", "0", "NEGATIVE"):
        return "NORMAL"
    return None


def _answer_key(root: Path) -> dict[str, dict]:
    path = root / "answer_key.csv"
    out: dict[str, dict] = {}
    if not path.exists():
        return out
    try:
        with path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fields = [c for c in (reader.fieldnames or [])]
            fcol = next((c for c in fields if "file" in c.lower() or "name" in c.lower() or "image" in c.lower()), None)
            lcol = next((c for c in fields if any(k in c.lower() for k in ("label", "truth", "class", "answer"))), None)
            if not fcol:
                return out
            for row in reader:
                key = (row.get(fcol) or "").strip().replace("\\", "/")
                if key:
                    out[key.lower()] = {"label": row.get(lcol, "") if lcol else "", "row": row}
                    out[Path(key).name.lower()] = out[key.lower()]
    except Exception:
        return {}
    return out


def _title(stem: str) -> str:
    return stem.replace("_", " ").replace("-", " ").strip().capitalize()


def list_samples() -> list[dict]:
    root = config.SAMPLES_DIR
    if not root.exists():
        return []
    key = _answer_key(root)
    items: list[dict] = []
    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in EXTS]
    for p in sorted(files, key=lambda q: str(q.relative_to(root)).lower()):
        rel = p.relative_to(root).as_posix()
        lower = rel.lower()
        entry = key.get(lower) or key.get(p.name.lower())
        label = _norm_label(entry["label"]) if entry else None
        if "not_xray" in lower or "non_xray" in lower or (entry and "not" in str(entry["label"]).lower()):
            category, label = "not_xray", None
        elif label is None:
            label = "PNEUMONIA" if p.name.lower().startswith("pneumonia") else (
                "NORMAL" if p.name.lower().startswith("normal") else None)
            category = label.lower() if label else "not_xray"
        else:
            category = label.lower()
        items.append({
            "id": rel,
            "filename": p.name,
            "url": "/samples/" + rel,
            "thumb_url": "/api/samples/thumb/" + rel,
            "category": category,
            "ground_truth": label,
            "title": _title(p.stem),
        })
    order = {"pneumonia": 0, "normal": 0, "not_xray": 1}
    items.sort(key=lambda it: (order.get(it["category"], 2), it["filename"].lower()))
    return items


def sample_path(rel: str) -> Path | None:
    root = config.SAMPLES_DIR.resolve()
    try:
        p = (root / rel).resolve()
        p.relative_to(root)
    except Exception:
        return None
    return p if p.is_file() and p.suffix.lower() in EXTS else None


def thumbnail(p: Path, long_side: int = 320) -> bytes:
    k = (str(p), p.stat().st_mtime)
    with _lock:
        if k in _thumb_cache:
            return _thumb_cache[k]
    if p.suffix.lower() == ".dcm":
        from .imaging import decode_image

        img = decode_image(p.read_bytes(), p.name).image
    else:
        img = Image.open(p)
        img = ImageOps.exif_transpose(img) or img
    img = img.convert("RGB")
    img.thumbnail((long_side, long_side), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    data = buf.getvalue()
    with _lock:
        _thumb_cache[k] = data
    return data
