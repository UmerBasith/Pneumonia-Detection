"""Browser (Playwright, headless Chromium) tests of every page and flow against the real server + real model.

Every page also asserts: no console errors/warnings, no page errors, no failed requests, no HTTP >= 400
(except where a test expects one).
"""
from __future__ import annotations

import csv
import io
import json
import re

import pytest
from playwright.sync_api import expect

from conftest import ROOT, SAMPLES, sample_files

VIEWPORTS = [(1280, 720), (1920, 1080), (390, 844)]
SCHEMES = ["light", "dark"]
PNEU = SAMPLES / "pneumonia_01.jpeg"
NORM = SAMPLES / "normal_01.jpeg"
PHOTO = SAMPLES / "not_xray" / "coffee.png"


def open_ready(page, path: str = "/"):
    page.goto(path, wait_until="networkidle")
    expect(page.get_by_role("status").filter(has_text="Model ready").first).to_be_attached(timeout=30000)


def history_total(http) -> int:
    return http.get("/api/history", params={"page_size": 1}).json()["total"]


def mobile(page) -> bool:
    return page.viewport_size["width"] < 1024


def go(page, name: str):
    """Click a main-nav link (opens the hamburger menu on phones)."""
    if mobile(page):
        page.get_by_role("button", name="Open menu").click()
    page.get_by_role("navigation", name="Main").get_by_role("link", name=name, exact=True).first.click()


# ------------------------------------------------------------------ Scan
@pytest.mark.parametrize("scheme", SCHEMES)
@pytest.mark.parametrize("vp", VIEWPORTS, ids=lambda v: f"{v[0]}x{v[1]}")
def test_scan_flow_result_viewer_notes_pdf(new_page, http, qa_dir, vp, scheme):
    page, probe = new_page(*vp, scheme)
    open_ready(page)
    page.get_by_role("button", name="Patient details").click()
    page.get_by_label("Patient name").fill("Priya Raman")
    page.get_by_role("textbox", name="Age (years)").fill("58")
    page.get_by_role("radio", name="Female").click()
    page.get_by_label("Patient ID").fill("OP-2026-0142")
    page.get_by_label("Symptoms").fill("Cough and fever for 4 days")
    page.locator("input[type=file]").set_input_files(str(PNEU))
    expect(page.locator("#verdict")).to_have_text(re.compile("Pneumonia likely"), timeout=30000)
    body = page.locator("main")
    expect(body).to_contain_text("95.6")
    expect(body).to_contain_text("High risk")
    expect(body).to_contain_text("Not a diagnosis")          # disclaimer on the result screen
    expect(body).to_contain_text("not a medical diagnosis")
    expect(page.get_by_label("Patient name")).to_have_value("Priya Raman")
    sid = page.locator("h1 .font-mono").inner_text().strip()
    assert re.fullmatch(r"PS-\d{8}-[0-9A-F]{6}", sid)

    # viewer modes, opacity, zoom
    viewer = page.get_by_role("region", name="X-ray viewer")
    for mode in ("Original", "Side by side", "Heatmap"):
        viewer.get_by_role("radio", name=mode).click()
    expect(viewer.get_by_role("img", name=re.compile("^Grad-CAM heatmap showing"))).to_have_count(1)
    viewer.get_by_label("Heatmap opacity").fill("25")
    expect(viewer).to_contain_text("25%")
    viewer.get_by_role("button", name="Zoom in").click()
    expect(viewer).to_contain_text("125%")
    stage = viewer.get_by_role("img", name=re.compile("Plus and minus zoom"))
    stage.focus()
    page.keyboard.press("0")
    expect(viewer).to_contain_text("100%")
    stage.dblclick()
    expect(viewer).to_contain_text("220%")
    page.keyboard.press("ArrowLeft")
    stage.dblclick()
    expect(viewer).to_contain_text("100%")
    imgs = viewer.locator("img")
    for i in range(imgs.count()):
        assert imgs.nth(i).evaluate("e => e.complete && e.naturalWidth > 0")

    # notes
    page.get_by_label("Doctor’s notes").fill("Right lower zone opacity. <b>not bold</b>")
    page.get_by_role("button", name="Save notes").click()
    expect(page.get_by_text("Notes saved")).to_be_visible()
    assert http.get(f"/api/history/{sid}").json()["doctor_notes"] == "Right lower zone opacity. <b>not bold</b>"

    # PDF
    with page.expect_download() as dl:
        page.get_by_role("button", name="Download PDF report").click()
    pdf_path = qa_dir / f"report_{vp[0]}_{scheme}.pdf"
    dl.value.save_as(pdf_path)
    assert dl.value.suggested_filename == f"PneumoScan_Report_{sid}.pdf"
    import pymupdf

    doc = pymupdf.open(pdf_path)
    text = " ".join("".join(p.get_text() for p in doc).split())  # ignore line wrapping
    for needle in ("Priya Raman", "OP-2026-0142", "Pneumonia likely", "95.6%", "High", "Disclaimer",
                   "not a certified medical device", "<b>not bold</b>", sid, "58", "Female"):
        assert needle in text, needle
    doc[0].get_pixmap(dpi=90).save(qa_dir / f"report_{vp[0]}_{scheme}_p1.png")
    probe.assert_clean()


