"""Team report in the department's case-study format (cover with logo, 9 numbered sections, page border,
double-line tables, screenshots with italic captions).

Output: report/PneumoScan_AI_Team_Report.docx (+ .pdf via word_finalize.ps1)

Run:  .venv\\Scripts\\python.exe report\\make_code_shots.py      (code + terminal screenshots)
      .venv\\Scripts\\python.exe report\\build_team_report.py
      powershell -File report\\word_finalize.ps1 -Docx report\\PneumoScan_AI_Team_Report.docx
                                                -Pdf  report\\PneumoScan_AI_Team_Report.pdf
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from docx import Document  # noqa: E402
from docx.enum.section import WD_SECTION  # noqa: E402,F401
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT  # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK  # noqa: E402
from docx.oxml import OxmlElement, parse_xml  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Inches, Pt, RGBColor  # noqa: E402
from PIL import Image  # noqa: E402

from content_end import REFERENCES as ALL_REFS  # noqa: E402
from docx_engine import (M_NS, W_NS, _set_fonts, add_field, add_inline, mbar, mfrac, mnary, mp, mparen,  # noqa: E402
                         msub, msubsup, msup, mt, shade)
from paths import FIG, ROOT, SHOTS  # noqa: E402

OUT = HERE / "PneumoScan_AI_Team_Report.docx"
CS = HERE / "figures" / "case_study"
FONT = "Times New Roman"
BLUE = RGBColor(0x4F, 0x81, 0xBD)
NAVY = RGBColor(0x2F, 0x54, 0x96)
TEXT_W = 8.27 - 1.15 - 1.05

# references, in order of first citation (numbers are taken from the full report's list)
REF_ORDER = [1, 2, 17, 14, 16, 3, 4, 5, 6, 8, 11, 13, 23, 24, 25, 26, 27, 28, 29, 30, 21, 22, 12]
R = {orig: i + 1 for i, orig in enumerate(REF_ORDER)}


def c(*orig):
    """Citation text like [3], [5] using the new numbering."""
    return ", ".join(f"[{R[o]}]" for o in orig)


# ----------------------------------------------------------------------------- document helpers
class Doc:
    def __init__(self):
        self.d = Document()
        self.fig_no = 0
        self.tab_no = 0
        self.labels = {}
        self.known = {}
        self._styles()
        s = self.d.sections[0]
        s.page_width, s.page_height = Inches(8.27), Inches(11.69)
        s.left_margin, s.right_margin = Inches(1.15), Inches(1.05)
        s.top_margin, s.bottom_margin = Inches(0.95), Inches(0.9)
        s.header_distance, s.footer_distance = Inches(0.45), Inches(0.45)
        s.different_first_page_header_footer = True
        self._page_border(s)
        fp = s.footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_field(fp, "PAGE", "1", size=10)

    def _styles(self):
        st = self.d.styles
        rpr = st.element.find(qn("w:docDefaults")).find(qn("w:rPrDefault")).find(qn("w:rPr"))
        _set_fonts(rpr, FONT)
        n = st["Normal"]
        n.font.name, n.font.size = FONT, Pt(12)
        _set_fonts(n.element.get_or_add_rPr(), FONT)
        pf = n.paragraph_format
        pf.line_spacing, pf.space_before, pf.space_after = 1.15, Pt(0), Pt(6)
        pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for name, size, color, italic, before, after in (("Heading 1", 16, BLUE, False, 14, 8),
                                                         ("Heading 2", 12.5, BLUE, True, 10, 4),
                                                         ("Heading 3", 12, RGBColor(0, 0, 0), False, 8, 3)):
            h = st[name]
            h.font.name, h.font.size, h.font.bold, h.font.italic = FONT, Pt(size), True, italic
            h.font.color.rgb = color
            _set_fonts(h.element.get_or_add_rPr(), FONT)
            f = h.paragraph_format
            f.space_before, f.space_after, f.keep_with_next, f.line_spacing = Pt(before), Pt(after), True, 1.1
            f.alignment = WD_ALIGN_PARAGRAPH.LEFT
        lb = st["List Bullet"]
        lb.font.name, lb.font.size = FONT, Pt(12)
        lb.paragraph_format.space_after = Pt(2)
        lb.paragraph_format.line_spacing = 1.15
        lb.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for lvl in (1, 2):
            s = st[f"TOC {lvl}"] if f"TOC {lvl}" in [x.name for x in st] else st.add_style(f"TOC {lvl}", 1)
            s.font.name, s.font.size, s.font.bold = FONT, Pt(12 if lvl == 1 else 11.5), lvl == 1
            s.paragraph_format.space_before = Pt(7 if lvl == 1 else 0)
            s.paragraph_format.space_after = Pt(2)
            s.paragraph_format.left_indent = Inches(0 if lvl == 1 else 0.35)
            from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER
            s.paragraph_format.tab_stops.add_tab_stop(Inches(TEXT_W), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
            s.element.name_val = f"toc {lvl}"

    @staticmethod
    def _page_border(section):
        sect = section._sectPr
        b = OxmlElement("w:pgBorders")
        b.set(qn("w:offsetFrom"), "page")
        for side in ("top", "left", "bottom", "right"):
            e = OxmlElement(f"w:{side}")
            e.set(qn("w:val"), "single")
            e.set(qn("w:sz"), "6")
            e.set(qn("w:space"), "24")
            e.set(qn("w:color"), "000000")
            b.append(e)
        sect.find(qn("w:pgMar")).addnext(b)

    def ref(self, text):
        def sub(m):
            k = m.group(1)
            if k == 'figs:app':
                a, b = self.known.get('fig:app_first', 'Figure ?'), self.known.get('fig:app_last', 'Figure ?')
                return 'Figures ' + a.split()[-1] + '–' + b.split()[-1]
            return self.known.get(k, '??')
        return re.sub(r'\{((?:fig|tab|figs):[\w]+)\}', sub, text)

    # -------------------------------------------------------------- blocks
    def p(self, text, align=None, size=None, bold=False, italic=False, before=None, after=None, color=None,
          keep=False, spacing=None):
        par = self.d.add_paragraph()
        add_inline(par, self.ref(text), size=size, bold=bold, italic=italic)
        f = par.paragraph_format
        if align is not None:
            f.alignment = align
        if before is not None:
            f.space_before = Pt(before)
        if after is not None:
            f.space_after = Pt(after)
        if spacing is not None:
            f.line_spacing = spacing
        if keep:
            f.keep_with_next = True
        if color is not None:
            for r in par.runs:
                r.font.color.rgb = color
        return par

    def h1(self, text, new_page=False):
        par = self.d.add_paragraph(text, style="Heading 1")
        par.paragraph_format.page_break_before = new_page

    def h2(self, text):
        self.d.add_paragraph(text, style="Heading 2")

    def h3(self, text):
        self.d.add_paragraph(text, style="Heading 3")

    def bullets(self, items):
        for it in items:
            add_inline(self.d.add_paragraph(style="List Bullet"), it)

    def numbered(self, items):
        for i, it in enumerate(items, 1):
            par = self.d.add_paragraph()
            f = par.paragraph_format
            f.left_indent, f.first_line_indent = Inches(0.3), Inches(-0.3)
            f.space_after = Pt(2)
            f.tab_stops.add_tab_stop(Inches(0.3))
            add_inline(par, f"{i}.\t" + it)

    def figure(self, path, width, caption, key=None):
        self.fig_no += 1
        if key:
            self.labels[f'fig:{key}'] = f'Figure {self.fig_no}'
        par = self.d.add_paragraph()
        f = par.paragraph_format
        f.alignment = WD_ALIGN_PARAGRAPH.CENTER
        f.keep_with_next, f.space_before, f.space_after, f.line_spacing = True, Pt(4), Pt(0), 1.0
        par.add_run().add_picture(str(path), width=Inches(width))
        cap = self.d.add_paragraph()
        cap.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.space_after = Pt(8)
        cap.paragraph_format.line_spacing = 1.0
        add_inline(cap, f"Figure {self.fig_no}. {caption}", size=11, italic=True)

    def table(self, caption, headers, rows, widths, size=10.5, align=None, bold_first_col=True, bold_last=False,
              key=None):
        self.tab_no += 1
        if key:
            self.labels[f'tab:{key}'] = f'Table {self.tab_no}'
        cap = self.d.add_paragraph()
        cap.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.keep_with_next = True
        cap.paragraph_format.space_before = Pt(4)
        cap.paragraph_format.space_after = Pt(3)
        add_inline(cap, f"Table {self.tab_no}. {caption}", size=11, italic=True, bold=False)
        t = self.d.add_table(rows=1 + len(rows), cols=len(headers))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        tblPr = t._tbl.tblPr
        bd = OxmlElement("w:tblBorders")
        for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
            e = OxmlElement(f"w:{side}")
            e.set(qn("w:val"), "double")
            e.set(qn("w:sz"), "4")
            e.set(qn("w:space"), "0")
            e.set(qn("w:color"), "000000")
            bd.append(e)
        tblPr.append(bd)
        lay = OxmlElement("w:tblLayout")
        lay.set(qn("w:type"), "fixed")
        tblPr.append(lay)
        mar = OxmlElement("w:tblCellMar")
        for side, v in (("top", 40), ("bottom", 40), ("left", 90), ("right", 90)):
            e = OxmlElement(f"w:{side}")
            e.set(qn("w:w"), str(v))
            e.set(qn("w:type"), "dxa")
            mar.append(e)
        tblPr.append(mar)
        amap = {"L": WD_ALIGN_PARAGRAPH.LEFT, "C": WD_ALIGN_PARAGRAPH.CENTER}
        align = align or ["L"] * len(headers)
        for ri, row in enumerate([headers] + rows):
            tr = t.rows[ri]
            trPr = tr._tr.get_or_add_trPr()
            trPr.append(OxmlElement("w:cantSplit"))
            if ri == 0:
                trPr.append(OxmlElement("w:tblHeader"))
            for ci, val in enumerate(row):
                cell = tr.cells[ci]
                cell.width = Inches(widths[ci])
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                par = cell.paragraphs[0]
                f = par.paragraph_format
                f.space_after, f.line_spacing = Pt(0), 1.0
                f.alignment = WD_ALIGN_PARAGRAPH.CENTER if ri == 0 else amap[align[ci]]
                if (len(rows) <= 6 or ri == 0) and ri < len(rows):
                    f.keep_with_next = True
                bold = ri == 0 or (bold_first_col and ci == 0) or (bold_last and ri == len(rows))
                add_inline(par, str(val), size=size, bold=bold)
                if ri == 0:
                    shade(cell._tc.get_or_add_tcPr(), "DCE6F1")
        for gc, w in zip(t._tbl.tblGrid.findall(qn("w:gridCol")), widths):
            gc.set(qn("w:w"), str(int(w * 1440)))
        sp = self.d.add_paragraph()
        sp.paragraph_format.space_after = Pt(0)
        sp.paragraph_format.line_spacing = Pt(8)

    def table_k(self, key, *a, **k):
        return self.table(*a, key=key, **k)

    def eq(self, omml):
        par = self.d.add_paragraph()
        par.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.space_before, par.paragraph_format.space_after = Pt(2), Pt(6)
        par._p.append(parse_xml(f'<m:oMathPara xmlns:m="{M_NS}" xmlns:w="{W_NS}"><m:oMath>{omml}</m:oMath>'
                                f'</m:oMathPara>'))

    def page_break(self):
        self.d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# ----------------------------------------------------------------------------- images
def crop_ratio(src, ratio):
    im = Image.open(src).convert("RGB")
    w, h = im.size
    if h / w > ratio:
        im = im.crop((0, 0, w, int(w * ratio)))
    return im


def combine(parts, out, gap=36, height=900, labels=True):
    """Put screenshots side by side at the same height, with (a) (b) labels underneath."""
    from PIL import ImageDraw, ImageFont
    ims = [p.resize((round(p.width * height / p.height), height), Image.Resampling.LANCZOS) for p in parts]
    lab_h = 70 if labels else 0
    W = sum(i.width for i in ims) + gap * (len(ims) - 1)
    canvas = Image.new("RGB", (W, height + lab_h), "white")
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/timesi.ttf", 46)
    except OSError:
        font = ImageFont.load_default()
    x = 0
    for k, im in enumerate(ims):
        canvas.paste(im, (x, 0))
        draw.rectangle([x, 0, x + im.width - 1, height - 1], outline=(170, 170, 170), width=2)
        if labels:
            t = f"({'abcd'[k]})"
            tw = draw.textlength(t, font=font)
            draw.text((x + (im.width - tw) / 2, height + 12), t, fill=(0, 0, 0), font=font)
        x += im.width + gap
    canvas.save(out, optimize=True)
    return out


def shot(name, theme="light", size="1280x720", ratio=0.5625):
    return crop_ratio(SHOTS / f"{name}_{size}_{theme}.png", ratio)


def make_app_figures():
    figs = {}
    figs["scan"] = combine([shot("01_scan_home"), shot("02_scan_analysing")], CS / "app_scan.png")
    figs["result"] = combine([shot("03_scan_result"), shot("04_viewer_side_by_side")], CS / "app_result.png")
    figs["explain"] = combine([crop_ratio(SHOTS / "03b_scan_result_full_1280x720_light.png", 1.25),
                               crop_ratio(SHOTS / "15_pdf_report_page1.png", 1.42)], CS / "app_explain_pdf.png")
    figs["reject"] = combine([shot("05_scan_rejected"), shot("06_triage_running")], CS / "app_reject_triage.png")
    figs["triage"] = combine([shot("07_triage_done"), shot("08_history_grid")], CS / "app_triage_history.png")
    figs["curb"] = combine([shot("09_history_list"), shot("10_curb65")], CS / "app_list_curb.png")
    figs["learn"] = combine([shot("11_learn"), shot("12_model")], CS / "app_learn_model.png")
    figs["dark"] = combine([shot("03_scan_result", "dark"),
                            crop_ratio(SHOTS / "03_scan_result_390x844_light.png", 2.0),
                            crop_ratio(SHOTS / "01_scan_home_390x844_dark.png", 2.0)], CS / "app_dark_mobile.png")
    cm = Image.open(FIG / "confusion_matrix_test.png").convert("RGB")
    roc = Image.open(FIG / "roc_curve_test.png").convert("RGB")
    figs["cmroc"] = combine([cm, roc], CS / "cm_roc.png", labels=True, height=1100)
    return figs


# ----------------------------------------------------------------------------- content
def cover(doc):
    d = doc
    d.p("", after=40)
    par = d.d.add_paragraph()
    par.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.add_run().add_picture(str(CS / "crescent_logo.png"), width=Inches(5.0))
    d.p("", after=40)
    d.p("CSDX 530 – DEEP LEARNING", align=WD_ALIGN_PARAGRAPH.CENTER, size=26, bold=True, color=NAVY, after=10,
        spacing=1.0)
    d.p("Mini Project Report: Pneumonia Detection Using ResNet", align=WD_ALIGN_PARAGRAPH.CENTER, size=22,
        bold=True, color=BLUE, after=8, spacing=1.05)
    d.p("PneumoScan AI – An Explainable Deep-Learning System for Chest X-ray Screening",
        align=WD_ALIGN_PARAGRAPH.CENTER, size=14, italic=True, after=150, spacing=1.0)
    right = WD_ALIGN_PARAGRAPH.RIGHT
    for text, bold in (("Submitted by:", True),
                       ("Umer Basith G  –  RRN: 230171601192", False),
                       ("Vignesh A  –  RRN: 230171601195", False),
                       ("B.Tech Artificial Intelligence & Data Science", False),
                       ("", False),
                       ("Submitted to: Mrs. Mahalakshmi R", False),
                       ("Assistant Professor / CSE", False),
                       ("Submitted on: 11th November 2026", False)):
        d.p(text, align=right, bold=bold, after=0, spacing=1.1)


def contents(doc):
    doc.page_break()
    par = doc.p("Table of Contents", align=WD_ALIGN_PARAGRAPH.CENTER, size=16, bold=True, color=BLUE, after=12)
    par.paragraph_format.keep_with_next = True
    t = doc.d.add_paragraph()
    t.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    add_field(t, 'TOC \\o "1-2" \\h \\z \\u', "Right-click and choose Update Field.")


def section1(doc):
    d = doc
    d.h1("1. Introduction to the Case Study", new_page=True)
    d.h2("Objective")
    d.p("This case study presents **PneumoScan AI**, a deep-learning system that detects **pneumonia** in "
        "paediatric chest X-ray images using **deep residual networks (ResNet)** " + c(1) + ". The objective is to "
        "build the complete pipeline end-to-end – **data preparation, transfer learning, model training, "
        "ensembling, calibration, explainability and deployment** – and to evaluate it honestly on the official, "
        "independent test set of 624 X-rays " + c(2, 17) + ". The project targets an accuracy of at least 95%, a "
        "**very high sensitivity** (so that children with pneumonia are not missed), a **visual explanation for "
        "every prediction**, and an easy-to-use **offline web application** for doctors, students and patients.")
    d.h2("Problem Statement")
    d.p("Pneumonia is an infection in which the air sacs of the lungs fill with pus and fluid. It caused "
        "**740,180 deaths of children under five in 2019**, 14% of all deaths in that age group " + c(14) + ". "
        "The chest X-ray is the most common imaging test used to confirm it, but reading X-rays needs trained "
        "radiologists, and India has only **about one radiologist per 100,000 people**, mostly in cities "
        + c(16) + ". Manual reading is slow, varies between readers, and films are usually read in the order "
        "they arrive, so an urgent case may wait behind routine ones. At the same time, many published "
        "deep-learning models are evaluated on re-split data, give no explanation, accept any image (even a "
        "photograph) and are never packaged as a usable tool. There is therefore a need for an **accurate, "
        "explainable, honestly evaluated and easy-to-use** system that gives a fast second opinion on a chest "
        "X-ray and helps prioritise patients, while leaving the final decision to a qualified doctor.")
    d.h2("Context")
    d.p("Deep learning, and in particular **convolutional neural networks (CNNs)**, learn image features directly "
        "from pixels. CheXNet, a 121-layer CNN, exceeded the average radiologist (F1 metric) for pneumonia on "
        "adult chest X-rays " + c(3) + ", and Kermany et al. showed that **transfer learning** from ImageNet can "
        "build an accurate paediatric pneumonia classifier from a few thousand X-rays " + c(2) + ". **ResNet** "
        "made very deep networks trainable with identity **skip connections** " + c(1) + ", and **Grad-CAM** "
        "shows which image regions drove a CNN’s decision " + c(4) + ". PneumoScan AI combines these techniques "
        "with probability calibration, an out-of-distribution check and a complete FastAPI + React application, "
        "and it runs fully offline on an ordinary laptop.")
    d.h2("Project Team")
    d.table("Team members", ["Name", "Register Number (RRN)", "Programme"],
            [["Umer Basith G", "230171601192", "B.Tech AI & DS"],
             ["Vignesh A", "230171601195", "B.Tech AI & DS"]], [2.2, 2.0, 1.9], align=["L", "C", "C"])


def section2(doc):
    d = doc
    d.h1("2. Understanding of Tool Used and Techniques")
    d.h3("Overview of ResNet and the PneumoScan AI Pipeline")
    d.p("A **Residual Network (ResNet)** is a deep CNN built from residual blocks. Instead of learning a mapping "
        "H(x) directly, each block learns the residual F(x) = H(x) − x and adds its input back through an "
        "identity shortcut " + c(1) + ":")
    d.eq(mt("y = F") + mparen(mt("x, {") + msub(mt("W"), mt("i")) + mt("}")) + mt(" + x"))
    d.p("The shortcut gives gradients a direct path through the network, which solved the **degradation "
        "problem** of very deep plain networks and won ILSVRC 2015 " + c(1) + ". PneumoScan AI fine-tunes three "
        "ImageNet-pretrained ResNets, combines them into an **ensemble**, calibrates the output into a "
        "trustworthy probability, explains each decision with **Grad-CAM** and refuses images that are not chest "
        "X-rays.")
    d.figure(FIG / "residual_block_diagram.png", 2.2, "Bottleneck residual block with an identity shortcut "
                                                      "(used in ResNet-50).")
    d.h3("Core Techniques")
    d.bullets([
        "**Residual Learning (ResNet-34 / ResNet-50):** basic blocks (two 3×3 convolutions) in ResNet-34 and "
        "bottleneck blocks (1×1, 3×3, 1×1) in ResNet-50, with stages of 3, 4, 6 and 3 blocks.",
        "**Transfer Learning:** weights pretrained on ImageNet " + c(23) + "; the 1000-class layer is replaced by "
        "Dropout(0.2) and a 2-class linear layer, and **all layers are fine-tuned**, the backbone at one third of "
        "the head’s learning rate.",
        "**Weighted Cross-Entropy with Label Smoothing:** class weights 1.94 (NORMAL) and 0.67 (PNEUMONIA) "
        "balance the 1 : 3 class ratio; label smoothing ε = 0.1 " + c(24) + " prevents over-confidence.",
        "**AdamW, Cosine Schedule, Mixed Precision and EMA:** AdamW " + c(25) + " with one warm-up epoch and "
        "cosine decay; fp16 automatic mixed precision " + c(26) + " fits training into a 6 GB GPU; an exponential "
        "moving average of the weights gives a smoother final model.",
        "**Ensemble with Test-Time Augmentation:** three ResNets each score the X-ray and its mirror image; the "
        "six logit margins are averaged.",
        "**Temperature Scaling and Youden’s J Threshold:** the averaged margin is calibrated with a temperature "
        "T = 0.602 " + c(27) + ", and the decision threshold t = 0.0743 maximises Youden’s J " + c(28) + "; both "
        "are fitted on validation data only.",
        "**Grad-CAM Explainability:** gradient-weighted class activation maps " + c(4) + " from the last residual "
        "stage are averaged over the ensemble and overlaid on the X-ray.",
        "**X-ray Gate (Out-of-Distribution Detection):** colour, blank and size checks plus a **Mahalanobis "
        "distance** " + c(29) + " with a Ledoit-Wolf covariance " + c(30) + " on ResNet features reject photographs, "
        "documents and other non-X-ray images.",
    ])
    d.table("Models used and their key features",
            ["Model Version", "Key Features", "Input Requirements"],
            [["ResNet-50 @ 384 px (r50_384_s1)", "Bottleneck blocks, 23.5 M parameters, ImageNet V2 weights, "
              "batch 24, seed 1", "384 × 384 grayscale X-ray copied to 3 channels"],
             ["ResNet-34 @ 384 px (r34_384_s2)", "Basic blocks, 21.3 M parameters, ImageNet V1 weights, batch 32, "
              "seed 2", "384 × 384 grayscale X-ray copied to 3 channels"],
             ["ResNet-50 @ 448 px (r50_448_s3)", "Higher input resolution for finer detail, batch 16, seed 3",
              "448 × 448 grayscale X-ray copied to 3 channels"],
             ["Final Ensemble (PneumoScan AI)", "3 members × 2 views averaged, temperature T = 0.602, threshold "
              "0.0743, Grad-CAM, X-ray gate", "Any frontal chest X-ray: JPG, PNG, BMP, WEBP, TIFF or DICOM, "
              "up to 25 MB"]],
            [1.75, 2.45, 1.85])
    d.h3("Methodological Advantages")
    d.bullets([
        "Analyses an X-ray in about **0.4 s on the GPU** and about 1.25 s on a CPU-only laptop.",
        "**Honest evaluation:** every setting is chosen on validation data and the official test set was scored "
        "**exactly once**.",
        "**Explainable:** a Grad-CAM heat map for every prediction lets a doctor check the model’s reasoning.",
        "**Safe input handling:** non-X-ray images are rejected instead of receiving a meaningless diagnosis.",
        "**Private and offline:** runs on 127.0.0.1 without internet; patient data never leave the computer.",
        "**Reproducible:** fixed random seeds, logged training runs and a single command per pipeline step.",
    ])
    d.h3("Technology Stack")
    d.table("Technology stack of PneumoScan AI",
            ["Layer", "Technology (version)", "Purpose"],
            [["Language", "Python 3.11.9, TypeScript 5.8.3", "ML pipeline and back-end; front-end"],
             ["Deep learning", "PyTorch 2.11.0 + CUDA 12.8 " + c(21) + ", torchvision 0.26.0",
              "ResNet models, ImageNet weights, GPU training and inference"],
             ["Machine learning / data", "scikit-learn 1.9.1 " + c(22) + ", NumPy 2.4.6, SciPy 1.17.1, "
              "pandas 3.1.1", "Metrics, patient-level split, Ledoit-Wolf covariance, temperature fitting"],
             ["Image processing", "Pillow 13.0.0, OpenCV 5.0, pydicom 3.0.2",
              "Image decoding, colour maps, DICOM support"],
             ["Visualisation", "matplotlib 3.11.2, scikit-image 0.26.0", "Report figures; non-X-ray test images"],
             ["Back-end", "FastAPI 0.162.2, Uvicorn 0.54.0", "REST API and local web server"],
             ["Database", "SQLite (Python sqlite3)", "Local scan history"],
             ["PDF reports", "ReportLab 5.1.0, uharfbuzz 0.57.0", "Patient reports, incl. Tamil / Hindi text"],
             ["Front-end", "React 19.1, Vite 7.3.7, Tailwind CSS 4.1.18, React Router 7.18.5, Motion 12.43, "
              "lucide-react 0.577", "User interface, routing, animation and icons"],
             ["Testing", "pytest 9.2.0, Playwright 1.64.1 (headless Chromium), ESLint 9.39.5",
              "Unit, API and end-to-end browser tests; code quality"],
             ["Hardware", "NVIDIA RTX 3050 Laptop GPU (6 GB), Intel Core i5-12450HX, 16 GB RAM, Windows 11",
              "Training, testing and the classroom demo"]],
            [1.35, 2.75, 1.95])


def section3(doc):
    d = doc
    d.h1("3. Data Collection and Preprocessing")
    d.h2("Chest X-ray Dataset")
    d.p("The project uses the public **paediatric chest X-ray dataset of Kermany et al.** " + c(2, 17) + ", "
        "collected at Guangzhou Women and Children’s Medical Center from children aged 1–5 years and labelled by "
        "expert physicians. It is one of the most widely used benchmarks for pneumonia detection and comes with an "
        "**official, independent test set**. The archive was downloaded from Mendeley Data without any login and "
        "verified against its published SHA-256 hash.")
    d.table("Summary of the dataset", ["Item", "Value"],
            [["Source", "Mendeley Data, “Labeled OCT and Chest X-Ray Images for Classification”, v2, DOI "
                        "10.17632/rscbjbr9sj.2 (ChestXRay2017.zip, 1,235,512,464 bytes)"],
             ["Licence", "CC BY 4.0 (credit: Kermany et al., Cell, 2018)"],
             ["Total images", "5,856 frontal chest X-rays (JPEG): 1,583 NORMAL and 4,273 PNEUMONIA"],
             ["Official training set", "5,232 images: 1,349 NORMAL, 3,883 PNEUMONIA (2,538 bacterial, 1,345 viral)"],
             ["Official test set", "624 images: 234 NORMAL, 390 PNEUMONIA (used once, for the final evaluation)"],
             ["Image size", "Median 1281 × 888 pixels; width 384–2916 pixels; 283 RGB-encoded grayscale files"]],
            [1.65, 4.4])
    d.table("Preprocessing pipeline", ["Stage", "Tool / Method", "Purpose"],
            [["Integrity check", "SHA-256 hash (hashlib)", "Make sure the download matches the published file"],
             ["Count verification", "ml/prepare_data.py", "Exact official image counts per split and class"],
             ["Patient-level split", "StratifiedGroupKFold (7 folds, seed 42)",
              "Validation set with no child shared with training"],
             ["Grayscale conversion", "Pillow (ITU-R 601 luma), DICOM min–max scaling, EXIF rotation",
              "Uniform 8-bit input from any image mode"],
             ["Canonical view + cache", "Lanczos resize to 512 × 512", "Whole chest always visible; fast loading"],
             ["Network input", "Resize to 384 / 448, 3 channels, ImageNet mean / std",
              "Match the pretrained ResNet backbones"],
             ["Data augmentation", "torchvision transforms v2", "Reduce over-fitting with realistic variation"],
             ["Class balancing", "Inverse-frequency loss weights w_c = N / (2 N_c)",
              "Handle about 3 pneumonia images per normal image"],
             ["Leakage checks", "SHA-1 hashes, 64 × 64 thumbnail correlation", "No shared patients or duplicates"]],
            [1.55, 2.4, 2.1])
    d.h3("Preprocessing and Augmentation Considerations")
    d.bullets([
        "Images are **squashed, not cropped**, to the square view so that no part of the lungs is ever cut off "
        "and the heat map maps back exactly onto the original image.",
        "Training augmentation: random resized crop (scale 0.75–1.0), horizontal flip, rotation ±10°, shift ±5%, "
        "brightness and contrast ±20%, Gaussian blur (p = 0.2) and sensor noise (σ = 0.02, p = 0.2).",
        "**Vertical flips are not used**, because an upside-down chest X-ray is not realistic.",
        "The same pre-processing code is used for training, evaluation and the web application, so the model "
        "always sees images in exactly the same way.",
    ])
    d.figure(HERE / "figures" / "sample_images.jpg", 5.4, "Sample training X-rays: NORMAL (top row) and "
                                                          "PNEUMONIA (bottom row).")
    d.h3("Data Quality Metrics")
    d.table("Images and patients in each split", ["Split", "NORMAL", "PNEUMONIA", "Total", "Patients",
                                                  "Pneumonia share"],
            [["Train", "1,157", "3,328", "4,485", "2,272", "74.2%"],
             ["Validation", "192", "555", "747", "378", "74.3%"],
             ["Test (official)", "234", "390", "624", "404", "62.5%"],
             ["Total", "1,583", "4,273", "5,856", "–", "73.0%"]],
            [1.4, 0.85, 1.05, 0.8, 0.85, 1.1], align=["L", "C", "C", "C", "C", "C"], bold_last=True)
    d.table("Leakage checks (run automatically by ml/prepare_data.py)", ["Check", "Result"],
            [["Patients in both training and validation", "0"],
             ["Exact duplicate files between test and train / validation", "0"],
             ["Near duplicates between test and train / validation (thumbnail correlation ≥ 0.99)",
              "0 (highest 0.968)"]],
            [4.6, 1.45], align=["L", "C"], bold_first_col=False)


def section4(doc, figs):
    d = doc
    d.h1("4. Analysis and Implementation")
    d.h3("Step 1: Environment Setup and Parameter Configuration")
    d.bullets([
        "Framework: **PyTorch 2.11.0 with CUDA 12.8** on an **NVIDIA RTX 3050 (6 GB)** laptop GPU.",
        "Backbones: torchvision **ResNet-34** and **ResNet-50** with ImageNet weights; 2-class head.",
        "Input resolution: **384 × 384** (two members) and **448 × 448** (one member).",
        "Loss: weighted cross-entropy (1.94 / 0.67) with **label smoothing 0.1**.",
        "Optimiser: **AdamW**, weight decay 0.01; learning rate 3 × 10⁻⁴ (head) and 1 × 10⁻⁴ (backbone).",
        "Schedule: 1 warm-up epoch, then **per-step cosine decay**; gradient clipping at norm 2.0.",
        "Precision: **fp16 mixed precision**; EMA of weights with decay 0.998.",
        "Epochs: up to 20, **early stopping** after 7 epochs without a better validation ROC-AUC.",
    ])
    d.figure(CS / "code_build_model.png", 5.3, "Building a ResNet with a two-class head (ml/common.py).")
    d.h3("Step 2: Data Preparation Pipeline")
    d.p("The data preparation script verifies the dataset, builds the 512 × 512 cache, carves the patient-level "
        "validation split out of the training images only, and runs the leakage checks ({fig:split}). The dataset "
        "module defines the training augmentation and the evaluation transform ({fig:tf}).")
    d.figure(CS / "code_prepare_split.png", 5.3, key="split", caption= "Patient-level stratified validation split and leakage checks "
                                                 "(ml/prepare_data.py).")
    d.figure(CS / "code_transforms.png", 5.3, key="tf", caption= "Training and evaluation transforms (ml/datasets.py).")
    d.h3("Step 3: Training the ResNet Models")
    d.p("Each member is trained with one command. For every step the learning rate is set from the warm-up / "
        "cosine schedule, the forward pass runs in fp16, the scaled loss is back-propagated, gradients are "
        "clipped and the EMA weights are updated ({fig:loop}). After each epoch the EMA model is evaluated on the "
        "validation set and the best checkpoint is kept. {fig:trainlog} is the real training log of the first member.")
    d.figure(CS / "code_train_loop.png", 5.3, key="loop", caption= "Core of the training loop (ml/train.py).")
    d.figure(CS / "term_train.png", 5.8, key="trainlog", caption= "Execution of the training command for ResNet-50 @ 384 px (real log).")
    d.table("Training runs on the RTX 3050 GPU (total training time 55.5 minutes)",
            ["Run", "Model", "Input", "Epochs run", "Best epoch", "Time (min)", "Best val AUC"],
            [["r50_384_s1", "ResNet-50", "384", "14", "7", "17.7", "0.9965"],
             ["r34_384_s2", "ResNet-34", "384", "17", "10", "13.9", "0.9971"],
             ["r50_448_s3", "ResNet-50", "448", "14", "7", "23.9", "0.9974"]],
            [1.05, 0.95, 0.6, 0.85, 0.85, 0.85, 0.95], align=["L", "L", "C", "C", "C", "C", "C"])
    d.figure(FIG / "training_curves_r50_384_s1.png", 6.0, "Training and validation curves of ResNet-50 @ 384 px.")
    d.h3("Step 4: Ensemble, Calibration and Threshold Selection")
    d.p("For each member m and view v (original and mirror), the logit margin is z = ℓ_PNEUMONIA − ℓ_NORMAL. The "
        "six margins are averaged and calibrated with a temperature T fitted on the validation set, and the "
        "threshold t maximises Youden’s J on validation:")
    d.eq(mt("p = σ") + mparen(mfrac(mbar(mt("z")), mt("T"))) + mt(",     J") + mparen(mt("t")) + mt(" = ")
         + mp("Sensitivity") + mparen(mt("t")) + mt(" + ") + mp("Specificity") + mparen(mt("t")) + mt(" − 1"))
    d.p("This gave **T = 0.602** and **t = 0.0743**. A prediction is PNEUMONIA when p ≥ t, and the app also shows "
        "a **risk level**: Low (p < 0.037), Moderate (0.037 ≤ p < 0.537) or High (p ≥ 0.537).")
    d.figure(CS / "code_calibration.png", 5.3, "Temperature scaling and Youden-J threshold (ml/evaluate.py).")
    d.h3("Step 5: Explainability (Grad-CAM) and the X-ray Gate")
    d.p("Grad-CAM weights each feature map A^k of layer4 by the average gradient of the class score and keeps the "
        "positive part " + c(4) + ":")
    d.eq(msubsup(mt("α"), mt("k"), mt("c")) + mt(" = ") + mfrac(mt("1"), mt("Z"))
         + mnary("∑", mt("i,j"), "", mfrac(mt("∂") + msup(mt("y"), mt("c")),
                                           mt("∂") + msubsup(mt("A"), mt("ij"), mt("k"))))
         + mt(",     ") + msup(mt("L"), mt("c")) + mt(" = ") + mp("ReLU")
         + mparen(mnary("∑", mt("k"), "", msubsup(mt("α"), mt("k"), mt("c")) + mt(" ") + msup(mt("A"), mt("k")))))
    d.figure(CS / "code_gradcam.png", 5.3, "Grad-CAM for torchvision ResNets (ml/gradcam.py).")
    d.p("The X-ray gate compares the 2048 pooled ResNet-50 features of an image with those of the training X-rays "
        "using a Mahalanobis distance; the cut-off (66.04) is 1.15 × the 99.5th percentile of validation distances.")
    d.figure(CS / "code_xray_gate.png", 5.3, "Distance, score and decision of the X-ray gate (ml/xray_gate.py).")
    d.h3("Step 6: Inference Pipeline")
    d.p("The application uses one class, **PneumoniaModel**, which loads the three members once, checks the image "
        "with the X-ray gate, runs the ensemble with test-time augmentation and returns the label, calibrated "
        "probability, risk level and three aligned images (input, heat map and overlay). It can also be run from "
        "the command line ({fig:infer}).")
    d.figure(CS / "code_inference.png", 5.3, "Ensemble decision inside PneumoniaModel.predict (ml/inference.py).")
    d.figure(CS / "term_inference.png", 5.8, key="infer", caption= "Running the inference module on a sample pneumonia X-ray (real "
                                              "output; images shown as base64 lengths).")
    d.h3("Step 7: Web Application Development")
    d.p("The trained model is delivered as a three-layer offline web application ({fig:arch}): a **React + "
        "TypeScript** single-page front-end, a **FastAPI** back-end with a JSON REST API, and the model and data "
        "layer (X-ray gate, ResNet ensemble, Grad-CAM, SQLite history). The API is listed in {tab:api}.")
    d.figure(HERE / "figures" / "system_architecture.png", 5.0, key="arch", caption= "Overall system architecture of PneumoScan AI.")
    d.table_k("api", "REST API endpoints (app/backend/main.py)", ["Method", "Path", "Purpose"],
            [["GET", "/api/health", "Status, model mode, device and model version"],
             ["GET", "/api/model-info", "Test metrics, model card and figure URLs"],
             ["POST", "/api/predict", "One X-ray (+ optional patient details) → result and saved scan"],
             ["POST", "/api/batch", "Up to 50 X-rays → results sorted by pneumonia probability"],
             ["GET", "/api/history", "Search, filter and page through saved scans"],
             ["GET / PATCH / DELETE", "/api/history/{id}", "Read, edit (patient details, notes) or delete a scan"],
             ["DELETE", "/api/history", "Clear all history"],
             ["GET", "/api/history/{id}/image/{kind}", "Saved input, overlay, heat-map or thumbnail image"],
             ["GET", "/api/report/{id}.pdf", "Patient PDF report"],
             ["GET", "/api/samples", "Demo X-rays from the test split"]],
            [1.45, 2.2, 2.4], bold_first_col=False)
    d.figure(CS / "code_api_predict.png", 5.3, "Prediction endpoint of the FastAPI back-end (app/backend/main.py).")
    d.figure(CS / "code_frontend_ruler.png", 5.3, "React component that draws the probability ruler with the "
                                                  "decision threshold (ProbabilityRuler.tsx).")
    d.figure(CS / "code_project_tree.png", 5.3, "Project folder structure and README of the codebase.")
    d.figure(CS / "term_start.png", 5.8, "Starting the application with start.bat (real output).")
    d.h3("Step 8: Testing and Validation")
    d.p("Because this is a healthcare tool, the system was tested at four levels and **all 180 automated tests "
        "pass** ({tab:tests}). {fig:tests} shows the real output of the model and back-end test suites.")
    d.table_k("tests", "Automated tests", ["Level", "Tests", "What is checked"],
            [["ML contract (ml/test_inference.py)", "24", "Result format, image sizes, every image mode, 16-bit "
              "DICOM, rejection of photographs, blank and noise images"],
             ["Back-end (app/backend/tests)", "35", "Every API endpoint, bad and huge files, mixed batches, "
              "history create / read / update / delete, PDF reports"],
             ["End-to-end (tests/)", "121", "Real model + headless browser: 12 demo X-rays, 40+ random test "
              "images, non-X-rays, path-traversal and script-injection attempts, Tamil and Hindi names in the "
              "PDF, 6 screen-size / theme combinations, server down and back"],
             ["Front-end", "–", "ESLint and the TypeScript build: zero problems"],
             ["Total", "180", "All passing"]],
            [1.9, 0.55, 3.6], align=["L", "C", "L"], bold_last=True)
    d.figure(CS / "term_tests.png", 5.8, key="tests", caption= "Model and back-end test suites passing (real output).")
    d.h3("Step 9: Application Features")
    d.p("{tab:features} lists every feature of the finished application, and {figs:app} show each screen, taken "
        "from the running application with the real trained model (patient details are fictitious demo data).")
    d.table_k("features", "Features of the PneumoScan AI application", ["Feature", "What it does", "Helps"],
            [["Scan page", "Drag-and-drop, browse or paste (Ctrl+V) an X-ray (JPG, PNG, BMP, WEBP, TIFF, DICOM, "
              "≤ 25 MB) or pick a sample from the test set", "Everyone"],
             ["Result + risk level", "Verdict, calibrated probability on a 0–100 ruler with the threshold, "
              "confidence, Low / Moderate / High risk, inference time", "Doctors, students"],
             ["Grad-CAM viewer", "Original / Heat map / Side-by-side views, opacity slider, zoom and pan "
              "(mouse and keyboard)", "Doctors, students"],
             ["Explanation and next steps", "Plain-English meaning of the result, recommended next steps and a "
              "responsible-AI disclaimer", "Patients"],
             ["Patient PDF report", "One-click report with patient details, result, heat map, explanation and "
              "disclaimer; Tamil and Hindi names supported", "Doctors, patients"],
             ["X-ray gate", "Turns away photographs, documents and blank images with a friendly reason; nothing "
              "is saved", "Everyone (safety)"],
             ["Triage queue", "Up to 50 X-rays at once with per-file progress, sorted by probability, urgent "
              "flags, filters, CSV export", "Doctors, hospitals"],
             ["Scan history", "Local SQLite history: search, filters, grid / list view, edit patient details and "
              "notes, re-download PDF, delete, clear all", "Doctors"],
             ["CURB-65 calculator", "Adult severity score " + c(5) + " (urea mmol/L or BUN mg/dL; CRB-65 without "
              "urea), 30-day mortality and care setting", "Doctors"],
             ["Learn page", "Pneumonia explained simply: danger signs, symptoms, children (WHO), causes, "
              "prevention, home care, X-ray signs, with sources", "Patients, families"],
             ["Model page", "Test accuracy, sensitivity, specificity, ROC-AUC, confusion matrix, figures, ResNet "
              "explainer, limitations", "Students, teachers"],
             ["About page", "Project, course, tech stack, dataset credit and disclaimer", "Everyone"],
             ["Dark mode and phone layout", "Light / dark themes remembered; responsive layout for phones and "
              "projectors", "Everyone"],
             ["Offline and private", "Runs on 127.0.0.1 with bundled fonts; no internet needed; data stay on the "
              "computer", "Hospitals, patients"]],
            [1.55, 3.35, 1.15], size=10)
    w = 5.7
    d.figure(figs["scan"], w, key="app_first", caption= "Scan page: (a) upload area, patient details and sample gallery; (b) analysis in "
                              "progress.")
    d.figure(figs["result"], w, "Result screen: (a) verdict, probability ruler, risk level and Grad-CAM heat map; "
                                "(b) side-by-side view of the X-ray and the heat map.")
    d.figure(figs["explain"], 4.4, "(a) Explanation, next steps and disclaimer below the result; (b) first page "
                                   "of the patient PDF report.")
    d.figure(figs["reject"], w, "(a) A colour photograph rejected by the X-ray gate; (b) triage queue analysing "
                                "several X-rays with per-file progress.")
    d.figure(figs["triage"], w, "(a) Completed triage queue sorted by pneumonia probability with urgent flags; "
                                "(b) scan history in grid view.")
    d.figure(figs["curb"], w, "(a) Scan history in list view with search and filters; (b) CURB-65 severity "
                              "calculator.")
    d.figure(figs["learn"], w, "(a) Learn page with sourced health information; (b) Model page with test-set "
                               "performance.")
    d.figure(figs["dark"], w, key="app_last", caption= "(a) Result screen in dark mode; (b) result and (c) scan page on a phone.")


def section5(doc, figs):
    d = doc
    d.h1("5. Results and Evaluation")
    d.p("All settings were fixed on the 747-image validation split; the final ensemble was then applied **once** to "
        "the official 624-image test set, and nothing was re-trained or re-thresholded afterwards.")
    d.h2("Prediction Summary")
    d.table("Final ensemble on the official test set (624 X-rays)", ["Metric", "Value", "Interpretation"],
            [["Accuracy", "94.55%", "590 of 624 X-rays classified correctly"],
             ["Sensitivity (Recall)", "99.74%", "389 of 390 pneumonia X-rays detected – only 1 missed"],
             ["Specificity", "85.90%", "201 of 234 normal X-rays correctly cleared"],
             ["Precision", "92.18%", "Of all PNEUMONIA predictions, 92% were correct"],
             ["F1-Score", "95.81%", "Strong balance of precision and recall"],
             ["ROC-AUC", "0.9867", "Excellent ranking of pneumonia above normal images"],
             ["PR-AUC", "0.9898", "High precision across almost all recall levels"],
             ["Balanced Accuracy", "92.82%", "Average of sensitivity and specificity"],
             ["Negative Predictive Value", "99.50%", "A NORMAL result is almost always truly normal (201 / 202)"]],
            [1.85, 0.85, 3.35], align=["L", "C", "L"])
    d.figure(figs["cmroc"], 6.0, "(a) Confusion matrix of the final ensemble; (b) ROC curves of the ensemble and "
                                 "its members on the test set.")
    d.h2("Validation and Member Results")
    d.table("Validation results (747 images; settings fitted on validation)",
            ["Model", "T", "Threshold", "Accuracy", "Sensitivity", "Specificity", "ROC-AUC"],
            [["ResNet-50 @ 384", "0.609", "0.038", "98.39%", "98.20%", "98.96%", "0.9974"],
             ["ResNet-34 @ 384", "0.612", "0.067", "98.13%", "97.66%", "99.48%", "0.9977"],
             ["ResNet-50 @ 448", "0.618", "0.044", "98.13%", "98.38%", "97.40%", "0.9972"],
             ["Ensemble (final)", "0.602", "0.074", "98.39%", "98.20%", "98.96%", "0.9980"]],
            [1.4, 0.55, 0.8, 0.8, 0.85, 0.85, 0.8], align=["L"] + ["C"] * 6, bold_last=True)
    d.table("Official test results of each member and the ensemble",
            ["Model", "Accuracy", "Precision", "Sensitivity", "Specificity", "F1", "ROC-AUC"],
            [["ResNet-50 @ 384", "91.99%", "88.81%", "99.74%", "79.06%", "93.96%", "0.9811"],
             ["ResNet-34 @ 384", "94.87%", "92.82%", "99.49%", "87.18%", "96.04%", "0.9884"],
             ["ResNet-50 @ 448", "91.67%", "88.41%", "99.74%", "78.21%", "93.73%", "0.9828"],
             ["Ensemble (final)", "94.55%", "92.18%", "99.74%", "85.90%", "95.81%", "0.9867"]],
            [1.4, 0.8, 0.8, 0.85, 0.85, 0.7, 0.75], align=["L"] + ["C"] * 6, bold_last=True)
    d.p("The ensemble clearly improved on the two ResNet-50 members. ResNet-34 alone scored slightly higher on the "
        "test set, but validation did not prefer it, and switching after seeing test results would be test-set "
        "tuning – so the pre-committed ensemble remains the reported model.")
    d.h2("Performance Metrics")
    d.table("Error rates and per-type sensitivity", ["Metric", "Score"],
            [["False Positive Rate", "14.10% (33 / 234)"], ["False Negative Rate", "0.26% (1 / 390)"],
             ["Sensitivity – bacterial pneumonia", "99.6% (241 / 242)"],
             ["Sensitivity – viral pneumonia", "100% (148 / 148)"]],
            [3.0, 2.0], align=["L", "C"])
    d.table("X-ray gate and speed", ["Check", "Result"],
            [["Official test chest X-rays accepted by the gate", "620 / 624 (99.36%)"],
             ["Non-X-ray images rejected (photographs, textures, documents, noise, plain colours)", "33 / 33"],
             ["Grayscale copies of the colour images rejected", "16 / 16"],
             ["Time per X-ray on GPU (3 ResNets × 2 views + Grad-CAM)", "376 ms (median)"],
             ["Time per X-ray on CPU only", "1,248 ms (median)"]],
            [4.3, 1.75], align=["L", "C"], bold_first_col=False)
    d.h2("Explainability Results")
    d.p("For correct predictions, the Grad-CAM maps mostly cover the lung fields (dense regions in pneumonia, broad "
        "areas of both lungs in normal X-rays). Some maps also highlight the burned-in “R” marker or text, a sign "
        "of partial shortcut learning that is reported honestly as a limitation " + c(13) + ".")
    d.figure(HERE / "figures" / "gradcam_examples.jpg", 4.5, "Grad-CAM explanations on test X-rays: correct "
                                                             "pneumonia, correct normal, a false positive and the "
                                                             "only false negative.")
    d.h2("Comparative Evaluation")
    d.table("Comparison with published results on the same official test set",
            ["Work", "Model", "Accuracy", "Sensitivity", "Other"],
            [["Kermany et al. " + c(2), "Inception-V3, transfer learning", "92.8%", "93.2%", "AUC 0.968"],
             ["Yang et al. " + c(6), "ResNet-18 (224 px)", "86.4%", "–", "AUC 0.956"],
             ["Yang et al. " + c(6), "ResNet-50 (224 px)", "88.4%", "–", "AUC 0.962"],
             ["Liang & Zheng " + c(11), "Residual + dilated convolution", "–", "96.7%", "F1 92.7%"],
             ["Chouhan et al. " + c(8), "Ensemble of 5 CNNs (voting)", "96.4%", "99.62%", "–"],
             ["**PneumoScan AI (ours)**", "**Ensemble of 3 ResNets**", "**94.55%**", "**99.74%**",
              "**AUC 0.987, F1 95.8%**"]],
            [1.55, 1.85, 0.8, 0.85, 1.0], align=["L", "L", "C", "C", "C"])
    d.p("PneumoScan AI is well above the published ResNet baselines (86.4–88.4%) and the dataset authors’ own "
        "Inception-V3 (92.8%), and its **sensitivity of 99.74% is the highest in the table**.")


def section6_9(doc):
    d = doc
    d.h1("6. Discussion")
    d.p("The ResNet ensemble proved highly effective for **pneumonia screening on paediatric chest X-rays**. It "
        "missed only **one of 390 pneumonia cases**, and its ROC-AUC of 0.987 shows that it ranks pneumonia above "
        "normal images very reliably. The remaining errors are almost all **normal X-rays flagged for review** – "
        "the safer kind of error for a screening aid, which a doctor can quickly dismiss. The project target of "
        "95% accuracy was **missed by three images** (94.55%). A threshold of 0.5 would have given 95.8%, but "
        "choosing it after seeing the test results would be tuning on the test set, so the honest, "
        "validation-chosen result is reported. The gap comes from the shift between the validation data (very "
        "clean normals) and the harder official test set, which is also seen in published work " + c(2, 6) + ".")
    d.h3("Strengths Identified")
    d.bullets([
        "**Very high sensitivity (99.74%)** and negative predictive value (99.50%).",
        "**Honest methodology:** patient-level split, leakage checks and a single logged test evaluation.",
        "**Explainable:** Grad-CAM heat maps for every prediction.",
        "**Safe:** the X-ray gate rejected all 33 non-X-ray check images.",
        "**Complete, tested product:** offline web app with 14 features and 180 passing automated tests.",
        "**Fast and affordable:** about 0.4 s per X-ray on a laptop GPU; trained in under one hour.",
    ])
    d.h3("Limitations Observed")
    d.bullets([
        "Trained and tested on X-rays of **children aged 1–5 from one hospital**; it may be less accurate on "
        "adults or other X-ray machines " + c(13) + ".",
        "**Specificity of 85.9%:** false alarms on normal X-rays are the main error.",
        "Some heat maps highlight the **“R” marker or burned-in text** (partial shortcut learning).",
        "Only **two classes**; it cannot tell bacterial from viral pneumonia or detect other lung diseases.",
        "A **decision-support tool for education**, not a certified medical device.",
    ])
    d.h1("7. Future Recommendations")
    d.table("Future improvements", ["Improvement Area", "Suggested Method", "Expected Benefit"],
            [["Multi-centre data", "Train and validate on larger adult and multi-hospital data, including Indian "
              "hospitals", "Better generalisation to new patients and machines"],
             ["Threshold on deployment-like data", "Choose the threshold on a validation set from the target "
              "hospital", "Higher specificity without losing sensitivity"],
             ["Lung segmentation", "Segment the lungs or mask burned-in text and markers before classification",
              "Removes shortcut learning; more trustworthy heat maps"],
             ["Multi-class diagnosis", "Classify bacterial vs viral pneumonia and other chest findings",
              "More useful clinical information"],
             ["Clinical validation", "Prospective study alongside radiologists", "Real-world evidence of benefit"],
             ["Hospital integration", "Connect to PACS and teleconsultation services", "Fits into existing "
              "hospital workflows"],
             ["Mobile and regional languages", "Lightweight mobile model and Tamil / Hindi interface for primary "
              "health centres", "Reaches rural areas with few radiologists"]],
            [1.65, 2.5, 1.9])
    d.h1("8. Conclusion")
    d.p("This project built **PneumoScan AI**, a complete and explainable system that detects pneumonia in "
        "paediatric chest X-rays using an **ensemble of three fine-tuned ResNets**. Using transfer learning, "
        "class-weighted and label-smoothed training, mixed precision, test-time augmentation and temperature "
        "scaling, the system reached an accuracy of **94.55%**, a **sensitivity of 99.74%**, a specificity of "
        "**85.90%**, an F1-score of **95.81%** and a **ROC-AUC of 0.9867** on the official test set, which was "
        "scored only once. These results are well above the published ResNet baselines on the same images.")
    d.p("Beyond accuracy, the project delivers what a real user needs: **Grad-CAM explanations**, an **X-ray "
        "gate** that refuses invalid images, and an **offline web application** with patient PDF reports, a "
        "doctor’s triage queue, scan history, a CURB-65 calculator and sourced patient education, all verified by "
        "**180 automated tests**. PneumoScan AI shows that a carefully and honestly evaluated deep-learning system "
        "can give fast, explainable support for pneumonia screening on ordinary hardware, while the final "
        "decision always stays with a qualified doctor.")
    d.h1("9. References")
    for i, orig in enumerate(REF_ORDER, 1):
        par = d.d.add_paragraph()
        f = par.paragraph_format
        f.left_indent, f.first_line_indent = Inches(0.35), Inches(-0.35)
        f.tab_stops.add_tab_stop(Inches(0.35))
        f.line_spacing, f.space_after = 1.0, Pt(1.5)
        f.alignment = WD_ALIGN_PARAGRAPH.LEFT
        add_inline(par, f"{i}.\t" + ALL_REFS[orig - 1], size=10)


def main():
    figs = make_app_figures()
    known = {}
    for _ in range(2):
        doc = Doc()
        doc.known = known
        cover(doc)
        contents(doc)
        section1(doc)
        section2(doc)
        section3(doc)
        section4(doc, figs)
        section5(doc, figs)
        section6_9(doc)
        known = dict(doc.labels)
    bad = [p.text for p in doc.d.paragraphs if "??" in p.text]
    if bad:
        raise SystemExit(f"unresolved references: {bad}")
    doc.d.save(str(OUT))
    print("saved", OUT, "figures", doc.fig_no, "tables", doc.tab_no)


if __name__ == "__main__":
    main()
