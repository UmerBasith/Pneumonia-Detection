"""Step 3: evaluate trained ResNets, build the ensemble, calibrate and pick the threshold.

Everything that is *chosen* (temperature, decision threshold) is fitted on the
VALIDATION split. The test split is only scored, and every test scoring is appended
to logs/test_evaluations.jsonl so the report can list all of them honestly.

  python -m ml.evaluate --members r50_384_s1 r34_320_s1 --val-only   # validation only
  python -m ml.evaluate --members r50_384_s1 r34_320_s1 --export     # final: writes models/
"""
from __future__ import annotations

import argparse
import json
import shutil
import time

import numpy as np
import torch
from scipy.optimize import minimize_scalar
from torch.utils.data import DataLoader

from ml.common import CKPT_DIR, LOGS_DIR, MODELS_DIR, SPLIT_CSV, binary_metrics, build_model
from ml.datasets import XrayDataset, eval_transform


def load_member(name: str, device) -> tuple[torch.nn.Module, dict]:
    """Load a checkpoint, rounding weights through fp16 exactly as they are shipped."""
    ckpt = torch.load(CKPT_DIR / name / "best.pt", map_location="cpu", weights_only=False)
    model = build_model(ckpt["arch"], pretrained=False)
    sd = {k: v.half().float() if v.is_floating_point() else v for k, v in ckpt["state_dict"].items()}
    model.load_state_dict(sd)
    return model.to(device).eval(), ckpt


@torch.no_grad()
def margins(model, split: str, res: int, device, tta: bool) -> tuple[np.ndarray, np.ndarray]:
    """Logit margin z = logit(PNEUMONIA) - logit(NORMAL); TTA averages original + mirrored."""
    dl = DataLoader(XrayDataset(split, eval_transform(res)), batch_size=32, num_workers=4)
    zs, ys = [], []
    for x, y in dl:
        x = x.to(device)
        with torch.autocast("cuda", dtype=torch.float16, enabled=device.type == "cuda"):
            views = [x, torch.flip(x, dims=[3])] if tta else [x]
            z = torch.stack([(lg[:, 1] - lg[:, 0]).float() for lg in map(model, views)]).mean(0)
        zs.append(z.cpu())
        ys.append(y)
    return torch.cat(zs).numpy(), torch.cat(ys).numpy()


def fit_temperature(z: np.ndarray, y: np.ndarray) -> float:
    """Temperature T minimising validation negative log-likelihood of sigmoid(z / T)."""
    def nll(log_t):
        p = 1 / (1 + np.exp(-z / np.exp(log_t)))
        p = np.clip(p, 1e-7, 1 - 1e-7)
        return -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
    return float(np.exp(minimize_scalar(nll, bounds=(-3, 3), method="bounded").x))


def pick_threshold(prob: np.ndarray, y: np.ndarray) -> float:
    """Threshold maximising Youden's J (= balanced accuracy) on validation.

    Ties are common (a whole interval of thresholds gives the same J), so we take
    the middle of the best interval, measured in logit space.
    """
    cands = np.unique(np.concatenate([prob, [0.0, 1.0]]))
    mids = (cands[:-1] + cands[1:]) / 2
    j = np.array([np.mean(prob[y == 1] >= t) + np.mean(prob[y == 0] < t) - 1 for t in mids])
    best = mids[np.isclose(j, j.max())]
    logit = np.log(np.clip(best, 1e-6, 1 - 1e-6) / (1 - np.clip(best, 1e-6, 1 - 1e-6)))
    return float(1 / (1 + np.exp(-(logit.min() + logit.max()) / 2)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--members", nargs="+", required=True)
    ap.add_argument("--no-tta", action="store_true")
    ap.add_argument("--val-only", action="store_true", help="never touch the test split")
    ap.add_argument("--export", action="store_true", help="write final models/ files")
    ap.add_argument("--note", default="", help="free-text note stored with the test log entry")
    a = ap.parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tta = not a.no_tta
    splits = ["val"] if a.val_only else ["val", "test"]

    z, y, ckpts, t0 = {}, {}, {}, time.time()
    for name in a.members:
        model, ckpt = load_member(name, device)
        ckpts[name] = ckpt
        for s in splits:
            z[(name, s)], y[s] = margins(model, s, ckpt["res"], device, tta)
            if s == "val":  # cached for threshold analysis / figures (validation only)
                np.savez(CKPT_DIR / name / f"val_margins{'_tta' if tta else ''}.npz", z=z[(name, s)], y=y[s])
        del model
        torch.cuda.empty_cache()

    results = {}
    for name in a.members + (["ensemble"] if len(a.members) > 1 else []):
        pick = a.members if name == "ensemble" else [name]
        zv = np.mean([z[(m, "val")] for m in pick], axis=0)
        t = fit_temperature(zv, y["val"])
        pv = 1 / (1 + np.exp(-zv / t))
        thr = pick_threshold(pv, y["val"])
        r = {"temperature": t, "threshold": thr, "val": binary_metrics(y["val"], pv, thr)}
        if not a.val_only:
            zt = np.mean([z[(m, "test")] for m in pick], axis=0)
            pt = 1 / (1 + np.exp(-zt / t))
            r["test"] = binary_metrics(y["test"], pt, thr)
            r["_test_prob"] = pt
        r["_val_prob"] = pv
        results[name] = r
        line = f"{name:>14}  T={t:.3f} thr={thr:.3f}  VAL acc {r['val']['accuracy']:.4f} " \
               f"bal {r['val']['balanced_accuracy']:.4f} auc {r['val']['roc_auc']:.4f}"
        if "test" in r:
            m = r["test"]
            line += f" | TEST acc {m['accuracy']:.4f} sens {m['recall_sensitivity']:.4f} " \
                    f"spec {m['specificity']:.4f} auc {m['roc_auc']:.4f}"
        print(line)

    if not a.val_only:  # honesty log: every time the test split is scored
        LOGS_DIR.mkdir(exist_ok=True)
        with open(LOGS_DIR / "test_evaluations.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"time": time.strftime("%Y-%m-%d %H:%M:%S"), "members": a.members,
                                "tta": tta, "note": a.note,
                                "results": {k: {"threshold": v["threshold"], "test": v["test"]}
                                            for k, v in results.items()}}) + "\n")

    if a.export:
        export(a.members, ckpts, results, y, tta)
    print(f"done in {time.time() - t0:.0f}s")


