"""Step 1: verify the dataset, make a patient-level validation split, and cache images.

Input : data/raw/chest_xray/{train,test}/{NORMAL,PNEUMONIA}/*.jpeg  (Kermany et al. 2018)
Output: data/splits.csv            one row per image: path, label, patient, split, sha1
        data/processed/...png      512x512 grayscale copies (fast to load during training)
        data/dataset_summary.json  counts + leakage checks (used by the report)

Run:  python -m ml.prepare_data
"""
from __future__ import annotations

import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
from PIL import Image
from sklearn.model_selection import StratifiedGroupKFold

from ml.common import CACHE_DIR, CLASSES, DATA_DIR, RAW_DIR, SPLIT_CSV, canonical_view

EXPECTED = {("train", "NORMAL"): 1349, ("train", "PNEUMONIA"): 3883,
            ("test", "NORMAL"): 234, ("test", "PNEUMONIA"): 390}
VAL_FOLDS = 7          # 1 of 7 folds -> ~14% of TRAIN becomes validation
SEED = 42


def patient_id(filename: str, label: str) -> str:
    """Patient identifier parsed from the file name.

    PNEUMONIA: person123_bacteria_456.jpeg -> P123
    NORMAL   : IM-0115-0001.jpeg / NORMAL2-IM-0115-0001.jpeg -> N0115
    (the NORMAL2- prefix is ignored on purpose: grouping more conservatively can only
    reduce leakage between train and validation, never add it).
    """
    if label == "PNEUMONIA":
        m = re.match(r"person(\d+)_", filename)
        return f"P{int(m.group(1))}"
    m = re.search(r"IM-(\d+)-", filename)
    return f"N{int(m.group(1))}"


def near_duplicate_corr(test_paths, other_paths) -> np.ndarray:
    """For each test image: highest Pearson correlation with any train/val image (64x64 thumbnails).
    Values >= 0.99 would indicate the same radiograph re-saved; independent chest X-rays stay below."""
    def thumbs(paths):
        a = np.stack([np.asarray(Image.open(CACHE_DIR / p).resize((64, 64), Image.Resampling.BILINEAR),
                                 dtype=np.float32).ravel() for p in paths])
        return (a - a.mean(1, keepdims=True)) / (a.std(1, keepdims=True) + 1e-6)
    a, b = thumbs(other_paths), thumbs(test_paths)
    return (b @ a.T / a.shape[1]).max(1)


def process(row: dict) -> dict:
    src = RAW_DIR / row["raw_path"]
    data = src.read_bytes()
    row["sha1"] = hashlib.sha1(data).hexdigest()
    with Image.open(src) as im:
        row["orig_w"], row["orig_h"], row["orig_mode"] = im.width, im.height, im.mode
        view = canonical_view(im)
    dst = CACHE_DIR / row["path"]
    dst.parent.mkdir(parents=True, exist_ok=True)
    view.save(dst, optimize=False)
    return row


def main() -> None:
    rows = []
    for split in ("train", "test"):
        for label in CLASSES:
            files = sorted((RAW_DIR / split / label).glob("*.jpeg"))
            assert len(files) == EXPECTED[(split, label)], (split, label, len(files))
            for f in files:
                rows.append({"raw_path": f"{split}/{label}/{f.name}",
                             "path": f"{split}/{label}/{f.stem}.png",
                             "label": label, "y": CLASSES.index(label),
                             "patient": patient_id(f.name, label), "split": split})
    print(f"Found {len(rows)} images; counts match the official release.")

    with ThreadPoolExecutor(max_workers=12) as pool:
        rows = list(pool.map(process, rows))
    df = pd.DataFrame(rows)

    # Patient-level, stratified validation split carved out of TRAIN only.
    train_idx = df.index[df.split == "train"]
    sgkf = StratifiedGroupKFold(n_splits=VAL_FOLDS, shuffle=True, random_state=SEED)
    _, val_pos = next(sgkf.split(train_idx, df.loc[train_idx, "y"], df.loc[train_idx, "patient"]))
    df.loc[train_idx[val_pos], "split"] = "val"

    # Leakage checks.
    tr, va, te = (df[df.split == s] for s in ("train", "val", "test"))
    checks = {
        "patients_train_and_val": len(set(tr.patient) & set(va.patient)),
        "patients_train_or_val_and_test": len(set(df[df.split != "test"].patient) & set(te.patient)),
        "exact_duplicate_files_test_vs_trainval": int(te.sha1.isin(df[df.split != "test"].sha1).sum()),
        "exact_duplicate_files_val_vs_train": int(va.sha1.isin(tr.sha1).sum()),
    }
    corr = near_duplicate_corr(list(te.path), list(df[df.split != "test"].path))
    checks["near_duplicates_test_vs_trainval_corr_ge_0.99"] = int((corr >= 0.99).sum())
    checks["max_thumbnail_corr_test_vs_trainval"] = round(float(corr.max()), 4)
    checks["note"] = ("patient numbers are assigned separately inside the official train and test folders, "
                      "so equal numbers across them are NOT the same patient (dataset authors: independent "
                      "patients); exact-hash and near-duplicate checks confirm no shared images")
    assert checks["patients_train_and_val"] == 0
    assert checks["exact_duplicate_files_test_vs_trainval"] == 0, "test image found in train!"

    counts = {s: {c: int(((df.split == s) & (df.label == c)).sum()) for c in CLASSES}
              for s in ("train", "val", "test")}
    patients = {s: int(df[df.split == s].patient.nunique()) for s in ("train", "val", "test")}
    summary = {"counts": counts, "patients": patients, "leakage_checks": checks,
               "val_fraction_of_official_train": round(len(va) / (len(tr) + len(va)), 4),
               "original_size_px": {"median_w": int(df.orig_w.median()), "median_h": int(df.orig_h.median()),
                                    "min_w": int(df.orig_w.min()), "max_w": int(df.orig_w.max())},
               "original_modes": df.orig_mode.value_counts().to_dict()}
    df.drop(columns=["y"]).to_csv(SPLIT_CSV, index=False)
    (DATA_DIR / "dataset_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
