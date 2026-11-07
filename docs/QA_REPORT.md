# PneumoScan AI - QA report

QA agent, 2026-11-08. Independent hostile testing of the finished app (real ResNet ensemble on the RTX 3050, FastAPI
backend, built React frontend, `start.bat`). Model numbers, threshold, metrics and weights were **not** changed.

## 1. What was tested

| Area | How | Result |
|---|---|---|
| **Fresh start with `start.bat`** | Ran `start.bat` through `cmd /c` with no server running | Picked port 8000, health up in ~3 s, model on `cuda (NVIDIA GeForce RTX 3050 6GB Laptop GPU)`, warm-up finished, "Model ready" after ~16 s, URL `http://127.0.0.1:8000/` |
| Port 8000 busy | Another program (`python -m http.server`) on 8000 | Started on **8001** with the right URL |
| `start.bat` twice | Second run while the app was running | "PneumoScan AI is already running at http://127.0.0.1:8000/", reopens the browser, exits cleanly |
| No GPU | `CUDA_VISIBLE_DEVICES=-1` | Loads on **cpu**, predictions identical (pneumonia_01 0.9557 / normal_01 0.0006), about 4-6 s per X-ray on this laptop's CPU |
| Binds to localhost only | `netstat` | `127.0.0.1:8000` only, never `0.0.0.0` |
| **12 demo X-rays** | API vs `answer_key.csv` vs `python -m ml.inference` CLI | All 12: same label, same risk, probability equal to the answer key's 4 decimals and to the CLI at 3 decimals |
| 3 non-X-rays | API and UI | All rejected with a friendly reason, nothing saved |
| **40+ random official TEST images** (seed 2026, incl. RGB-encoded JPEGs) | API vs direct `PneumoniaModel.predict` vs `models/checkpoints/final_preds.npz` | 39 analysed + 1 refused by the X-ray gate in both paths. App vs direct call: **max difference 0.0** (identical). App vs evaluation run: max 0.00009, 0 label changes. No pre-processing mismatch. |
| File formats | API | 8-bit and 16-bit PNG, RGBA (opaque and partly transparent), EXIF-rotated phone JPEG (turned upright, same result), CMYK JPEG, BMP, WEBP, TIFF, synthetic DICOM MONOCHROME2 and MONOCHROME1, grayscale vs RGB copy (identical probability), 18 MB 16-bit scanner export (accepted), 26 MB (refused, 413), 40 MB multipart (refused), 40x40 px (too small), empty file, text file renamed `.png`, `.txt`, truncated JPEG, request without a file - all give the right result or a friendly error |
| Filenames | API + PDF + search | Tamil, emoji + spaces, `a<b>c:d"e\|f?g*h`, `CON`, `..\..\windows\evil`, `../../etc/passwd` - stored as a plain name, searchable, PDF downloads |
| **Every UI flow** | Playwright headless Chromium at 1280x720, 1920x1080, 390x844, light + dark | Scan (browse, drag-drop, paste, sample gallery with ground-truth reveal, patient form, Original/Heatmap/Side-by-side, opacity slider, zoom buttons, keyboard 0/arrows, double-click zoom, save notes, PDF download checked with PyMuPDF and rendered to PNG), rejected image screen, bad-file toasts, invalid age |
| Triage | 12 samples + 1 photo + 1 `.txt` + a file named `=HYPERLINK("x").jpeg` | 15/15 finished, sorted by probability, 6 urgent, filters (urgent/pneumonia/normal/issues), CSV export (priorities 1-13, urgent flags, formula injection neutralised with `'`), open a row, queue survives navigation |
| History | UI | Search by name / patient ID, label filter, grid/list, open, edit notes -> reload -> still there, PDF from detail and list, delete one, clear all |
| CURB-65 | 16 parametrised cases + invalid input | Every score 0-5 and CRB-65 0-4; boundaries urea 7.0 -> 0 / 7.1 -> 1, BUN 19 -> 0 / 20 -> 1, RR 29/30, SBP 90/89, DBP 61/60, age 64/65; risk group and care text match `docs/research/medical_content.md` (Lim et al. 2003 + NICE); "Enter a number", range errors, comma decimals, child warning |
| Learn | UI + link check | Every external link opens in a new tab with `rel=noopener`; all 27 external URLs checked: 22 answer 200 directly, CDC (3) answer 200 in a real browser engine, BMJ (2 DOIs) resolve to the right article behind a Cloudflare browser check - none broken |
| Model page | UI vs `models/metrics.json` | Accuracy 94.6, sensitivity 99.7, specificity 85.9, ROC-AUC 98.7, precision 92.2, F1 95.8, confusion 201/33/1/389, threshold 0.074 - all equal; all 12 figures load |
| About | UI | Umer Basith G, RRN 230171601192, CSDX530 Deep Learning, Mahalakshmi R (AP / CSE), BSARCIST |
| Navigation | UI | 404 page, refresh on every route (SPA fallback), titles, back/forward, unknown scan id -> "Scan not found", theme toggle persists after reload, keyboard-only (skip link, every nav item, start a scan with Enter, visible focus ring), phone menu, **no horizontal overflow on any page at any size** |
| Robustness | API + UI | 5 parallel predictions (all correct), 50-file batch (sorted, per-file errors), 51 files refused, 100 predictions: server RAM 1497 -> 1497 MB and GPU 678 -> 678 MB (stable), slow server (4 s delay) shows the analysing screen, server stopped mid-session -> red "server is not responding" banner + upload disabled -> server restarted -> Retry -> works again, server restart keeps history (notes, images, PDF), double-click / paste during a running scan -> one scan only |
| Security / privacy | API | Path traversal on `/api/history/.../image`, `/api/report`, `/api/samples/thumb`, `/samples`, `/figures`, `/assets` and the SPA fallback (16 encoded variants) - nothing outside the allowed folders is ever served; no CORS headers for a foreign origin; XSS text in name/symptoms/notes is shown as plain text in the UI and the PDF; field length / age validation |
| Browser hygiene | every Playwright page | no console errors or warnings, no page errors, no failed requests, no HTTP >= 400 except the intentional ones (404 for a deleted scan, 422 for a fake image) |
| Server logs | log of the QA server after the whole run | no tracebacks, no ERROR lines |
| Visual check | read every screenshot of every page (3 sizes x 2 themes) and the PDF | no broken, clipped, overlapping or unreadable element found in the app; one PDF alignment defect (below) |

