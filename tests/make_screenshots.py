"""Regenerate docs/screenshots/ (same flows and file names the App agent used).

Needs a running server with the REAL model and an EMPTY history (use a scratch storage folder):
    set PNEUMOSCAN_STORAGE=%TEMP%\pneumoscan_shots
    .venv\Scripts\python -m uvicorn app.backend.main:app --port 8102
    .venv\Scripts\python tests\make_screenshots.py [--base http://127.0.0.1:8102] [--only 03,04] [--combo 1280x720_light]
"""
import argparse
import glob
import os
import tempfile

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMBOS = [(1280, 720, "light"), (1280, 720, "dark"), (1920, 1080, "light"), (1920, 1080, "dark"),
          (390, 844, "light"), (390, 844, "dark")]


def load_all(page):
    """Scroll through the page so lazy thumbnails load."""
    h = page.evaluate("document.body.scrollHeight")
    y = 0
    while y < h:
        page.evaluate(f"window.scrollTo(0, {y})")
        page.wait_for_timeout(120)
        y += 600
    page.wait_for_load_state("networkidle")
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(500)


def shoot(p, w, h, theme, out, base, samples, only=None):
    tag = f"{w}x{h}_{theme}"
    msgs = []

    def snap(page, name, full=True):
        if only and name.split("_")[0] not in only:
            return
        page.wait_for_timeout(700)
        page.evaluate("() => { if (document.activeElement) document.activeElement.blur(); window.scrollTo(0, 0) }")
        page.wait_for_timeout(250)
        page.screenshot(path=os.path.join(out, f"{name}_{tag}.png"), full_page=full)

    if True:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": w, "height": h}, color_scheme=theme, accept_downloads=True)
        page = ctx.new_page()
        page.on("console", lambda m: msgs.append(f"[{page.url}] {m.type}: {m.text}") if m.type in ("error", "warning") else None)
        page.on("pageerror", lambda e: msgs.append(f"[{page.url}] pageerror: {e}"))

        page.goto(base + "/", wait_until="networkidle")
        snap(page, "01_scan_home", full=False)

        # result with patient details
        page.get_by_role("button", name="Patient details").click()
        page.get_by_label("Patient name").fill("Priya Raman")
        page.get_by_role("textbox", name="Age (years)").fill("58")
        page.get_by_role("radio", name="Female").click()
        page.get_by_label("Patient ID").fill("OP-2026-0142")
        page.get_by_label("Symptoms").fill("Cough and fever for 4 days, short of breath on walking")
        page.locator("button[aria-label^='Analyse X-ray']").nth(1).click()
        page.wait_for_timeout(450)
        snap(page, "02_scan_analysing", full=False)
        page.wait_for_selector("#verdict", timeout=30000)
        page.wait_for_timeout(1200)
        page.get_by_label("Doctor’s notes").fill("Right lower zone opacity on review. Started oral antibiotics; review in 48 h.")
        page.get_by_role("button", name="Save notes").click()
        page.wait_for_timeout(600)
        page.get_by_role("button", name="Dismiss notification").first.click()
        page.evaluate("window.scrollTo(0,0)")
        snap(page, "03_scan_result", full=False)
        snap(page, "03b_scan_result_full", full=True)
        # side by side
        page.get_by_role("radio", name="Side by side").click()
        snap(page, "04_viewer_side_by_side", full=False)
        with page.expect_download() as dl:
            page.get_by_role("button", name="Download PDF report").click()
        dl.value.save_as(os.path.join(tempfile.gettempdir(), f"pneumoscan_report_{tag}.pdf"))  # not kept in docs/
        page.wait_for_timeout(300)
        page.get_by_role("button", name="Dismiss notification").first.click()

        # rejected
        page.get_by_role("button", name="New scan").click()
        others = page.locator("button[aria-label^='Analyse Other image']")
        if others.count():
            others.first.click()
            page.wait_for_selector("text=This doesn’t look like a chest X-ray", timeout=30000)
            snap(page, "05_scan_rejected", full=False)
            page.get_by_role("button", name="Try another image").click()

        # triage
        page.goto(base + "/triage", wait_until="networkidle")
        files = sorted(glob.glob(os.path.join(samples, "*.jp*g")) + glob.glob(os.path.join(samples, "*.png")))
        files += sorted(glob.glob(os.path.join(samples, "not_xray", "*")))[:1]
        page.locator("input[type=file]").set_input_files(files)
        page.wait_for_timeout(500)
        snap(page, "06_triage_running", full=False)
        page.wait_for_function("() => !document.body.innerText.includes('Analysing')", timeout=120000)
        snap(page, "07_triage_done", full=True)

        page.goto(base + "/history", wait_until="networkidle")
        load_all(page)
        snap(page, "08_history_grid", full=True)
        page.get_by_role("radio", name="List view").click()
        page.wait_for_timeout(400)
        load_all(page)
        snap(page, "09_history_list", full=True)
        page.get_by_role("radio", name="Grid view").click()

        page.goto(base + "/curb-65", wait_until="networkidle")
        page.get_by_role("radio", name="Yes, confused").click()
        page.get_by_label("Blood urea").fill("8.4")
        page.get_by_label("Breaths per minute").fill("32")
        page.get_by_label("Systolic").fill("118")
        page.get_by_label("Diastolic").fill("74")
        page.get_by_role("textbox", name="Age").fill("71")
        snap(page, "10_curb65", full=True)

        page.goto(base + "/learn", wait_until="networkidle")
        snap(page, "11_learn", full=True)
        page.goto(base + "/model", wait_until="networkidle")
        page.wait_for_timeout(800)
        snap(page, "12_model", full=True)
        page.goto(base + "/about", wait_until="networkidle")
        snap(page, "13_about", full=True)
        page.goto(base + "/does-not-exist", wait_until="networkidle")
        snap(page, "14_not_found", full=False)
        b.close()

    return msgs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8102")
    ap.add_argument("--out", default=os.path.join(ROOT, "docs", "screenshots"))
    ap.add_argument("--samples", default=os.path.join(ROOT, "sample_xrays"))
    ap.add_argument("--only", help="comma-separated screenshot numbers, e.g. 03,03b,07")
    ap.add_argument("--combo", action="append", help="e.g. 1280x720_light (default: all six)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    only = set(a.only.split(",")) if a.only else None
    combos = COMBOS
    if a.combo:
        combos = [(int(c.split("x")[0]), int(c.split("x")[1].split("_")[0]), c.split("_")[1]) for c in a.combo]
    with sync_playwright() as p:
        for w, h, theme in combos:
            msgs = shoot(p, w, h, theme, a.out, a.base, a.samples, only)
            print(w, h, theme, "->", " | ".join(msgs) or "no console errors or warnings")


if __name__ == "__main__":
    main()