def test_drag_drop_and_paste(new_page, http):
    page, probe = new_page()
    open_ready(page)
    before = history_total(http)
    page.evaluate("""async () => {
        const blob = await (await fetch('/samples/normal_01.jpeg')).blob();
        const dt = new DataTransfer();
        dt.items.add(new File([blob], 'dropped.jpeg', {type: 'image/jpeg'}));
        const zone = document.querySelector('.lightbox');
        for (const type of ['dragenter', 'dragover', 'drop'])
            zone.dispatchEvent(new DragEvent(type, {dataTransfer: dt, bubbles: true, cancelable: true}));
    }""")
    expect(page.locator("#verdict")).to_have_text(re.compile("No pneumonia detected"), timeout=30000)
    expect(page.locator("main")).to_contain_text("dropped.jpeg")
    page.get_by_role("button", name="New scan").click()
    page.evaluate("""async () => {
        const blob = await (await fetch('/samples/pneumonia_02.jpeg')).blob();
        const dt = new DataTransfer();
        dt.items.add(new File([blob], 'image.png', {type: 'image/jpeg'}));
        window.dispatchEvent(new ClipboardEvent('paste', {clipboardData: dt, bubbles: true, cancelable: true}));
    }""")
    expect(page.locator("#verdict")).to_have_text(re.compile("Pneumonia likely"), timeout=30000)
    expect(page.locator("main")).to_contain_text("pasted-image.jpg")
    assert history_total(http) == before + 2
    probe.assert_clean()


def test_sample_gallery_reveals_truth_and_rejects_photo(new_page, http):
    page, probe = new_page()
    open_ready(page)
    before = history_total(http)
    tiles = page.locator("button[aria-label^='Analyse X-ray']")
    expect(tiles).to_have_count(12)
    tiles.first.click()
    expect(page.locator("#verdict")).to_be_visible(timeout=30000)
    expect(page.locator("main")).to_contain_text("Ground truth")
    expect(page.locator("main")).to_contain_text("the model got this test X-ray right")
    page.get_by_role("button", name="New scan").click()
    expect(page.locator("button[aria-label*='ground truth']")).to_have_count(1)
    page.locator("button[aria-label^='Analyse Other image']").first.click()
    expect(page.get_by_text("This doesn’t look like a chest X-ray")).to_be_visible(timeout=30000)
    expect(page.locator("main")).to_contain_text("nothing was saved")
    assert history_total(http) == before + 1
    page.get_by_role("button", name="Try another image").click()
    expect(page.get_by_role("button", name=re.compile("Choose a chest X-ray"))).to_be_visible()
    probe.assert_clean()


