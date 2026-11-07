"""X-ray gate: refuse images that are not chest X-rays (selfies, pets, documents, blanks...).

Two layers of checks:
  1. Cheap image heuristics: too small, blank/uniform, clearly colourful.
  2. Out-of-distribution score: the 2048-d (ResNet50) pooled layer4 features of the
     trained network are compared with the training X-rays using a class-conditional
     Mahalanobis distance with a shared (Ledoit-Wolf) covariance (Lee et al., 2018).
     The cut-off is set from VALIDATION X-rays only.

Fit + validate:  python -m ml.xray_gate
Outputs: models/xray_gate.npz (means, precision, threshold), models/xray_gate_metrics.json
"""
from __future__ import annotations

import json

import numpy as np
from PIL import Image

from ml.common import MODELS_DIR, to_gray_uint8

MIN_SIDE = 64          # px; anything smaller cannot be a usable radiograph
MIN_STD = 8.0          # gray-level std; below this the image is essentially blank
MAX_MEAN_SAT = 0.12    # mean HSV saturation of non-dark pixels; X-rays are ~0
MAX_SAT_FRAC = 0.05    # fraction of strongly coloured pixels (saturation > 0.25)
THRESH_QUANTILE = 0.995
THRESH_MARGIN = 1.15   # threshold = margin x 99.5th percentile of validation distances


def heuristics(img: Image.Image) -> tuple[bool, str, dict]:
    """Fast checks that need no neural network."""
    w, h = img.size
    if min(w, h) < MIN_SIDE:
        return False, f"Image is too small ({w}x{h} px). Please upload the full X-ray.", {}
    gray = to_gray_uint8(img)
    std = float(gray.std())
    if std < MIN_STD:
        return False, "Image looks blank or uniform, not an X-ray.", {"gray_std": std}
    stats = {"gray_std": std, "mean_saturation": 0.0, "colour_fraction": 0.0}
    if img.mode not in ("L", "LA", "1", "I", "I;16", "I;16B", "I;16L", "I;16N", "F"):
        rgb = img.convert("RGB")
        rgb.thumbnail((256, 256))
        a = np.asarray(rgb, dtype=np.float32)
        mx, mn = a.max(2), a.min(2)
        lit = mx > 25                                    # ignore near-black pixels
        sat = np.where(lit, (mx - mn) / np.maximum(mx, 1), 0)
        stats["mean_saturation"] = float(sat[lit].mean()) if lit.any() else 0.0
        stats["colour_fraction"] = float((sat > 0.25).mean())
        if stats["mean_saturation"] > MAX_MEAN_SAT or stats["colour_fraction"] > MAX_SAT_FRAC:
            return False, "Image is in colour; chest X-rays are grayscale.", stats
    return True, "ok", stats


class XrayGate:
    """Mahalanobis OOD detector on network features (parameters from models/xray_gate.npz)."""

    def __init__(self, path=MODELS_DIR / "xray_gate.npz"):
        p = np.load(path)
        self.means, self.precision, self.threshold = p["means"], p["precision"], float(p["threshold"])
        self.member = str(p["member"])

    def distance(self, feats: np.ndarray) -> np.ndarray:
        """Min over classes of sqrt(Mahalanobis distance); feats: (N, D)."""
        feats = np.atleast_2d(feats).astype(np.float64)
        d = [np.einsum("nd,de,ne->n", feats - m, self.precision, feats - m) for m in self.means]
        return np.sqrt(np.maximum(np.min(d, axis=0), 0))

    def score(self, dist: float) -> float:
        """Map distance to 0..1 (1 = typical chest X-ray, 0.5 exactly at the cut-off)."""
        return float(1 / (1 + (dist / self.threshold) ** 4))

    def decide(self, img: Image.Image, feats: np.ndarray | None) -> dict:
        ok, reason, stats = heuristics(img)
        if not ok:
            return {"is_xray": False, "score": 0.0, "reason": reason}
        dist = float(self.distance(feats)[0])
        s = self.score(dist)
        if dist > self.threshold:
            return {"is_xray": False, "score": s,
                    "reason": "This does not look like a chest X-ray (it is unlike the X-rays the model was trained on)."}
        return {"is_xray": True, "score": s, "reason": "Looks like a chest X-ray."}


# ----------------------------------------------------------------------------- fitting