def export(members, ckpts, results, y, tta) -> None:
    """Ship fp16 weights + ensemble.json + metrics.json + predictions for the figures."""
    final = results["ensemble" if len(members) > 1 else members[0]]
    thr = final["threshold"]
    ens = {"members": [], "temperature": final["temperature"], "threshold": thr, "tta_hflip": tta,
           "combine": "mean of member logit margins (PNEUMONIA - NORMAL), then sigmoid(z / temperature)",
           "risk_bands": {"Low": [0.0, thr / 2], "Moderate": [thr / 2, (1 + thr) / 2],
                          "High": [(1 + thr) / 2, 1.0]}}
    per_model, pred_dump = {}, {"y_val": y["val"], "y_test": y["test"]}
    for name in members:
        ck = ckpts[name]
        sd = {k: v.half() if v.is_floating_point() else v for k, v in ck["state_dict"].items()}
        torch.save({"arch": ck["arch"], "res": ck["res"], "state_dict": sd}, MODELS_DIR / f"{name}.pt")
        cfg = json.loads((CKPT_DIR / name / "config.json").read_text())
        summ = json.loads((CKPT_DIR / name / "summary.json").read_text())
        ens["members"].append({"name": name, "file": f"{name}.pt", "arch": ck["arch"], "res": ck["res"]})
        per_model[name] = {k: results[name][k] for k in ("temperature", "threshold", "val", "test")}
        per_model[name].update(hyperparameters=cfg, training=summ)
        pred_dump[f"{name}_val"], pred_dump[f"{name}_test"] = results[name]["_val_prob"], results[name]["_test_prob"]
        shutil.copy(CKPT_DIR / name / "history.json", MODELS_DIR / f"{name}_history.json")
    pred_dump["ensemble_val"], pred_dump["ensemble_test"] = final["_val_prob"], final["_test_prob"]
    np.savez(CKPT_DIR / "final_preds.npz", **pred_dump)
    (MODELS_DIR / "ensemble.json").write_text(json.dumps(ens, indent=2))

    summary = json.loads((SPLIT_CSV.parent / "dataset_summary.json").read_text())
    metrics = {
        "model_version": "pneumoscan-resnet-ensemble-v1",
        "task": "binary classification of pediatric chest X-rays: NORMAL vs PNEUMONIA",
        "final": {"members": members, "tta_hflip": tta, "temperature": final["temperature"],
                  "threshold": thr, "threshold_rule": "maximise Youden's J on validation (middle of best interval)",
                  "risk_bands": ens["risk_bands"], "val": final["val"], "test": final["test"]},
        "per_model": per_model,
        "dataset": {"name": "Kermany et al. 2018, Chest X-Ray Images (Pneumonia), ChestXRay2017.zip",
                    "source": "https://data.mendeley.com/datasets/rscbjbr9sj/2",
                    "doi": "10.17632/rscbjbr9sj.2", "license": "CC BY 4.0",
                    "counts": summary["counts"], "patients": summary["patients"],
                    "split_method": "official test set held out; validation = patient-level stratified "
                                    "1/7 of official train (StratifiedGroupKFold, seed 42)",
                    "leakage_checks": summary["leakage_checks"]},
    }
    gate_file = MODELS_DIR / "xray_gate_metrics.json"
    if gate_file.exists():
        metrics["xray_gate"] = json.loads(gate_file.read_text())
    (MODELS_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print("exported to", MODELS_DIR)


if __name__ == "__main__":
    main()
