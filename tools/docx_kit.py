# -*- coding: utf-8 -*-
"""docx_kit.py —— 中文毕设系列文档的统一排版工具。

所有文档共用：A4 / 页边距 2.5cm / 正文宋体小四 1.5 倍行距 / 标题黑体 /
表头浅蓝底纹 / 页眉文档名 / 页脚页码。
"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import (WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_BREAK,
                            WD_TAB_ALIGNMENT)
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

CN_BODY = "宋体"
CN_HEAD = "黑体"
EN_FONT = "Times New Roman"

C_ACCENT = RGBColor(0x1F, 0x3B, 0x63)   # 深蓝
C_SUB = RGBColor(0x44, 0x54, 0x6A)
C_GRAY = RGBColor(0x59, 0x59, 0x59)
C_RED = RGBColor(0xB0, 0x30, 0x24)
C_GREEN = RGBColor(0x1E, 0x6B, 0x3A)

HDR_BG = "DCE6F1"
BOX_BG = "F2F5F9"
WARN_BG = "FDF0E6"
OK_BG = "EAF4EC"


# ---------------------------------------------------------------- 基础设置
def _set_run(run, size=12, bold=False, color=None, cn=CN_BODY, en=EN_FONT, italic=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.name = en
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:ascii"), en)
    rFonts.set(qn("w:hAnsi"), en)
    rFonts.set(qn("w:eastAsia"), cn)
    if color is not None:
        run.font.color.rgb = color
    return run


def _emit_runs(para, text, size=12, bold=False, color=None, cn=CN_BODY,
               en=EN_FONT, italic=False):
    """把一个字符串写入段落，支持 **行内加粗** 标记。"""
    parts = str(text).split("**")
    for i, seg in enumerate(parts):
        if not seg:
            continue
        _set_run(para.add_run(seg), size=size,
                 bold=(bold or (i % 2 == 1)), color=color, cn=cn, en=en,
                 italic=italic)


def _style_font(style, cn, en, size, bold=False, color=None):
    style.font.name = en
    style.font.size = Pt(size)
    style.font.bold = bold
    if color is not None:
        style.font.color.rgb = color
    rPr = style.element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:ascii"), en)
    rFonts.set(qn("w:hAnsi"), en)
    rFonts.set(qn("w:eastAsia"), cn)


def _page_number_footer(section, prefix=""):
    footer = section.footer
    footer.is_linked_to_previous = False
    para = footer.paragraphs[0]
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.text = ""
    if prefix:
        _set_run(para.add_run(prefix), size=9, color=C_GRAY)
    r = para.add_run()
    _set_run(r, size=9, color=C_GRAY)
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    r._r.append(fld_begin)
    r._r.append(instr)
    r._r.append(fld_end)


def new_doc(header_text="", landscape=False):
    """创建文档并完成全局样式/页眉页脚设置。"""
    doc = Document()

    sec = doc.sections[0]
    if landscape:
        sec.orientation = 1
        sec.page_width, sec.page_height = Cm(29.7), Cm(21.0)
    else:
        sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.top_margin = Cm(2.4)
    sec.bottom_margin = Cm(2.2)
    sec.left_margin = Cm(2.5)
    sec.right_margin = Cm(2.3)
    sec.header_distance = Cm(1.4)
    sec.footer_distance = Cm(1.2)

    normal = doc.styles["Normal"]
    _style_font(normal, CN_BODY, EN_FONT, 12)
    pf = normal.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    pf.space_before = Pt(0)
    pf.space_after = Pt(4)

    if header_text:
        hdr = sec.header
        hdr.is_linked_to_previous = False
        hp = hdr.paragraphs[0]
        hp.text = ""
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        _set_run(hp.add_run(header_text), size=9, color=C_GRAY, cn=CN_BODY)
        pPr = hp._p.get_or_add_pPr()
        pbdr = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), "6")
        bottom.set(qn("w:space"), "1")
        bottom.set(qn("w:color"), "BFBFBF")
        pbdr.append(bottom)
        pPr.append(pbdr)

    _page_number_footer(sec, "")
    return doc


# ---------------------------------------------------------------- 段落构件
def cover(doc, kicker, title, subtitle, metas, footer_note=""):
    """封面。metas: [(标签, 内容), ...]"""
    for _ in range(2):
        pb = doc.add_paragraph()
        pb.paragraph_format.space_after = Pt(0)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(6)
    _set_run(p.add_run(kicker), size=12, color=C_GRAY, cn=CN_HEAD)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(6)
    _set_run(p.add_run(title), size=26, bold=True, color=C_ACCENT, cn=CN_HEAD)

    if subtitle:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(10)
        _set_run(p.add_run(subtitle), size=13, color=C_SUB, cn=CN_HEAD)

    # 分隔线
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pPr = p._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "12")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "1F3B63")
    pbdr.append(bottom)
    pPr.append(pbdr)

    doc.add_paragraph().paragraph_format.space_after = Pt(18)

    # 元信息：用制表位排版（表格在 LibreOffice/Word 下边框行为不可靠）
    for label, value in metas:
        para = doc.add_paragraph()
        pf = para.paragraph_format
        pf.left_indent = Cm(7.9)
        pf.first_line_indent = Cm(-4.7)
        pf.space_before = Pt(3)
        pf.space_after = Pt(3)
        pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
        ts = pf.tab_stops
        ts.add_tab_stop(Cm(7.4), WD_TAB_ALIGNMENT.RIGHT)
        ts.add_tab_stop(Cm(7.9), WD_TAB_ALIGNMENT.LEFT)
        _set_run(para.add_run(label), size=11, bold=True, color=C_SUB, cn=CN_HEAD)
        _set_run(para.add_run("\t\t"), size=11, color=C_GRAY)
        _emit_runs(para, value, size=11, color=C_GRAY)

    if footer_note:
        doc.add_paragraph().paragraph_format.space_after = Pt(10)
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(2.0)
        p.paragraph_format.right_indent = Cm(2.0)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _emit_runs(p, footer_note, size=9, color=C_GRAY, italic=True)
    page_break(doc)


def h1(doc, text, num=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(16)
    pf.space_after = Pt(8)
    pf.keep_with_next = True
    _set_run(p.add_run(text), size=17, bold=True, color=C_ACCENT, cn=CN_HEAD)
    # 下边框
    pPr = p._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "8")
    bottom.set(qn("w:space"), "3")
    bottom.set(qn("w:color"), "9DB3CE")
    pbdr.append(bottom)
    pPr.append(pbdr)
    return p


def h2(doc, text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(12)
    pf.space_after = Pt(5)
    pf.keep_with_next = True
    _set_run(p.add_run(text), size=13.5, bold=True, color=C_ACCENT, cn=CN_HEAD)
    return p


def h3(doc, text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(8)
    pf.space_after = Pt(3)
    pf.keep_with_next = True
    _set_run(p.add_run(text), size=12, bold=True, color=C_SUB, cn=CN_HEAD)
    return p


def p(doc, text, indent=True, size=12, bold=False, color=None, space_after=4, align=None):
    para = doc.add_paragraph()
    if indent:
        para.paragraph_format.first_line_indent = Cm(0.85)
    para.paragraph_format.space_after = Pt(space_after)
    if align == "center":
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "right":
        para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    else:
        para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    _emit_runs(para, text, size=size, bold=bold, color=color)
    return para


def rich(doc, parts, indent=True, space_after=4):
    """parts: [(text, {opts}), ...] 支持同段内不同加粗。"""
    para = doc.add_paragraph()
    if indent:
        para.paragraph_format.first_line_indent = Cm(0.85)
    para.paragraph_format.space_after = Pt(space_after)
    para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for text, opts in parts:
        _set_run(para.add_run(text), **_norm_opts(opts))
    return para


def _norm_opts(o):
    o = dict(o or {})
    m = {"b": "bold", "sz": "size", "c": "color", "it": "italic", "cn": "cn"}
    for k, v in list(o.items()):
        if k in m:
            o[m[k]] = o.pop(k)
    return o


def bullet(doc, text, level=0, size=12, marker="●"):
    para = doc.add_paragraph()
    pf = para.paragraph_format
    pf.left_indent = Cm(0.85 + 0.75 * level)
    pf.first_line_indent = Cm(-0.45)
    pf.space_after = Pt(2)
    para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    marks = {0: "●", 1: "○", 2: "▪"}
    _set_run(para.add_run(f"{marks.get(level, '·')} "), size=size - 1, color=C_ACCENT)
    if isinstance(text, (list, tuple)):
        for seg, opts in text:
            _set_run(para.add_run(seg), **_norm_opts({"size": size, **opts}))
    else:
        _emit_runs(para, text, size=size)
    return para


def num(doc, idx, text, size=12):
    para = doc.add_paragraph()
    pf = para.paragraph_format
    pf.left_indent = Cm(1.0)
    pf.first_line_indent = Cm(-0.6)
    pf.space_after = Pt(2)
    para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    _set_run(para.add_run(f"{idx}. "), size=size, bold=True, color=C_ACCENT)
    _emit_runs(para, text, size=size)
    return para


def hint(doc, text, size=10):
    para = doc.add_paragraph()
    para.paragraph_format.left_indent = Cm(0.85)
    para.paragraph_format.space_after = Pt(4)
    _emit_runs(para, text, size=size, color=C_GRAY, italic=True)
    return para


def _shade(paragraph_or_cell, color):
    el = paragraph_or_cell._p if hasattr(paragraph_or_cell, "_p") else paragraph_or_cell._tc
    pPr = el.get_or_add_pPr() if hasattr(el, "get_or_add_pPr") else el.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    pPr.append(shd)


def _tc_borders(cell, color="C9D6E5", left_sz=4, left_color=None):
    """写入 tcBorders，并保证在 tcPr 中位于 w:shd 之前（OOXML 顺序要求）。"""
    tcPr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right"):
        b = OxmlElement(f"w:{side}")
        b.set(qn("w:val"), "single")
        if side == "left" and left_sz != 4:
            b.set(qn("w:sz"), str(left_sz))
            b.set(qn("w:color"), left_color or color)
        else:
            b.set(qn("w:sz"), "4")
            b.set(qn("w:color"), color)
        borders.append(b)
    shd = tcPr.find(qn("w:shd"))
    if shd is not None:
        shd.addprevious(borders)
    else:
        tcPr.append(borders)
    return borders


def _apply_widths(t, widths):
    """同时设置 gridCol 与 tcW，否则 Word/LibreOffice 会退回等宽渲染。"""
    t.autofit = False
    for i, w in enumerate(widths):
        if i < len(t.columns):
            t.columns[i].width = Cm(w)
    for row in t.rows:
        for i, w in enumerate(widths):
            if i < len(row.cells):
                row.cells[i].width = Cm(w)


def _clear_borders(t):
    """去掉表格全部边框（封面元信息表用）。"""
    tblPr = t._tbl.tblPr
    for existing in tblPr.findall(qn("w:tblBorders")):
        tblPr.remove(existing)
    borders = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"), "none")
        el.set(qn("w:sz"), "0")
        el.set(qn("w:space"), "0")
        borders.append(el)
    anchor = None
    for tag in ("w:shd", "w:tblLayout", "w:tblCellMar", "w:tblLook",
                "w:tblCaption", "w:tblDescription"):
        anchor = tblPr.find(qn(tag))
        if anchor is not None:
            break
    if anchor is not None:
        anchor.addprevious(borders)
    else:
        tblPr.append(borders)


def callout(doc, title, lines, kind="info"):
    """带底纹的提示框。kind: info / warn / ok"""
    bg = {"info": BOX_BG, "warn": WARN_BG, "ok": OK_BG}.get(kind, BOX_BG)
    accent = {"info": C_ACCENT, "warn": C_RED, "ok": C_GREEN}.get(kind, C_ACCENT)
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = t.rows[0].cells[0]
    cell.width = Cm(16.2)
    _tc_borders(cell, color="C9D6E5", left_sz=18, left_color="1F3B63")
    _shade(cell, bg)
    cell.paragraphs[0].text = ""
    if title:
        pp = cell.paragraphs[0]
        pp.paragraph_format.space_after = Pt(3)
        _set_run(pp.add_run(title), size=11, bold=True, color=accent, cn=CN_HEAD)
        first = False
    else:
        first = True
    for line in lines:
        if isinstance(line, (list, tuple)):
            txt, opts = line
        else:
            txt, opts = line, {}
        para = cell.paragraphs[0] if first else cell.add_paragraph()
        first = False
        para.paragraph_format.space_after = Pt(2)
        para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        _emit_runs(para, txt, **_norm_opts({"size": 10.5, **opts}))
    after = doc.add_paragraph()
    after.paragraph_format.space_after = Pt(2)
    return t


def table(doc, headers, rows, widths=None, font_size=9.5, header_bg=HDR_BG,
          align=None, first_col_bold=False, zebra=False, bold_rows=None,
          row_height=None):
    """标准表格。rows 单元格内容支持 '\\n' 换行。"""
    ncol = len(headers)
    t = doc.add_table(rows=1, cols=ncol)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False

    hdr = t.rows[0]
    trPr = hdr._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    trPr.append(th)
    for i, htext in enumerate(headers):
        cell = hdr.cells[i]
        _shade(cell, header_bg)
        para = cell.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para.paragraph_format.space_after = Pt(1)
        para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        _set_run(para.add_run(htext), size=font_size, bold=True, color=C_ACCENT, cn=CN_HEAD)

    bold_rows = set(bold_rows or [])
    for ri, row in enumerate(rows):
        tr = t.add_row()
        trPr2 = tr._tr.get_or_add_trPr()
        cant = OxmlElement("w:cantSplit")
        trPr2.append(cant)
        cells = tr.cells
        for ci, val in enumerate(row):
            cell = cells[ci]
            if zebra and ri % 2 == 1:
                _shade(cell, "F7F9FC")
            lines = str(val).split("\n")
            cell.paragraphs[0].text = ""
            for li, line in enumerate(lines):
                para = cell.paragraphs[0] if li == 0 else cell.add_paragraph()
                para.paragraph_format.space_after = Pt(0)
                para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
                if align and ci < len(align):
                    para.alignment = {"l": WD_ALIGN_PARAGRAPH.LEFT,
                                      "c": WD_ALIGN_PARAGRAPH.CENTER,
                                      "r": WD_ALIGN_PARAGRAPH.RIGHT}[align[ci]]
                bold = (first_col_bold and ci == 0) or (ri in bold_rows)
                _emit_runs(para, line, size=font_size, bold=bold)

    if widths:
        _apply_widths(t, widths)
    if row_height:
        for row in t.rows:
            row.height = Cm(row_height)
    after = doc.add_paragraph()
    after.paragraph_format.space_after = Pt(1)
    after.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    return t


def caption(doc, text, above=False):
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.space_before = Pt(4 if above else 0)
    para.paragraph_format.space_after = Pt(4 if not above else 2)
    _set_run(para.add_run(text), size=9.5, color=C_GRAY)
    return para


def code_block(doc, text, size=8.5):
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = t.rows[0].cells[0]
    cell.width = Cm(16.2)
    _tc_borders(cell, color="D9D9D9")
    _shade(cell, "F4F4F4")
    lines = text.strip("\n").split("\n")
    cell.paragraphs[0].text = ""
    for li, line in enumerate(lines):
        para = cell.paragraphs[0] if li == 0 else cell.add_paragraph()
        para.paragraph_format.space_after = Pt(0)
        para.paragraph_format.space_before = Pt(0)
        para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        _set_run(para.add_run(line if line else " "), size=size,
                 cn="Consolas", en="Consolas", color=RGBColor(0x33, 0x33, 0x33))
    after = doc.add_paragraph()
    after.paragraph_format.space_after = Pt(2)
    return t


def page_break(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def save(doc, path):
    doc.save(path)
    return path
