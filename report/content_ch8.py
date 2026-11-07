"""Chapter 8: Application and Screenshots (real-model screenshots from docs/screenshots)."""
from PIL import Image

from paths import RFIG, SHOTS

MAX_RATIO = 1.32      # crop very tall full-page screenshots to their top part (height / width)
MAX_H_IN = 7.9        # never taller than this on the page


def shot(name: str, theme: str = "light", size: str = "1280x720", max_ratio: float = MAX_RATIO,
         width_in: float = 6.0):
    """Return (path, width_in) of a screenshot prepared for the report (cropped if very tall)."""
    src = SHOTS / f"{name}_{size}_{theme}.png"
    im = Image.open(src).convert("RGB")
    w, h = im.size
    if h / w > max_ratio:
        im = im.crop((0, 0, w, int(w * max_ratio)))
        w, h = im.size
    out = RFIG / "shots" / f"{name}_{theme}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, optimize=True)
    width = min(width_in, MAX_H_IN * w / h)
    return out, round(width, 2)


def pdf_page_image():
    """First page of a PDF report produced by the app, rendered to PNG (None if not available)."""
    pdfs = sorted(SHOTS.glob("*.pdf"))
    if not pdfs:
        return None
    import pymupdf
    pref = [p for p in pdfs if "1280x720_light" in p.name] or pdfs
    doc = pymupdf.open(pref[0])
    pix = doc[0].get_pixmap(dpi=170)
    out = RFIG / "shots" / "pdf_report_page1.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    pix.save(out)
    return out, doc.page_count


def fig(key, name, caption, theme="light", size="1280x720", max_ratio=MAX_RATIO, width_in=6.0):
    path, width = shot(name, theme, size, max_ratio, width_in)
    return ("fig", key, path, width, caption)


