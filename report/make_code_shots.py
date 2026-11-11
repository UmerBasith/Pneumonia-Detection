"""Make the codebase screenshots for the team report (report/figures/case_study/).

* Editor screenshots: the REAL source files with their REAL line numbers, shown in a dark code editor
  window with the project's real folder tree on the left (read from disk).
* Terminal screenshots: REAL output of commands run on this project (training logs, the inference command,
  the test suites and the start.bat launcher). Captured outputs are kept in report/figures/case_study/text/.

Run:  .venv\\Scripts\\python.exe report\\make_code_shots.py
"""
import html
import re
from pathlib import Path

from playwright.sync_api import sync_playwright
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_for_filename

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "report" / "figures" / "case_study"
TXT = OUT / "text"
STYLE = "one-dark"
SKIP = {"__pycache__", ".pytest_cache", "node_modules", ".venv", "dist", "storage", "checkpoints", ".git",
        "figures", "screenshots", "research", "public", "text", "shots"}

EDITOR_SHOTS = [
    # (output name, file, first line, last line)
    ("code_prepare_split", "ml/prepare_data.py", 85, 100),
    ("code_transforms", "ml/datasets.py", 37, 63),
    ("code_build_model", "ml/common.py", 62, 75),
    ("code_train_loop", "ml/train.py", 132, 154),
    ("code_calibration", "ml/evaluate.py", 50, 71),
    ("code_gradcam", "ml/gradcam.py", 17, 44),
    ("code_xray_gate", "ml/xray_gate.py", 62, 84),
    ("code_inference", "ml/inference.py", 113, 141),
    ("code_api_predict", "app/backend/main.py", 214, 236),
    ("code_frontend_ruler", "app/frontend/src/components/ProbabilityRuler.tsx", 1, 40),
    ("code_project_tree", "README.md", 1, 26),
]


# ----------------------------------------------------------------------------- explorer tree
def tree_rows(open_file: str, expand_all: bool = False):
    """Rows (depth, name, is_dir, is_open, is_current) of the real project tree, opened along open_file."""
    open_parts = Path(open_file).parts
    rows = []

    def walk(d: Path, depth: int):
        items = sorted([p for p in d.iterdir() if p.name not in SKIP and not p.name.startswith(".")
                        and not p.name.startswith("~$")],
                       key=lambda p: (p.is_file(), p.name.lower()))
        for p in items:
            rel = p.relative_to(ROOT).parts
            if p.is_dir():
                is_open = (rel == open_parts[:len(rel)]) or (expand_all and p.name in ("ml", "app", "backend",
                                                                                         "frontend", "models",
                                                                                         "tests"))
                if p.name == "data" or p.name == "logs":
                    is_open = False
                rows.append((depth, p.name, True, is_open, False))
                if is_open:
                    walk(p, depth + 1)
            else:
                if p.suffix in (".pt", ".npz", ".docx", ".pdf", ".jpeg", ".png", ".csv") and depth > 0:
                    continue
                rows.append((depth, p.name, False, False, rel == open_parts))

    walk(ROOT, 0)
    return rows


ICON = {".py": ("py", "#4b8bbe"), ".tsx": ("tsx", "#4fc1ff"), ".ts": ("ts", "#3178c6"), ".md": ("md", "#7aa6da"),
        ".json": ("{}", "#cbcb41"), ".bat": ("bat", "#c1c1c1"), ".txt": ("txt", "#999"), ".css": ("css", "#56b6c2"),
        ".html": ("<>", "#e37933"), ".ps1": ("ps", "#4fa3d9")}


def explorer_html(open_file, max_rows, expand_all=False):
    out = []
    for depth, name, is_dir, is_open, cur in tree_rows(open_file, expand_all)[:max_rows]:
        pad = 10 + depth * 12
        if is_dir:
            icon = f'<span class="chev">{"▾" if is_open else "▸"}</span>'
        else:
            label, col = ICON.get(Path(name).suffix, ("·", "#888"))
            icon = f'<span class="fic" style="color:{col}">{label}</span>'
        cls = "row cur" if cur else "row"
        out.append(f'<div class="{cls}" style="padding-left:{pad}px">{icon}{html.escape(name)}</div>')
    return "\n".join(out)