def test_bad_files_get_friendly_messages(new_page, http, qa_dir):
    page, probe = new_page(allow_status=(422,))
    open_ready(page)
    before = history_total(http)
    page.locator("input[type=file]").set_input_files({"name": "notes.txt", "mimeType": "text/plain", "buffer": b"hi"})
    expect(page.get_by_text("is not a supported type")).to_be_visible()
    page.locator("input[type=file]").set_input_files({"name": "empty.png", "mimeType": "image/png", "buffer": b""})
    expect(page.get_by_text("empty.png is empty")).to_be_visible()
    page.locator("input[type=file]").set_input_files({"name": "fake.png", "mimeType": "image/png",
                                                      "buffer": b"this is text, not a picture" * 20})
    expect(page.get_by_text("not a readable image")).to_be_visible(timeout=30000)
    expect(page.get_by_role("button", name=re.compile("Choose a chest X-ray"))).to_be_visible()
    page.get_by_role("button", name="Patient details").click()
    page.get_by_role("textbox", name="Age (years)").fill("abc")
    page.locator("input[type=file]").set_input_files(str(PNEU))
    expect(page.get_by_text("Check the patient details")).to_be_visible()
    assert history_total(http) == before
    probe.assert_clean(allow_console=("status of 422",))  # the intentional "not a readable image" answer


def test_double_click_and_upload_while_scanning_make_one_scan(new_page, http):
    page, probe = new_page()
    open_ready(page)
    before = history_total(http)
    page.locator("button[aria-label^='Analyse X-ray']").nth(2).dblclick()
    page.wait_for_timeout(150)
    # paste another image while the first one is still being analysed: must be ignored
    page.evaluate("""async () => {
        const blob = await (await fetch('/samples/normal_02.jpeg')).blob();
        const dt = new DataTransfer();
        dt.items.add(new File([blob], 'second.jpeg', {type: 'image/jpeg'}));
        window.dispatchEvent(new ClipboardEvent('paste', {clipboardData: dt, bubbles: true, cancelable: true}));
    }""")
    expect(page.locator("#verdict")).to_be_visible(timeout=30000)
    page.wait_for_timeout(2500)
    assert history_total(http) == before + 1
    probe.assert_clean()


def test_slow_server_shows_progress(new_page):
    page, probe = new_page()
    open_ready(page)

    def slow(route):
        page.wait_for_timeout(4000)
        route.continue_()

    page.route("**/api/predict", slow)
    page.locator("input[type=file]").set_input_files(str(NORM))
    expect(page.locator("main")).to_contain_text("normal_01.jpeg")
    page.wait_for_timeout(1500)
    expect(page.locator("#verdict")).to_have_count(0)
    expect(page.locator("#verdict")).to_be_visible(timeout=40000)
    probe.assert_clean()


