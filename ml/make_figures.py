"""Step 5: all report figures (PNG, 250 dpi, white background) -> docs/figures/.

  python -m ml.make_figures            # everything
  python -m ml.make_figures arch       # only the two diagrams (no model needed)
"""
from __future__ import annotations

import json
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402
from PIL import Image  # noqa: E402

from ml.common import CACHE_DIR, CKPT_DIR, DATA_DIR, FIG_DIR, MODELS_DIR, RAW_DIR, SPLIT_CSV  # noqa: E402

DPI = 250
BLUE, ORANGE, GREEN, RED, GREY = "#2563eb", "#ea580c", "#16a34a", "#dc2626", "#6b7280"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.25,
                     "figure.facecolor": "white", "savefig.facecolor": "white"})


def save(fig, name: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / name, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print("wrote", FIG_DIR / name)


def ensemble_cfg() -> dict:
    p = MODELS_DIR / "ensemble.json"
    return json.loads(p.read_text()) if p.exists() else \
        {"members": [{"name": "resnet50", "arch": "resnet50", "res": 384}], "threshold": 0.5}


# ----------------------------------------------------------------------------- data figures

def class_distribution() -> None:
    s = json.loads((DATA_DIR / "dataset_summary.json").read_text())["counts"]
    splits = ["train", "val", "test"]
    fig, ax = plt.subplots(figsize=(7, 4.2))
    x = np.arange(3)
    for i, (c, col) in enumerate([("NORMAL", BLUE), ("PNEUMONIA", ORANGE)]):
        v = [s[sp][c] for sp in splits]
        bars = ax.bar(x + (i - 0.5) * 0.38, v, 0.38, label=c, color=col)
        ax.bar_label(bars, padding=2, fontsize=10)
    ax.set_xticks(x, ["Train", "Validation", "Test (official)"])
    ax.set_ylabel("Number of images")
    ax.set_title("Class distribution per split")
    ax.legend(frameon=False)
    ax.grid(axis="x", visible=False)
    save(fig, "class_distribution.png")


def sample_grid() -> None:
    df = pd.read_csv(SPLIT_CSV)
    tr = df[df.split == "train"]
    fig, axes = plt.subplots(2, 4, figsize=(12, 6.4))
    for r, lab in enumerate(["NORMAL", "PNEUMONIA"]):
        rows = tr[tr.label == lab].sample(4, random_state=7)
        for c, (_, row) in enumerate(rows.iterrows()):
            ax = axes[r, c]
            ax.imshow(Image.open(RAW_DIR / row.raw_path).convert("L"), cmap="gray")
            ax.set_xticks([]), ax.set_yticks([]), ax.grid(False)
            kind = "" if lab == "NORMAL" else (" (bacterial)" if "bacteria" in row.raw_path else " (viral)")
            ax.set_title(f"{lab}{kind}", fontsize=11, color=BLUE if lab == "NORMAL" else ORANGE)
    fig.suptitle("Sample chest X-rays from the training set (Kermany et al., 2018)", fontsize=13)
    fig.tight_layout()
    save(fig, "sample_images.png")


# ----------------------------------------------------------------------------- result figures

def training_curves() -> None:
    for m in ensemble_cfg()["members"]:
        h = json.loads((MODELS_DIR / f"{m['name']}_history.json").read_text())
        ep = [r["epoch"] for r in h]
        best = max(h, key=lambda r: (r["val_auc"], -r["val_loss"]))["epoch"]
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.2))
        a1.plot(ep, [r["train_acc"] for r in h], "-o", ms=3, color=BLUE, label="Train")
        a1.plot(ep, [r["val_acc"] for r in h], "-o", ms=3, color=ORANGE, label="Validation")
        a1.set_title("Accuracy"), a1.set_xlabel("Epoch"), a1.set_ylabel("Accuracy")
        a2.plot(ep, [r["train_loss"] for r in h], "-o", ms=3, color=BLUE, label="Train")
        a2.plot(ep, [r["val_loss"] for r in h], "-o", ms=3, color=ORANGE, label="Validation")
        a2.set_title("Loss (weighted cross-entropy, label smoothing)"), a2.set_xlabel("Epoch")
        for a in (a1, a2):
            a.axvline(best, color=GREY, ls="--", lw=1)
            a.legend(frameon=False)
        a1.text(best, a1.get_ylim()[0], f" best epoch {best}", color=GREY, va="bottom", fontsize=9)
        fig.suptitle(f"Training curves: {m['arch']} at {m['res']}x{m['res']} ({m['name']})", fontsize=13)
        fig.tight_layout()
        save(fig, f"training_curves_{m['name']}.png")


