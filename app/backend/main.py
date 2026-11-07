"""PneumoScan AI backend: FastAPI app serving the JSON API and the built React frontend.

Run from the project root:
    .venv\\Scripts\\python -m uvicorn app.backend.main:app --port 8000
"""
from __future__ import annotations

import logging
import re
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import config, report, samples
from .errors import AppError
from .imaging import check_size, decode_image
from .model_service import ModelService
from .storage import IMAGE_KINDS, Store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("pneumoscan")

SCAN_ID_RE = re.compile(r"^PS-\d{8}-[0-9A-F]{6}$")
SOURCES = {"scan", "sample", "triage"}
LIMITS = {"name": 120, "sex": 20, "patient_id": 64, "symptoms": 2000, "doctor_notes": 5000}

FIGURE_TITLES = {
    "confusion_matrix": "Confusion matrix (test set)",
    "roc_curve": "ROC curve (test set)",
    "roc": "ROC curve (test set)",
    "pr_curve": "Precision–recall curve (test set)",
    "training_curves": "Training curves",
    "architecture": "Model architecture",
    "architecture_diagram": "Model architecture",
    "residual_block_diagram": "Residual (bottleneck) block",
    "sample_images": "Sample X-rays from the dataset",
    "confusion_matrix_test": "Confusion matrix (test set)",
    "roc_curve_test": "ROC curve (test set)",
    "pr_curve_test": "Precision–recall curve (test set)",
    "probability_histogram_test": "Predicted probabilities (test set)",
    "gradcam_examples": "Grad-CAM examples",
    "sample_grid": "Sample images from the dataset",
    "class_distribution": "Class distribution",
    "calibration": "Calibration (reliability) curve",
}


# ---------------------------------------------------------------------------- helpers
def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


def _clean_text(value: object, field: str) -> str:
    s = "" if value is None else str(value)
    s = s.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "").strip()
    limit = LIMITS[field]
    if len(s) > limit:
        nice = field.replace("_", " ")
        raise AppError(422, "invalid_field", f"The {nice} is too long (max {limit} characters).")
    return s


def _clean_age(value: object) -> int | None:
    if value is None:
        return None
    s = str(value).strip()
    if s == "":
        return None
    try:
        age = float(s)
    except ValueError:
        raise AppError(422, "invalid_field", "Age must be a number of years, for example 45.") from None
    if not (0 <= age <= 130) or age != age:
        raise AppError(422, "invalid_field", "Age must be between 0 and 130 years.")
    return int(age)


def _clean_sex(value: object) -> str:
    s = ("" if value is None else str(value)).strip().lower()
    mapping = {"": "", "f": "Female", "female": "Female", "m": "Male", "male": "Male", "o": "Other", "other": "Other"}
    if s not in mapping:
        raise AppError(422, "invalid_field", "Sex must be Female, Male or Other (or left empty).")
    return mapping[s]


def _patient_from_form(name: str, age: str, sex: str, patient_id: str, symptoms: str) -> dict:
    return {
        "name": _clean_text(name, "name"),
        "age": _clean_age(age),
        "sex": _clean_sex(sex),
        "patient_id": _clean_text(patient_id, "patient_id"),
        "symptoms": _clean_text(symptoms, "symptoms"),
    }


async def _read_upload(file: UploadFile) -> bytes:
    data = await file.read(config.MAX_UPLOAD_BYTES + 1)
    check_size(len(data))
    return data


FIGURE_ORDER = ("architecture", "roc", "confusion", "pr_curve", "probability", "calibration", "gradcam", "training_curves",
                "class_distribution", "sample", "residual")


def _figures() -> list[dict]:
    root = config.FIGURES_DIR
    if not root.exists():
        return []
    out = []
    for p in root.glob("*.png"):
        stem = p.stem.lower()
        title = FIGURE_TITLES.get(stem)
        if title is None:
            key = next((k for k in FIGURE_TITLES if stem.startswith(k + "_")), None)
            if key:
                rest = p.stem[len(key) + 1:].replace("_", " ")
                title = f"{FIGURE_TITLES[key]} · {rest}" if rest else FIGURE_TITLES[key]
        rank = next((i for i, k in enumerate(FIGURE_ORDER) if stem.startswith(k)), len(FIGURE_ORDER))
        out.append((rank, stem, {"name": p.stem, "title": title or p.stem.replace("_", " ").capitalize(),
                                 "url": f"/figures/{p.name}"}))
    return [f for _, _, f in sorted(out, key=lambda t: (t[0], t[1]))]


