"""Small rendering engine: turns a list of content blocks into a formatted Word report (python-docx).

Blocks are tuples; figures/tables/equations/listings are numbered per chapter in a first pass so the
text can refer to them as {fig:key}, {tab:key}, {eq:key}, {lst:key} before they appear.
Inline markup inside paragraphs: **bold** and ^^italic^^ (nothing else is interpreted).
"""
from __future__ import annotations

import re
from pathlib import Path
from xml.sax.saxutils import escape

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

FONT = "Times New Roman"
MONO = "Consolas"
TEXT_W = 8.27 - 1.25 - 1.0          # usable width in inches (A4, binding margin 1.25")
HEADER_TEXT = "Pneumonia Detection using ResNet (PneumoScan AI)"
HEADER_RIGHT = "CSDX530 – Deep Learning"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"


# ----------------------------------------------------------------------------- OMML helpers
def mt(s: str, plain: bool = False) -> str:
    rpr = '<m:rPr><m:sty m:val="p"/></m:rPr>' if plain else ""
    return (f'<m:r>{rpr}<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/></w:rPr>'
            f'<m:t xml:space="preserve">{escape(s)}</m:t></m:r>')


def mp(s: str) -> str:  # plain (upright) text, e.g. function names
    return mt(s, plain=True)


def msub(b: str, s: str) -> str:
    return f"<m:sSub><m:e>{b}</m:e><m:sub>{s}</m:sub></m:sSub>"


def msup(b: str, s: str) -> str:
    return f"<m:sSup><m:e>{b}</m:e><m:sup>{s}</m:sup></m:sSup>"


def msubsup(b: str, s: str, p: str) -> str:
    return f"<m:sSubSup><m:e>{b}</m:e><m:sub>{s}</m:sub><m:sup>{p}</m:sup></m:sSubSup>"


def mfrac(n: str, d: str) -> str:
    return f"<m:f><m:num>{n}</m:num><m:den>{d}</m:den></m:f>"


def mnary(ch: str, sub: str, sup: str, e: str) -> str:
    hide = ("" if sub else '<m:subHide m:val="1"/>') + ("" if sup else '<m:supHide m:val="1"/>')
    return (f'<m:nary><m:naryPr><m:chr m:val="{ch}"/><m:limLoc m:val="undOvr"/>{hide}</m:naryPr>'
            f"<m:sub>{sub}</m:sub><m:sup>{sup}</m:sup><m:e>{e}</m:e></m:nary>")


def mparen(e: str, l: str = "(", r: str = ")") -> str:
    return f'<m:d><m:dPr><m:begChr m:val="{l}"/><m:endChr m:val="{r}"/></m:dPr><m:e>{e}</m:e></m:d>'


def mbar(e: str) -> str:
    return f'<m:bar><m:barPr><m:pos m:val="top"/></m:barPr><m:e>{e}</m:e></m:bar>'


def mrad(e: str) -> str:
    return f'<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/><m:e>{e}</m:e></m:rad>'


# ----------------------------------------------------------------------------- low-level XML helpers
def _set_fonts(rpr_parent, name: str):
    rpr = rpr_parent.get_or_add_rPr() if hasattr(rpr_parent, "get_or_add_rPr") else rpr_parent
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.insert(0, rf)
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if rf.get(qn(a)) is not None:
            del rf.attrib[qn(a)]
    for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rf.set(qn(a), name)


def style_font(style, name=FONT, size=12, bold=None, italic=None, color=(0, 0, 0)):
    style.font.name = name
    style.font.size = Pt(size)
    if bold is not None:
        style.font.bold = bold
    if italic is not None:
        style.font.italic = italic
    if color is not None:
        style.font.color.rgb = RGBColor(*color)
    _set_fonts(style.element, name)


def shade(el_pr, fill: str):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    el_pr.append(shd)


