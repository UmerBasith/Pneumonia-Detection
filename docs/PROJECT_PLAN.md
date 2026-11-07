# PneumoScan AI — Pneumonia Detection from Chest X-rays using ResNet

Shared plan and contract for every agent working on this project. Read it fully before you start.

## Owner / submission
- Student: **Umer Basith G**, RRN **230171601192**
- Course: CSDX530 – Deep Learning (CAT-2 Mini Project), B.S. Abdur Rahman Crescent Institute of Science and Technology (BSARCIST)
- Faculty: Mahalakshmi R, AP / CSE
- Official title: **Pneumonia Detection using ResNet**
- Report submission: 09.11.2026 (printed, soft binding). Report must include: project explanation, model architecture diagram, dataset details, implementation code, results, screenshots, conclusion.

## Non-negotiable rules (healthcare project)
1. **Honest numbers only.** Never tune anything (threshold, epochs, model choice, TTA) on the test set. Use a validation split carved out of the training data. Report the real test result even if it is below target.
2. Target: **≥95% accuracy on the official held-out test set** (624 images: 234 NORMAL, 390 PNEUMONIA). Also report precision, recall (sensitivity), specificity, F1, ROC-AUC.
3. Final model must be a **ResNet** (ResNet18/34/50, or an ensemble of ResNets). That is the project title.
4. The app is a **decision-support / educational tool, not a medical device**. A clear disclaimer appears on the result screen and in every PDF.
5. Everything must run **offline** in the classroom: no CDN scripts or fonts at runtime, model weights stored locally.
6. Windows 11 machine, folder path has no spaces: `C:\PersonalProjects\pneumoscan-ai`. GPU: RTX 3050 6 GB (CUDA). Python env: `.venv\Scripts\python.exe` (Python 3.11). Node 24 available for the frontend.
7. Never commit or push anything; the orchestrator handles git. Never spend money, never sign in anywhere, never use Kaggle (needs login).

## Folder layout and ownership
| Path | Owner | What |
|---|---|---|
| `docs/research/` | Research agent | Accuracy research notes, medical content (sourced), literature survey, references |
| `data/` | ML agent | Raw + processed dataset (gitignored) |
| `ml/` | ML agent | `train.py`, `evaluate.py`, `inference.py`, `gradcam.py`, `xray_gate.py`, configs |
| `models/` | ML agent | Final weights + `metrics.json` + `model_card.json` |
| `docs/figures/` | ML agent | Training curves, confusion matrix, ROC, Grad-CAM examples, sample-image grid, architecture diagram (PNG, 300 dpi) |
| `sample_xrays/` | ML agent | Test X-rays for the demo (from the TEST split only) + a few non-X-ray images |
| `app/backend/` | App agent | FastAPI server, serves API + built frontend |
| `app/frontend/` | App agent | React + Vite + TypeScript UI, built to `app/frontend/dist` |
| `start.bat` | App agent | Double-click launcher that starts the server and opens the browser |
| `tests/` | QA agent | Automated tests (pytest + browser checks) |
| `report/` | Report agent | Final Word report (.docx) + PDF |

## Contract between ML and App: `ml/inference.py`
```python
from PIL import Image

class PneumoniaModel:
    def __init__(self, models_dir: str = "models", device: str | None = None): ...
    def check_image(self, img: Image.Image) -> dict:
        # {"is_xray": bool, "score": float (0..1, higher = more like a chest X-ray), "reason": str}
    def predict(self, img: Image.Image, with_gradcam: bool = True) -> dict:
        # {
        #   "label": "PNEUMONIA" | "NORMAL",
        #   "prob_pneumonia": float,        # 0..1, calibrated ensemble probability
        #   "confidence": float,            # prob of the predicted label, 0..1
        #   "threshold": float,             # decision threshold chosen on VALIDATION
        #   "risk_level": "Low" | "Moderate" | "High",
        #   "gradcam_overlay_png": str,     # base64 PNG, heatmap blended on the X-ray, same aspect as input
        #   "gradcam_heatmap_png": str,     # base64 PNG, heatmap only (for an opacity slider), same size as overlay
        #   "input_png": str,               # base64 PNG of the preprocessed grayscale view shown to the user
        #   "xray_check": {...},            # result of check_image
        #   "inference_ms": float,
        #   "model_version": str,
        # }
    def info(self) -> dict:  # contents of models/metrics.json + model_card.json
```
- `predict` must call `check_image` first; if it is not a chest X-ray, it returns `{"rejected": True, "xray_check": {...}}` with no label.
- Must accept any PIL mode (L, RGB, RGBA, I;16 from DICOM/PNG16) and any size.
- Must be thread-safe for sequential calls, load weights once, work on CPU if CUDA is missing.
- Until the real model exists, the App agent uses `app/backend/mock_inference.py` with the exact same API.

## App features (for patients AND doctors)
1. **Scan**: drag-drop or browse upload (JPG/PNG/DICOM `.dcm`), or "Try a sample X-ray" gallery. Result card: label, probability gauge, risk level, plain-English explanation, next steps.
2. **Explainability**: Grad-CAM heatmap with an opacity slider and side-by-side / overlay toggle.
3. **Image check**: rejects photos that are not chest X-rays, with a friendly message.
4. **Patient report PDF**: patient name/age/sex/ID, symptoms, doctor notes, result, heatmap, disclaimer, date. One-click download.
5. **Doctor triage queue**: upload many X-rays at once, get a table sorted by pneumonia probability, with urgent ones flagged and a CSV export.
6. **CURB-65 severity calculator** (standard clinical pneumonia score) with the recommended care setting per score.
7. **Scan history**: saved locally (SQLite on the backend), searchable, can be deleted.
8. **Learn**: what pneumonia is, symptoms, warning signs, prevention, when to see a doctor (sourced from WHO / NHS / CDC).
9. **Model page**: accuracy, sensitivity, specificity, AUC, confusion matrix, training curves, how ResNet works, limitations. Great for the classroom demo.
10. Light/dark mode, works on a laptop screen and a projector, keyboard accessible.
