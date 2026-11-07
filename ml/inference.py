"""PneumoScan AI inference API (the contract used by the app, see docs/PROJECT_PLAN.md).

    from ml.inference import PneumoniaModel
    model = PneumoniaModel("models")          # loads weights once (GPU if available)
    model.check_image(pil_img)                # {"is_xray", "score", "reason"}
    model.predict(pil_img)                    # label, calibrated probability, risk, Grad-CAM PNGs...
    model.info()                              # {"metrics": metrics.json, "model_card": model_card.json}

CLI self-test:  python -m ml.inference sample_xrays/pneumonia_01.jpeg
"""
from __future__ import annotations

import base64
import io
import json
import threading
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from ml.common import CLASSES, MODELS_DIR, build_model, canonical_view, to_gray_uint8
from ml.datasets import eval_transform
from ml.gradcam import GradCAM, colorize, overlay

DISPLAY_LONG_SIDE = 768   # longest side (px) of input_png / overlay / heatmap PNGs
OVERLAY_OPACITY = 0.6     # heatmap opacity used for gradcam_overlay_png


def load_image(path: str | Path) -> Image.Image:
    """Open JPG/PNG/BMP/TIFF with PIL, or a DICOM (.dcm) with pydicom (returned as 32-bit 'F')."""
    path = Path(path)
    if path.suffix.lower() == ".dcm":
        import pydicom
        ds = pydicom.dcmread(str(path))
        arr = ds.pixel_array.astype(np.float32)
        arr = arr * float(getattr(ds, "RescaleSlope", 1)) + float(getattr(ds, "RescaleIntercept", 0))
        if getattr(ds, "PhotometricInterpretation", "") == "MONOCHROME1":
            arr = arr.max() - arr  # MONOCHROME1 stores bones dark; flip to the usual look
        if arr.ndim == 3:
            arr = arr[..., :3].mean(-1) if arr.shape[-1] in (3, 4) else arr[0]
        return Image.fromarray(np.ascontiguousarray(arr, dtype=np.float32))  # mode "F"
    img = Image.open(path)
    img.load()
    return img


def _png_b64(arr: np.ndarray) -> str:
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