def para_border(p_pr, sides=("top", "left", "bottom", "right"), sz=4, color="A6A6A6", space=4):
    bdr = p_pr.find(qn("w:pBdr"))
    if bdr is None:
        bdr = OxmlElement("w:pBdr")
        # pBdr must come before shd/tabs/spacing etc.; inserting early is schema-safe enough for Word
        anchor = None
        for tag in ("w:shd", "w:tabs", "w:suppressAutoHyphens", "w:spacing", "w:ind", "w:jc"):
            anchor = p_pr.find(qn(tag))
            if anchor is not None:
                break
        if anchor is not None:
            anchor.addprevious(bdr)
        else:
            p_pr.append(bdr)
    for s in sides:
        e = OxmlElement(f"w:{s}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), str(sz))
        e.set(qn("w:space"), str(space))
        e.set(qn("w:color"), color)
        bdr.append(e)


def add_field(par, instr: str, placeholder: str = "", result: bool = True, size=None):
    def run_with(el):
        r = par.add_run()
        if size:
            r.font.size = Pt(size)
        r._r.append(el)
        return r

    b = OxmlElement("w:fldChar")
    b.set(qn("w:fldCharType"), "begin")
    run_with(b)
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = f" {instr} "
    run_with(it)
    if result:
        s = OxmlElement("w:fldChar")
        s.set(qn("w:fldCharType"), "separate")
        run_with(s)
        r = par.add_run(placeholder)
        if size:
            r.font.size = Pt(size)
    e = OxmlElement("w:fldChar")
    e.set(qn("w:fldCharType"), "end")
    run_with(e)


def add_inline(par, text: str, size=None, bold=False, italic=False, font=None):
    """Add text with **bold** and ^^italic^^ markup."""
    tokens = re.split(r"(\*\*.+?\*\*|\^\^.+?\^\^)", text)
    for tok in tokens:
        if not tok:
            continue
        b, i = bold, italic
        if tok.startswith("**") and tok.endswith("**"):
            tok, b = tok[2:-2], True
        elif tok.startswith("^^") and tok.endswith("^^"):
            tok, i = tok[2:-2], True
        r = par.add_run(tok)
        r.bold = b or None
        r.italic = i or None
        if size:
            r.font.size = Pt(size)
        if font:
            r.font.name = font
            _set_fonts(r._r, font)
    return par


# ----------------------------------------------------------------------------- the engine
class Report:
    def __init__(self):
        self.doc = Document()
        self._styles()
        s = self.doc.sections[0]
        s.page_width, s.page_height = Inches(8.27), Inches(11.69)
        s.left_margin, s.right_margin = Inches(1.25), Inches(1.0)
        s.top_margin, s.bottom_margin = Inches(1.0), Inches(1.0)
        s.header_distance, s.footer_distance = Inches(0.5), Inches(0.5)
        self.chapter = 0
        self.labels: dict[str, str] = {}

    # -------------------------------------------------------------- styles
    def _styles(self):
        st = self.doc.styles
        rpr_default = self.doc.styles.element.find(qn("w:docDefaults")).find(qn("w:rPrDefault")).find(qn("w:rPr"))
        _set_fonts(rpr_default, FONT)
        n = st["Normal"]
        style_font(n, FONT, 12)
        pf = n.paragraph_format
        pf.line_spacing = 1.5
        pf.space_before = Pt(0)
        pf.space_after = Pt(6)
        pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        pf.widow_control = True

        def heading(name, size, align, before, after):
            h = st[name]
            style_font(h, FONT, size, bold=True, italic=False)
            f = h.paragraph_format
            f.alignment = align
            f.space_before, f.space_after = Pt(before), Pt(after)
            f.keep_with_next = True
            f.line_spacing = 1.15
            f.page_break_before = False

        heading("Heading 1", 16, WD_ALIGN_PARAGRAPH.CENTER, 0, 24)
        heading("Heading 2", 14, WD_ALIGN_PARAGRAPH.LEFT, 14, 6)
        heading("Heading 3", 12, WD_ALIGN_PARAGRAPH.LEFT, 10, 4)

        def pstyle(name, base="Normal"):
            try:
                s = st[name]
            except KeyError:
                s = st.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
            s.base_style = st[base]
            return s

        lab = pstyle("Chapter Label")
        style_font(lab, FONT, 14, bold=True)
        lab.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        lab.paragraph_format.space_after = Pt(6)
        lab.paragraph_format.keep_with_next = True
        lab.paragraph_format.line_spacing = 1.15

        for name, italic in (("Figure Caption", False), ("Table Caption", False), ("Listing Caption", False)):
            c = pstyle(name)
            style_font(c, FONT, 11, bold=True, italic=italic)
            c.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            c.paragraph_format.line_spacing = 1.15
            c.paragraph_format.space_before = Pt(4)
            c.paragraph_format.space_after = Pt(12) if name == "Figure Caption" else Pt(6)
            c.paragraph_format.keep_with_next = name != "Figure Caption"

        code = pstyle("Code")
        style_font(code, MONO, 8.5, color=(0x1F, 0x1F, 0x1F))
        cf = code.paragraph_format
        cf.line_spacing = 1.0
        cf.space_before = Pt(0)
        cf.space_after = Pt(0)
        cf.alignment = WD_ALIGN_PARAGRAPH.LEFT
        cf.left_indent = Inches(0.06)
        cf.right_indent = Inches(0.06)
        cf.widow_control = False
        ppr = code.element.get_or_add_pPr()
        para_border(ppr, sz=4, color="A6A6A6", space=3)
        shade(ppr, "F4F5F7")

        cell = pstyle("Table Text")
        style_font(cell, FONT, 10.5)
        cell.paragraph_format.line_spacing = 1.0
        cell.paragraph_format.space_after = Pt(0)
        cell.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

        for lvl in range(1, 10):
            name = f"TOC {lvl}"
            s = pstyle(name)
            style_font(s, FONT, 12, bold=(lvl == 1))
            f = s.paragraph_format
            f.line_spacing = 1.15
            f.space_before = Pt(6 if lvl == 1 else 0)
            f.space_after = Pt(2)
            f.alignment = WD_ALIGN_PARAGRAPH.LEFT
            f.left_indent = Inches({1: 0, 2: 0.3, 3: 0.7}.get(lvl, 0))
            f.tab_stops.add_tab_stop(Inches(TEXT_W), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        st["TOC 9"].font.bold = False
        st["TOC 9"].paragraph_format.space_before = Pt(0)
        st["TOC 9"].paragraph_format.space_after = Pt(3)
        st["TOC 9"].paragraph_format.left_indent = Inches(0.9)
        st["TOC 9"].paragraph_format.first_line_indent = Inches(-0.9)

        lb = st["List Bullet"]
        style_font(lb, FONT, 12)
        lb.paragraph_format.space_after = Pt(3)
        lb.paragraph_format.line_spacing = 1.5
        lb.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for lvl in range(1, 10):  # Word's built-in TOC styles are named "toc N" internally
            el = st[f"TOC {lvl}"].element
            el.name_val = f"toc {lvl}"
            if el.get(qn("w:customStyle")) is not None:
                del el.attrib[qn("w:customStyle")]

    # -------------------------------------------------------------- numbering pass
    def number(self, blocks):
        ch, cnt = "0", {}
        for b in blocks:
            k = b[0]
            if k == "chapter":
                ch, cnt = str(b[1]), {}
            elif k == "appendix":
                ch, cnt = b[1], {}
            elif k in ("fig", "tab", "eq", "code") and b[1]:
                kind = {"fig": "fig", "tab": "tab", "eq": "eq", "code": "lst"}[k]
                cnt[kind] = cnt.get(kind, 0) + 1
                num = f"{ch}.{cnt[kind]}"
                word = {"fig": "Figure", "tab": "Table", "eq": "Equation", "lst": "Listing"}[kind]
                self.labels[f"{kind}:{b[1]}"] = f"{word} {num}" if kind != "eq" else f"({num})"
                self.labels[f"{kind}#:{b[1]}"] = num

    def ref(self, text: str) -> str:
        def sub(m):
            key = m.group(1)
            if key not in self.labels:
                raise KeyError(f"unknown reference {key}")
            return self.labels[key]
        text = re.sub(r"\(\{(eq:[\w-]+)\}\)", lambda m: "{" + m.group(1) + "}", text)
        return re.sub(r"\{((?:fig|tab|eq|lst)#?:[\w-]+)\}", sub, text)

    # -------------------------------------------------------------- sections
    def new_section(self, kind: str):
        d = self.doc
        sec = d.add_section(WD_SECTION.NEW_PAGE)
        sect = sec._sectPr
        pg = OxmlElement("w:pgNumType")
        pg.set(qn("w:fmt"), "lowerRoman" if kind == "front" else "decimal")
        pg.set(qn("w:start"), "1")
        cols = sect.find(qn("w:cols"))
        if cols is not None:
            cols.addprevious(pg)
        else:
            sect.append(pg)
        sec.footer.is_linked_to_previous = False
        sec.header.is_linked_to_previous = False
        fp = sec.footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        fp.paragraph_format.space_after = Pt(0)
        add_field(fp, "PAGE", "1", size=11)
        hp = sec.header.paragraphs[0]
        hp.paragraph_format.space_after = Pt(0)
        if kind == "main":
            for pos in (3.25, 6.5):
                hp.paragraph_format.tab_stops.add_tab_stop(Inches(pos), WD_TAB_ALIGNMENT.CLEAR)
            hp.paragraph_format.tab_stops.add_tab_stop(Inches(TEXT_W), WD_TAB_ALIGNMENT.RIGHT)
            r = hp.add_run(HEADER_TEXT + "\t" + HEADER_RIGHT)
            r.italic = True
            r.font.size = Pt(9)
            r.font.color.rgb = RGBColor(0x59, 0x59, 0x59)
            para_border(hp._p.get_or_add_pPr(), sides=("bottom",), sz=4, color="A6A6A6", space=1)
        return sec

    # -------------------------------------------------------------- block renderers
    def p(self, text, align=None, size=None, bold=False, italic=False, before=None, after=None,
          spacing=None, keep=False, indent=None):
        par = self.doc.add_paragraph()
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
        if indent is not None:
            f.left_indent = Inches(indent)
        return par

    def tc(self, par, text, level=1):
        add_field(par, f'TC "{text}" \\l {level}', result=False)

    def chapter_block(self, num, title):
        lab = self.doc.add_paragraph(f"CHAPTER {num}", style="Chapter Label")
        lab.paragraph_format.page_break_before = True
        h = self.doc.add_paragraph(title.upper(), style="Heading 1")
        self.tc(h, f"{num}\t{title.upper()}")

    def front_heading(self, title, toc=True, page_break=True):
        h = self.doc.add_paragraph(title.upper(), style="Heading 1")
        h.paragraph_format.page_break_before = page_break
        if toc:
            self.tc(h, title.upper())
        return h

    def bullets(self, items, level=0):
        for it in items:
            par = self.doc.add_paragraph(style="List Bullet")
            add_inline(par, self.ref(it))
            if level:
                par.paragraph_format.left_indent = Inches(0.25 + 0.25 * (level + 1))

    def numbered(self, items):
        for i, it in enumerate(items, 1):
            par = self.doc.add_paragraph()
            f = par.paragraph_format
            f.left_indent = Inches(0.35)
            f.first_line_indent = Inches(-0.35)
            f.space_after = Pt(3)
            f.tab_stops.add_tab_stop(Inches(0.35))
            add_inline(par, f"{i}.\t" + self.ref(it))

    def figure(self, key, path, width, caption):
        par = self.doc.add_paragraph()
        f = par.paragraph_format
        f.alignment = WD_ALIGN_PARAGRAPH.CENTER
        f.keep_with_next = True
        f.space_before = Pt(6)
        f.space_after = Pt(0)
        f.line_spacing = 1.0
        par.add_run().add_picture(str(path), width=Inches(width))
        num = self.labels[f"fig#:{key}"]
        c = self.doc.add_paragraph(style="Figure Caption")
        add_inline(c, f"Figure {num}: " + self.ref(caption))

    def table(self, key, caption, headers, rows, widths, size=10.5, align=None, bold_last=False, note=None,
              header_fill="D9E2F3", bold_rows=()):
        num = self.labels[f"tab#:{key}"]
        c = self.doc.add_paragraph(style="Table Caption")
        add_inline(c, f"Table {num}: " + self.ref(caption))
        ncol = len(headers)
        t = self.doc.add_table(rows=1 + len(rows), cols=ncol)
        t.style = self.doc.styles["Table Grid"]
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        tblPr = t._tbl.tblPr
        lay = OxmlElement("w:tblLayout")
        lay.set(qn("w:type"), "fixed")
        tblPr.append(lay)
        mar = OxmlElement("w:tblCellMar")
        for side, v in (("top", 30), ("bottom", 30), ("left", 80), ("right", 80)):
            e = OxmlElement(f"w:{side}")
            e.set(qn("w:w"), str(v))
            e.set(qn("w:type"), "dxa")
            mar.append(e)
        tblPr.append(mar)
        align = align or ["L"] * ncol
        amap = {"L": WD_ALIGN_PARAGRAPH.LEFT, "C": WD_ALIGN_PARAGRAPH.CENTER, "R": WD_ALIGN_PARAGRAPH.RIGHT}
        for ri, row in enumerate([headers] + rows):
            tr = t.rows[ri]
            trPr = tr._tr.get_or_add_trPr()
            cs = OxmlElement("w:cantSplit")
            trPr.append(cs)
            if ri == 0:
                th = OxmlElement("w:tblHeader")
                trPr.append(th)
            for ci, val in enumerate(row):
                cell = tr.cells[ci]
                cell.width = Inches(widths[ci])
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                par = cell.paragraphs[0]
                par.style = self.doc.styles["Table Text"]
                par.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER if ri == 0 else amap[align[ci]]
                if ri == 0 or ri < len(rows) and False:
                    pass
                is_bold = ri == 0 or (bold_last and ri == len(rows)) or (ri - 1) in bold_rows
                add_inline(par, self.ref(str(val)), size=size, bold=is_bold)
                if ri == 0:
                    shade(cell._tc.get_or_add_tcPr(), header_fill)
                if ri < len(rows):
                    par.paragraph_format.keep_with_next = True if len(rows) < 25 else False
        # grid widths
        grid = t._tbl.tblGrid
        for gc, w in zip(grid.findall(qn("w:gridCol")), widths):
            gc.set(qn("w:w"), str(int(w * 1440)))
        after = self.doc.add_paragraph()
        after.paragraph_format.space_after = Pt(4)
        after.paragraph_format.line_spacing = 1.0
        if note:
            add_inline(after, self.ref(note), size=10, italic=True)
            after.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
            after.paragraph_format.space_before = Pt(3)
            after.paragraph_format.space_after = Pt(8)
        else:
            if getattr(self, "_skip_spacer", False):
                after._p.getparent().remove(after._p)
            else:
                after.paragraph_format.line_spacing = Pt(6)
                after.paragraph_format.space_after = Pt(0)

    def equation(self, key, omml):
        t = self.doc.add_table(rows=1, cols=2)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        tblPr = t._tbl.tblPr
        b = OxmlElement("w:tblBorders")
        for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
            e = OxmlElement(f"w:{side}")
            e.set(qn("w:val"), "nil")
            b.append(e)
        tblPr.append(b)
        lay = OxmlElement("w:tblLayout")
        lay.set(qn("w:type"), "fixed")
        tblPr.append(lay)
        widths = (TEXT_W - 0.75, 0.75)
        for gc, w in zip(t._tbl.tblGrid.findall(qn("w:gridCol")), widths):
            gc.set(qn("w:w"), str(int(w * 1440)))
        c_eq, c_no = t.rows[0].cells
        c_eq.width, c_no.width = Inches(widths[0]), Inches(widths[1])
        for c in (c_eq, c_no):
            c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        par = c_eq.paragraphs[0]
        f = par.paragraph_format
        f.alignment = WD_ALIGN_PARAGRAPH.CENTER
        f.space_before = Pt(3)
        f.space_after = Pt(3)
        f.line_spacing = 1.0
        xml = (f'<m:oMathPara xmlns:m="{M_NS}" xmlns:w="{W_NS}"><m:oMathParaPr><m:jc m:val="center"/>'
               f'</m:oMathParaPr><m:oMath>{omml}</m:oMath></m:oMathPara>')
        par._p.append(parse_xml(xml))
        pn = c_no.paragraphs[0]
        pn.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        pn.paragraph_format.space_after = Pt(0)
        pn.paragraph_format.line_spacing = 1.0
        pn.add_run(self.labels[f"eq:{key}"])
        sp = self.doc.add_paragraph()
        sp.paragraph_format.space_after = Pt(0)
        sp.paragraph_format.line_spacing = Pt(4)

    def code(self, key, caption, text, size=8.5):
        if caption:
            num = self.labels[f"lst#:{key}"]
            c = self.doc.add_paragraph(style="Listing Caption")
            add_inline(c, f"Listing {num}: " + self.ref(caption))
        lines = text.expandtabs(4).rstrip("\n").split("\n")
        for i, line in enumerate(lines):
            par = self.doc.add_paragraph(style="Code")
            r = par.add_run(line if line else "")
            if size != 8.5:
                r.font.size = Pt(size)
            if i < 2 or len(lines) <= 30 or i >= len(lines) - 4:
                par.paragraph_format.keep_with_next = i < len(lines) - 1
            if i == len(lines) - 1:
                par.paragraph_format.keep_with_next = False
        if getattr(self, "_skip_spacer", False):
            return
        sp = self.doc.add_paragraph()
        sp.paragraph_format.space_after = Pt(0)
        sp.paragraph_format.line_spacing = Pt(8)

    def toc(self, instr, placeholder="Right-click and choose Update Field to build this list."):
        par = self.doc.add_paragraph()
        par.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        add_field(par, instr, placeholder)

    def page_break(self):
        par = self.doc.add_paragraph()
        par.paragraph_format.space_after = Pt(0)
        par.add_run().add_break(WD_BREAK.PAGE)

    # -------------------------------------------------------------- driver
    def render(self, blocks):
        self.number(blocks)
        for i, b in enumerate(blocks):
            nxt = blocks[i + 1][0] if i + 1 < len(blocks) else "end"
            self._skip_spacer = nxt in ("chapter", "appendix", "front", "raw", "section", "end")
            k = b[0]
            if k == "raw":
                b[1](self)
            elif k == "section":
                self.new_section(b[1])
            elif k == "chapter":
                self.chapter_block(b[1], b[2])
            elif k == "appendix":
                self.front_heading(b[2], toc=False)
                self.tc(self.doc.paragraphs[-1], b[2].upper())
            elif k == "front":
                self.front_heading(b[1], toc=b[2] if len(b) > 2 else True)
            elif k == "h2":
                self.doc.add_paragraph(self.ref(b[1]), style="Heading 2")
            elif k == "h3":
                self.doc.add_paragraph(self.ref(b[1]), style="Heading 3")
            elif k == "p":
                self.p(b[1], **(b[2] if len(b) > 2 else {}))
            elif k == "bullets":
                self.bullets(b[1])
            elif k == "numbered":
                self.numbered(b[1])
            elif k == "fig":
                self.figure(*b[1:])
            elif k == "tab":
                self.table(*b[1:6], **(b[6] if len(b) > 6 else {}))
            elif k == "eq":
                self.equation(b[1], b[2])
            elif k == "code":
                self.code(*b[1:])
            elif k == "pagebreak":
                self.page_break()
            else:
                raise ValueError(k)

    def save(self, path: Path):
        self.doc.save(str(path))
