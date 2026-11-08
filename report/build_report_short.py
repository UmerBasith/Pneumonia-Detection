"""Build the 30-page report: report/PneumoScan_AI_Report_30_Pages.docx.

Same content, figures and code as the full report, cut down to the core sections. It has no bonafide
certificate, declaration or acknowledgement, and no appendices; the key code is in Chapter 6.

Run:  .venv\\Scripts\\python.exe report\\build_report_short.py
Then: powershell -File report\\word_finalize.ps1 -Docx report\\PneumoScan_AI_Report_30_Pages.docx
                                                -Pdf  report\\PneumoScan_AI_Report_30_Pages.pdf
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from docx.enum.text import WD_ALIGN_PARAGRAPH  # noqa: E402
from docx.shared import Inches, Pt  # noqa: E402
from PIL import Image  # noqa: E402

from build_report import prep_images  # noqa: E402
from content_ch1_2 import ch1, ch2  # noqa: E402
from content_ch3_5 import ch3, ch4, ch5  # noqa: E402
from content_ch6_7 import ch6, ch7  # noqa: E402
from content_ch8 import fig as shot_fig, pdf_page_image  # noqa: E402
from content_end import REFERENCES, ch9  # noqa: E402
from content_front import abstract, cover  # noqa: E402
from docx_engine import Report, add_inline, mbar, mfrac, mparen, msup, mt  # noqa: E402
from paths import FIG, RFIG  # noqa: E402

OUT = HERE / "PneumoScan_AI_Report_30_Pages.docx"


# ----------------------------------------------------------------------------- helpers
def sec(blocks, title):
    """The h2 block whose title (without its number) is `title`, plus everything up to the next h2/chapter."""
    out, on = [], False
    for b in blocks:
        if b[0] in ("h2", "chapter"):
            on = b[0] == "h2" and re.sub(r"^[\d.]+\s+", "", b[1]) == title
        if on:
            out.append(b)
    if not out:
        raise KeyError(title)
    return out


def without(blocks, *keys):
    """Drop figures / tables / listings / equations with these keys."""
    return [b for b in blocks if not (b[0] in ("fig", "tab", "code", "eq") and b[1] in keys)]


def subst(obj, pairs):
    """Replace text everywhere inside nested blocks; every pattern must be found at least once."""
    used = set()

    def go(o):
        if isinstance(o, str):
            for a, b in pairs:
                if a in o:
                    used.add(a)
                    o = o.replace(a, b)
            return o
        if isinstance(o, tuple):
            return tuple(go(x) for x in o)
        if isinstance(o, list):
            return [go(x) for x in o]
        if isinstance(o, dict):
            return {k: go(v) for k, v in o.items()}
        return o

    res = go(obj)
    missing = [a for a, _ in pairs if a not in used]
    if missing:
        raise ValueError(f"text not found: {missing}")
    return res


def renumber(blocks):
    """Number h2 / h3 headings again (1.1, 1.2, ... and 3.2.1, ...) after sections were removed."""
    out, ch, n2, n3 = [], 0, 0, 0
    for b in blocks:
        if b[0] == "chapter":
            ch, n2, n3 = b[1], 0, 0
        elif b[0] == "h2":
            n2, n3 = n2 + 1, 0
            b = ("h2", f"{ch}.{n2} " + re.sub(r"^[\d.]+\s+", "", b[1]))
        elif b[0] == "h3":
            n3 += 1
            b = ("h3", f"{ch}.{n2}.{n3} " + re.sub(r"^[\d.]+\s+", "", b[1]))
        out.append(b)
    return out


def small(blocks, size=8.0):
    """Code listings in a slightly smaller font."""
    return [b[:4] + (size,) if b[0] == "code" else b for b in blocks]


def side_by_side(left, right, out, gap=40):
    a, b = Image.open(left).convert("RGB"), Image.open(right).convert("RGB")
    h = min(a.height, b.height)
    a = a.resize((round(a.width * h / a.height), h), Image.Resampling.LANCZOS)
    b = b.resize((round(b.width * h / b.height), h), Image.Resampling.LANCZOS)
    im = Image.new("RGB", (a.width + gap + b.width, h), "white")
    im.paste(a, (0, 0))
    im.paste(b, (a.width + gap, 0))
    im.save(out, optimize=True)
    return out


# ----------------------------------------------------------------------------- front matter
def contents(r):
    r.front_heading("Table of Contents", toc=False)
    r.toc('TOC \\f \\h \\z')   # chapters (TC fields) only, so the contents fit on one page


# ----------------------------------------------------------------------------- chapters
def short_ch1():
    c = ch1()
    return [c[0], c[1]] + sec(c, "Background") + sec(c, "Role of the Chest X-ray")[:2] + sec(c, "Problem Statement") \
        + sec(c, "Objectives") + sec(c, "Scope")


def short_ch2():
    c = ch2()
    blocks = [c[0]] + sec(c, "Introduction")[:2] + sec(c, "Summary of the Literature") + sec(c, "Research Gap")
    return subst(blocks, [
        ("and this is pointed out for each paper.", "and this is shown in the “Data / evaluation” column of "
                                                    "{tab:lit}."),
        ("Acc 92.8%, Sens 93.2%, Spec 90.1%, AUC 96.8%", "Acc 92.8%, Sens 93.2%, Spec 90.1%, AUC 96.8% (as quoted "
                                                         "in [18])"),
    ])


def short_ch3():
    c = ch3()
    arch = [b[:3] + (5.4,) + b[4:] if b[0] == "fig" else b for b in sec(c, "System Architecture")]
    return subst([c[0]] + sec(c, "Proposed System") + arch, [
        ("plus an out-of-distribution distance on ResNet features reject",
         "plus an out-of-distribution distance (Mahalanobis distance [29] with a Ledoit-Wolf covariance [30]) on "
         "ResNet features reject"),
    ])


def short_ch4():
    c = ch4()
    src = sec(c, "Source of the Dataset")
    src = [b[:4] + ([row for row in b[4] if row[0] not in ("File used", "Image format", "DOI")],) + b[5:]
           if b[0] == "tab" else b for b in src]
    samples = [b[:3] + (5.0,) + b[4:] if b[0] == "fig" else b for b in sec(c, "Sample Images")]
    blocks = [c[0]] + src + without(sec(c, "Class Distribution and Split"), "classdist") + samples + [
        ("h2", "Pre-processing and Augmentation"),
        ("p", "The same pre-processing code (ml/common.py) is used for training, evaluation and the application, so "
              "the network always sees images in the same way. Every image is converted to 8-bit grayscale (16-bit "
              "DICOM images are rescaled and the EXIF orientation is applied), squashed to a 512 × 512 canonical "
              "view so that the whole chest is always visible, resized to the member’s input size (384 or 448 "
              "pixels), copied to three channels and normalised with the ImageNet mean and standard deviation, "
              "because the backbones were pretrained on colour ImageNet photographs [23]."),
        ("p", "To reduce over-fitting, each training image is randomly transformed every time it is used: a random "
              "crop (75–100% of the image), a left–right flip, a small rotation (±10°) and shift, brightness and "
              "contrast changes (±20%), slight blur and sensor noise. These imitate real differences between X-ray "
              "acquisitions; vertical flips are not used because an upside-down chest X-ray is not realistic. "
              "Because there are about three pneumonia images for every normal one, the loss is weighted by inverse "
              "class frequency, w_c = N / (2 N_c): **1.94 for NORMAL** and **0.67 for PNEUMONIA**."),
    ]
    blocks = [b for b in blocks if not (b[0] == "p" and b[1].startswith("The training data are imbalanced"))]
    return subst(blocks, [
        (" Patient "
         "identifiers were parsed from the file names (person123_bacteria_456.jpeg → patient P123; "
         "IM-0115-0001.jpeg or NORMAL2-IM-0115-0001.jpeg → patient N0115).",
         " Patient identifiers were parsed from the file names."),
        ("images) became the validation set. {tab:split} and {fig:classdist} show the resulting split.",
         "images) became the validation set. {tab:split} shows the resulting split. Automatic checks found no "
         "patient in both training and validation, and no exact or near-duplicate image shared between the test "
         "set and the training or validation images."),
    ])


def short_ch5():
    c = ch5()
    tr = sec(c, "Training Setup")
    loss = next(b for b in tr if b[0] == "eq" and b[1] == "loss")
    thr = sec(c, "Threshold Selection and Risk Levels")[1:]   # without its heading
    blocks_sec = [b[:3] + (2.3,) + b[4:] if b[0] == "fig" and b[1] == "resblock" else b
                  for b in sec(c, "Basic and Bottleneck Blocks")]
    variants = subst(without(sec(c, "ResNet-18, ResNet-34 and ResNet-50"), "resnets"), [
        ("They differ in the number and type of blocks ({tab:resnets}).",
         "They differ in the number and type of blocks: ResNet-18 uses 2, 2, 2, 2 basic blocks, ResNet-34 uses 3, 4, "
         "6, 3 basic blocks and ResNet-50 uses 3, 4, 6, 3 bottleneck blocks, which end with 2048 channels instead "
         "of 512. With our two-class head, ResNet-34 has 21.3 million and ResNet-50 23.5 million parameters."),
    ])
    residual = without(sec(c, "Residual Learning"), "proj")
    residual = subst(residual, [(" a 1 × 1 projection W_s is used on the shortcut ({eq:proj}) [1].",
                                 " a 1 × 1 projection W_s is used on the shortcut instead, y = F(x) + W_s x [1].")])
    blocks = [c[0]] + residual + blocks_sec + variants + [
        ("h2", "Training Setup"),
        ("p", "Each network starts from ImageNet weights [23] (transfer learning). The 1000-class ImageNet layer is "
              "replaced by Dropout(0.2) and a two-class linear layer, and all layers are fine-tuned end-to-end, with "
              "the backbone learning three times more slowly than the new head. The loss ({eq:loss}) is "
              "cross-entropy with the class weights w_c of Section 4.4 and label smoothing ε = 0.1 [24], where q_c "
              "is the smoothed target. Training uses AdamW [25] with one warm-up epoch and a cosine learning-rate "
              "decay, automatic mixed precision [26] to fit the 6 GB GPU, and an exponential moving average (EMA) "
              "of the weights. After every epoch the validation ROC-AUC is computed; the best checkpoint is kept and "
              "training stops after 7 epochs without improvement (at most 20 epochs, batch size 16–32)."),
        loss,
        ("h2", "Ensemble, Calibration and Threshold"),
        ("p", "For each member and each view (the original image and its horizontal mirror), the logit margin "
              "z = ℓ_PNEUMONIA − ℓ_NORMAL is computed, and the six margins (3 members × 2 views) are averaged. "
              "Averaging models that make different mistakes reduces the variance of the prediction. Modern networks "
              "are often over-confident, so the averaged margin is divided by a temperature T fitted on the "
              "validation set (temperature scaling [27]; T = 0.602) and passed through a sigmoid to give a calibrated "
              "probability p = σ(z / T)."),
    ]
    pipeline =[b[:3] + (3.4,) + b[4:] if b[0] == "fig" else b for b in sec(c, "Complete Pipeline")]
    return blocks + thr + sec(c, "Grad-CAM Explanations") + pipeline   # full-page figure last, with its text


def short_ch6():
    c = ch6()
    return [c[0],
            ("h2", "Development Environment"),
            ("p", "The project was developed and tested on a Windows 11 laptop with an NVIDIA GeForce RTX 3050 "
                  "Laptop GPU (6 GB), an Intel Core i5-12450HX processor and 16 GB of RAM. Training the three "
                  "ResNets took 55.5 minutes in total, and the finished application also runs without a GPU (about "
                  "1.25 s per X-ray). All software is free and open source: Python 3.11, PyTorch 2.11 with CUDA "
                  "12.8 [21] and torchvision for the ResNets, scikit-learn [22] for the metrics and the "
                  "patient-level split, FastAPI for the back-end, SQLite for the scan history, ReportLab for the "
                  "PDF reports, and React 19 with TypeScript, Vite and Tailwind CSS for the front-end. The code "
                  "listings below are copied automatically from the project’s source files, so they match the "
                  "submitted code exactly."),
            ] + small(sec(c, "Building the Model") + sec(c, "Training Loop") + sec(c, "Inference API")) + [
            ("h2", "Back-end and Front-end"),
            ("p", "The back-end (app/backend/main.py) is a FastAPI server with a JSON REST API: POST /api/predict for "
                  "one X-ray, POST /api/batch for up to 50 X-rays, /api/history for the saved scans and "
                  "/api/report/{id}.pdf for the patient report. It also serves the built front-end, so the whole "
                  "application runs from one local server. {lst:api} shows the prediction endpoint: the upload is "
                  "size-checked, the patient fields are validated, and the heavy analysis runs in a worker thread so "
                  "that the server stays responsive. The front-end is a React 19 single-page application written in "
                  "TypeScript, styled with Tailwind CSS and built with Vite; all fonts are bundled, so nothing is "
                  "loaded from the internet."),
            *small([next(b for b in sec(c, "Back-end API (FastAPI)") if b[0] == "code")]),
            ("h2", "Testing"),
            ("p", "Because this is a healthcare tool, the system was tested at four levels ({tab:tests}), and "
                  "**all 180 automated tests pass**."),
            ("tab", "tests", "Automated tests (all passing)",
             ["Level", "Tests", "What is checked"],
             [
                 ["ML contract (ml/test_inference.py)", "24", "Result format, image sizes, every image mode, 16-bit "
                  "DICOM, rejection of photographs, blank and noise images"],
                 ["Back-end (app/backend/tests)", "35", "Every API endpoint, bad and huge files, mixed batches, "
                  "history create / read / update / delete, PDF reports"],
                 ["End-to-end (tests/)", "121", "Real model + headless browser: 12 demo X-rays, 40+ random test "
                  "images, non-X-rays, path-traversal and script-injection attempts, Tamil and Hindi names in the "
                  "PDF, 6 screen-size / theme combinations, server down and back"],
                 ["Front-end", "–", "ESLint and the TypeScript build: zero problems"],
                 ["Total", "180", "All passing"],
             ], [1.85, 0.55, 3.6], {"size": 10, "align": ["L", "C", "L"], "bold_last": True}),
        ]


def short_ch7():
    c = ch7()
    cmroc = side_by_side(FIG / "confusion_matrix_test.png", FIG / "roc_curve_test.png", RFIG / "cm_roc_test.png")
    blocks = [c[0]] + without(sec(c, "Training Behaviour"), "curves1", "curves2", "curves3") \
        + sec(c, "Official Test Results") + [
            ("h2", "Confusion Matrix and ROC Curve"),
            ("p", "{fig:cmroc} shows the confusion matrix of the final ensemble (left) and the ROC curves of the "
                  "ensemble and its members (right). Of the 34 errors, **33 are false positives** (normal X-rays "
                  "labelled PNEUMONIA) and only **one is a false negative** (a missed pneumonia). The ROC curves rise "
                  "steeply towards the top-left corner, with AUC values between 0.981 and 0.988, and the marked "
                  "operating point of the ensemble sits at very high sensitivity, which reflects the low "
                  "validation-chosen threshold."),
            ("fig", "cmroc", cmroc, 6.0, "Confusion matrix (left) and ROC curves (right) on the official test set"),
        ] + sec(c, "Grad-CAM Explanations") + sec(c, "Comparison with Published Work") \
        + without(sec(c, "Discussion of the 95% Target"), "posthoc")
    return subst(blocks, [
        ("{tab:runs} summarises the three training runs and {fig:curves1} to {fig:curves3} show the training and "
         "validation curves.",
         "All settings (epochs, ensemble members, test-time augmentation, temperature and threshold) were chosen on "
         "the 747-image validation split; the official 624-image test set was then scored **once**, and nothing was "
         "re-trained or re-thresholded afterwards. {tab:runs} summarises the three training runs."),
        ("would have scored with other thresholds ({tab:posthoc}). With a threshold of 0.5",
         "would have scored with other thresholds. With a threshold of 0.5"),
        ("would have been 95.8%.", "would have been 95.8% (sensitivity 98.7%, specificity 91.0%)."),
    ])


def short_ch8():
    w = 4.8
    pdf_path, _ = pdf_page_image()
    return [
        ("chapter", 8, "Application and Screenshots"),
        ("h2", "Overview"),
        ("p", "The trained ensemble is delivered through an offline web application. A double-click on start.bat "
              "starts the server on the local computer and opens the browser; the status pill in the top bar changes "
              "to **Model ready** once the model is loaded. The navigation bar gives access to seven pages: Scan, "
              "Triage, History, CURB-65, Learn, Model and About. All screenshots were taken from the running "
              "application with the real trained model; the patient details are fictitious demo data."),
        ("h2", "Scan Page"),
        ("p", "The user drops a chest X-ray on the upload area, browses for a file or pastes an image (JPG, PNG, BMP, "
              "WEBP, TIFF or DICOM). Patient details are optional and are printed on the PDF report. A gallery of "
              "sample X-rays from the test set lets a teacher or student try the model at once ({fig:scan})."),
        shot_fig("scan", "01_scan_home", "Scan page with the upload area and optional patient details", width_in=w),
        ("h2", "Result with Grad-CAM Heat Map"),
        ("p", "The result screen ({fig:result}) shows the verdict, the calibrated pneumonia probability on a 0–100 "
              "ruler with the decision threshold marked, the confidence, the risk level and the inference time. The "
              "X-ray viewer shows the Grad-CAM heat map with an opacity slider, zoom, pan and a side-by-side view. "
              "Below the verdict the page gives a plain-English explanation, next steps and the disclaimer."),
        shot_fig("result", "03_scan_result", "Result screen for a pneumonia X-ray with the Grad-CAM heat map",
                 width_in=w),
        ("h2", "Rejection of Non-X-ray Images"),
        ("p", "If the image is not a chest X-ray, the X-ray gate turns it away with a friendly reason; no prediction "
              "is made and nothing is saved ({fig:reject})."),
        shot_fig("reject", "05_scan_rejected", "A colour photograph rejected by the X-ray gate", width_in=w),
        ("h2", "Patient PDF Report"),
        ("p", "A one-click PDF report ({fig:pdf}) contains the patient details, the result with probability and risk "
              "level, the X-ray with its heat map, the explanation, next steps, the disclaimer and the model version. "
              "It is made on the local computer, so it works offline."),
        ("fig", "pdf", pdf_path, 3.3,"First page of a patient PDF report generated by the application"),
        ("h2", "Triage Queue (Doctor Mode)"),
        ("p", "The Triage page accepts up to 50 X-rays at once. As results arrive, the queue re-orders itself so that "
              "the most likely pneumonia cases rise to the top, high-risk results are flagged as urgent, and the "
              "queue can be exported as CSV ({fig:triage})."),
        shot_fig("triage", "07_triage_done", "Completed triage queue sorted by pneumonia probability", width_in=w),
        ("h2", "CURB-65 Severity Calculator"),
        ("p", "For adults with pneumonia, the CURB-65 page ({fig:curb}) computes the standard severity score of "
              "Lim et al. [5] and shows the risk group, the 30-day mortality (1.5% for scores 0–1, 9.2% for 2 and 22% "
              "for 3–5) and the suggested care setting. Without a urea value it switches to CRB-65."),
        shot_fig("curb", "10_curb65", "CURB-65 severity calculator (top part of the page)", max_ratio=0.75,
                 width_in=w),
        ("h2", "Model Page"),
        ("p", "The Model page is designed for the classroom. It shows the official test accuracy, "
              "sensitivity, specificity and ROC-AUC, the confusion matrix, how ResNet’s skip connection works, the "
              "ensemble members, the dataset and the limitations. A Learn page with sourced health information "
              "(WHO, NHS, CDC) and an About page complete the application."),
    ]


def short_ch9():
    c = ch9()
    return [c[0],
            ("h2", "Conclusion"),
            ("p", "This project built **PneumoScan AI**, a complete and explainable system that detects pneumonia in "
                  "children’s chest X-rays with an ensemble of three fine-tuned ResNets. Every setting was chosen on a "
                  "patient-level validation split, and the official 624-image test set was scored only once. The "
                  "system reached an accuracy of **94.55%**, a sensitivity of **99.74%** (one missed pneumonia out of "
                  "390), a specificity of **85.90%** and a ROC-AUC of **0.9867**: well above the published ResNet "
                  "baselines on the same test set, although the 95% target was missed by three images. Grad-CAM heat "
                  "maps explain each decision, non-X-ray images are rejected, and the offline application adds PDF "
                  "reports, a triage queue, scan history and a CURB-65 calculator."),
            ("h2", "Limitations"),
            ("bullets", [
                "Trained and tested on X-rays of children aged 1–5 from one hospital; it may be less accurate on "
                "adults or other X-ray machines [13].",
                "Only two classes; it cannot tell bacterial from viral pneumonia or find other lung diseases.",
                "Most errors are false alarms on normal X-rays (specificity 85.9%), and some heat maps highlight the "
                "“R” marker or burned-in text.",
                "It is a student project for decision support, not a certified medical device.",
            ]),
            ("h2", "Future Enhancements"),
            ("bullets", [
                "Train on larger, multi-centre and adult data, including Indian hospitals.",
                "Add lung segmentation or mask burned-in text so the model looks only at the lungs.",
                "Classify bacterial and viral pneumonia and other chest findings.",
                "A light mobile version for primary health centres, in regional languages.",
            ]),
            ]


def references(r):
    r.front_heading("References", toc=True)
    for i, ref in enumerate(REFERENCES, 1):
        par = r.doc.add_paragraph()
        f = par.paragraph_format
        f.left_indent = Inches(0.45)
        f.first_line_indent = Inches(-0.45)
        f.tab_stops.add_tab_stop(Inches(0.45))
        f.line_spacing = 1.0
        f.space_after = Pt(5)
        f.alignment = WD_ALIGN_PARAGRAPH.LEFT
        add_inline(par, f"[{i}]\t" + ref, size=10.5)


def blocks():
    body = (short_ch1() + short_ch2() + short_ch3() + short_ch4() + short_ch5() + short_ch6() + short_ch7()
            + short_ch8() + short_ch9())
    return ([("raw", cover), ("section", "front"), ("raw", abstract), ("raw", contents)]
            + renumber(body) + [("raw", references)])


def main():
    prep_images()
    b = blocks()
    # every reference [n] must be cited somewhere in the text
    text = repr(b)
    uncited = [n for n in range(1, len(REFERENCES) + 1) if not re.search(rf"\[{n}\]|\[\d+\], \[{n}\]", text)]
    if uncited:
        raise SystemExit(f"uncited references: {uncited}")
    r = Report()
    r.render(b)
    for st in r.doc.styles:   # tighter contents so it fits on one page
        if st.element.name_val in ("toc 1", "toc 2"):
            f = st.paragraph_format
            f.space_before, f.space_after, f.line_spacing = Pt(10), Pt(4), 1.15
            st.font.size = Pt(12)
    # let long tables break across pages (the header row repeats) instead of jumping whole to the next page
    for t in r.doc.tables:
        if len(t.rows) > 6:
            for row in t.rows[1:]:
                for cell in row.cells:
                    for par in cell.paragraphs:
                        par.paragraph_format.keep_with_next = False
    r.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    main()
