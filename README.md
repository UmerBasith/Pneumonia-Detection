# PneumoScan AI — Pneumonia Detection using ResNet

CSDX530 Deep Learning (CAT-2 mini project), B.S. Abdur Rahman Crescent Institute of Science and Technology.
Student: **Umer Basith G** (RRN 230171601192) · Faculty: **Mahalakshmi R**, AP / CSE.

PneumoScan AI reads a chest X-ray, estimates the chance of pneumonia with a ResNet ensemble, and shows
**why** with a Grad-CAM heatmap. It runs fully offline on this computer.

> Educational decision-support tool, **not a medical device**. Every result must be checked by a qualified doctor.

---

## Run it (classroom demo)

1. Double-click **`start.bat`** in this folder.
2. Wait a few seconds. Your browser opens at `http://127.0.0.1:8000/` (or the next free port up to 8010).
3. Keep the black `start.bat` window open while you use the app. Close it (or press Ctrl+C) to stop.

The status pill in the top bar shows **Model ready**, **Warming up** (weights loading) or **Demo mode**.
If the trained model files are missing, the app runs a **mock model** and shows a striped
**DEMO MODE – mock model** banner on every page, so simulated results can never be mistaken for real ones.

Double-clicking `start.bat` again while the app is running just reopens it in the browser.

## What you can do

| Page | What it does |
|---|---|
| **Scan** | Drag-and-drop, browse or paste (Ctrl+V) a chest X-ray (JPG, PNG, BMP, WEBP, TIFF, DICOM `.dcm`, up to 25 MB), or try a sample from the test set. Shows the verdict, probability ruler with the decision threshold, confidence, risk level, plain-English explanation, next steps and the disclaimer. The viewer has Original / Heatmap / Side-by-side views, a heatmap opacity slider and zoom/pan (Ctrl + mouse wheel, drag, double-click, + − 0 and arrow keys). Optional patient details; one-click PDF report. Images that are not chest X-rays are turned away and not saved. |
| **Triage** | Doctor mode: drop up to 50 X-rays at once. Each file shows its own progress; the table re-sorts by pneumonia probability, flags high-risk rows as urgent, filters (urgent / pneumonia / normal / issues), opens details and exports CSV. |
| **History** | Every saved scan (SQLite on this computer). Search, filter, grid or list view, open, edit patient details and doctor's notes, re-download the PDF, delete one or clear all (with confirmation). |
| **CURB-65** | Severity score for adults with pneumonia. Urea in mmol/L or BUN mg/dL; switches to CRB-65 when urea is not available. Live score, risk group, 30-day mortality and care setting from Lim et al., *Thorax* 2003. |
| **Learn** | Pneumonia explained simply: emergency signs, symptoms, signs in children (WHO), causes, risk, prevention, diagnosis, home care, X-ray appearance — every card lists its sources (WHO, NHS, CDC, NIH, Radiopaedia). |
| **Model** | Test-set accuracy, sensitivity, specificity, ROC-AUC, confusion matrix, figures, how ResNet's skip connection works, ensemble members, dataset facts, intended use and limitations. |
| **About** | Project, student, course, faculty, tech stack, dataset credit and disclaimer. |

Light and dark mode follow the system setting; the moon/sun button switches and remembers your choice.

## First-time setup (only if `.venv` or the built web interface is missing)

```bat
cd C:\PersonalProjects\pneumoscan-ai
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -r app\backend\requirements.txt
REM plus PyTorch/torchvision for the real model (see ml/ and docs/PROJECT_PLAN.md)

cd app\frontend
npm install
npm run build
```

`start.bat` builds the web interface automatically the first time if `app\frontend\dist` is missing and Node.js is installed.

## Folder guide (app part)

