"""Step 2: fine-tune an ImageNet-pretrained ResNet on the training split.

Model selection uses ONLY the validation split (val ROC-AUC, ties -> lower val loss).
The test split is never touched here.

Example:
  python -m ml.train --name r50_384_s1 --arch resnet50 --res 384 --epochs 20 --bs 24
Outputs (models/checkpoints/<name>/): best.pt, history.json, val_preds.npz, config.json
Log: logs/train_<name>.log
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import time

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from ml.common import CKPT_DIR, LOGS_DIR, binary_metrics, build_model
from ml.datasets import XrayDataset, eval_transform, train_transform


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--name", required=True)
    p.add_argument("--arch", default="resnet50", choices=["resnet18", "resnet34", "resnet50"])
    p.add_argument("--res", type=int, default=384)
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--bs", type=int, default=24)
    p.add_argument("--lr", type=float, default=3e-4, help="head learning rate")
    p.add_argument("--backbone-lr-mult", type=float, default=0.33, help="backbone lr = lr * mult")
    p.add_argument("--wd", type=float, default=1e-2)
    p.add_argument("--warmup", type=float, default=1.0, help="warm-up epochs")
    p.add_argument("--label-smoothing", type=float, default=0.1)
    p.add_argument("--ema", type=float, default=0.998, help="EMA decay of weights (0 = off)")
    p.add_argument("--patience", type=int, default=7, help="early-stopping patience (epochs)")
    p.add_argument("--workers", type=int, default=3)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


class EMA:
    """Exponential moving average of model weights (a smoother model for evaluation)."""

    def __init__(self, model: nn.Module, decay: float):
        self.decay, self.steps, self.model = decay, 0, copy.deepcopy(model).eval()
        for p in self.model.parameters():
            p.requires_grad_(False)

    @torch.no_grad()
    def update(self, model: nn.Module) -> None:
        self.steps += 1
        d = min(self.decay, (1 + self.steps) / (10 + self.steps))  # warm-up: follow closely at first
        for e, m in zip(self.model.state_dict().values(), model.state_dict().values()):
            if e.dtype.is_floating_point:
                e.mul_(d).add_(m.detach(), alpha=1 - d)
            else:
                e.copy_(m)


@torch.no_grad()
def predict_logits(model, loader, device) -> tuple[np.ndarray, np.ndarray]:
    model.eval()
    out, ys = [], []
    for x, y in loader:
        x = x.to(device, non_blocking=True)
        with torch.autocast("cuda", dtype=torch.float16, enabled=device.type == "cuda"):
            out.append(model(x).float().cpu())
        ys.append(y)
    return torch.cat(out).numpy(), torch.cat(ys).numpy()


def main() -> None:
    a = parse_args()
    torch.manual_seed(a.seed)
    np.random.seed(a.seed)
    # NOTE: channels_last memory format was measured 8x SLOWER on this RTX 3050 + torch 2.11
    # (66 vs 516 img/s for ResNet18), so the default NCHW layout is used everywhere.
    torch.backends.cudnn.benchmark = False  # benchmark mode gave no speed-up here and spikes memory
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    out_dir = CKPT_DIR / a.name
    out_dir.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    log_f = open(LOGS_DIR / f"train_{a.name}.log", "a", encoding="utf-8")

    def log(msg: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        log_f.write(line + "\n")
        log_f.flush()

    log(f"config {vars(a)} device={device}")
    (out_dir / "config.json").write_text(json.dumps(vars(a), indent=2))

    train_ds = XrayDataset("train", train_transform(a.res))
    val_ds = XrayDataset("val", eval_transform(a.res))
    # Each Windows worker process costs ~0.6 GB RAM (it re-imports torch), so keep them few;
    # validation runs in the main process (747 images, a few seconds).
    train_dl = DataLoader(train_ds, batch_size=a.bs, shuffle=True, drop_last=True, num_workers=a.workers,
                          pin_memory=True, persistent_workers=a.workers > 0)
    val_dl = DataLoader(val_ds, batch_size=a.bs * 2, shuffle=False, num_workers=0)
    log(f"train={len(train_ds)} val={len(val_ds)}")

    # Class-weighted loss: NORMAL is the minority class (~26% of train).
    counts = np.bincount(train_ds.labels, minlength=2)
    class_w = torch.tensor(counts.sum() / (2 * counts), dtype=torch.float32, device=device)
    criterion = nn.CrossEntropyLoss(weight=class_w, label_smoothing=a.label_smoothing)
    log(f"class counts={counts.tolist()} weights={class_w.tolist()}")

    model = build_model(a.arch).to(device)
    head = list(model.fc.parameters())
    head_ids = {id(p) for p in head}
    backbone = [p for p in model.parameters() if id(p) not in head_ids]
    opt = torch.optim.AdamW([{"params": backbone, "lr": a.lr * a.backbone_lr_mult},
                             {"params": head, "lr": a.lr}], weight_decay=a.wd)
    base_lrs = [g["lr"] for g in opt.param_groups]
    steps_per_epoch = len(train_dl)
    total, warm = a.epochs * steps_per_epoch, int(a.warmup * steps_per_epoch)
    scaler = torch.amp.GradScaler("cuda", enabled=device.type == "cuda")
    ema = EMA(model, a.ema) if a.ema > 0 else None

    history, best, bad_epochs, step = [], (-1.0, 1e9), 0, 0
    t_start = time.time()
    for epoch in range(1, a.epochs + 1):
        model.train()
        t0, run_loss, run_correct, seen = time.time(), 0.0, 0, 0
        for x, y in train_dl:
            # Cosine schedule with linear warm-up, updated every step.
            f = (step + 1) / max(warm, 1) if step < warm else \
                0.5 * (1 + math.cos(math.pi * (step - warm) / max(total - warm, 1)))
            for g, lr0 in zip(opt.param_groups, base_lrs):
                g["lr"] = lr0 * f
            x = x.to(device, non_blocking=True)
            y = y.to(device, non_blocking=True)
            with torch.autocast("cuda", dtype=torch.float16, enabled=device.type == "cuda"):
                logits = model(x)
                loss = criterion(logits.float(), y)
            opt.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.unscale_(opt)
            nn.utils.clip_grad_norm_(model.parameters(), 2.0)
            scaler.step(opt)
            scaler.update()
            if ema:
                ema.update(model)
            step += 1
            run_loss += loss.item() * len(y)
            run_correct += (logits.argmax(1) == y).sum().item()
            seen += len(y)

        eval_model = ema.model if ema else model
        logits, yv = predict_logits(eval_model, val_dl, device)
        val_loss = float(criterion(torch.from_numpy(logits).to(device), torch.from_numpy(yv).to(device)))
        prob = torch.softmax(torch.from_numpy(logits), 1)[:, 1].numpy()
        m = binary_metrics(yv, prob, 0.5)
        rec = {"epoch": epoch, "train_loss": run_loss / seen, "train_acc": run_correct / seen,
               "val_loss": val_loss, "val_acc": m["accuracy"], "val_bal_acc": m["balanced_accuracy"],
               "val_auc": m["roc_auc"], "lr": opt.param_groups[1]["lr"], "sec": time.time() - t0}
        history.append(rec)
        improved = (m["roc_auc"], -val_loss) > (best[0], -best[1])
        if improved:
            best, bad_epochs = (m["roc_auc"], val_loss), 0
            torch.save({"arch": a.arch, "res": a.res, "epoch": epoch, "state_dict": eval_model.state_dict()},
                       out_dir / "best.pt")
            np.savez(out_dir / "val_preds.npz", logits=logits, y=yv)
        else:
            bad_epochs += 1
        log(f"ep {epoch:02d} train_loss {rec['train_loss']:.4f} acc {rec['train_acc']:.4f} | val_loss {val_loss:.4f} "
            f"acc {m['accuracy']:.4f} bal {m['balanced_accuracy']:.4f} auc {m['roc_auc']:.5f} "
            f"| {rec['sec']:.0f}s {'*best*' if improved else ''}")
        (out_dir / "history.json").write_text(json.dumps(history, indent=2))
        if bad_epochs >= a.patience:
            log(f"early stop at epoch {epoch}")
            break

    best_ep = max(history, key=lambda r: (r["val_auc"], -r["val_loss"]))["epoch"]
    summary = {"best_epoch": best_ep, "best_val_auc": best[0], "best_val_loss": best[1],
               "epochs_run": len(history), "train_minutes": (time.time() - t_start) / 60}
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    log(f"DONE {summary}")


if __name__ == "__main__":
    main()
