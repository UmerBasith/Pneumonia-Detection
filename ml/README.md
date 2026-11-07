# PneumoScan AI - machine-learning code

Pneumonia detection from paediatric chest X-rays with an ensemble of ImageNet-pretrained ResNets.
All commands run from the project root with the project virtual environment:

```bat
set PY=.venv\Scripts\python.exe
```

| Step | Command | What it does |
|---|---|---|
| 1 | `%PY% -m ml.prepare_data` | Checks image counts, makes the patient-level validation split (`data/splits.csv`), caches 512x512 grayscale copies, runs leakage checks (`data/dataset_summary.json`). |
| 2 | `%PY% -m ml.train --name r50_384_s1 --arch resnet50 --res 384 --epochs 20 --bs 24 --seed 1` | Fine-tunes one ResNet. Best epoch chosen by validation ROC-AUC. Writes `models/checkpoints/<name>/` and `logs/train_<name>.log`. |
| 3 | `%PY% -m ml.evaluate --members A B --val-only` | Validation metrics only (used for every decision). |
| 3b | `%PY% -m ml.evaluate --members A B --export` | Final: temperature + threshold from validation, scores the test set once, writes `models/*.pt` (fp16), `models/ensemble.json`, `models/metrics.json`. Every test scoring is appended to `logs/test_evaluations.jsonl`. |
| 4 | `%PY% -m ml.xray_gate` | Fits the "is this a chest X-ray?" detector and validates it (`models/xray_gate.npz`, `models/xray_gate_metrics.json`). |
| 5 | `%PY% -m ml.make_figures` | All report figures into `docs/figures/`. |
| 6 | `%PY% -m ml.make_samples` | Demo images into `sample_xrays/` (test split only) + answer key. |
| 7 | `%PY% -m pytest ml/test_inference.py -q` | Contract tests for `ml/inference.py`. |

Quick check of a single image:

```bat
%PY% -m ml.inference sample_xrays\pneumonia_01.jpeg --save out_cam
```

## Files

| File | Purpose |
|---|---|
| `common.py` | Paths, image conversion for every PIL mode (`to_gray_uint8`), the canonical 512x512 view, `build_model`, metrics. |
| `prepare_data.py` | Dataset verification, patient-level split, cache, leakage checks. |
| `datasets.py` | PyTorch `Dataset` + training augmentation / evaluation transforms. |
| `train.py` | Training loop: AdamW, cosine schedule with warm-up, AMP (fp16), class-weighted cross-entropy with label smoothing, weight EMA, early stopping on validation AUC. |
| `evaluate.py` | Flip TTA, ensemble, temperature scaling, Youden-J threshold (validation only), test scoring, export. |
| `gradcam.py` | Grad-CAM on `layer4` (one backward pass gives the map for both classes). |
| `xray_gate.py` | Colour / blank / size checks + Mahalanobis out-of-distribution detector on ResNet features. |
| `inference.py` | `PneumoniaModel` - the API used by the app (contract in `docs/PROJECT_PLAN.md`). |
| `make_figures.py`, `make_samples.py` | Report figures and demo images. |
| `test_inference.py` | pytest checks of the inference contract. |

## Inference API (summary)

```python
from PIL import Image
from ml.inference import PneumoniaModel, load_image   # load_image also reads .dcm files

model = PneumoniaModel("models")          # loads once; GPU if available, else CPU
model.check_image(img)  # {"is_xray": bool, "score": 0..1, "reason": str}
model.predict(img)      # label, prob_pneumonia, confidence, threshold, risk_level,
                        # gradcam_overlay_png, gradcam_heatmap_png, input_png (base64 PNGs, same size),
                        # xray_check, inference_ms, model_version
                        # or {"rejected": True, "xray_check": {...}, ...} if it is not a chest X-ray
model.info()            # {"metrics": <models/metrics.json>, "model_card": <models/model_card.json>}
```

* `input_png`, `gradcam_overlay_png` and `gradcam_heatmap_png` have identical size: the upload's aspect
  ratio, longest side 768 px. The heatmap PNG is an RGBA "jet" map whose alpha grows with the Grad-CAM value
  (0.2 to 1.0); `gradcam_overlay_png` equals that heatmap drawn over `input_png` at 60 % opacity, so an
  opacity slider (CSS `opacity` on the heatmap layered over `input_png`) reproduces and extends it.
* `risk_level` bands are relative to the validation-chosen threshold `t`:
  Low `p < t/2`, Moderate `t/2 <= p < (1+t)/2`, High `p >= (1+t)/2` (stored in `models/ensemble.json`).
* Thread-safe (internal lock), weights loaded once, CPU fallback, accepts L, RGB, RGBA, LA, P, I;16, I, F, CMYK, 1.

## Practical notes (this laptop)

* `channels_last` memory format made training 8x slower on the RTX 3050 with torch 2.11, so it is not used.
* Each Windows DataLoader worker costs ~0.6 GB of RAM; 3 workers are enough to keep the GPU busy.
* Weights are shipped as fp16 state dicts (< 50 MB each, GitHub limit is 100 MB) and cast to fp32 on load;
  all reported metrics were computed with these exact fp16-rounded weights.