def result_figures() -> None:
    from sklearn.metrics import precision_recall_curve, roc_curve, auc, average_precision_score

    cfg, p = ensemble_cfg(), np.load(CKPT_DIR / "final_preds.npz")
    y, pe, thr = p["y_test"], p["ensemble_test"], cfg["threshold"]
    pred = (pe >= thr).astype(int)
    cm = np.array([[np.sum((y == i) & (pred == j)) for j in (0, 1)] for i in (0, 1)])

    fig, ax = plt.subplots(figsize=(5.2, 4.6))
    ax.imshow(cm, cmap="Blues")
    ax.grid(False)
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{cm[i, j]}\n({cm[i, j] / cm[i].sum():.1%})", ha="center", va="center",
                    fontsize=13, color="white" if cm[i, j] > cm.max() / 2 else "black")
    ax.set_xticks([0, 1], ["NORMAL", "PNEUMONIA"]), ax.set_yticks([0, 1], ["NORMAL", "PNEUMONIA"])
    ax.set_xlabel("Predicted"), ax.set_ylabel("True")
    ax.set_title(f"Confusion matrix, test set (n={len(y)})\naccuracy {np.mean(pred == y):.2%}, threshold {thr:.3f}")
    save(fig, "confusion_matrix_test.png")

    names = [m["name"] for m in cfg["members"]]
    curves = [("Ensemble", pe, BLUE, 2.4)] + [(n, p[f"{n}_test"], c, 1.2) for n, c in zip(names, [ORANGE, GREEN, RED])]
    fig, ax = plt.subplots(figsize=(5.6, 5))
    for lab, pr, col, lw in curves:
        fpr, tpr, _ = roc_curve(y, pr)
        ax.plot(fpr, tpr, color=col, lw=lw, label=f"{lab} (AUC {auc(fpr, tpr):.3f})")
    ax.plot([0, 1], [0, 1], ls=":", color=GREY)
    ax.scatter([1 - np.mean(pred[y == 0] == 0)], [np.mean(pred[y == 1] == 1)], color="black", zorder=5,
               label="Operating point (val-chosen threshold)")
    ax.set_xlabel("False positive rate (1 - specificity)"), ax.set_ylabel("True positive rate (sensitivity)")
    ax.set_title("ROC curve, test set"), ax.legend(frameon=False, fontsize=9, loc="lower right")
    save(fig, "roc_curve_test.png")

    fig, ax = plt.subplots(figsize=(5.6, 5))
    for lab, pr, col, lw in curves:
        prec, rec, _ = precision_recall_curve(y, pr)
        ax.plot(rec, prec, color=col, lw=lw, label=f"{lab} (AP {average_precision_score(y, pr):.3f})")
    ax.axhline(y.mean(), ls=":", color=GREY, label=f"Chance ({y.mean():.2f})")
    ax.set_xlabel("Recall (sensitivity)"), ax.set_ylabel("Precision")
    ax.set_ylim(0.5, 1.01), ax.set_title("Precision-recall curve, test set")
    ax.legend(frameon=False, fontsize=9, loc="lower left")
    save(fig, "pr_curve_test.png")

    fig, ax = plt.subplots(figsize=(7, 4))
    bins = np.linspace(0, 1, 26)
    ax.hist(pe[y == 0], bins, color=BLUE, alpha=0.7, label="True NORMAL")
    ax.hist(pe[y == 1], bins, color=ORANGE, alpha=0.7, label="True PNEUMONIA")
    ax.axvline(thr, color="black", ls="--", label=f"Threshold {thr:.3f} (from validation)")
    ax.set_xlabel("Calibrated probability of pneumonia"), ax.set_ylabel("Test images")
    ax.set_title("Ensemble output distribution, test set"), ax.legend(frameon=False)
    save(fig, "probability_histogram_test.png")


