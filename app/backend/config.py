"""Paths and limits for the PneumoScan backend (override with environment variables)."""
from __future__ import annotations

import os
from pathlib import Path

APP_VERSION = "1.0.0"

BACKEND_DIR = Path(__file__).resolve().parent
ROOT = BACKEND_DIR.parents[1]  # project root: C:\PersonalProjects\pneumoscan-ai

MODELS_DIR = Path(os.environ.get("PNEUMOSCAN_MODELS_DIR", ROOT / "models"))
ML_DIR = ROOT / "ml"
SAMPLES_DIR = Path(os.environ.get("PNEUMOSCAN_SAMPLES_DIR", ROOT / "sample_xrays"))
FIGURES_DIR = Path(os.environ.get("PNEUMOSCAN_FIGURES_DIR", ROOT / "docs" / "figures"))
FRONTEND_DIST = Path(os.environ.get("PNEUMOSCAN_FRONTEND_DIST", ROOT / "app" / "frontend" / "dist"))
STORAGE_DIR = Path(os.environ.get("PNEUMOSCAN_STORAGE", BACKEND_DIR / "storage"))
ASSETS_DIR = BACKEND_DIR / "assets"

# "auto" (real model when its files exist, else mock), "mock" or "real"
MODEL_MODE = os.environ.get("PNEUMOSCAN_MODEL", "auto").strip().lower()
# "1" skips the warm-up prediction (used by the tests)
SKIP_WARMUP = os.environ.get("PNEUMOSCAN_SKIP_WARMUP", "0") == "1"

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_BATCH_FILES = 50
THUMB_LONG_SIDE = 360
