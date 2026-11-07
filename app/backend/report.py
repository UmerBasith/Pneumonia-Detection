"""Hospital-style patient report PDF (reportlab), Unicode-safe via a bundled TTF font."""
from __future__ import annotations

import io
import logging
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from . import config, content

log = logging.getLogger("pneumoscan.report")

INK = colors.HexColor("#0B1620")
INK2 = colors.HexColor("#3F4D5A")
INK3 = colors.HexColor("#5D6A77")
LINE = colors.HexColor("#D7DFE7")
SOFT = colors.HexColor("#F2F5F8")
ACCENT = colors.HexColor("#1D5BD0")
FLAG = colors.HexColor("#BF2F25")
FLAG_SOFT = colors.HexColor("#FBE6E3")
CLEAR = colors.HexColor("#17734F")
CLEAR_SOFT = colors.HexColor("#E1F3EA")
CAUTION = colors.HexColor("#9A6100")
CAUTION_SOFT = colors.HexColor("#FBF0D9")

_FONTS: tuple[str, str] | None = None


def _register_fonts() -> tuple[str, str]:
    """Bundled DejaVu Sans first (covers ₹, quotes, accents), then Windows fonts, then Helvetica."""
    global _FONTS
    if _FONTS:
        return _FONTS
    fonts_dir = config.ASSETS_DIR / "fonts"
    candidates = [
        (fonts_dir / "DejaVuSans.ttf", fonts_dir / "DejaVuSans-Bold.ttf"),
        (Path("C:/Windows/Fonts/segoeui.ttf"), Path("C:/Windows/Fonts/segoeuib.ttf")),
        (Path("C:/Windows/Fonts/arial.ttf"), Path("C:/Windows/Fonts/arialbd.ttf")),
    ]
    for regular, bold in candidates:
        if regular.exists() and bold.exists():
            try:
                pdfmetrics.registerFont(TTFont("PSans", str(regular)))
                pdfmetrics.registerFont(TTFont("PSans-Bold", str(bold)))
                from reportlab.lib.fonts import addMapping

                addMapping("PSans", 0, 0, "PSans")
                addMapping("PSans", 1, 0, "PSans-Bold")
                addMapping("PSans", 0, 1, "PSans")
                addMapping("PSans", 1, 1, "PSans-Bold")
                _FONTS = ("PSans", "PSans-Bold")
                return _FONTS
            except Exception:
                log.warning("Could not register font %s", regular)
    _FONTS = ("Helvetica", "Helvetica-Bold")
    return _FONTS


# Fallback fonts for characters the main font lacks (e.g. Tamil and other Indian scripts in patient names,
# emoji in symptoms). Windows ships these; when missing, those characters print as empty boxes as before.
_FALLBACK_CANDIDATES = [
    ("PIndic", Path("C:/Windows/Fonts/Nirmala.ttc"), 0),      # Nirmala UI: Tamil, Devanagari, Telugu, ...
    ("PSymbol", Path("C:/Windows/Fonts/seguisym.ttf"), 0),     # Segoe UI Symbol
    ("PEmoji", Path("C:/Windows/Fonts/seguiemj.ttf"), 0),      # Segoe UI Emoji (outlines)
]
_FALLBACKS: list[tuple[str, set[int]]] | None = None
_MAIN_CMAP: set[int] | None = None


def _fallbacks() -> list[tuple[str, set[int]]]:
    """Register the fallback fonts once; returns [(font name, covered code points)]."""
    global _FALLBACKS, _MAIN_CMAP
    if _FALLBACKS is not None:
        return _FALLBACKS
    _FALLBACKS = []
    regular = _register_fonts()[0]
    try:
        _MAIN_CMAP = set(pdfmetrics.getFont(regular).face.charToGlyph) if regular != "Helvetica" else None
    except Exception:
        _MAIN_CMAP = None
    if _MAIN_CMAP is None:
        return _FALLBACKS
    for name, path, index in _FALLBACK_CANDIDATES:
        if not path.exists():
            continue
        try:
            font = TTFont(name, str(path), subfontIndex=index)
            pdfmetrics.registerFont(font)
            _FALLBACKS.append((name, set(font.face.charToGlyph)))
        except Exception:
            log.warning("Could not register fallback font %s", path)
    return _FALLBACKS