# ------------------------------------------------------------------ Triage
def test_triage_flow_sorting_filters_csv(new_page, http, qa_dir):
    page, probe = new_page(1280, 720)
    open_ready(page, "/triage")
    files = [str(p) for p in sample_files()] + [str(PHOTO)]
    payload = [{"name": "=HYPERLINK(\"x\").jpeg", "mimeType": "image/jpeg", "buffer": NORM.read_bytes()},
               {"name": "broken.txt", "mimeType": "text/plain", "buffer": b"nope"}]
    page.locator("input[type=file]").set_input_files(files)
    page.locator("input[type=file]").set_input_files(payload)
    expect(page.locator("main")).to_contain_text("15/15 analysed", timeout=120000)
    rows = page.locator("tbody tr")
    expect(rows).to_have_count(15)
    # sorted: first 6 are the pneumonia samples, highest probability first
    probs = [float(t.rstrip("%")) for t in page.locator("tbody tr td:nth-child(4) span.font-mono").all_inner_texts()]
    assert probs == sorted(probs, reverse=True) and len(probs) == 13
    assert all("pneumonia" in rows.nth(i).inner_text() for i in range(6))
    expect(page.get_by_role("radio", name="Urgent 6")).to_be_visible()
    page.get_by_role("radio", name="Urgent 6").click()
    expect(rows).to_have_count(6)
    page.get_by_role("radio", name="Normal 7").click()
    expect(rows).to_have_count(7)
    page.get_by_role("radio", name="Issues 2").click()
    expect(rows).to_have_count(2)
    expect(page.locator("tbody")).to_contain_text("Not a chest X-ray")
    expect(page.locator("tbody")).to_contain_text("not a supported type")
    page.get_by_role("radio", name="All 15").click()

    with page.expect_download() as dl:
        page.get_by_role("button", name="Export CSV").click()
    path = qa_dir / "triage.csv"
    dl.value.save_as(path)
    text = path.read_text(encoding="utf-8-sig")
    table = list(csv.DictReader(io.StringIO(text)))
    assert len(table) == 15
    assert [r["priority"] for r in table[:13]] == [str(i) for i in range(1, 14)]
    assert sum(r["urgent"] == "yes" for r in table) == 6
    inj = next(r for r in table if "HYPERLINK" in r["file"])
    assert inj["file"].startswith("'="), inj["file"]          # formula injection neutralised
    p1 = next(r for r in table if r["file"] == "pneumonia_01.jpeg")
    assert p1["result"] == "PNEUMONIA" and p1["prob_pneumonia"] == "0.9558" and p1["risk_level"] == "High"

    page.get_by_role("link", name="Open details for pneumonia_06.jpeg").click()
    expect(page).to_have_url(re.compile(r"/history/PS-"))
    expect(page.locator("#verdict")).to_have_text(re.compile("Pneumonia likely"))
    page.go_back()
    expect(page.locator("tbody tr")).to_have_count(15)  # queue survives navigation
    probe.assert_clean()


# ------------------------------------------------------------------ History
def test_history_search_filter_open_edit_delete_clear(new_page, http, qa_dir):
    page, probe = new_page(1280, 720)
    # one clearly named scan to find
    with open(PNEU, "rb") as f:
        sid = http.post("/api/predict", files={"file": ("findme.jpeg", f.read(), "image/jpeg")},
                        data={"name": "Kavya Unique", "patient_id": "QA-77"}).json()["scan"]["id"]
    open_ready(page, "/history")
    page.get_by_label("Search scans").fill("Kavya Uni")
    expect(page.locator("main")).to_contain_text("Kavya Unique")
    expect(page.locator("main")).to_contain_text(sid)
    page.get_by_label("Search scans").fill("QA-77")
    expect(page.locator("main")).to_contain_text(sid)
    page.get_by_label("Search scans").fill("zzz-no-such-thing")
    expect(page.locator("main")).not_to_contain_text(sid)
    page.get_by_role("button", name="Clear search", exact=True).click()
    page.get_by_role("radio", name="Normal").click()
    expect(page.locator("main")).not_to_contain_text("Kavya Unique")
    page.get_by_role("radio", name="Pneumonia").click()
    expect(page.locator("main")).to_contain_text("Kavya Unique")
    page.get_by_role("radio", name="List view").click()
    expect(page.locator("main")).to_contain_text("Kavya Unique")

    # open, edit notes, reload -> persists
    page.get_by_role("link", name=re.compile("Kavya Unique")).first.click()
    expect(page).to_have_url(re.compile(sid))
    page.get_by_label("Doctor’s notes").fill("Persist me 123")
    page.get_by_role("button", name="Save notes").click()
    expect(page.get_by_text("Notes saved")).to_be_visible()
    page.reload(wait_until="networkidle")
    expect(page.get_by_label("Doctor’s notes")).to_have_value("Persist me 123")
    with page.expect_download() as dl:
        page.get_by_role("button", name="Download PDF report").click()
    dl.value.save_as(qa_dir / "history_report.pdf")
    import pymupdf

    assert "Persist me 123" in "".join(p.get_text() for p in pymupdf.open(qa_dir / "history_report.pdf"))

    # re-download from the list, then delete one
    page.goto("/history", wait_until="networkidle")
    with page.expect_download():
        page.get_by_role("button", name=f"Download PDF report for {sid}").click()
    page.get_by_role("button", name=f"Delete scan {sid}").click()
    page.get_by_role("dialog").get_by_role("button", name="Delete scan").click()
    expect(page.get_by_text("Scan deleted")).to_be_visible()
    assert http.get(f"/api/history/{sid}").status_code == 404
    probe.assert_clean()