CSS_EDITOR = """
* { box-sizing: border-box; }
body { margin: 0; padding: 18px; background: #ffffff; }
.win { width: 1180px; border-radius: 9px; overflow: hidden; background: #282c34;
       box-shadow: 0 6px 24px rgba(0,0,0,.35); border: 1px solid #1b1d23; font-family: 'Segoe UI', sans-serif; }
.title { height: 32px; background: #21252b; color: #9da5b4; font-size: 12.5px; display: flex; align-items: center;
         padding: 0 12px; border-bottom: 1px solid #181a1f; }
.dots span { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 7px; }
.title .t { flex: 1; text-align: center; margin-right: 60px; }
.body { display: flex; }
.side { width: 255px; background: #21252b; color: #c5cad3; font-size: 12.5px; padding: 6px 0 10px;
        border-right: 1px solid #181a1f; overflow: hidden; }
.side .hdr { font-size: 11px; letter-spacing: .08em; color: #7f8794; padding: 4px 12px 8px; }
.row { height: 21px; line-height: 21px; white-space: nowrap; }
.row.cur { background: #2c313c; color: #ffffff; box-shadow: inset 2px 0 0 #528bff; }
.chev { display: inline-block; width: 14px; color: #8b93a1; }
.fic { display: inline-block; width: 30px; font-size: 10px; font-weight: 700; font-family: Consolas, monospace; }
.main { flex: 1; min-width: 0; }
.tabs { height: 34px; background: #21252b; display: flex; align-items: flex-end; }
.tab { background: #282c34; color: #d7dae0; font-size: 12.5px; padding: 8px 16px; border-top: 2px solid #528bff; }
.crumb { color: #7f8794; font-size: 12px; padding: 5px 14px 6px; }
.code { padding: 2px 0 12px; overflow: hidden; }
.code table { border-spacing: 0; }
.code td.linenos { color: #636d83; text-align: right; padding: 0 14px 0 10px; user-select: none; }
.code td.linenos pre, .code td.code pre { margin: 0; font: 14px/21px Consolas, 'Cascadia Mono', monospace; }
.code td.code { padding-left: 6px; }
.status { height: 24px; background: #21252b; color: #9da5b4; font-size: 11.5px; display: flex; align-items: center;
          padding: 0 12px; gap: 22px; border-top: 1px solid #181a1f; }
"""


