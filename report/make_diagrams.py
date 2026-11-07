"""Extra diagrams for the printed report (system architecture, use cases, training workflow).

Run: .venv\\Scripts\\python.exe report\\make_diagrams.py   -> report/figures/*.png (300 dpi)
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).resolve().parent / "figures"
OUT.mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})

INK = "#1f2937"
C = {
    "user": ("#f3f4f6", "#6b7280"),
    "ui": ("#e0e7ff", "#4f46e5"),
    "api": ("#dbeafe", "#2563eb"),
    "ml": ("#fef3c7", "#d97706"),
    "xai": ("#fee2e2", "#dc2626"),
    "store": ("#dcfce7", "#16a34a"),
}


def box(ax, x, y, w, h, text, kind, fs=9.5, bold_first=True):
    fc, ec = C[kind]
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                                fc=fc, ec=ec, lw=1.4))
    lines = text.split("\n")
    if bold_first:
        ax.text(x + w / 2, y + h - 0.22, lines[0], ha="center", va="top", fontsize=fs + 0.5,
                fontweight="bold", color=INK)
        if len(lines) > 1:
            ax.text(x + w / 2, y + h - 0.55, "\n".join(lines[1:]), ha="center", va="top",
                    fontsize=fs - 0.8, color=INK, linespacing=1.35)
    else:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=INK)


def arrow(ax, p, q, label=None, color=INK, style="-|>", ls="-", lx=0, ly=0.12, fs=8.3, rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=13, lw=1.3, color=color,
                                 linestyle=ls, connectionstyle=f"arc3,rad={rad}"))
    if label:
        ax.text((p[0] + q[0]) / 2 + lx, (p[1] + q[1]) / 2 + ly, label, ha="center", va="bottom",
                fontsize=fs, color="#374151", style="italic")


def system_architecture():
    fig, ax = plt.subplots(figsize=(11, 7.7))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 7.7)
    ax.axis("off")

    # Layer bands
    for y0, h, name in [(5.75, 1.25, "Presentation layer"), (3.05, 2.45, "Application layer (FastAPI, Python 3.11)"),
                        (0.15, 2.65, "Model and data layer")]:
        ax.add_patch(FancyBboxPatch((0.1, y0), 10.8, h, boxstyle="round,pad=0.0,rounding_size=0.1",
                                    fc="none", ec="#cbd5e1", lw=1.0, ls="--"))
        ax.text(0.22, y0 + h - 0.08, name, ha="left", va="top", fontsize=8.5, color="#64748b", style="italic")

    box(ax, 0.35, 5.9, 2.0, 0.85, "Users\npatient / doctor / student", "user")
    box(ax, 3.1, 5.9, 4.6, 0.85, "React + TypeScript UI (Vite build)\nScan | Triage | History | CURB-65 | Learn | Model | About", "ui")
    box(ax, 8.35, 5.9, 2.35, 0.85, "Web browser\nlocalhost:8000, offline", "user")
    arrow(ax, (2.35, 6.32), (3.1, 6.32))
    arrow(ax, (7.7, 6.32), (8.35, 6.32), style="<|-|>")

    box(ax, 0.35, 3.25, 2.6, 1.85, "REST API (main.py)\n/api/predict  /api/batch\n/api/history  /api/report\n/api/model-info  /api/health", "api")
    box(ax, 3.3, 3.25, 2.1, 1.85, "Image decoding\n(imaging.py)\nJPG, PNG, BMP,\nWEBP, TIFF, DICOM\nsize / corruption\nchecks", "api")
    box(ax, 5.75, 3.25, 2.3, 1.85, "Model service\n(model_service.py)\nloads weights once,\nwarm-up, one\nprediction at a time", "api")
    box(ax, 8.4, 3.25, 2.3, 1.85, "PDF report\n(report.py, ReportLab)\npatient details,\nresult, heat map,\ndisclaimer", "api")
    arrow(ax, (5.4, 6.0), (1.65, 5.1), label="HTTP / JSON", lx=0.95, ly=-0.25)
    arrow(ax, (2.95, 4.18), (3.3, 4.18))
    arrow(ax, (5.4, 4.18), (5.75, 4.18))

    box(ax, 0.35, 0.35, 2.3, 2.05, "X-ray gate\n(xray_gate.py)\ncolour / blank / size\nheuristics +\nMahalanobis distance\non ResNet features", "ml")
    box(ax, 2.95, 0.35, 2.6, 2.05, "ResNet ensemble\n(inference.py)\nResNet50 @ 384\nResNet34 @ 384\nResNet50 @ 448\n+ flip TTA", "ml")
    box(ax, 5.85, 0.35, 2.05, 2.05, "Decision\nsigmoid(z / T),\nT = 0.602;\nthreshold 0.074;\nrisk level", "ml")
    box(ax, 8.2, 1.45, 2.5, 0.95, "Grad-CAM\nlayer4 heat map", "xai")
    box(ax, 8.2, 0.35, 2.5, 0.9, "SQLite + image files\n(storage.py) history", "store")
    arrow(ax, (6.9, 3.25), (1.5, 2.4), label="PIL image", lx=-0.6, ly=0.25)
    arrow(ax, (2.65, 1.38), (2.95, 1.38))
    arrow(ax, (5.55, 1.38), (5.85, 1.38))
    arrow(ax, (7.9, 1.9), (8.2, 1.9))
    arrow(ax, (7.9, 0.8), (8.2, 0.8))
    arrow(ax, (9.45, 2.4), (7.2, 3.25), label="result + PNGs", lx=0.55, ly=-0.05, ls="--", color="#2563eb")
    ax.plot([10.7, 10.84, 10.84], [0.8, 0.8, 2.95], color="#16a34a", lw=1.3, ls=":")
    arrow(ax, (10.84, 2.95), (10.45, 3.25), ls=":", color="#16a34a")
    ax.text(10.8, 2.6, "saved\nscans", ha="right", va="center", fontsize=8, color="#374151", style="italic")
    ax.text(5.5, 7.65, "PneumoScan AI: overall system architecture", ha="center", va="top",
            fontsize=13, fontweight="bold", color=INK)
    fig.savefig(OUT / "system_architecture.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def stick(ax, x, y, name):
    ax.add_patch(plt.Circle((x, y + 0.62), 0.13, fc="white", ec=INK, lw=1.4))
    ax.plot([x, x], [y + 0.49, y + 0.05], color=INK, lw=1.4)
    ax.plot([x - 0.25, x + 0.25], [y + 0.36, y + 0.36], color=INK, lw=1.4)
    ax.plot([x, x - 0.2], [y + 0.05, y - 0.3], color=INK, lw=1.4)
    ax.plot([x, x + 0.2], [y + 0.05, y - 0.3], color=INK, lw=1.4)
    ax.text(x, y - 0.42, name, ha="center", va="top", fontsize=10, fontweight="bold", color=INK)


def use_case():
    fig, ax = plt.subplots(figsize=(10, 7.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7.4)
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((2.4, 0.2), 5.2, 6.75, boxstyle="round,pad=0.0,rounding_size=0.15",
                                fc="#f8fafc", ec="#475569", lw=1.3))
    ax.text(5.0, 6.85, "PneumoScan AI (offline web application)", ha="center", va="top", fontsize=10.5,
            fontweight="bold", color=INK)
    cases = ["Upload chest X-ray and get result", "View Grad-CAM heat map", "Download patient PDF report",
             "Batch triage queue + CSV export", "Search / edit / delete scan history", "CURB-65 severity calculator",
             "Learn about pneumonia", "View model performance"]
    ys = [6.1 - i * 0.74 for i in range(len(cases))]
    for t, y in zip(cases, ys):
        ax.add_patch(Ellipse((5.0, y), 4.6, 0.56, fc="#e0e7ff", ec="#4f46e5", lw=1.2))
        ax.text(5.0, y, t, ha="center", va="center", fontsize=9.2, color=INK)
    stick(ax, 0.9, 5.0, "Patient")
    stick(ax, 0.9, 1.6, "Student")
    stick(ax, 9.1, 3.6, "Doctor")
    pat = [0, 1, 2, 6]
    stu = [0, 1, 6, 7]
    doc = [0, 1, 2, 3, 4, 5, 7]
    for i in pat:
        ax.plot([1.2, 2.7], [5.35, ys[i]], color="#64748b", lw=0.9)
    for i in stu:
        ax.plot([1.2, 2.7], [1.95, ys[i]], color="#64748b", lw=0.9)
    for i in doc:
        ax.plot([8.8, 7.3], [3.95, ys[i]], color="#64748b", lw=0.9)
    fig.savefig(OUT / "use_case_diagram.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def workflow():
    fig, ax = plt.subplots(figsize=(11, 4.6))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 4.6)
    ax.axis("off")
    row1 = [
        (0.1, "Kermany dataset\nMendeley Data v2\n5,232 train +\n624 test images", "user"),
        (2.3, "prepare_data.py\nverify counts, patient-\nlevel split (1/7 val),\n512 px gray cache,\nleakage checks", "api"),
        (4.5, "train.py (x3)\nResNet50 @ 384,\nResNet34 @ 384,\nResNet50 @ 448;\nbest epoch by val AUC", "ml"),
        (6.7, "evaluate.py\non validation only:\nflip TTA, ensemble,\ntemperature T,\nYouden-J threshold", "ml"),
        (8.9, "Test set (624)\nscored ONCE with\nthe frozen pipeline\n(logged)", "xai"),
    ]
    for x, t, k in row1:
        box(ax, x, 2.45, 2.0, 1.75, t, k, fs=9)
    for i in range(4):
        arrow(ax, (row1[i][0] + 2.0, 3.32), (row1[i + 1][0], 3.32))
    row2 = [
        (2.3, "xray_gate.py\nMahalanobis OOD gate\nfitted on train,\ncut-off from validation", "ml"),
        (4.5, "models/\nfp16 weights,\nensemble.json,\nmetrics.json,\nmodel_card.json", "store"),
        (6.7, "inference.py\nPneumoniaModel API:\ncheck_image, predict,\ninfo (+ Grad-CAM)", "ml"),
        (8.9, "FastAPI + React\napplication\n(start.bat)", "ui"),
    ]
    for x, t, k in row2:
        box(ax, x, 0.25, 2.0, 1.75, t, k, fs=9)
    for i in range(3):
        arrow(ax, (row2[i][0] + 2.0, 1.12), (row2[i + 1][0], 1.12))
    arrow(ax, (7.7, 2.45), (5.5, 2.0), label="export", lx=0.2, ly=0.02)
    ax.text(5.5, 4.55, "Training, validation and deployment workflow", ha="center", va="top", fontsize=12.5,
            fontweight="bold", color=INK)
    fig.savefig(OUT / "training_workflow.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    system_architecture()
    use_case()
    workflow()
    print("ok")