def test_clear_all_resets_scan_page(new_page, http):
    """After 'Clear all' the Scan page must not keep showing a deleted result with broken images."""
    page, probe = new_page(1280, 720)
    open_ready(page)
    page.locator("input[type=file]").set_input_files(str(NORM))
    expect(page.locator("#verdict")).to_be_visible(timeout=30000)
    go(page, "History")
    page.get_by_role("button", name="Clear all").click()
    page.get_by_role("dialog").get_by_role("button", name="Delete all scans").click()
    expect(page.get_by_text("History cleared")).to_be_visible()
    assert history_total(http) == 0
    go(page, "Scan")
    expect(page.get_by_role("button", name=re.compile("Choose a chest X-ray"))).to_be_visible()
    expect(page.locator("#verdict")).to_have_count(0)
    probe.assert_clean()


def test_deleting_current_scan_resets_scan_page(new_page, http):
    """Deleting the scan that the Scan page is showing must send the Scan page back to the upload box."""
    page, probe = new_page(1280, 720)
    open_ready(page)
    page.locator("input[type=file]").set_input_files(str(NORM))
    expect(page.locator("#verdict")).to_be_visible(timeout=30000)
    sid = page.locator("h1 .font-mono").inner_text().strip()
    go(page, "History")
    page.get_by_role("button", name=f"Delete scan {sid}").click()
    page.get_by_role("dialog").get_by_role("button", name="Delete scan").click()
    expect(page.get_by_text("Scan deleted")).to_be_visible()
    go(page, "Scan")
    expect(page.get_by_role("button", name=re.compile("Choose a chest X-ray"))).to_be_visible()
    # and from the scan's own detail page
    page.locator("input[type=file]").set_input_files(str(NORM))
    expect(page.locator("#verdict")).to_be_visible(timeout=30000)
    sid = page.locator("h1 .font-mono").inner_text().strip()
    go(page, "History")
    page.get_by_role("link", name=re.compile(sid)).first.click()
    expect(page).to_have_url(re.compile(sid))
    page.get_by_role("button", name="Delete").first.click()
    page.get_by_role("dialog").get_by_role("button", name=re.compile("Delete")).click()
    expect(page).to_have_url(re.compile("/history$"))
    go(page, "Scan")
    expect(page.get_by_role("button", name=re.compile("Choose a chest X-ray"))).to_be_visible()
    probe.assert_clean()


# ------------------------------------------------------------------ CURB-65
CURB_CASES = [
    # (confusion, urea, unit, resp, sbp, dbp, age, crb, expected score, expected risk word)
    ("no", "7.0", "mmol", "29", "90", "61", "64", False, 0, "Low"),
    ("no", "7.1", "mmol", "29", "90", "61", "64", False, 1, "Low"),
    ("no", "19", "bun", "29", "90", "61", "64", False, 0, "Low"),
    ("no", "20", "bun", "29", "90", "61", "64", False, 1, "Low"),
    ("no", "", "mmol", "30", "90", "61", "64", False, 1, "Low"),
    ("no", "", "mmol", "29", "89", "61", "64", False, 1, "Low"),
    ("no", "", "mmol", "29", "90", "60", "64", False, 1, "Low"),
    ("no", "", "mmol", "29", "90", "61", "65", False, 1, "Low"),
    ("yes", "7.1", "mmol", "", "", "", "", False, 2, "Intermediate"),
    ("yes", "8", "mmol", "30", "", "", "", False, 3, "High"),
    ("yes", "8", "mmol", "30", "85", "", "", False, 4, "High"),
    ("yes", "8", "mmol", "30", "85", "55", "80", False, 5, "High"),
    ("no", "", "mmol", "", "", "", "", True, 0, "Low"),
    ("yes", "", "mmol", "", "", "", "", True, 1, "Intermediate"),
    ("yes", "", "mmol", "31", "", "", "", True, 2, "Intermediate"),
    ("yes", "", "mmol", "31", "80", "", "70", True, 4, "High"),
]
CARE = {0: "Likely suitable for home treatment", 1: "Likely suitable for home treatment",
        2: "Consider hospital-supervised treatment", 3: "Manage in hospital as severe pneumonia",
        4: "assess for ICU", 5: "assess for ICU"}