def gradcam_grid() -> None:
    import base64
    import io

    from ml.inference import PneumoniaModel

    cfg, p = ensemble_cfg(), np.load(CKPT_DIR / "final_preds.npz")
    df = pd.read_csv(SPLIT_CSV)
    te = df[df.split == "test"].reset_index(drop=True)
    y, pe, thr = p["y_test"], p["ensemble_test"], cfg["threshold"]
    order = np.argsort(pe)
    picks = [("Correct PNEUMONIA", i) for i in order[::-1][[5, 40]]]
    picks += [("Correct NORMAL", i) for i in order[[5, 40]]]
    fp = [i for i in order[::-1] if y[i] == 0 and pe[i] >= thr]
    fn = [i for i in order if y[i] == 1 and pe[i] < thr]
    picks += [("Error: false positive", fp[len(fp) // 2])] if fp else []
    picks += [("Error: false negative", fn[len(fn) // 2])] if fn else []
    model = PneumoniaModel(MODELS_DIR, gate=False)
    fig, axes = plt.subplots(len(picks) // 2, 4, figsize=(13, 3.4 * (len(picks) // 2)))
    for k, (title, i) in enumerate(picks):
        img = Image.open(RAW_DIR / te.raw_path[i])
        r = model.predict(img)
        dec = lambda s: Image.open(io.BytesIO(base64.b64decode(s)))  # noqa: E731
        a, b = axes.flat[2 * k], axes.flat[2 * k + 1]
        a.imshow(dec(r["input_png"]), cmap="gray"), b.imshow(dec(r["gradcam_overlay_png"]))
        for ax in (a, b):
            ax.set_xticks([]), ax.set_yticks([]), ax.grid(False)
        a.set_title(f"{title}\ntrue {te.label[i]}", fontsize=10)
        b.set_title(f"Grad-CAM: predicted {r['label']}\np(pneumonia) = {r['prob_pneumonia']:.2f}", fontsize=10)
    fig.suptitle("Grad-CAM explanations on test X-rays (red = regions driving the prediction)", fontsize=13)
    fig.tight_layout()
    save(fig, "gradcam_examples.png")


# ----------------------------------------------------------------------------- diagrams

def _box(ax, x, y, w, h, text, fc, ec=None, fs=9.5, tc="black", bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                                fc=fc, ec=ec or fc, lw=1.4))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc,
            fontweight="bold" if bold else "normal", linespacing=1.35)


def _arrow(ax, p, q, color="#374151", style="-|>", rad=0.0, lw=1.6):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=14, color=color, lw=lw,
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=2, shrinkB=2))


def architecture_diagram() -> None:
    cfg = ensemble_cfg()
    res = cfg["members"][0]["res"]
    fig, ax = plt.subplots(figsize=(18, 8.4))
    ax.set_xlim(0, 36), ax.set_ylim(0, 17), ax.axis("off")
    ax.text(18, 16.4, "PneumoScan AI: ResNet50 pipeline for pneumonia detection", ha="center",
            fontsize=17, fontweight="bold")

    # Row 1: input -> preprocessing -> backbone (block height shrinks with spatial size).
    yc = 11.0
    _box(ax, 0.3, yc - 1.6, 3.0, 3.2, "Input\nchest X-ray\n\nany size / mode\nJPG, PNG, DICOM", "#f3f4f6", "#9ca3af")
    _box(ax, 4.0, yc - 1.6, 3.4, 3.2, "Pre-processing\n\ngrayscale (8-bit)\nresize to\n"
         f"{res}x{res}\ngray -> 3 channels\nImageNet normalise", "#e0e7ff", "#818cf8", fs=8.8)
    stages = [("conv1\n7x7, 64, /2\nBN, ReLU", res // 2, 64, "#dbeafe"),
              ("max-pool\n3x3, /2", res // 4, 64, "#dbeafe"),
              ("layer1\n3 x bottleneck", res // 4, 256, "#bfdbfe"),
              ("layer2\n4 x bottleneck", res // 8, 512, "#93c5fd"),
              ("layer3\n6 x bottleneck", res // 16, 1024, "#60a5fa"),
              ("layer4\n3 x bottleneck", res // 32, 2048, "#3b82f6")]
    x = 8.1
    prev = (7.4, yc)
    _arrow(ax, (3.3, yc), (4.0, yc))
    for name, s, ch, col in stages:
        h = 1.6 + 3.2 * (s / (res // 2))
        w = 2.3
        _box(ax, x, yc - h / 2, w, h, name, col, fs=9, tc="white" if ch >= 1024 else "black", bold=False)
        ax.text(x + w / 2, yc - h / 2 - 0.45, f"{s}x{s}x{ch}", ha="center", fontsize=8.6, color="#1f2937")
        _arrow(ax, prev, (x, yc))
        prev, x = (x + w, yc), x + w + 0.55
    layer4_x = x - 0.55 - 2.3 / 2
    _box(ax, x, yc - 1.0, 2.2, 2.0, "Global\naverage pool\n2048", "#1d4ed8", fs=9, tc="white")
    _arrow(ax, prev, (x, yc))
    _box(ax, x + 2.75, yc - 1.0, 2.4, 2.0, "Dropout 0.2\nFC 2048 -> 2\n(NORMAL,\nPNEUMONIA)", "#1e3a8a", fs=8.8, tc="white")
    _arrow(ax, (x + 2.2, yc), (x + 2.75, yc))
    ax.text(21.6, 14.7, "ResNet50 backbone (ImageNet-pretrained, fine-tuned end-to-end)", ha="center",
            fontsize=11, color="#1e3a8a", style="italic")
    ax.add_patch(FancyBboxPatch((7.9, 7.2), 27.8, 7.0, boxstyle="round,pad=0.05,rounding_size=0.3",
                                fc="none", ec="#93c5fd", lw=1.2, ls="--"))

    # Row 2: ensemble, calibration, decision, explanation.
    y2 = 3.6
    names = "\n".join(f"{m['arch'].replace('resnet', 'ResNet')} @ {m['res']}x{m['res']}" for m in cfg["members"])
    _box(ax, 0.3, y2 - 1.5, 6.6, 3.0, f"Ensemble of {len(cfg['members'])} ResNet{'s' if len(cfg['members']) > 1 else ''}\n{names}\n"
         "TTA: original + mirrored image", "#fef3c7", "#f59e0b", fs=9)
    _box(ax, 7.8, y2 - 1.5, 5.4, 3.0, "Combine\n\nmean logit margin\nz = logit(P) - logit(N)\n"
         "averaged over models + views", "#fde68a", "#f59e0b", fs=9)
    _box(ax, 14.1, y2 - 1.5, 4.9, 3.0, "Calibrate\n\np = sigmoid(z / T)\n"
         f"temperature T = {cfg.get('temperature', 1):.2f}\n(fitted on validation)", "#fde68a", "#f59e0b", fs=9)
    _box(ax, 19.9, y2 - 1.5, 5.6, 3.0, "Decision\n\nPNEUMONIA if p >= "
         f"{cfg['threshold']:.3f}\n(threshold chosen on validation)\nrisk: Low / Moderate / High", "#dcfce7", "#22c55e", fs=9)
    _box(ax, 26.6, y2 - 1.5, 4.0, 3.0, "Output\n\nlabel\nprobability\nrisk level", "#bbf7d0", "#16a34a", fs=9.5, bold=False)
    _box(ax, 31.6, y2 - 1.5, 4.1, 3.0, "Grad-CAM\n\nheatmap from layer4\naveraged over\nensemble members",
         "#fee2e2", "#ef4444", fs=9)
    for a_, b_ in [(6.9, 7.8), (13.2, 14.1), (19.0, 19.9), (25.5, 26.6)]:
        _arrow(ax, (a_, y2), (b_, y2))
    # Orthogonal connectors: logits -> ensemble (grey) and layer4 -> Grad-CAM (red, bridged).
    fc_x, l4_bottom, y_log, y_cam = x + 3.95, yc - (1.6 + 3.2 * (res // 32) / (res // 2)) / 2 - 0.65, 6.0, 6.6
    ax.plot([fc_x, fc_x, 3.6], [yc - 1.0, y_log, y_log], color=GREY, lw=1.6, zorder=1)
    _arrow(ax, (3.6, y_log + 0.02), (3.6, y2 + 1.5), color=GREY)
    ax.text(18.5, y_log - 0.45, "class scores (logits) of every ensemble member", color=GREY, fontsize=9, ha="center")
    ax.plot([layer4_x, layer4_x, 33.6], [l4_bottom, y_cam, y_cam], color=RED, lw=1.4, zorder=3)
    ax.add_patch(plt.Rectangle((33.6 - 0.18, y_log - 0.14), 0.36, 0.28, fc="white", ec="none", zorder=2))
    _arrow(ax, (33.6, y_cam + 0.02), (33.6, y2 + 1.5), color=RED, lw=1.4)
    ax.text((layer4_x + 33.6) / 2, y_cam + 0.2, "layer4 activations + gradients", color=RED, fontsize=9, ha="center")
    _arrow(ax, (31.6, y2), (30.6, y2), color=RED)
    if any(m["arch"] != "resnet50" for m in cfg["members"]):
        ax.text(18, 0.9, "Output sizes shown for ResNet50 at the first member's input size. ResNet18/34 members use "
                "basic blocks (two 3x3 convs) and end with 512 channels instead of 2048.",
                ha="center", fontsize=9, color="#374151", style="italic")
    save(fig, "architecture_diagram.png")


def residual_block_diagram() -> None:
    fig, ax = plt.subplots(figsize=(7.5, 9.6))
    ax.set_xlim(0, 10), ax.set_ylim(0, 13), ax.axis("off")
    ax.text(5, 12.5, "ResNet bottleneck residual block", ha="center", fontsize=15, fontweight="bold")
    steps = [("Input x   (H x W x 256)", "#f3f4f6", 11.0),
             ("1x1 conv, 64   (reduce channels)", "#dbeafe", 9.6),
             ("Batch norm + ReLU", "#eef2ff", 8.6),
             ("3x3 conv, 64   (spatial features)", "#93c5fd", 7.6),
             ("Batch norm + ReLU", "#eef2ff", 6.6),
             ("1x1 conv, 256   (restore channels)", "#60a5fa", 5.6),
             ("Batch norm", "#eef2ff", 4.6)]
    for i, (t, c, y) in enumerate(steps):
        _box(ax, 1.4, y - 0.36, 5.2, 0.72, t, c, "#94a3b8" if c == "#f3f4f6" else c, fs=10.5)
        if i:
            _arrow(ax, (4.0, steps[i - 1][2] - 0.38), (4.0, y + 0.38))
    ax.add_patch(plt.Circle((4.0, 3.3), 0.42, fc="white", ec="#111827", lw=1.6))
    ax.text(4.0, 3.3, "+", ha="center", va="center", fontsize=20)
    _arrow(ax, (4.0, 4.6 - 0.38), (4.0, 3.3 + 0.44))
    _box(ax, 1.4, 1.9 - 0.36, 5.2, 0.72, "ReLU", "#eef2ff", fs=10.5)
    _arrow(ax, (4.0, 3.3 - 0.44), (4.0, 1.9 + 0.38))
    _box(ax, 1.4, 0.6 - 0.36, 5.2, 0.72, "Output = ReLU( F(x) + x )", "#1d4ed8", fs=11, tc="white")
    _arrow(ax, (4.0, 1.9 - 0.38), (4.0, 0.6 + 0.38))
    # Skip connection.
    ax.plot([6.6, 8.0, 8.0], [11.0, 11.0, 3.3], color=ORANGE, lw=2.2, solid_joinstyle="round")
    _arrow(ax, (8.0, 3.3), (4.42, 3.3), color=ORANGE, lw=2.2)
    ax.text(8.2, 7.4, "identity\nshortcut\n(skip\nconnection)", color=ORANGE, fontsize=10.5, ha="left", va="center")
    ax.text(0.5, 7.6, "residual\nfunction F(x)", rotation=90, ha="center", va="center", fontsize=10.5, color="#1e3a8a")
    ax.plot([0.95, 0.95], [4.3, 9.9], color="#1e3a8a", lw=1.2)
    ax.text(5, -0.35, "The first block of each stage uses a 1x1 conv (stride 2) on the shortcut to match size.\n"
            "The skip path lets gradients flow straight back, so very deep networks still train.",
            ha="center", fontsize=9.2, color="#374151")
    save(fig, "residual_block_diagram.png")


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    architecture_diagram(), residual_block_diagram()
    if which == "all":
        class_distribution(), sample_grid(), training_curves(), result_figures(), gradcam_grid()