def non_xray_images() -> dict[str, Image.Image]:
    """Validation set of things that are NOT chest X-rays (all free to use)."""
    from PIL import ImageDraw
    from skimage import data

    imgs = {}
    for n in ["astronaut", "chelsea", "coffee", "rocket", "text", "camera", "moon", "page", "coins",
              "horse", "clock", "hubble_deep_field", "immunohistochemistry", "retina", "brick",
              "grass", "gravel", "cell", "checkerboard", "cat", "colorwheel", "logo", "motorcycle_left"]:
        try:
            arr = getattr(data, n)()
            if arr.dtype == bool:
                arr = arr.astype(np.uint8) * 255
            imgs[f"skimage_{n}"] = Image.fromarray(arr)
        except Exception as e:  # some images need an optional download
            print("skip", n, e)
    rng = np.random.default_rng(0)
    imgs["noise_gray"] = Image.fromarray(rng.integers(0, 256, (512, 512), dtype=np.uint8))
    imgs["noise_rgb"] = Image.fromarray(rng.integers(0, 256, (512, 512, 3), dtype=np.uint8))
    for c in [(0, 0, 0), (255, 255, 255), (128, 128, 128), (220, 30, 30), (30, 90, 200)]:
        imgs[f"plain_{c}"] = Image.new("RGB", (400, 300), c)
    imgs["gradient"] = Image.fromarray(np.tile(np.linspace(0, 255, 512, dtype=np.uint8), (512, 1)))
    for k in range(3):  # synthetic documents: black text on white paper
        doc = Image.new("L", (850, 1100), 255)
        d = ImageDraw.Draw(doc)
        for i in range(40):
            words = " ".join("".join(chr(97 + rng.integers(26)) for _ in range(rng.integers(2, 9)))
                             for _ in range(10))
            d.text((60, 40 + i * 25 + k * 3), words, fill=0)
        if k == 2:
            doc = Image.fromarray(255 - np.asarray(doc))  # inverted (white text on black)
        imgs[f"document_{k}"] = doc
    return imgs


def main() -> None:
    from sklearn.covariance import LedoitWolf
    from torch.utils.data import DataLoader

    from ml.datasets import XrayDataset, eval_transform
    from ml.inference import PneumoniaModel

    pm = PneumoniaModel(MODELS_DIR, gate=False)       # loads the shipped ensemble weights
    member = pm.members[0]
    print("gate feature extractor:", member["name"])

    def feats_for(split):
        dl = DataLoader(XrayDataset(split, eval_transform(member["res"])), batch_size=32, num_workers=4)
        out, ys = [], []
        for x, y in dl:
            out.append(pm.features(x))
            ys.append(y.numpy())
        return np.concatenate(out), np.concatenate(ys)

    ftr, ytr = feats_for("train")
    lw = LedoitWolf().fit(np.concatenate([ftr[ytr == c] - ftr[ytr == c].mean(0) for c in (0, 1)]))
    means = np.stack([ftr[ytr == c].mean(0) for c in (0, 1)])
    np.savez(MODELS_DIR / "xray_gate.npz", means=means, precision=lw.precision_.astype(np.float32),
             threshold=1.0, member=member["name"])
    gate = XrayGate()
    dval = gate.distance(feats_for("val")[0])
    thr = float(np.quantile(dval, THRESH_QUANTILE) * THRESH_MARGIN)
    np.savez(MODELS_DIR / "xray_gate.npz", means=means, precision=lw.precision_.astype(np.float32),
             threshold=thr, member=member["name"])
    pm.gate = XrayGate()

    # Validate end-to-end with check_image() on real files (test X-rays) and non-X-rays.
    import pandas as pd

    from ml.common import RAW_DIR, SPLIT_CSV
    df = pd.read_csv(SPLIT_CSV)
    test_rows = df[df.split == "test"]
    acc = [pm.check_image(Image.open(RAW_DIR / r)) for r in test_rows.raw_path]
    rejected_test = [r for r, c in zip(test_rows.raw_path, acc) if not c["is_xray"]]
    imgs = non_xray_images()
    nx = {k: pm.check_image(v) for k, v in imgs.items()}
    wrongly_accepted = [k for k, c in nx.items() if c["is_xray"]]
    # Harder variant: grayscale copies of the colour images, so only the feature-distance test can catch them.
    gray = {k: pm.check_image(v.convert("L")) for k, v in imgs.items() if v.mode != "L"}
    gray_accepted = [k for k, c in gray.items() if c["is_xray"]]
    res = {"feature_member": member["name"], "threshold_distance": thr,
           "threshold_rule": f"{THRESH_MARGIN} x {THRESH_QUANTILE:.1%} quantile of validation distances",
           "val_distance_quantiles": {q: float(np.quantile(dval, q)) for q in (0.5, 0.9, 0.99, 0.995, 1.0)},
           "test_xrays_accepted": f"{len(acc) - len(rejected_test)}/{len(acc)}",
           "test_xray_accept_rate": (len(acc) - len(rejected_test)) / len(acc),
           "test_xrays_rejected": rejected_test,
           "non_xray_rejected": f"{len(nx) - len(wrongly_accepted)}/{len(nx)}",
           "non_xray_wrongly_accepted": wrongly_accepted,
           "grayscale_copies_of_colour_images_rejected": f"{len(gray) - len(gray_accepted)}/{len(gray)}",
           "grayscale_copies_wrongly_accepted": gray_accepted,
           "non_xray_details": {k: {"is_xray": c["is_xray"], "score": round(c["score"], 4), "reason": c["reason"]}
                                for k, c in nx.items()}}
    (MODELS_DIR / "xray_gate_metrics.json").write_text(json.dumps(res, indent=2))
    mpath = MODELS_DIR / "metrics.json"
    if mpath.exists():
        m = json.loads(mpath.read_text())
        m["xray_gate"] = res
        mpath.write_text(json.dumps(m, indent=2))
    print(json.dumps({k: v for k, v in res.items() if k != "non_xray_details"}, indent=2))


if __name__ == "__main__":
    main()