## 2. Bugs found and fixed

| # | Bug | Fix |
|---|---|---|
| 1 | **PDF printed Tamil / Hindi (any Indian-language) patient names and symptoms as empty boxes** (DejaVu Sans has no Indic letters). The UI showed them fine. | `app/backend/report.py`: per-character font fallback to Windows' Nirmala UI (Indic scripts) and Segoe UI Symbol/Emoji; HarfBuzz shaping (`uharfbuzz`, added to `requirements.txt`) applied **only** to the Indic font so Tamil vowel signs sit in the right place, while English text is untouched (shaping DejaVu would have turned "st" into a ligature). Test: `test_pdf_prints_tamil_and_hindi_names`. |
| 2 | **Scan page kept showing a deleted result.** After "Clear all" in History (or deleting the scan that was on screen), going back to Scan showed the old result with broken images; "Save notes" then failed with "does not exist". The Triage queue also kept rows whose thumbnails were deleted. | `lib/scanSession.ts` `forgetScans()` called by History (delete, clear all) and the scan detail page (delete); the Triage queue store moved to the same file so it can be tidied too. Tests: `test_clear_all_resets_scan_page`, `test_deleting_current_scan_resets_scan_page`. |
| 3 | PDF: the two image captions started on different lines (left one sat lower). | `report.py`: caption row top-aligned. `docs/screenshots/15_pdf_report_page1.png` and `sample_patient_report.pdf` regenerated (see `docs/screenshots/CHANGED.md`). |
| 4 | `start.bat` window showed a raw log line (`2026-11-08 ... INFO pneumoscan.model: Model ready: ...`) between the friendly messages. | `launcher.py`: app loggers at WARNING when started by the launcher (warnings and errors still print). |
| 5 | `start.bat --no-browser` on an already running app still said "Opened it in your browser". | `launcher.py`: message now matches what happened. |
| 6 | README said the viewer zooms with the mouse wheel; it zooms with **Ctrl + wheel** (plain wheel scrolls the page, on purpose). | README corrected. |