CRB_CARE = {0: "Likely suitable for home treatment", 1: "Likely need hospital referral", 2: "Likely need hospital referral",
            3: "Urgent hospital admission", 4: "Urgent hospital admission"}


@pytest.fixture(scope="module")
def curb_page(browser, base):
    ctx = browser.new_context(viewport={"width": 1280, "height": 720}, base_url=base)
    page = ctx.new_page()
    page.goto("/curb-65", wait_until="networkidle")
    yield page
    ctx.close()


@pytest.mark.parametrize("case", CURB_CASES, ids=lambda c: "-".join(str(x) for x in c[:8]))
def test_curb65_scores(curb_page, case):
    page = curb_page
    conf, urea, unit, rr, sbp, dbp, age, crb, score, risk = case
    page.get_by_role("button", name="Reset").click()
    page.get_by_role("radio", name="Yes, confused" if conf == "yes" else "No", exact=True).click()
    if crb:
        page.get_by_label("Urea not available — use CRB-65").check()
    else:
        page.get_by_role("radio", name="BUN mg/dL" if unit == "bun" else "mmol/L").click()
        page.get_by_label("Blood urea nitrogen (BUN)" if unit == "bun" else "Blood urea", exact=True).fill(urea)
    page.get_by_label("Breaths per minute").fill(rr)
    page.get_by_label("Systolic").fill(sbp)
    page.get_by_label("Diastolic").fill(dbp)
    page.get_by_role("textbox", name="Age", exact=True).fill(age)
    result = page.get_by_role("complementary", name=re.compile("CRB-65 result" if crb else "CURB-65 result"))
    expect(result.locator(".font-display.tabular").first).to_have_text(str(score))
    expect(result).to_contain_text(f"/ {4 if crb else 5}")
    expect(result).to_contain_text(f"{risk} risk")
    expect(result).to_contain_text((CRB_CARE if crb else CARE)[score])


def test_curb65_invalid_and_child(curb_page):
    page = curb_page
    page.get_by_role("button", name="Reset").click()
    page.get_by_label("Breaths per minute").fill("abc")
    expect(page.get_by_text("Enter a number.")).to_be_visible()
    page.get_by_label("Breaths per minute").fill("500")
    expect(page.get_by_text("Enter a value between 0 and 80 /min.")).to_be_visible()
    page.get_by_label("Breaths per minute").fill("")
    page.get_by_role("textbox", name="Age", exact=True).fill("-3")
    expect(page.get_by_text("Enter a value between 0 and 130 years.")).to_be_visible()
    page.get_by_role("textbox", name="Age", exact=True).fill("4")
    expect(page.get_by_text("CURB-65 is for adults. For children")).to_be_visible()
    page.get_by_label("Blood urea", exact=True).fill("7,5")  # comma decimal
    result = page.get_by_role("complementary", name=re.compile("CURB-65 result"))
    expect(result.locator(".font-display.tabular").first).to_have_text("1")
    expect(page.get_by_text("criteria not entered yet")).to_be_visible()


# ------------------------------------------------------------------ Learn / Model / About / 404
def test_learn_sections_have_sources_and_safe_links(new_page):
    page, probe = new_page()
    page.goto("/learn", wait_until="networkidle")
    links = page.locator("main a[href^='http']")
    assert links.count() >= 10
    for i in range(links.count()):
        a = links.nth(i)
        assert a.get_attribute("target") == "_blank", a.get_attribute("href")
        assert "noopener" in (a.get_attribute("rel") or "") or "noreferrer" in (a.get_attribute("rel") or "")
    cards = page.locator("main section, main article")
    assert cards.count() > 3
    expect(page.locator("main")).to_contain_text("Sources")
    probe.assert_clean()