def ch8():
    blocks = [
        ("chapter", 8, "Application and Screenshots"),
        ("h2", "8.1 Overview"),
        ("p", "The trained ensemble is delivered through an offline web application. A double-click on start.bat "
              "starts the FastAPI server on the local computer and opens the browser; the model is loaded once in the "
              "background and the status pill in the top bar changes to **Model ready**. All screenshots in this "
              "chapter were taken from the running application with the real trained model (not the mock model used "
              "during development), in a browser window 1280 pixels wide; tall pages were captured in full and are shown "
              "from the top. The patient details in the screenshots are fictitious demo data. The navigation bar gives access to seven "
              "pages: Scan, Triage, History, CURB-65, Learn, Model and About. The sample X-rays used in the "
              "screenshots come from the held-out test split."),
        ("h2", "8.2 Scan Page"),
        ("p", "{fig:scan} shows the home page. The user drops a chest X-ray on the “lightbox”, browses for a file or "
              "pastes an image (JPG, PNG, BMP, WEBP, TIFF or DICOM, up to 25 MB). Patient details are optional and are "
              "printed on the PDF report. A gallery of sample X-rays from the test set, with their true diagnosis, "
              "lets a teacher or student try the model immediately."),
        fig("scan", "01_scan_home", "Scan page with the upload lightbox and optional patient details"),
        ("h2", "8.3 Result with Grad-CAM Heat Map"),
        ("p", "The result screen ({fig:result}) shows the verdict (“Pneumonia likely” or “Looks normal”), the "
              "calibrated pneumonia probability on a 0–100 ruler with the decision threshold marked, the confidence, "
              "the risk level, the decision threshold and the inference time. The X-ray viewer shows the Grad-CAM "
              "heat map over the X-ray with an opacity slider, zoom and pan."),
        fig("result", "03_scan_result", "Result screen for a pneumonia X-ray with the Grad-CAM heat map"),
        ("p", "Below the verdict the page gives a plain-English explanation, recommended next steps and the "
              "responsible-AI disclaimer ({fig:resultfull})."),
        fig("resultfull", "03b_scan_result_full", "Full result page with explanation, next steps and disclaimer "
                                                  "(top part of the page)"),
        ("p", "The viewer can also show the original X-ray and the heat map side by side ({fig:side}), so a doctor can "
              "compare the highlighted regions with the underlying image."),
        fig("side", "04_viewer_side_by_side", "Side-by-side view of the X-ray and the Grad-CAM heat map"),
    ]
    pdf = pdf_page_image()
    blocks += [("h2", "8.4 Patient PDF Report")]
    if pdf:
        path, npages = pdf
        blocks += [
            ("p", "A one-click PDF report ({fig:pdf}) contains the patient details, the result with probability and "
                  "risk level, the X-ray with its heat map, the explanation, next steps and the disclaimer, and the "
                  "model version and date. It is generated on the server with ReportLab using a bundled font, so it "
                  "works offline."),
            ("fig", "pdf", path, 4.6, "First page of a patient PDF report generated by the application"),
        ]
    else:
        blocks += [
            ("p", "A one-click PDF report contains the patient details, the result with probability and risk level, "
                  "the X-ray with its heat map, the explanation, next steps and the disclaimer. It is generated on the "
                  "server with ReportLab using a bundled font, so it works offline."),
        ]
    blocks += [
        ("h2", "8.5 Rejection of Non-X-ray Images"),
        ("p", "If the uploaded image is not a chest X-ray, the X-ray gate turns it away with a friendly reason and a "
              "chest X-ray likeness score; no prediction is made and nothing is saved ({fig:reject})."),
        fig("reject", "05_scan_rejected", "A colour photograph rejected by the X-ray gate"),
        ("h2", "8.6 Triage Queue (Doctor Mode)"),
        ("p", "The Triage page accepts up to 50 X-rays at once and shows the progress of each file. As results "
              "arrive, the queue re-orders itself so that the most likely pneumonia "
              "cases rise to the top, high-risk results are flagged as urgent, images that are not X-rays are listed "
              "as issues, and the queue can be filtered and exported as CSV ({fig:triage})."),
        fig("triage", "07_triage_done", "Completed triage queue sorted by pneumonia probability"),
        ("h2", "8.7 Scan History"),
        ("p", "Every analysed scan is stored locally in SQLite. The History page can be shown as a grid of thumbnails "
              "({fig:histgrid}) or as a list; it supports search and filters, and each scan can be "
              "opened, edited (patient details and doctor’s notes), re-downloaded as PDF or deleted."),
        fig("histgrid", "08_history_grid", "Scan history in grid view (top part of the page)", max_ratio=1.0),
        ("h2", "8.8 CURB-65 Severity Calculator"),
        ("p", "For adults with pneumonia, the CURB-65 page ({fig:curb}) computes the severity score from Lim et al. "
              "[5]. Urea can be entered in mmol/L or as BUN in mg/dL; if urea is not available the page switches to "
              "CRB-65. The live score, risk group, 30-day mortality and recommended care setting are shown "
              "({tab:curb}). The page states that the score is for adults; for children the WHO danger signs on the "
              "Learn page apply."),
        ("tab", "curb", "CURB-65 risk groups used by the calculator (derivation cohort of Lim et al. [5])",
         ["Score", "Risk group", "30-day mortality", "Suggested care"],
         [
             ["0–1", "Low", "1.5%", "Likely suitable for home treatment"],
             ["2", "Intermediate", "9.2%", "Consider hospital-supervised treatment"],
             ["3–5", "High", "22%", "Manage in hospital as severe pneumonia; assess for ICU, especially at 4–5"],
         ], [0.8, 1.2, 1.3, 2.7], {"size": 10, "align": ["C", "L", "C", "L"]}),
        fig("curb", "10_curb65", "CURB-65 severity calculator (top part of the page)", max_ratio=1.15),
        ("h2", "8.9 Learn Page"),
        ("p", "The Learn page ({fig:learn}) explains pneumonia in simple English for patients and families: "
              "emergency warning signs, symptoms in adults, danger signs in children (WHO), causes, who is at risk, "
              "prevention, how doctors diagnose pneumonia, care at home and how pneumonia looks on an X-ray. Every "
              "card lists its sources (WHO, NHS, CDC, NIH, Radiopaedia)."),
        fig("learn", "11_learn", "Learn page with sourced health information (top part of the page)", max_ratio=1.15),
        ("h2", "8.10 Model Page"),
        ("p", "The Model page ({fig:model}) is designed for the classroom: it shows the official test accuracy, "
              "sensitivity, specificity and ROC-AUC, the confusion matrix, the report figures, how ResNet’s skip "
              "connection works, the ensemble members, dataset facts, intended use and limitations."),
        fig("model", "12_model", "Model page with test-set performance (top part of the page)", max_ratio=1.15),
        ("h2", "8.11 About Page"),
        ("p", "The About page ({fig:about}) gives the project, student, course and faculty details, the technology "
              "stack, the dataset credit and the disclaimer."),
        fig("about", "13_about", "About page"),
        ("h2", "8.12 Dark Mode"),
        ("p", "Light and dark themes follow the system setting and can be switched with the moon/sun button; the "
              "choice is remembered. {fig:dark} shows the result screen in dark mode, which is comfortable on a "
              "projector in a darkened classroom."),
        fig("dark", "03_scan_result", "Result screen in dark mode", theme="dark"),
    ]
    return blocks
