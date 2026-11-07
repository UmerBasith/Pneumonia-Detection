"""Step 6: copy demo images into sample_xrays/ (TEST split only) + non-X-ray examples.

Picks 6 NORMAL and 6 PNEUMONIA test X-rays that the final model classifies correctly
with a clear margin (representative, not borderline), and writes an answer key.
  python -m ml.make_samples
"""
from __future__ import annotations

import shutil

import numpy as np
import pandas as pd
from PIL import Image

from ml.common import CKPT_DIR, MODELS_DIR, RAW_DIR, ROOT, SPLIT_CSV
from ml.inference import PneumoniaModel

OUT = ROOT / "sample_xrays"


def main() -> None:
    df = pd.read_csv(SPLIT_CSV)
    te = df[df.split == "test"].reset_index(drop=True)
    prob = np.load(CKPT_DIR / "final_preds.npz")["ensemble_test"]
    model = PneumoniaModel(MODELS_DIR)
    thr = model.cfg["threshold"]
    OUT.mkdir(exist_ok=True)
    rows = []
    rng = np.random.default_rng(3)
    for label, correct in [("NORMAL", prob < thr * 0.5), ("PNEUMONIA", prob > (1 + thr) / 2)]:
        cand = te.index[(te.label == label) & correct].to_numpy()
        if label == "PNEUMONIA":  # show both bacterial and viral cases
            bac = [i for i in cand if "bacteria" in te.raw_path[i]]
            vir = [i for i in cand if "virus" in te.raw_path[i]]
            chosen = list(rng.choice(bac, 3, replace=False)) + list(rng.choice(vir, 3, replace=False))
        else:
            chosen = list(rng.choice(cand, 6, replace=False))
        for k, i in enumerate(chosen, 1):
            name = f"{label.lower()}_{k:02d}.jpeg"
            shutil.copy(RAW_DIR / te.raw_path[i], OUT / name)
            r = model.predict(Image.open(OUT / name), with_gradcam=False)
            rows.append({"filename": name, "true_label": label, "model_prediction": r["label"],
                         "prob_pneumonia": round(r["prob_pneumonia"], 4), "risk_level": r["risk_level"],
                         "source_file": te.raw_path[i]})
    pd.DataFrame(rows).to_csv(OUT / "answer_key.csv", index=False)
    print(pd.DataFrame(rows).to_string())

    from skimage import data
    nx = OUT / "not_xray"
    nx.mkdir(exist_ok=True)
    for n in ["astronaut", "chelsea", "coffee"]:
        Image.fromarray(getattr(data, n)()).save(nx / f"{n}.png")
        print(n, model.check_image(Image.open(nx / f"{n}.png")))


if __name__ == "__main__":
    main()