class ScanPatch(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str | None = None
    age: int | float | str | None = None
    sex: str | None = None
    patient_id: str | None = None
    symptoms: str | None = None
    doctor_notes: str | None = None


# ---------------------------------------------------------------------------- app
def create_app() -> FastAPI:
    model = ModelService()
    store = Store(config.STORAGE_DIR)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        model.start(background=True)
        yield

    app = FastAPI(title="PneumoScan AI", version=config.APP_VERSION, lifespan=lifespan,
                  docs_url="/api/docs", redoc_url=None, openapi_url="/api/openapi.json")
    app.state.model = model
    app.state.store = store

    # -------------------------------------------------------------- errors
    @app.exception_handler(AppError)
    async def _app_error(_req: Request, exc: AppError):
        return _err(exc.status, exc.code, exc.message)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_req: Request, exc: StarletteHTTPException):
        if exc.status_code == 404:
            return _err(404, "not_found", "This page or item does not exist.")
        if exc.status_code == 405:
            return _err(405, "method_not_allowed", "This action is not allowed here.")
        detail = exc.detail if isinstance(exc.detail, str) else "The request could not be processed."
        return _err(exc.status_code, f"http_{exc.status_code}", detail)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_req: Request, exc: RequestValidationError):
        errs = exc.errors()
        first = errs[0] if errs else {}
        loc = [str(x) for x in first.get("loc", []) if x not in ("body", "query", "path")]
        field = loc[0] if loc else ""
        if field in ("file", "files") and first.get("type") == "missing":
            return _err(400, "no_file", "No file was uploaded. Choose a chest X-ray image and try again.")
        msg = first.get("msg", "Invalid request.")
        return _err(422, "invalid_request", f"{field + ': ' if field else ''}{msg}")

    @app.exception_handler(Exception)
    async def _unexpected(_req: Request, exc: Exception):
        log.exception("Unexpected error: %s", exc)
        return _err(500, "internal_error", "Something went wrong on the server. Please try again.")

    # -------------------------------------------------------------- core
    @app.get("/api/health")
    def health():
        return model.health()

    @app.get("/api/model-info")
    def model_info():
        info = model.info()
        h = model.health()
        return {"mode": h["mode"], "ready": h["ready"], "model_version": h["model_version"],
                "metrics": info["metrics"], "model_card": info["model_card"], "figures": _figures()}

    def _analyse(data: bytes, filename: str, *, source: str, patient: dict, notes: str,
                 ground_truth: str | None) -> dict:
        dec = decode_image(data, filename)
        result = model.predict(dec.image)
        check = result.get("xray_check") or {}
        check = {"is_xray": bool(check.get("is_xray", False)), "score": float(check.get("score") or 0.0),
                 "reason": str(check.get("reason") or "This does not look like a chest X-ray.")}
        if result.get("rejected"):
            return {"rejected": True, "saved": False, "filename": filename, "xray_check": check}
        result = {**result, "xray_check": check}
        scan = store.save_scan(result, filename=filename, source=source, mode=model.mode or "mock",
                               patient=patient, notes=notes, ground_truth=ground_truth,
                               width=dec.width, height=dec.height)
        return {"rejected": False, "saved": True, "scan": scan}

    @app.post("/api/predict")
    async def predict(
        file: UploadFile = File(...),
        name: str = Form(""),
        age: str = Form(""),
        sex: str = Form(""),
        patient_id: str = Form(""),
        symptoms: str = Form(""),
        notes: str = Form(""),
        source: str = Form("scan"),
        ground_truth: str = Form(""),
    ):
        model.require_ready()
        patient = _patient_from_form(name, age, sex, patient_id, symptoms)
        notes_clean = _clean_text(notes, "doctor_notes")
        src = source if source in SOURCES else "scan"
        gt = ground_truth.strip().upper() or None
        if gt not in (None, "NORMAL", "PNEUMONIA"):
            gt = None
        data = await _read_upload(file)
        fname = Path(file.filename or "upload").name
        return await run_in_threadpool(_analyse, data, fname, source=src, patient=patient,
                                       notes=notes_clean, ground_truth=gt)

    @app.post("/api/batch")
    async def batch(files: list[UploadFile] = File(...)):
        model.require_ready()
        if len(files) > config.MAX_BATCH_FILES:
            raise AppError(413, "too_many_files", f"Upload at most {config.MAX_BATCH_FILES} X-rays at a time.")
        items = []
        for f in files:
            fname = Path(f.filename or "upload").name
            item = {"filename": fname, "ok": False, "rejected": False, "error": None, "scan": None, "xray_check": None}
            try:
                data = await _read_upload(f)
                res = await run_in_threadpool(_analyse, data, fname, source="triage", patient={}, notes="",
                                              ground_truth=None)
                if res["rejected"]:
                    item.update(rejected=True, xray_check=res["xray_check"],
                                error={"code": "not_xray", "message": (res["xray_check"] or {}).get("reason")
                                       or "This does not look like a chest X-ray."})
                else:
                    item.update(ok=True, scan=res["scan"])
            except AppError as exc:
                item["error"] = exc.to_dict()
            except Exception:
                log.exception("Batch item failed: %s", fname)
                item["error"] = {"code": "internal_error", "message": "This file could not be processed."}
            items.append(item)

        def rank(it: dict):
            if it["ok"]:
                return (0, -it["scan"]["prob_pneumonia"])
            return (1 if it["rejected"] else 2, 0)

        items.sort(key=rank)
        return {"items": items, "count": len(items)}

    # -------------------------------------------------------------- history
    def _get_or_404(scan_id: str) -> dict:
        if not SCAN_ID_RE.match(scan_id):
            raise AppError(404, "not_found", "This scan does not exist. It may have been deleted.")
        scan = store.get(scan_id)
        if scan is None:
            raise AppError(404, "not_found", "This scan does not exist. It may have been deleted.")
        return scan

    @app.get("/api/history")
    def history(
        q: str = Query("", max_length=200),
        page: int = Query(1, ge=1, le=100000),
        page_size: int = Query(24, ge=1, le=100),
        label: str = Query(""),
        source: str = Query(""),
    ):
        lab = label.strip().upper() or None
        if lab not in (None, "NORMAL", "PNEUMONIA"):
            raise AppError(422, "invalid_request", "label must be NORMAL or PNEUMONIA.")
        src = source.strip().lower() or None
        if src is not None and src not in SOURCES:
            raise AppError(422, "invalid_request", "source must be scan, sample or triage.")
        return store.list(q.strip(), page, page_size, lab, src)

    @app.get("/api/history/{scan_id}")
    def history_item(scan_id: str):
        return _get_or_404(scan_id)

    @app.get("/api/history/{scan_id}/image/{kind}")
    def history_image(scan_id: str, kind: str):
        _get_or_404(scan_id)
        if kind not in IMAGE_KINDS:
            raise AppError(404, "not_found", "Unknown image type.")
        p = store.image_path(scan_id, kind)
        if not p.exists() and kind == "heatmap":
            p = store.image_path(scan_id, "overlay")
        if not p.exists():
            raise AppError(404, "not_found", "This image is missing.")
        return FileResponse(p, headers={"Cache-Control": "private, max-age=86400"})

    @app.patch("/api/history/{scan_id}")
    def history_update(scan_id: str, body: ScanPatch):
        _get_or_404(scan_id)
        fields: dict = {}
        sent = body.model_dump(exclude_unset=True)
        for key, val in sent.items():
            if key == "age":
                fields["age"] = _clean_age(val)
            elif key == "sex":
                fields["sex"] = _clean_sex(val)
            else:
                fields[key] = _clean_text(val, key)
        scan = store.update(scan_id, fields)
        if scan is None:
            raise AppError(404, "not_found", "This scan does not exist. It may have been deleted.")
        return scan

    @app.delete("/api/history/{scan_id}")
    def history_delete(scan_id: str):
        _get_or_404(scan_id)
        store.delete(scan_id)
        return {"deleted": 1}

    @app.delete("/api/history")
    def history_clear():
        return {"deleted": store.clear()}

    @app.get("/api/report/{scan_id}.pdf")
    def report_pdf(scan_id: str):
        scan = _get_or_404(scan_id)
        try:
            pdf = report.build_report(scan, model.info(), store.image_path)
        except Exception as exc:
            log.exception("Report failed")
            raise AppError(500, "report_failed", "The PDF report could not be created. Please try again.") from exc
        return Response(pdf, media_type="application/pdf", headers={
            "Content-Disposition": f'attachment; filename="PneumoScan_Report_{scan_id}.pdf"',
            "Cache-Control": "no-store",
        })

    # -------------------------------------------------------------- samples + figures
    @app.get("/api/samples")
    def samples_list():
        return {"items": samples.list_samples()}

    @app.get("/api/samples/thumb/{rel:path}")
    def sample_thumb(rel: str):
        p = samples.sample_path(rel)
        if p is None:
            raise AppError(404, "not_found", "Sample not found.")
        try:
            data = samples.thumbnail(p)
        except Exception as exc:
            raise AppError(422, "corrupt_image", "This sample image could not be read.") from exc
        return Response(data, media_type="image/jpeg", headers={"Cache-Control": "public, max-age=3600"})

    @app.api_route("/api/{rest:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], include_in_schema=False)
    def api_404(rest: str):
        path = f"/api/{rest}"
        for route in app.routes:
            if (getattr(route, "name", "") != "api_404" and str(getattr(route, "path", "")).startswith("/api/")
                    and route.path_regex.match(path)):
                raise AppError(405, "method_not_allowed", "This action is not allowed here.")
        raise AppError(404, "not_found", f"Unknown API endpoint: {path}")

    app.mount("/samples", StaticFiles(directory=str(config.SAMPLES_DIR), check_dir=False), name="samples")
    app.mount("/figures", StaticFiles(directory=str(config.FIGURES_DIR), check_dir=False), name="figures")

    # -------------------------------------------------------------- frontend (SPA)
    dist = config.FRONTEND_DIST

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        if dist.exists():
            if full_path:
                target = (dist / full_path).resolve()
                try:
                    target.relative_to(dist.resolve())
                    if target.is_file():
                        cache = "public, max-age=31536000, immutable" if full_path.startswith("assets/") else "no-cache"
                        return FileResponse(target, headers={"Cache-Control": cache})
                except ValueError:
                    pass
                if full_path.startswith("assets/"):
                    raise AppError(404, "not_found", "File not found.")
            index = dist / "index.html"
            if index.exists():
                return FileResponse(index, headers={"Cache-Control": "no-cache"})
        return HTMLResponse(
            "<h1>PneumoScan AI</h1><p>The frontend has not been built yet. Run "
            "<code>npm run build</code> in app/frontend.</p>", status_code=503)

    return app


app = create_app()