def _font_for(ch: str) -> str | None:
    """None = main font; else the name of the first fallback font that has this character."""
    cp = ord(ch)
    if _MAIN_CMAP is None or cp in _MAIN_CMAP or ch in "\n\t ":
        return None
    for name, cmap in _fallbacks():
        if cp in cmap:
            return name
    return None


def _txt(value: object) -> str:
    """Escape user text for reportlab Paragraph markup; keep line breaks; switch fonts for other scripts."""
    s = "" if value is None else str(value)
    if _register_fonts()[0] == "Helvetica":
        s = s.encode("latin-1", "replace").decode("latin-1")
    # Strip control characters that break PDF text (keep newlines and tabs).
    s = "".join(ch for ch in s if ch in "\n\t" or ord(ch) >= 32)
    _fallbacks()
    out: list[str] = []
    run, run_font = "", None
    for ch in s:
        f = _font_for(ch)
        # combining marks (Tamil vowel signs, virama, emoji modifiers) stay with the run before them
        if f != run_font and run and not (f is None and run_font is not None and _joins(ch)):
            out.append(_wrap(run, run_font))
            run = ""
        if not run:
            run_font = f
        run += ch
    if run:
        out.append(_wrap(run, run_font))
    return "".join(out).replace("\n", "<br/>")


_SHAPE_READY: bool | None = None


def _can_shape() -> bool:
    """HarfBuzz shaping (optional `uharfbuzz` package) for the Indic fallback font ONLY.

    ReportLab would otherwise also shape DejaVu words with discretionary ligatures ("st" -> "ﬆ"),
    which changes how ordinary English text looks and breaks copy/paste, so other words are left alone.
    """
    global _SHAPE_READY
    if _SHAPE_READY is not None:
        return _SHAPE_READY
    _SHAPE_READY = False
    try:
        import uharfbuzz  # noqa: F401
        from reportlab.platypus import paragraph as rl_paragraph

        original = rl_paragraph.shapeFragWord
        shaped_fonts = {"PIndic"}

        def shape_fallback_only(w, *args, **kwargs):
            try:
                if any(getattr(f, "fontName", None) in shaped_fonts for f, _ in w[1:]):
                    return original(w, *args, **kwargs)
            except Exception:
                log.warning("Text shaping failed; printing the word unshaped")
            return w

        rl_paragraph.shapeFragWord = shape_fallback_only
        _SHAPE_READY = True
    except Exception:
        pass
    return _SHAPE_READY


def _joins(ch: str) -> bool:
    import unicodedata

    return unicodedata.category(ch) in ("Mn", "Mc", "Me", "Cf") or ch in "\u200c\u200d\ufe0f"


def _wrap(text: str, font: str | None) -> str:
    t = escape(text)
    return f'<font name="{font}">{t}</font>' if font else t


