"""Cover page, certificate, declaration, acknowledgement, abstract, lists."""
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from docx_engine import para_border

C = WD_ALIGN_PARAGRAPH.CENTER
J = WD_ALIGN_PARAGRAPH.JUSTIFY

TITLE = "PNEUMONIA DETECTION USING RESNET"
STUDENT = "UMER BASITH G"
RRN = "230171601192"
COURSE = "CSDX530 – Deep Learning"
GUIDE = "Mrs. Mahalakshmi R"
GUIDE_ROLE = "Assistant Professor / CSE"
DEPT = "DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING"
INST = "B.S. ABDUR RAHMAN CRESCENT INSTITUTE OF SCIENCE AND TECHNOLOGY"
PLACE = "Vandalur, Chennai"


def _rule(r, before=4, after=4, color="1F3864", sz=12):
    par = r.doc.add_paragraph()
    f = par.paragraph_format
    f.space_before, f.space_after, f.line_spacing = Pt(before), Pt(after), 1.0
    para_border(par._p.get_or_add_pPr(), sides=("bottom",), sz=sz, color=color, space=1)
    par.add_run("").font.size = Pt(2)


def cover(r):
    def line(text, size=12, bold=False, italic=False, before=0, after=0, color=None, caps=False):
        p = r.p(text, align=C, size=size, bold=bold, italic=italic, before=before, after=after, spacing=1.15)
        if color:
            for run in p.runs:
                run.font.color.rgb = RGBColor(*color)
        return p

    navy = (0x1F, 0x38, 0x64)
    line("PNEUMONIA DETECTION", 24, bold=True, before=30, after=0, color=navy)
    line("USING RESNET", 24, bold=True, after=10, color=navy)
    line("PneumoScan AI: an explainable ResNet-ensemble system for chest X-ray screening", 13, italic=True,
         after=10)
    _rule(r)
    line("A MINI PROJECT REPORT", 13, bold=True, before=36, after=4)
    line("submitted for", 12, italic=True, after=4)
    line("CSDX530 – DEEP LEARNING", 14, bold=True, after=2)
    line("(CAT-2 Mini Project)", 12, after=36)
    line("Submitted by", 12, italic=True, after=4)
    line(STUDENT, 15, bold=True, after=2)
    line(f"Register Number: {RRN}", 12, after=36)
    line("Under the guidance of", 12, italic=True, after=4)
    line(GUIDE, 14, bold=True, after=2)
    line(GUIDE_ROLE, 12, after=2)
    line("Department of Computer Science and Engineering", 12, after=60)
    _rule(r, sz=6)
    line(DEPT, 13, bold=True, before=10, after=4, color=navy)
    line(INST, 13, bold=True, after=4, color=navy)
    line(PLACE, 12, after=30)
    line("NOVEMBER 2026", 13, bold=True)