def test_model_page_numbers_equal_metrics_json(new_page):
    m = json.loads((ROOT / "models" / "metrics.json").read_text(encoding="utf-8"))["final"]["test"]
    page, probe = new_page(1920, 1080)
    page.goto("/model", wait_until="networkidle")
    main = page.locator("main")
    for v in (m["accuracy"], m["recall_sensitivity"], m["specificity"], m["roc_auc"], m["precision"], m["f1"]):
        expect(main).to_contain_text(f"{v * 100:.1f}")
    cm = m["confusion_matrix"]
    for k in ("tn", "fp", "fn", "tp"):
        expect(main).to_contain_text(str(cm[k]))
    expect(main).to_contain_text("0.074")
    # every figure loads
    page.evaluate("async () => { for (let y = 0; y < document.body.scrollHeight; y += 500) "
                  "{ window.scrollTo(0, y); await new Promise(r => setTimeout(r, 60)); } }")
    page.wait_for_load_state("networkidle")
    figs = page.locator("main img")
    assert figs.count() >= 10
    for i in range(figs.count()):
        assert figs.nth(i).evaluate("e => e.complete && e.naturalWidth > 0"), figs.nth(i).get_attribute("src")
    probe.assert_clean()


def test_about_page_facts(new_page):
    page, probe = new_page()
    page.goto("/about", wait_until="networkidle")
    main = page.locator("main")
    for t in ("Umer Basith G", "230171601192", "CSDX530", "Deep Learning", "Mahalakshmi R",
              "B.S. Abdur Rahman Crescent Institute of Science and Technology"):
        expect(main).to_contain_text(t)
    probe.assert_clean()


def test_404_refresh_back_forward_and_title(new_page):
    page, probe = new_page()
    page.goto("/does-not-exist/at/all", wait_until="networkidle")
    expect(page.locator("main")).to_contain_text(re.compile("not found|doesn’t exist|does not exist", re.I))
    for path, title in [("/", "Scan"), ("/triage", "Triage"), ("/history", "History"), ("/curb-65", "CURB-65"),
                        ("/learn", "Learn"), ("/model", "Model"), ("/about", "About")]:
        r = page.goto(path, wait_until="networkidle")
        assert r.status == 200
        page.reload(wait_until="networkidle")
        expect(page).to_have_title(re.compile(title))
    page.go_back()
    expect(page).to_have_url(re.compile("/model$"))
    page.go_back()
    expect(page).to_have_url(re.compile("/learn$"))
    page.go_forward()
    expect(page).to_have_url(re.compile("/model$"))
    r = page.goto("/history/PS-20990101-ABCDEF", wait_until="networkidle")
    expect(page.locator("main")).to_contain_text("Scan not found")
    # the only HTTP error allowed is the intentional 404 for the missing scan
    assert probe.bad_status and all("PS-20990101-ABCDEF" in s for s in probe.bad_status)
    probe.bad_status.clear()
    probe.assert_clean(allow_console=("status of 404",))


def test_theme_toggle_persists(new_page):
    page, probe = new_page(scheme="light")
    page.goto("/", wait_until="networkidle")
    assert not page.evaluate("document.documentElement.classList.contains('dark')")
    page.get_by_role("button", name="Switch to dark mode").click()
    assert page.evaluate("document.documentElement.classList.contains('dark')")
    page.reload(wait_until="networkidle")
    assert page.evaluate("document.documentElement.classList.contains('dark')")
    page.goto("/model", wait_until="networkidle")
    assert page.evaluate("document.documentElement.classList.contains('dark')")
    page.get_by_role("button", name="Switch to light mode").click()
    page.reload(wait_until="networkidle")
    assert not page.evaluate("document.documentElement.classList.contains('dark')")
    probe.assert_clean()