def _fmt_date(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%d %b %Y, %H:%M")
    except Exception:
        return iso


def _pct(v: object, digits: int = 1) -> str:
    try:
        return f"{float(v) * 100:.{digits}f}%"
    except Exception:
        return "–"


def _fit_image(path: Path, max_w: float, max_h: float) -> Image | Paragraph:
    """Embed as high-quality JPEG (keeps the PDF small) scaled to fit the box."""
    try:
        with PILImage.open(path) as im:
            w, h = im.size
            buf = io.BytesIO()
            im.convert("RGB").save(buf, format="JPEG", quality=90)
        buf.seek(0)
        s = min(max_w / w, max_h / h)
        return Image(buf, width=w * s, height=h * s)
    except Exception:
        return Paragraph("Image not available", ParagraphStyle("na", fontSize=9, textColor=INK3))


def _test_metrics(info: dict) -> dict | None:
    m = info.get("metrics") or {}
    test = (m.get("final") or {}).get("test") if isinstance(m.get("final"), dict) else None
    if not isinstance(test, dict):
        test = m.get("test") if isinstance(m.get("test"), dict) else None
    return test


def build_report(scan: dict, model_info: dict, image_path) -> bytes:
    regular, bold = _register_fonts()
    buf = io.BytesIO()
    page_w, page_h = A4
    margin = 16 * mm
    content_w = page_w - 2 * margin - 12  # frame has 6 pt padding each side

    st = {
        "body": ParagraphStyle("body", fontName=regular, fontSize=9.5, leading=13.5, textColor=INK2),
        "small": ParagraphStyle("small", fontName=regular, fontSize=8, leading=11, textColor=INK3),
        "label": ParagraphStyle("label", fontName=bold, fontSize=7.2, leading=9, textColor=INK3),
        "value": ParagraphStyle("value", fontName=regular, fontSize=10, leading=13.5, textColor=INK),
        "h2": ParagraphStyle("h2", fontName=bold, fontSize=10.5, leading=14, textColor=INK, spaceBefore=6, spaceAfter=3),
        "title": ParagraphStyle("title", fontName=bold, fontSize=17, leading=20, textColor=INK),
        "sub": ParagraphStyle("sub", fontName=regular, fontSize=9, leading=12, textColor=INK3),
        "right": ParagraphStyle("right", fontName=regular, fontSize=9, leading=13, textColor=INK2, alignment=TA_RIGHT),
        "verdict": ParagraphStyle("verdict", fontName=bold, fontSize=15, leading=19, textColor=INK, alignment=TA_LEFT),
        "caption": ParagraphStyle("caption", fontName=regular, fontSize=8, leading=10.5, textColor=INK3),
    }
    if regular != "Helvetica" and _can_shape():
        for style in st.values():  # HarfBuzz shaping puts Tamil/Indic vowel signs in the right place
            style.shaping = 1

    is_pneu = scan["label"] == "PNEUMONIA"
    tone, tone_soft = (FLAG, FLAG_SOFT) if is_pneu else (CLEAR, CLEAR_SOFT)
    verdict = "Pneumonia likely" if is_pneu else "No pneumonia detected"
    patient = scan.get("patient") or {}
    created = _fmt_date(scan.get("created_at", ""))

    def on_page(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(ACCENT)
        canvas.setLineWidth(2.2)
        canvas.line(margin + 6, page_h - 10 * mm, page_w - margin - 6, page_h - 10 * mm)
        canvas.setFont(regular, 7.5)
        canvas.setFillColor(INK3)
        canvas.drawString(
            margin + 6, 8 * mm,
            _plain(f"PneumoScan AI · Scan {scan['id']} · Educational decision-support tool, not a medical device"),
        )
        canvas.drawRightString(page_w - margin - 6, 8 * mm, f"Page {doc.page}")
        canvas.restoreState()

    story: list = []

    # ---- header
    header = Table(
        [[
            [Paragraph("PneumoScan AI", st["title"]),
             Paragraph("Chest X-ray screening report · Pneumonia detection using ResNet", st["sub"])],
            Paragraph(
                f"<b>Scan ID</b> {_txt(scan['id'])}<br/><b>Date</b> {_txt(created)}<br/>"
                f"<b>Source file</b> {_txt(scan.get('filename') or '–')}",
                st["right"],
            ),
        ]],
        colWidths=[content_w * 0.58, content_w * 0.42],
    )
    header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    story += [header, Spacer(1, 3 * mm)]

    if scan.get("mode") == "mock":
        demo = Table([[Paragraph(
            "<b>DEMO MODE – mock model.</b> This result is simulated and is NOT a real prediction.",
            ParagraphStyle("demo", parent=st["body"], textColor=CAUTION))]], colWidths=[content_w])
        demo.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), CAUTION_SOFT),
                                  ("BOX", (0, 0), (-1, -1), 0.8, CAUTION),
                                  ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
        story += [demo, Spacer(1, 4 * mm)]

    # ---- patient
    def cell(label: str, value: object) -> list:
        v = value if (value is not None and str(value).strip() != "") else "–"
        return [Paragraph(label.upper(), st["label"]), Paragraph(_txt(v), st["value"])]

    pt = Table(
        [
            [cell("Patient name", patient.get("name")), cell("Age", patient.get("age")),
             cell("Sex", patient.get("sex")), cell("Patient ID", patient.get("patient_id"))],
            [cell("Symptoms", patient.get("symptoms")), "", "", ""],
        ],
        colWidths=[content_w * 0.42, content_w * 0.13, content_w * 0.17, content_w * 0.28],
    )
    pt.setStyle(TableStyle([
        ("SPAN", (0, 1), (-1, 1)),
        ("BACKGROUND", (0, 0), (-1, -1), SOFT),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story += [Paragraph("Patient", st["h2"]), pt, Spacer(1, 3 * mm)]

    # ---- result
    test = _test_metrics(model_info)
    sens = (test or {}).get("recall_sensitivity", (test or {}).get("sensitivity"))
    rows = [
        ("Risk level", str(scan.get("risk_level") or "–")),
        ("Pneumonia probability", _pct(scan.get("prob_pneumonia"))),
        ("Decision threshold", _pct(scan.get("threshold"))),
        ("Test-set sensitivity", _pct(sens) if sens is not None else "–"),
    ]
    metrics_tbl = Table(
        [[Paragraph(k.upper(), st["label"]) for k, _ in rows],
         [Paragraph(f"<b>{_txt(v)}</b>", st["value"]) for _, v in rows]],
        colWidths=[(content_w - 8) / 4] * 4,
    )
    metrics_tbl.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 1),
                                     ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
    result_box = Table(
        [[Paragraph(f"<font color='{tone.hexval().replace('0x', '#')}'>{'●' if regular != 'Helvetica' else ''}</font> "
                    f"{verdict}", st["verdict"])],
         [Paragraph(_txt(content.EXPLANATION[scan['label']] + " " + content.THRESHOLD_NOTE), st["body"])],
         [metrics_tbl]],
        colWidths=[content_w],
    )
    result_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), tone_soft),
        ("LINEBEFORE", (0, 0), (0, -1), 3, tone),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, 0), 9), ("BOTTOMPADDING", (0, -1), (-1, -1), 9),
    ]))
    story += [Paragraph("AI result", st["h2"]), result_box]

    # ---- images
    img_w = (content_w - 6 * mm) / 2
    img_h = 44 * mm
    pics = Table(
        [[_fit_image(image_path(scan["id"], "input"), img_w, img_h),
          _fit_image(image_path(scan["id"], "overlay"), img_w, img_h)],
         [Paragraph("Chest X-ray as analysed by the model", st["caption"]),
          Paragraph("Grad-CAM heatmap: warmer colours mark the regions that most influenced the result",
                    st["caption"])]],
        colWidths=[img_w + 3 * mm, img_w + 3 * mm],
    )
    pics.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, 0), "CENTER"), ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#060B11")),
        ("LINEAFTER", (0, 0), (0, 0), 3 * mm, colors.white),
        ("TOPPADDING", (0, 0), (-1, 0), 4), ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
        ("TOPPADDING", (0, 1), (-1, 1), 3), ("LEFTPADDING", (0, 1), (-1, 1), 0),
        ("VALIGN", (0, 1), (-1, 1), "TOP"),  # both captions start on the same line
    ]))
    story += [Spacer(1, 2 * mm), pics, Spacer(1, 1 * mm)]

    # ---- model
    model_lines = [f"<b>Model version</b> {_txt(scan.get('model_version') or '–')}"]
    if scan.get("mode") == "mock":
        model_lines.append("This scan used the mock model (demo mode), so its result is simulated.")
    if test:
        n = test.get("n")
        model_lines.append(
            f"<b>Held-out test set{f' ({n} X-rays)' if n else ''}:</b> accuracy {_pct(test.get('accuracy'))} · "
            f"sensitivity {_pct(test.get('recall_sensitivity', test.get('sensitivity')))} · "
            f"specificity {_pct(test.get('specificity'))} · ROC-AUC {float(test.get('roc_auc', 0) or 0):.3f}"
        )
    else:
        model_lines.append("Test-set metrics are not available yet.")
    model_lines.append(f"<b>Inference time</b> {float(scan.get('inference_ms') or 0):.0f} ms")
    model_lines.append(f"<font color='#5D6A77'>{_txt(content.MODEL_LIMITATION)}</font>")
    story += [KeepTogether([Paragraph("About the model", st["h2"]), Paragraph("<br/>".join(model_lines), st["small"])])]

    # ---- notes + next steps
    notes = (scan.get("doctor_notes") or "").strip()
    notes_para = Paragraph(_txt(notes) if notes else "No notes added.", st["body"] if notes else st["small"])
    step_style = ParagraphStyle("step", parent=st["body"], fontSize=8.8, leading=12)
    steps = ListFlowable(
        [ListItem(Paragraph(_txt(s), step_style), leftIndent=9, value="•") for s in content.NEXT_STEPS[scan["label"]]],
        bulletType="bullet", start="•", leftIndent=9, bulletFontName=regular, bulletColor=INK3,
    )
    disc = Table([[Paragraph(f"<b>Disclaimer.</b> {_txt(content.DISCLAIMER)}", st["small"])]], colWidths=[content_w])
    disc.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, LINE), ("BACKGROUND", (0, 0), (-1, -1), SOFT),
                              ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                              ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9)]))

    def signature(width: float, labels: list[str]) -> Table:
        gap = 6 * mm
        n = len(labels)
        w = (width - gap * (n - 1)) / n
        cols, top, bottom = [], [], []
        for i, label in enumerate(labels):
            if i:
                cols.append(gap); top.append(""); bottom.append("")
            cols.append(w); top.append(""); bottom.append(Paragraph(label, st["small"]))
        t = Table([top, bottom], colWidths=cols, rowHeights=[9 * mm, None])
        t.setStyle(TableStyle(
            [("LINEBELOW", (2 * i, 0), (2 * i, 0), 0.8, INK3) for i in range(n)]
            + [("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]
        ))
        return t

    if len(notes) <= 700:
        # Short notes: notes + signature beside the next steps keeps the report on one page.
        col = (content_w - 8 * mm) / 2
        left_w = col * 0.85
        left = [notes_para, Spacer(1, 4 * mm), signature(left_w, ["Reviewing doctor", "Signature and date"])]
        two = Table(
            [[Paragraph("Doctor's notes", st["h2"]), "", Paragraph("Recommended next steps", st["h2"])],
             [left, "", steps]],
            colWidths=[left_w, 8 * mm, col * 1.15],
        )
        two.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                 ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0),
                                 ("BOTTOMPADDING", (0, 0), (-1, 0), 2)]))
        story += [Spacer(1, 2 * mm), two, Spacer(1, 4 * mm), disc]
    else:
        story += [Paragraph("Doctor's notes", st["h2"]), notes_para,
                  KeepTogether([Paragraph("Recommended next steps", st["h2"]), steps]), Spacer(1, 3 * mm),
                  KeepTogether([disc, Spacer(1, 2 * mm),
                                signature(content_w, ["Reviewing doctor (name)", "Signature", "Date"])])]

    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=margin, rightMargin=margin, topMargin=14 * mm, bottomMargin=14 * mm,
        title=f"PneumoScan report {scan['id']}", author="PneumoScan AI", subject="Chest X-ray AI screening report",
        creator="PneumoScan AI",
    )
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return buf.getvalue()


def _plain(s: str) -> str:
    if _register_fonts()[0] == "Helvetica":
        return s.encode("latin-1", "replace").decode("latin-1")
    return s
