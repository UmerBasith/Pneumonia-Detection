"""Local scan history: SQLite rows + PNG/JPEG files. Nothing leaves this computer."""
from __future__ import annotations

import base64
import secrets
import shutil
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from . import config
from .imaging import make_thumbnail

IMAGE_KINDS = ("input", "overlay", "heatmap", "thumb")
EDITABLE = ("name", "age", "sex", "patient_id", "symptoms", "doctor_notes")

SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    id            TEXT PRIMARY KEY,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL,
    filename      TEXT NOT NULL DEFAULT '',
    source        TEXT NOT NULL DEFAULT 'scan',
    mode          TEXT NOT NULL DEFAULT 'real',
    label         TEXT NOT NULL,
    prob          REAL NOT NULL,
    confidence    REAL NOT NULL,
    threshold     REAL NOT NULL,
    risk          TEXT NOT NULL,
    inference_ms  REAL NOT NULL DEFAULT 0,
    model_version TEXT NOT NULL DEFAULT '',
    xray_score    REAL,
    xray_reason   TEXT NOT NULL DEFAULT '',
    name          TEXT NOT NULL DEFAULT '',
    age           INTEGER,
    sex           TEXT NOT NULL DEFAULT '',
    patient_id    TEXT NOT NULL DEFAULT '',
    symptoms      TEXT NOT NULL DEFAULT '',
    doctor_notes  TEXT NOT NULL DEFAULT '',
    ground_truth  TEXT,
    width         INTEGER,
    height        INTEGER
);
CREATE INDEX IF NOT EXISTS idx_scans_created ON scans(created_at DESC);
"""


def soft_heatmap(png: bytes) -> bytes:
    """Give an opaque jet-coloured Grad-CAM map an alpha channel that follows its intensity.

    Jet runs from blue (low) to red (high), so hue tells the intensity. Low-influence areas
    become transparent and the X-ray stays crisp there; the UI's opacity slider scales the rest.
    """
    import io

    import numpy as np
    from PIL import Image

    src = Image.open(io.BytesIO(png))
    if src.mode in ("RGBA", "LA") or "transparency" in src.info:
        return png  # the model already encodes importance in its alpha channel; keep it exactly
    img = src.convert("RGB")
    hsv = np.asarray(img.convert("HSV"), dtype=np.float32)
    hue_deg = hsv[..., 0] / 255.0 * 360.0
    hue_deg = np.where(hue_deg > 300, 0, hue_deg)  # magenta-ish wrap counts as red
    intensity = np.clip(1.0 - hue_deg / 240.0, 0, 1)
    alpha = np.clip((intensity - 0.25) / 0.5, 0, 1) ** 0.9
    rgba = np.dstack([np.asarray(img), (alpha * 255).astype(np.uint8)])
    out = io.BytesIO()
    Image.fromarray(rgba).save(out, format="PNG", optimize=True)
    return out.getvalue()


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


class Store:
    def __init__(self, root: Path | None = None):
        self.root = Path(root or config.STORAGE_DIR)
        self.scans_dir = self.root / "scans"
        self.db_path = self.root / "pneumoscan.db"
        self._lock = threading.Lock()
        self.root.mkdir(parents=True, exist_ok=True)
        self.scans_dir.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.executescript(SCHEMA)

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        c = sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)
        c.row_factory = sqlite3.Row
        try:
            yield c
            c.commit()
        finally:
            c.close()

    # ------------------------------------------------------------------ ids / files
    def _new_id(self, c: sqlite3.Connection) -> str:
        day = datetime.now().strftime("%Y%m%d")
        while True:
            sid = f"PS-{day}-{secrets.token_hex(3).upper()}"
            if c.execute("SELECT 1 FROM scans WHERE id=?", (sid,)).fetchone() is None:
                return sid

    def image_path(self, scan_id: str, kind: str) -> Path:
        ext = "jpg" if kind == "thumb" else "png"
        return self.scans_dir / scan_id / f"{kind}.{ext}"

    # ------------------------------------------------------------------ create
    def save_scan(self, result: dict, *, filename: str, source: str, mode: str, patient: dict,
                  notes: str, ground_truth: str | None, width: int | None, height: int | None) -> dict:
        input_png = base64.b64decode(result["input_png"])
        overlay_png = base64.b64decode(result.get("gradcam_overlay_png") or result["input_png"])
        heatmap_png = base64.b64decode(result["gradcam_heatmap_png"]) if result.get("gradcam_heatmap_png") else None
        if heatmap_png:
            try:
                heatmap_png = soft_heatmap(heatmap_png)
            except Exception:
                pass  # keep the model's own PNG
        thumb = make_thumbnail(input_png, config.THUMB_LONG_SIDE)
        check = result.get("xray_check") or {}
        with self._lock, self._conn() as c:
            sid = self._new_id(c)
            folder = self.scans_dir / sid
            folder.mkdir(parents=True, exist_ok=True)
            self.image_path(sid, "input").write_bytes(input_png)
            self.image_path(sid, "overlay").write_bytes(overlay_png)
            if heatmap_png:
                self.image_path(sid, "heatmap").write_bytes(heatmap_png)
            self.image_path(sid, "thumb").write_bytes(thumb)
            ts = now_iso()
            c.execute(
                """INSERT INTO scans (id, created_at, updated_at, filename, source, mode, label, prob, confidence,
                   threshold, risk, inference_ms, model_version, xray_score, xray_reason, name, age, sex,
                   patient_id, symptoms, doctor_notes, ground_truth, width, height)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    sid, ts, ts, filename[:255], source, mode, result["label"], float(result["prob_pneumonia"]),
                    float(result["confidence"]), float(result["threshold"]), result["risk_level"],
                    float(result.get("inference_ms") or 0), str(result.get("model_version") or ""),
                    float(check.get("score")) if check.get("score") is not None else None,
                    str(check.get("reason") or ""), patient.get("name", ""), patient.get("age"),
                    patient.get("sex", ""), patient.get("patient_id", ""), patient.get("symptoms", ""),
                    notes, ground_truth, width, height,
                ),
            )
        return self.get(sid)  # type: ignore[return-value]

    # ------------------------------------------------------------------ read
    def _to_dict(self, r: sqlite3.Row) -> dict:
        sid = r["id"]
        base = f"/api/history/{sid}/image"
        has_heat = self.image_path(sid, "heatmap").exists()
        return {
            "id": sid,
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
            "filename": r["filename"],
            "source": r["source"],
            "mode": r["mode"],
            "label": r["label"],
            "prob_pneumonia": r["prob"],
            "confidence": r["confidence"],
            "threshold": r["threshold"],
            "risk_level": r["risk"],
            "inference_ms": r["inference_ms"],
            "model_version": r["model_version"],
            "xray_check": {"is_xray": True, "score": r["xray_score"], "reason": r["xray_reason"]},
            "patient": {
                "name": r["name"],
                "age": r["age"],
                "sex": r["sex"],
                "patient_id": r["patient_id"],
                "symptoms": r["symptoms"],
            },
            "doctor_notes": r["doctor_notes"],
            "ground_truth": r["ground_truth"],
            "width": r["width"],
            "height": r["height"],
            "images": {
                "input": f"{base}/input",
                "overlay": f"{base}/overlay",
                "heatmap": f"{base}/heatmap" if has_heat else f"{base}/overlay",
                "thumb": f"{base}/thumb",
            },
            "report_url": f"/api/report/{sid}.pdf",
        }

    def get(self, scan_id: str) -> dict | None:
        with self._conn() as c:
            r = c.execute("SELECT * FROM scans WHERE id=?", (scan_id,)).fetchone()
        return self._to_dict(r) if r else None

    def list(self, q: str = "", page: int = 1, page_size: int = 24, label: str | None = None,
             source: str | None = None) -> dict:
        where, args = [], []
        if q:
            like = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
            cols = ("id", "name", "patient_id", "filename", "symptoms", "doctor_notes", "label")
            where.append("(" + " OR ".join(f"{col} LIKE ? ESCAPE '\\'" for col in cols) + ")")
            args += [like] * len(cols)
        if label:
            where.append("label = ?")
            args.append(label)
        if source:
            where.append("source = ?")
            args.append(source)
        clause = (" WHERE " + " AND ".join(where)) if where else ""
        with self._conn() as c:
            total = c.execute(f"SELECT COUNT(*) FROM scans{clause}", args).fetchone()[0]
            rows = c.execute(
                f"SELECT * FROM scans{clause} ORDER BY created_at DESC, rowid DESC LIMIT ? OFFSET ?",
                [*args, page_size, (page - 1) * page_size],
            ).fetchall()
        pages = max(1, -(-total // page_size))
        return {"items": [self._to_dict(r) for r in rows], "total": total, "page": page,
                "page_size": page_size, "pages": pages}

    # ------------------------------------------------------------------ update / delete
    def update(self, scan_id: str, fields: dict) -> dict | None:
        fields = {k: v for k, v in fields.items() if k in EDITABLE}
        if self.get(scan_id) is None:
            return None
        if fields:
            sets = ", ".join(f"{k}=?" for k in fields) + ", updated_at=?"
            with self._lock, self._conn() as c:
                c.execute(f"UPDATE scans SET {sets} WHERE id=?", [*fields.values(), now_iso(), scan_id])
        return self.get(scan_id)

    def delete(self, scan_id: str) -> bool:
        with self._lock, self._conn() as c:
            n = c.execute("DELETE FROM scans WHERE id=?", (scan_id,)).rowcount
        shutil.rmtree(self.scans_dir / scan_id, ignore_errors=True)
        return n > 0

    def clear(self) -> int:
        with self._lock, self._conn() as c:
            n = c.execute("DELETE FROM scans").rowcount
        shutil.rmtree(self.scans_dir, ignore_errors=True)
        self.scans_dir.mkdir(parents=True, exist_ok=True)
        return n