def test_keyboard_only(new_page):
    page, probe = new_page()
    open_ready(page)
    page.keyboard.press("Tab")
    expect(page.get_by_role("link", name="Skip to content")).to_be_focused()
    seen = []
    for _ in range(40):
        page.keyboard.press("Tab")
        seen.append(page.evaluate("(document.activeElement.innerText || document.activeElement.getAttribute('aria-label') || '').trim()"))
    for name in ("Triage", "History", "CURB-65", "Learn", "Model", "About", "Patient details"):
        assert any(name in s for s in seen), (name, seen)
    # focus a sample tile with the keyboard and start a scan with Enter
    page.locator("button[aria-label^='Analyse X-ray']").first.focus()
    page.keyboard.press("Enter")
    expect(page.locator("#verdict")).to_be_visible(timeout=30000)
    # visible focus ring on buttons
    page.get_by_role("button", name="New scan").focus()
    outline = page.evaluate("getComputedStyle(document.activeElement).outlineStyle")
    assert outline != "none"
    probe.assert_clean()


def test_mobile_menu(new_page):
    page, probe = new_page(390, 844)
    page.goto("/", wait_until="networkidle")
    for name in ("Learn", "Model", "About", "CURB-65"):
        go(page, name)
        expect(page.get_by_role("heading", level=1)).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    probe.assert_clean()


@pytest.mark.parametrize("path", ["/", "/triage", "/history", "/curb-65", "/learn", "/model", "/about", "/nope"])
@pytest.mark.parametrize("vp", VIEWPORTS, ids=lambda v: f"{v[0]}x{v[1]}")
def test_no_horizontal_overflow(new_page, path, vp):
    page, probe = new_page(*vp, "dark")
    page.goto(path, wait_until="networkidle")
    page.wait_for_timeout(300)
    over = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
    assert over <= 0, f"{path} overflows by {over}px"
    probe.assert_clean()


# ------------------------------------------------------------------ server goes down mid-session
def test_offline_banner_and_recovery(browser, qa_dir):
    """Stop the server while the page is open: offline banner + disabled upload; restart: Retry recovers."""
    from conftest import QAServer, PageProbe

    srv = QAServer(qa_dir / "offline_storage", qa_dir / "offline.log", {"PNEUMOSCAN_MODEL": "mock"}).start(60)
    ctx = browser.new_context(viewport={"width": 1280, "height": 720}, base_url=srv.base)
    page = ctx.new_page()
    probe = PageProbe(page)
    try:
        page.goto("/", wait_until="networkidle")
        expect(page.get_by_role("status").filter(has_text="Demo mode").first).to_be_attached(timeout=20000)
        expect(page.get_by_text("Demo mode – mock model.")).to_be_visible()     # mock can never pass as real
        srv.stop()
        expect(page.get_by_role("alert")).to_contain_text("not responding", timeout=30000)
        expect(page.get_by_role("button", name="Server offline")).to_be_disabled()
        srv2 = QAServer(qa_dir / "offline_storage", qa_dir / "offline2.log", {"PNEUMOSCAN_MODEL": "mock"},
                        port=srv.port).start(60)
        try:
            page.get_by_role("button", name="Retry").click()
            expect(page.get_by_role("alert")).to_have_count(0, timeout=15000)
            expect(page.get_by_role("button", name=re.compile("Choose a chest X-ray"))).to_be_enabled()
            page.locator("input[type=file]").set_input_files(str(NORM))
            expect(page.locator("#verdict")).to_be_visible(timeout=30000)
            expect(page.locator("main")).to_contain_text("Simulated result from the mock model")
        finally:
            srv2.stop()
        # while the server was down the browser logged refused health checks; nothing else is allowed
        probe.console = [c for c in probe.console if "Failed to load resource" not in c and "ERR_CONNECTION_REFUSED" not in c]
        probe.failed = [f for f in probe.failed if "/api/health" not in f]
        probe.assert_clean()
    finally:
        ctx.close()