```
start.bat                 double-click launcher (uses .venv, picks a free port 8000-8010, opens the browser)
app/backend/              FastAPI server
  main.py                 API routes + serves the built frontend (SPA)
  model_service.py        loads ml/inference.py once in the background; falls back to the mock
  mock_inference.py       fake model with the exact same API (demo mode only)
  imaging.py              safe decoding: JPG/PNG/BMP/WEBP/TIFF/DICOM, EXIF rotation, size and corruption checks
  storage.py              SQLite history + saved images (app/backend/storage/, not in git)
  report.py               PDF report (ReportLab, bundled DejaVu Sans font for ₹, quotes, accents)
  launcher.py             used by start.bat
  tests/                  pytest suite (run below)
app/frontend/             React + TypeScript + Vite + Tailwind CSS; built into app/frontend/dist
```

## API (all JSON; errors look like `{"error": {"code", "message"}}`)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | status, model mode (real/mock), device, model version |
| GET | `/api/model-info` | `models/metrics.json` + `models/model_card.json` + figure URLs |
| POST | `/api/predict` | multipart `file` + optional `name, age, sex, patient_id, symptoms, notes` → result + saved scan |
| POST | `/api/batch` | multipart `files` (≤ 50) → results sorted by probability; per-file errors (the Triage page sends files one by one to `/api/predict` instead, so it can show live progress per file) |
| GET | `/api/history` | `q, page, page_size, label, source` |
| GET / PATCH / DELETE | `/api/history/{id}` | read, edit patient details or notes, delete |
| DELETE | `/api/history` | clear all |
| GET | `/api/history/{id}/image/{input,overlay,heatmap,thumb}` | saved images |
| GET | `/api/report/{id}.pdf` | patient report PDF |
| GET | `/api/samples`, `/samples/...`, `/figures/...` | demo X-rays and training figures |

Interactive API docs: `http://127.0.0.1:8000/api/docs`.

## Tests

```bat
.venv\Scripts\python -m pytest ml\test_inference.py app\backend\tests -q
.venv\Scripts\python -m pytest tests -q
cd app\frontend && npm run lint && npm run build
```

`tests/` is the end-to-end QA suite (see `docs/QA_REPORT.md`): it starts its own server with the real model on a free
port (8150+) and a temporary history folder, so it never touches your saved scans. It checks the app against
`sample_xrays/answer_key.csv`, the `ml.inference` CLI and the evaluation predictions, hostile files and filenames,
security basics, and every page in headless Chromium (Playwright) at 1280x720, 1920x1080 and 390x844, light and dark.
`tests/make_screenshots.py` regenerates `docs/screenshots/`.

The backend suite covers every endpoint, bad and huge files, synthetic DICOM (MONOCHROME1/2, no window, no pixels),
mixed batches, history CRUD, PDF generation with long and Unicode text, and the real-vs-mock switch. The test that runs
the trained model end to end is skipped automatically until `models/ensemble.json` exists.

Options for developers: `PNEUMOSCAN_MODEL=mock|real|auto` (default auto), `PNEUMOSCAN_STORAGE=<folder>`,
`PNEUMOSCAN_SAMPLES_DIR=<folder>`. Frontend dev server: `npm run dev` in `app/frontend` (proxies `/api` to port 8000).

## Privacy

Patient details, images and notes are stored only in `app/backend/storage/` on this computer. The server listens on
`127.0.0.1` only, and the app loads no fonts or scripts from the internet.

## Credits

Dataset: Kermany D, et al. *Labeled Optical Coherence Tomography (OCT) and Chest X-Ray Images for Classification*,
Mendeley Data v2, 2018, DOI [10.17632/rscbjbr9sj.2](https://doi.org/10.17632/rscbjbr9sj.2), CC BY 4.0; described in
Kermany et al., *Cell* 172(5):1122–1131.e9, 2018. Medical content: see `docs/research/medical_content.md`.
Fonts: Familjen Grotesk, IBM Plex Sans and IBM Plex Mono (SIL OFL, bundled via Fontsource); DejaVu Sans for PDFs.