class PneumoniaModel:
    def __init__(self, models_dir: str = "models", device: str | None = None, gate: bool = True):
        self.dir = Path(models_dir) if Path(models_dir).is_absolute() else MODELS_DIR.parent / models_dir
        if not self.dir.exists():
            self.dir = MODELS_DIR
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.amp = self.device.type == "cuda"
        self.cfg = json.loads((self.dir / "ensemble.json").read_text())
        self.members, self._lock = [], threading.RLock()
        for m in self.cfg["members"]:
            ck = torch.load(self.dir / m["file"], map_location="cpu", weights_only=False)
            net = build_model(ck["arch"], pretrained=False)
            net.load_state_dict({k: v.float() if v.is_floating_point() else v for k, v in ck["state_dict"].items()})
            net = net.to(self.device).eval()
            for p in net.parameters():
                p.requires_grad_(False)  # Grad-CAM only needs gradients w.r.t. activations
            self.members.append({**m, "net": net, "cam": GradCAM(net), "tf": eval_transform(m["res"])})
        self._pooled = None
        self.members[0]["net"].avgpool.register_forward_hook(lambda _m, _i, o: setattr(self, "_pooled", o))
        self.gate = None
        if gate:
            from ml.xray_gate import XrayGate
            self.gate = XrayGate(self.dir / "xray_gate.npz")
        metrics_path = self.dir / "metrics.json"
        self.version = json.loads(metrics_path.read_text()).get("model_version", "unknown") \
            if metrics_path.exists() else "unknown"

    # ------------------------------------------------------------------ helpers
    def _tensor(self, member: dict, view: Image.Image) -> torch.Tensor:
        return member["tf"](view).unsqueeze(0).to(self.device)

    @torch.no_grad()
    def features(self, x: torch.Tensor) -> np.ndarray:
        """Pooled layer4 features of the first member for a normalised batch (used by the gate)."""
        x = x.to(self.device)
        with torch.autocast("cuda", dtype=torch.float16, enabled=self.amp):
            self.members[0]["net"](x)
        return self._pooled.flatten(1).float().cpu().numpy()

    def _risk(self, p: float) -> str:
        for level, (lo, hi) in self.cfg["risk_bands"].items():
            if lo <= p < hi or (level == "High" and p >= lo):
                return level
        return "High"

    # ------------------------------------------------------------------ public API
    def check_image(self, img: Image.Image) -> dict:
        """Is this a chest X-ray? {"is_xray": bool, "score": 0..1, "reason": str}"""
        from ml.xray_gate import heuristics
        with self._lock:
            ok, reason, _ = heuristics(img)
            if not ok:
                return {"is_xray": False, "score": 0.0, "reason": reason}
            if self.gate is None:
                return {"is_xray": True, "score": 1.0, "reason": "gate disabled"}
            feats = self.features(self._tensor(self.members[0], canonical_view(img)))
            return self.gate.decide(img, feats)

    def predict(self, img: Image.Image, with_gradcam: bool = True) -> dict:
        t0 = time.perf_counter()
        check = self.check_image(img)
        if not check["is_xray"]:
            return {"rejected": True, "xray_check": check,
                    "inference_ms": (time.perf_counter() - t0) * 1000, "model_version": self.version}
        with self._lock:
            gray = to_gray_uint8(img)
            view = canonical_view(img)
            margins, explained = [], []
            for m in self.members:
                x = self._tensor(m, view)
                with torch.autocast("cuda", dtype=torch.float16, enabled=self.amp):
                    if with_gradcam:
                        acts, grads, lg = m["cam"].explain(x)
                        explained.append((acts, grads, x.shape[-2:]))
                    else:
                        with torch.no_grad():
                            lg = m["net"](x)
                    views = [lg]
                    if self.cfg.get("tta_hflip", True):
                        with torch.no_grad():
                            views.append(m["net"](torch.flip(x, dims=[3])))
                margins.append(float(np.mean([float(v[0, 1] - v[0, 0]) for v in views])))
            z = float(np.mean(margins))
            prob = float(1 / (1 + np.exp(-z / self.cfg["temperature"])))
            thr = float(self.cfg["threshold"])
            label = CLASSES[int(prob >= thr)]

            # Display images keep the ORIGINAL aspect ratio; the square-view heatmap is
            # stretched back onto it, so all three PNGs line up pixel for pixel.
            h, w = gray.shape
            s = DISPLAY_LONG_SIDE / max(h, w)
            dw, dh = max(1, round(w * s)), max(1, round(h * s))
            disp = np.asarray(Image.fromarray(gray).resize((dw, dh), Image.Resampling.LANCZOS))
            out = {"label": label, "prob_pneumonia": prob,
                   "confidence": prob if label == "PNEUMONIA" else 1 - prob,
                   "threshold": thr, "risk_level": self._risk(prob),
                   "input_png": _png_b64(disp), "xray_check": check}
            if with_gradcam:
                # Explain the ENSEMBLE's decision: every member's map for the final label, averaged.
                target = CLASSES.index(label)
                maps = [GradCAM.cam(acts, grads, target, tuple(size)) for acts, grads, size in explained]
                avg = np.mean([np.asarray(Image.fromarray(c.astype(np.float32)).resize((dw, dh), Image.Resampling.BILINEAR))
                               for c in maps], axis=0)
                avg = avg / avg.max() if avg.max() > 0 else avg
                heat = colorize(avg)
                out["gradcam_overlay_png"] = _png_b64(overlay(disp, heat, OVERLAY_OPACITY))
                out["gradcam_heatmap_png"] = _png_b64(heat)
            else:
                out["gradcam_overlay_png"] = out["gradcam_heatmap_png"] = ""
        out["inference_ms"] = (time.perf_counter() - t0) * 1000
        out["model_version"] = self.version
        return out

    def info(self) -> dict:
        read = lambda n: json.loads((self.dir / n).read_text()) if (self.dir / n).exists() else {}
        return {"metrics": read("metrics.json"), "model_card": read("model_card.json")}


def _cli() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Run PneumoScan AI on image files")
    ap.add_argument("images", nargs="+")
    ap.add_argument("--save", help="folder to write the Grad-CAM overlay PNGs")
    ap.add_argument("--cpu", action="store_true")
    a = ap.parse_args()
    model = PneumoniaModel(device="cpu" if a.cpu else None)
    for path in a.images:
        res = model.predict(load_image(path))
        short = {k: (f"<{len(v)} base64 chars>" if k.endswith("_png") else v) for k, v in res.items()}
        print(Path(path).name, json.dumps(short, indent=2))
        if a.save and "gradcam_overlay_png" in res:
            Path(a.save).mkdir(parents=True, exist_ok=True)
            (Path(a.save) / f"{Path(path).stem}_gradcam.png").write_bytes(base64.b64decode(res["gradcam_overlay_png"]))


if __name__ == "__main__":
    _cli()