def _sign_table(r, left, right):
    t = r.doc.add_table(rows=1, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    widths = (3.0, 3.0)
    for cell, lines, w in zip(t.rows[0].cells, (left, right), widths):
        cell.width = Inches(w)
        first = True
        for text, bold in lines:
            par = cell.paragraphs[0] if first else cell.add_paragraph()
            first = False
            par.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
            par.paragraph_format.line_spacing = 1.15
            par.paragraph_format.space_after = Pt(1)
            run = par.add_run(text)
            run.bold = bold
            run.font.size = Pt(12)
    # no borders
    tblPr = t._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for s in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{s}")
        e.set(qn("w:val"), "nil")
        b.append(e)
    tblPr.append(b)


def certificate(r):
    r.p(INST, align=C, bold=True, size=13, after=2, spacing=1.15)
    r.p(PLACE.upper(), align=C, size=12, after=18, spacing=1.15)
    r.front_heading("Bonafide Certificate", toc=True, page_break=False)
    r.p(f"Certified that this mini project report titled **“PNEUMONIA DETECTION USING RESNET”** is the "
        f"bonafide work of **{STUDENT}** (Register Number: **{RRN}**), who carried out the project work under "
        f"my supervision for the course **{COURSE}** (CAT-2 Mini Project) in the Department of Computer "
        f"Science and Engineering, B.S. Abdur Rahman Crescent Institute of Science and Technology, during "
        f"November 2026.", align=J, spacing=2.0)
    r.p("Certified further that, to the best of my knowledge, the work reported herein does not form part of "
        "any other project report or dissertation on the basis of which a degree or award was conferred on an "
        "earlier occasion on this or any other candidate.", align=J, spacing=2.0, after=60)
    _sign_table(r,
                [("SIGNATURE", True), ("", False), ("", False), (GUIDE, True), ("FACULTY IN-CHARGE", True),
                 ("Assistant Professor", False), ("Department of Computer Science", False),
                 ("and Engineering", False), ("B.S. Abdur Rahman Crescent", False),
                 ("Institute of Science and Technology", False), ("Vandalur, Chennai", False)],
                [("SIGNATURE", True), ("", False), ("", False), ("", False), ("HEAD OF THE DEPARTMENT", True),
                 ("", False), ("Department of Computer Science", False), ("and Engineering", False),
                 ("B.S. Abdur Rahman Crescent", False), ("Institute of Science and Technology", False),
                 ("Vandalur, Chennai", False)])


def declaration(r):
    r.front_heading("Declaration")
    r.p(f"I, **{STUDENT}** (Register Number: **{RRN}**), hereby declare that the mini project report "
        f"entitled **“PNEUMONIA DETECTION USING RESNET”**, submitted for the course **{COURSE}** (CAT-2 Mini "
        f"Project) in the Department of Computer Science and Engineering, B.S. Abdur Rahman Crescent Institute "
        f"of Science and Technology, Chennai, is a record of original work carried out by me under the guidance "
        f"of **{GUIDE}**, {GUIDE_ROLE}.", align=J, spacing=2.0)
    r.p("I further declare that the work reported in this report has not been submitted, either in part or in "
        "full, for the award of any other degree or diploma in this institute or any other institute or "
        "university. All external sources of data, figures and text have been acknowledged and cited.",
        align=J, spacing=2.0, after=60)
    _sign_table(r, [("Place: Chennai", False), ("Date: 09.11.2026", False)],
                [("", False), ("", False), ("", False), (STUDENT, True), (f"RRN: {RRN}", False)])


def acknowledgement(r):
    r.front_heading("Acknowledgement")
    paras = [
        "I express my sincere gratitude to the Chancellor, the Vice-Chancellor and the Registrar of "
        "B.S. Abdur Rahman Crescent Institute of Science and Technology for providing an excellent academic "
        "environment and the facilities that made this work possible.",
        "I am thankful to the Head of the Department of Computer Science and Engineering for the constant "
        "encouragement and support extended to the students of the department.",
        f"I owe my deepest thanks to my faculty in-charge, **{GUIDE}**, {GUIDE_ROLE}, for teaching the course "
        f"CSDX530 – Deep Learning, for her valuable guidance and suggestions, and for giving me the opportunity "
        f"to carry out this mini project on a meaningful healthcare problem.",
        "I thank all the faculty members and staff of the Department of Computer Science and Engineering for "
        "their help during the course of this work. I also acknowledge Kermany and colleagues for making the "
        "paediatric chest X-ray dataset publicly available under an open licence, and the developers of the "
        "open-source software used in this project.",
        "Finally, I am grateful to my family and friends for their encouragement, patience and support "
        "throughout this project.",
    ]
    for t in paras:
        r.p(t, align=J)
    r.p(STUDENT, align=WD_ALIGN_PARAGRAPH.RIGHT, bold=True, before=36, after=0)


def abstract(r):
    r.front_heading("Abstract")
    paras = [
        "Pneumonia is an infection of the lungs and a leading cause of death in young children; the World Health "
        "Organization reports 740,180 deaths of children under five in 2019 [14]. Chest X-ray imaging is the most "
        "frequently used method for diagnosing pneumonia [12], but reading X-rays needs trained radiologists, who "
        "are scarce in India [16]. This project presents **PneumoScan AI**, a decision-support system that "
        "classifies frontal chest X-ray images as NORMAL or PNEUMONIA using deep residual networks (ResNet) [1].",
        "Three ImageNet-pretrained ResNets (ResNet-50 at 384 × 384 pixels, ResNet-34 at 384 × 384 and ResNet-50 at "
        "448 × 448) are fine-tuned end-to-end with transfer learning on the public paediatric chest X-ray dataset "
        "of Kermany et al. [2], [17], using class-weighted cross-entropy with label smoothing, realistic data "
        "augmentation, mixed-precision training and an exponential moving average of the weights. The members are "
        "combined into an ensemble with horizontal-flip test-time augmentation, the output is calibrated by "
        "temperature scaling, and the decision threshold is chosen by Youden’s J statistic. All of these choices "
        "were made on a patient-level validation split carved out of the training data; the official independent "
        "test set of 624 images was scored exactly once.",
        "On this test set the system achieves an accuracy of **94.55%**, a sensitivity of **99.74%** (only 1 of 390 "
        "pneumonia X-rays missed), a specificity of **85.90%**, a precision of **92.18%**, an F1-score of "
        "**95.81%** and a ROC-AUC of **0.9867**. The project target of 95% accuracy was missed by three images; the "
        "remaining errors are mainly normal X-rays flagged for review, which is the safer kind of error for a "
        "screening aid and matches the published behaviour of this test set. Grad-CAM heat maps [4] show the "
        "image regions behind each prediction, and an out-of-distribution gate turns away images that are not "
        "chest X-rays: it rejected all 33 non-X-ray check images (photographs, textures, documents and blank "
        "images) while accepting 620 of the 624 test X-rays.",
        "The model is delivered through an offline web application built with FastAPI and React, offering single "
        "and batch (triage) scanning, patient PDF reports, local scan history, a CURB-65 severity calculator [5] and "
        "sourced patient education. The tool is intended for education and decision support only and does not "
        "replace a qualified doctor.",
    ]
    for t in paras:
        r.p(t, align=J)
    r.p("**Keywords:** pneumonia, chest X-ray, deep learning, ResNet, transfer learning, ensemble, Grad-CAM, "
        "explainable AI, medical decision support.", align=J, before=6)


ABBREVIATIONS = [
    ("AI", "Artificial Intelligence"),
    ("AMP", "Automatic Mixed Precision"),
    ("API", "Application Programming Interface"),
    ("AUC", "Area Under the Curve"),
    ("BN", "Batch Normalisation"),
    ("CAP", "Community-Acquired Pneumonia"),
    ("CNN", "Convolutional Neural Network"),
    ("CPU", "Central Processing Unit"),
    ("CSV", "Comma-Separated Values"),
    ("CUDA", "Compute Unified Device Architecture (NVIDIA)"),
    ("CURB-65", "Confusion, Urea, Respiratory rate, Blood pressure, age ≥ 65 (severity score)"),
    ("DICOM", "Digital Imaging and Communications in Medicine"),
    ("EMA", "Exponential Moving Average"),
    ("FC", "Fully Connected (layer)"),
    ("FN / FP", "False Negative / False Positive"),
    ("GPU", "Graphics Processing Unit"),
    ("Grad-CAM", "Gradient-weighted Class Activation Mapping"),
    ("ICU", "Intensive Care Unit"),
    ("JSON", "JavaScript Object Notation"),
    ("NLL", "Negative Log-Likelihood"),
    ("OOD", "Out-of-Distribution"),
    ("PACS", "Picture Archiving and Communication System"),
    ("PDF", "Portable Document Format"),
    ("PNG / JPEG", "Portable Network Graphics / Joint Photographic Experts Group (image formats)"),
    ("PR", "Precision–Recall"),
    ("ReLU", "Rectified Linear Unit"),
    ("ResNet", "Residual Network"),
    ("REST", "Representational State Transfer"),
    ("ROC", "Receiver Operating Characteristic"),
    ("SQL", "Structured Query Language"),
    ("TN / TP", "True Negative / True Positive"),
    ("TTA", "Test-Time Augmentation"),
    ("UI", "User Interface"),
    ("WHO", "World Health Organization"),
]


def lists(r):
    r.front_heading("Table of Contents", toc=False)
    r.toc('TOC \\o "2-2" \\f \\h \\z')
    r.front_heading("List of Figures")
    r.toc('TOC \\h \\z \\t "Figure Caption,9"')
    r.front_heading("List of Tables")
    r.toc('TOC \\h \\z \\t "Table Caption,9"')


def abbreviations(r):
    r.front_heading("List of Abbreviations")
    t = r.doc.add_table(rows=len(ABBREVIATIONS), cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for row, (a, full) in zip(t.rows, ABBREVIATIONS):
        for cell, text, w, bold in ((row.cells[0], a, 1.5, True), (row.cells[1], full, 4.4, False)):
            cell.width = Inches(w)
            par = cell.paragraphs[0]
            par.paragraph_format.space_after = Pt(2)
            par.paragraph_format.line_spacing = 1.15
            par.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
            run = par.add_run(text)
            run.bold = bold
    tblPr = t._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for s in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{s}")
        e.set(qn("w:val"), "nil")
        b.append(e)
    tblPr.append(b)


def front_blocks():
    return [
        ("raw", cover),
        ("section", "front"),
        ("raw", certificate),
        ("raw", declaration),
        ("raw", acknowledgement),
        ("raw", abstract),
        ("raw", lists),
        ("raw", abbreviations),
    ]