def editor_page(rel, first, last, expand_all=False):
    src = (ROOT / rel).read_text(encoding="utf-8").splitlines()
    code = "\n".join(src[first - 1:last])
    lexer = get_lexer_for_filename(rel)
    fmt = HtmlFormatter(style=STYLE, linenos="table", linenostart=first, cssclass="hl", nobackground=True)
    body = highlight(code, lexer, fmt)
    n = last - first + 1
    rows = (40 if expand_all else max(n + 3, 14))
    lang = {"py": "Python", "tsx": "TypeScript JSX", "md": "Markdown"}.get(rel.rsplit(".", 1)[-1], "")
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS_EDITOR}
{fmt.get_style_defs('.hl')}
.hl {{ background: transparent; color: #abb2bf; }}
</style></head><body><div class="win">
<div class="title"><span class="dots"><span style="background:#ff5f57"></span><span style="background:#febc2e"></span><span style="background:#28c840"></span></span>
<span class="t">{html.escape(Path(rel).name)} — pneumoscan-ai</span></div>
<div class="body"><div class="side"><div class="hdr">EXPLORER: PNEUMOSCAN-AI</div>
{explorer_html(rel, rows, expand_all)}</div>
<div class="main"><div class="tabs"><div class="tab">{html.escape(Path(rel).name)}</div></div>
<div class="crumb">{' › '.join(html.escape(p) for p in Path(rel).parts)}</div>
<div class="code">{body}</div></div></div>
<div class="status"><span>main</span><span>Ln {first}–{last}</span><span>UTF-8</span><span>{lang}</span></div>
</div></body></html>"""


# ----------------------------------------------------------------------------- terminal
CSS_TERM = """
body { margin: 0; padding: 18px; background: #ffffff; }
.win { width: 1180px; border-radius: 9px; overflow: hidden; background: #0c0c0c;
       box-shadow: 0 6px 24px rgba(0,0,0,.35); border: 1px solid #333; }
.title { height: 32px; background: #1f1f1f; color: #cfcfcf; font: 12.5px 'Segoe UI', sans-serif;
         display: flex; align-items: center; padding: 0 12px; }
.title .tab { background: #0c0c0c; padding: 7px 16px; border-radius: 6px 6px 0 0; margin-top: 6px; }
pre { margin: 0; padding: 12px 16px 16px; color: #cccccc; font: 13.5px/20px Consolas, 'Cascadia Mono', monospace;
      white-space: pre-wrap; word-break: break-all; }
.p { color: #f9f1a5; } .ok { color: #16c60c; } .warn { color: #f9f1a5; } .b { color: #3b78ff; }
.c { color: #61d6d6; } .dim { color: #767676; } .w { color: #f2f2f2; font-weight: 600; }
"""


def colour(line: str) -> str:
    s = html.escape(line)
    if s.startswith("PS "):
        prompt, _, cmd = s.partition("&gt; ")
        return f'<span class="p">{prompt}&gt;</span> <span class="w">{cmd}</span>'
    s = re.sub(r"\b(PASSED|passed|\*best\*|Model ready:|Server is up:)", r'<span class="ok">\1</span>', s)
    s = re.sub(r"(=====+[^=]*=====+)", r'<span class="c">\1</span>', s)
    s = re.sub(r"^(\[\d\d:\d\d:\d\d\])", r'<span class="dim">\1</span>', s)
    s = re.sub(r"(&quot;[A-Za-z_]+&quot;):", r'<span class="b">\1</span>:', s)
    s = re.sub(r"(\[ *\d+%\])", r'<span class="c">\1</span>', s)
    return s


def terminal_page(lines, title="Windows PowerShell"):
    body = "\n".join(colour(l) for l in lines)
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS_TERM}</style></head><body>
<div class="win"><div class="title"><span class="tab">{html.escape(title)}</span></div><pre>{body}</pre></div>
</body></html>"""


PS = r"PS C:\PersonalProjects\pneumoscan-ai> "


def read(name):
    return (TXT / name).read_text(encoding="utf-8", errors="replace").rstrip("\n").splitlines()


def terminal_shots():
    log = (ROOT / "logs" / "stdout_r50_384_s1.txt").read_text(encoding="utf-8").splitlines()
    infer = read("infer.txt")
    start = [l for l in read("start.txt") if "could not start" not in l]   # last line came from stopping it
    ml = read("pytest_ml.txt")
    be = read("pytest_be.txt")
    return {
        "term_train": [PS + r".venv\Scripts\python.exe -m ml.train --name r50_384_s1 --arch resnet50 --res 384 "
                            r"--epochs 20 --bs 24 --seed 1"] + log,
        "term_inference": [PS + r".venv\Scripts\python.exe -m ml.inference sample_xrays\pneumonia_01.jpeg"] + infer,
        "term_tests": [PS + r".venv\Scripts\python.exe -m pytest ml\test_inference.py -v"] + ml[:6] + ml[6:]
                      + ["", PS + r".venv\Scripts\python.exe -m pytest app\backend\tests -q"] + be[-2:],
        "term_start": [PS + r".\start.bat"] + start,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(device_scale_factor=2, viewport={"width": 1240, "height": 900})
        for name, rel, a, z in EDITOR_SHOTS:
            pg.set_content(editor_page(rel, a, z, expand_all=(name == "code_project_tree")))
            pg.locator(".win").screenshot(path=str(OUT / f"{name}.png"))
            print("saved", name)
        for name, lines in terminal_shots().items():
            pg.set_content(terminal_page(lines))
            pg.locator(".win").screenshot(path=str(OUT / f"{name}.png"))
            print("saved", name)
        b.close()


if __name__ == "__main__":
    main()