## 3. Final test counts

| Suite | Command | Result |
|---|---|---|
| ML contract | `.venv\Scripts\python -m pytest ml	est_inference.py` | **24 passed** |
| Backend | `.venv\Scripts\python -m pytest appackend	ests` | **35 passed** |
| QA end-to-end (new) | `.venv\Scripts\python -m pytest tests` | **121 passed** (8 min; real model on GPU, headless Chromium), run with DeprecationWarnings as errors: 0 warnings |
| Frontend | `npm run lint` / `npm run build` in `app/frontend` | 0 problems / built with 0 warnings |
| **Total** | | **180 automated tests, all passing** |

QA suite breakdown: `test_predictions_e2e.py` 16 (12 demo X-rays, 3 non-X-rays, 40+ random test images),
`test_inputs_e2e.py` 40 (formats, filenames, parallel, batch, memory, 16 path-traversal URLs, CORS, XSS, restart,
Tamil PDF), `test_ui_e2e.py` 64 (scan flow x 6 size/theme combos, drag-drop/paste, gallery, bad files, double submit,
slow server, triage, history, stale-result fix, 16 CURB-65 cases + invalid input, Learn, Model, About, 404/refresh/back,
theme, keyboard, phone menu, overflow on 8 routes x 3 sizes, server down and back), `test_zz_server_log.py` 1.

## 4. Not fixed / for the student to know

* **Accuracy is 94.55 % (below the 95 % target)** - honest, unchanged, and explained in `docs/ML_REPORT.md`. Do not change the threshold.
* `answer_key.csv` stores probabilities with 4 decimals; one value (pneumonia_06: 0.96348) is written "0.9635", which a reader would round to 96.4 % while the app shows 96.3 %. Both are correct roundings of the same number; not changed (owned by the ML agent).
* CPU-only speed: about **4-6 s per X-ray** on this laptop's CPU in my run (the GPU path is about 0.4-1 s). The demo uses the GPU.
* `CUDA_VISIBLE_DEVICES=""` (empty) does not hide the GPU in this PyTorch build (it still uses the GPU and shows "cuda" without the name). Use `-1` to force CPU. Not a classroom scenario.
* The X-ray gate is a convenience, not a safety guarantee (adult or non-chest X-rays may be accepted); this is already stated on the Model page.
* Some publisher pages (BMJ via DOI) show a "checking your browser" screen before the article - normal for those sites, needs internet.
* The PDF uses Windows fonts (Nirmala UI, Segoe UI Symbol) for non-Latin text. On a machine without them, those characters fall back to boxes as before; everything else is unchanged.

## 5. Files added or changed by QA

* `tests/conftest.py`, `tests/test_predictions_e2e.py`, `tests/test_inputs_e2e.py`, `tests/test_ui_e2e.py`,
  `tests/test_zz_server_log.py` (new end-to-end suite), `tests/make_screenshots.py` (the App agent's screenshot
  script, moved into the repo).
* `app/backend/report.py`, `app/backend/launcher.py`, `app/backend/requirements.txt`.
* `app/frontend/src/lib/scanSession.ts`, `pages/HistoryPage.tsx`, `pages/ScanDetailPage.tsx`, `pages/TriagePage.tsx`;
  `app/frontend/dist` rebuilt from the final source.
* `README.md`, `docs/screenshots/15_pdf_report_page1.png`, `docs/screenshots/sample_patient_report.pdf`,
  `docs/screenshots/CHANGED.md`.
* History cleared at the end (the 4 old mock-mode scans and all test scans are gone).
