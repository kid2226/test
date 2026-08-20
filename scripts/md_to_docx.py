#!/usr/bin/env python3
"""Export the China bonds vs equities report to a readable Word file."""

import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Emu, Pt, RGBColor, Twips

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "reports" / "中国债券与股票资产比较研究报告.md"
DOCX = ROOT / "reports" / "中国债券与股票资产比较研究报告.docx"
FIG = ROOT / "reports" / "figures"

NAVY = RGBColor(0x1B, 0x36, 0x5D)
GOLD = RGBColor(0xC4, 0xA3, 0x5A)
BODY = RGBColor(0x22, 0x22, 0x22)
SLATE = RGBColor(0x5A, 0x67, 0x7A)
TEAL = RGBColor(0x1F, 0x7A, 0x6E)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
CN_FONT = "微软雅黑"
EN_FONT = "Calibri"


def set_run_font(run, name=CN_FONT, size=12, bold=False, color=BODY, italic=False, east_asia=None):
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.name = name
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn("w:ascii"), EN_FONT if name == CN_FONT else name)
    rFonts.set(qn("w:hAnsi"), EN_FONT if name == CN_FONT else name)
    rFonts.set(qn("w:eastAsia"), east_asia or CN_FONT)


def shade_paragraph(paragraph, fill: str):
    pPr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), fill)
    pPr.append(shd)


def set_cell_shading(cell, fill: str):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    shd.set(qn("w:val"), "clear")
    tcPr.append(shd)


def set_cell_margins(cell, top=60, bottom=60, left=80, right=80):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for m, val in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        node = OxmlElement(f"w:{m}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def set_paragraph_spacing(p, before=0, after=8, line=1.2, align=None, first_line=None):
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = line
    if align is not None:
        p.alignment = align
    if first_line is not None:
        pf.first_line_indent = Cm(first_line)


def add_bottom_border(paragraph, color="1B365D", size="12"):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), size)
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), color)
    pBdr.append(bottom)
    pPr.append(pBdr)


def prevent_split(paragraph):
    pPr = paragraph._p.get_or_add_pPr()
    kwn = OxmlElement("w:keepNext")
    kwn.set(qn("w:val"), "true")
    pPr.append(kwn)


def add_page_number_field(paragraph):
    run = paragraph.add_run()
    set_run_font(run, size=9, color=SLATE)
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)


def set_table_full_width(table):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl = table._tbl
    tblPr = tbl.tblPr
    tblW = tblPr.find(qn("w:tblW"))
    if tblW is None:
        tblW = OxmlElement("w:tblW")
        tblPr.append(tblW)
    tblW.set(qn("w:w"), "5000")
    tblW.set(qn("w:type"), "pct")


def configure_styles(doc):
    normal = doc.styles["Normal"]
    normal.font.name = CN_FONT
    normal.font.size = Pt(12)
    normal.font.color.rgb = BODY
    rPr = normal.element.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn("w:ascii"), EN_FONT)
    rFonts.set(qn("w:hAnsi"), EN_FONT)
    rFonts.set(qn("w:eastAsia"), CN_FONT)
    pf = normal.paragraph_format
    pf.line_spacing = 1.22
    pf.space_after = Pt(6)

    heading_specs = {
        "Heading 1": (18, NAVY, 16, 8),
        "Heading 2": (14, TEAL, 12, 6),
        "Heading 3": (12, NAVY, 10, 4),
    }
    for name, (size, color, before, after) in heading_specs.items():
        style = doc.styles[name]
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = color
        style.font.name = CN_FONT
        rPr = style.element.get_or_add_rPr()
        rFonts = rPr.get_or_add_rFonts()
        rFonts.set(qn("w:ascii"), EN_FONT)
        rFonts.set(qn("w:hAnsi"), EN_FONT)
        rFonts.set(qn("w:eastAsia"), CN_FONT)
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.line_spacing = 1.15


def pretty_math(text: str) -> str:
    text = text.replace("\\[", "").replace("\\]", "")
    text = text.replace("\\(", "").replace("\\)", "")
    text = re.sub(r"\\text\{([^}]+)\}", r"\1", text)
    text = re.sub(r"\\mathrm\{([^}]+)\}", r"\1", text)
    text = re.sub(r"\\frac\{([^}]+)\}\{([^}]+)\}", r"(\1)/(\2)", text)
    text = re.sub(r"\\sum_\{([^}]+)\}", r"Σ_{\1}", text)
    text = text.replace("\\sum", "Σ")
    text = text.replace("\\Delta", "Δ")
    text = text.replace("\\approx", "≈")
    text = text.replace("\\quad", "    ")
    text = text.replace("\\,", " ")
    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def add_mixed_runs(paragraph, text, size=12, color=BODY):
    text = pretty_math(text)
    pattern = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`)")
    pos = 0
    for m in pattern.finditer(text):
        if m.start() > pos:
            run = paragraph.add_run(text[pos : m.start()])
            set_run_font(run, size=size, color=color)
        token = m.group(0)
        if token.startswith("**"):
            run = paragraph.add_run(token[2:-2])
            set_run_font(run, size=size, bold=True, color=NAVY)
        else:
            run = paragraph.add_run(token[1:-1])
            set_run_font(run, name="Consolas", size=size, color=TEAL)
        pos = m.end()
    if pos < len(text):
        run = paragraph.add_run(text[pos:])
        set_run_font(run, size=size, color=color)


def is_table_separator(line: str) -> bool:
    return bool(re.match(r"^\s*\|?\s*:?-{3,}", line))


def parse_table_row(line: str):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def add_table(doc, rows):
    if not rows:
        return
    ncols = max(len(r) for r in rows)
    table = doc.add_table(rows=len(rows), cols=ncols)
    table.style = "Table Grid"
    set_table_full_width(table)
    for i, row in enumerate(rows):
        for j in range(ncols):
            cell = table.rows[i].cells[j]
            text = pretty_math(row[j] if j < len(row) else "")
            cell.text = ""
            p = cell.paragraphs[0]
            set_paragraph_spacing(p, before=1, after=1, line=1.08)
            run = p.add_run(re.sub(r"\*\*([^*]+)\*\*", r"\1", text))
            set_cell_margins(cell)
            if i == 0:
                set_run_font(run, size=10, bold=True, color=WHITE)
                set_cell_shading(cell, "1B365D")
            else:
                set_run_font(run, size=10, color=BODY)
                set_cell_shading(cell, "F7F5F2" if i % 2 == 0 else "FFFFFF")
    spacer = doc.add_paragraph()
    set_paragraph_spacing(spacer, before=2, after=8)


def add_picture(doc, rel_path: str, caption: str | None = None):
    path = (MD.parent / rel_path).resolve()
    if not path.exists():
        path = FIG / Path(rel_path).name
    if not path.exists():
        p = doc.add_paragraph()
        run = p.add_run(f"[缺失配图：{rel_path}]")
        set_run_font(run, size=10, italic=True, color=SLATE)
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_spacing(p, before=10, after=4)
    prevent_split(p)
    run = p.add_run()
    run.add_picture(str(path), width=Cm(15.8))
    if caption:
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_paragraph_spacing(cap, before=0, after=12)
        r = cap.add_run(caption)
        set_run_font(r, size=10, italic=True, color=SLATE)


def add_heading(doc, text, level):
    p = doc.add_paragraph(style=f"Heading {level}")
    p.clear()
    run = p.add_run(text)
    if level == 1:
        set_run_font(run, size=18, bold=True, color=NAVY)
        add_bottom_border(p)
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(8)
    else:
        set_run_font(run, size=14, bold=True, color=TEAL)
        p.paragraph_format.space_before = Pt(13)
        p.paragraph_format.space_after = Pt(6)
    prevent_split(p)
    return p


def collect_toc(lines):
    items = []
    for line in lines:
        s = line.strip()
        if s.startswith("## "):
            items.append((1, s[3:]))
        elif s.startswith("### "):
            items.append((2, s[4:]))
    return items


def add_cover(doc):
    banner = doc.add_paragraph()
    banner.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_spacing(banner, before=0, after=0, line=1.0)
    shade_paragraph(banner, "1B365D")
    run = banner.add_run("大类资产配置投研手册")
    set_run_font(run, size=12, bold=True, color=WHITE)

    for _ in range(3):
        p = doc.add_paragraph()
        set_paragraph_spacing(p, before=0, after=0)

    kicker = doc.add_paragraph()
    kicker.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_spacing(kicker, before=24, after=8)
    r = kicker.add_run("COMPARATIVE RESEARCH NOTE")
    set_run_font(r, size=11, color=GOLD)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_spacing(title, before=6, after=10)
    r = title.add_run("中国债券资产与股票资产比较研究")
    set_run_font(r, size=28, bold=True, color=NAVY)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_spacing(sub, before=0, after=18)
    r = sub.add_run("理论框架 · 市场结构 · 配置范式")
    set_run_font(r, size=16, color=TEAL)

    bar = doc.add_paragraph()
    bar.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_spacing(bar, before=0, after=16)
    add_bottom_border(bar, "C4A35A", "18")

    meta = [
        ("报告日期", "2026年8月"),
        ("数据截止", "原则上截至2025年末；比价补充至2026年8月中旬"),
        ("阅读建议", "可用 Word 左侧导航窗格按章节跳转"),
        ("版本", "便于阅读的排版导出（含封面、目录、14张配图）"),
    ]
    table = doc.add_table(rows=len(meta), cols=2)
    set_table_full_width(table)
    for i, (k, v) in enumerate(meta):
        left, right = table.rows[i].cells
        left.text = ""
        right.text = ""
        lp, rp = left.paragraphs[0], right.paragraphs[0]
        set_paragraph_spacing(lp, before=2, after=2)
        set_paragraph_spacing(rp, before=2, after=2)
        lr = lp.add_run(k)
        rr = rp.add_run(v)
        set_run_font(lr, size=11, bold=True, color=WHITE)
        set_run_font(rr, size=11, color=NAVY)
        set_cell_shading(left, "1B365D")
        set_cell_shading(right, "F7F5F2")
        set_cell_margins(left)
        set_cell_margins(right)

    note = doc.add_paragraph()
    set_paragraph_spacing(note, before=22, after=8, first_line=0)
    add_mixed_runs(
        note,
        "这份 Word 版与 Markdown 源文件内容一致，但按阅读习惯重排：封面、目录、Word 标题样式、页码和配图均已嵌入，可直接发给同事离线查看。",
        size=12,
    )

    disc = doc.add_paragraph()
    set_paragraph_spacing(disc, before=4, after=0, first_line=0)
    r = disc.add_run("供投研训练与框架学习使用，不构成投资建议。")
    set_run_font(r, size=11, italic=True, color=SLATE)

    doc.add_page_break()


def add_toc(doc, items):
    h = doc.add_paragraph(style="Heading 1")
    h.clear()
    run = h.add_run("目录")
    set_run_font(run, size=18, bold=True, color=NAVY)
    add_bottom_border(h)
    prevent_split(h)

    hint = doc.add_paragraph()
    set_paragraph_spacing(hint, before=2, after=10)
    r = hint.add_run("打开 Word 后，也可使用「视图 → 导航窗格」按章节浏览。")
    set_run_font(r, size=10, italic=True, color=SLATE)

    for level, title in items:
        p = doc.add_paragraph()
        set_paragraph_spacing(p, before=1, after=1, line=1.15)
        if level == 1:
            p.paragraph_format.left_indent = Cm(0)
            run = p.add_run(title)
            set_run_font(run, size=12, bold=True, color=NAVY)
        else:
            p.paragraph_format.left_indent = Cm(0.75)
            run = p.add_run(title)
            set_run_font(run, size=11, color=SLATE)
    doc.add_page_break()


def convert():
    lines = MD.read_text(encoding="utf-8").splitlines()
    toc_items = collect_toc(lines)

    doc = Document()
    configure_styles(doc)
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(2.3)
    section.right_margin = Cm(2.3)
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2.2)

    header = section.header
    header.is_linked_to_previous = False
    hp = header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_paragraph_spacing(hp, before=0, after=2)
    add_bottom_border(hp, "C4A35A", "8")
    hr = hp.add_run("中国债券与股票资产比较研究")
    set_run_font(hr, size=9, color=SLATE)

    footer = section.footer
    footer.is_linked_to_previous = False
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_spacing(fp, before=4, after=0)
    fr = fp.add_run("大类资产配置投研范式  ·  2026年8月  ·  第 ")
    set_run_font(fr, size=9, color=SLATE)
    add_page_number_field(fp)
    fr2 = fp.add_run(" 页")
    set_run_font(fr2, size=9, color=SLATE)

    props = doc.core_properties
    props.title = "中国债券资产与股票资产比较研究"
    props.subject = "大类资产配置投研范式"
    props.author = "Asset Allocation Research Note"
    props.category = "研究报告"

    add_cover(doc)
    add_toc(doc, toc_items)

    i = 0
    started = False
    while i < len(lines):
        stripped = lines[i].strip()
        if not started:
            if stripped.startswith("## 摘要"):
                started = True
            else:
                i += 1
                continue

        if not stripped:
            i += 1
            continue

        if stripped == "---":
            i += 1
            continue

        img = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)", stripped)
        if img:
            add_picture(doc, img.group(2), caption=img.group(1) or None)
            i += 1
            continue

        if stripped.startswith("## "):
            add_heading(doc, stripped[3:], 1)
            i += 1
            continue

        if stripped.startswith("### "):
            add_heading(doc, stripped[4:], 2)
            i += 1
            continue

        if stripped.startswith("|") and i + 1 < len(lines) and is_table_separator(lines[i + 1].strip()):
            rows = [parse_table_row(stripped)]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(parse_table_row(lines[i].strip()))
                i += 1
            add_table(doc, rows)
            continue

        if stripped.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            set_paragraph_spacing(p, before=1, after=3, line=1.18)
            add_mixed_runs(p, stripped[2:], size=12)
            i += 1
            continue

        numbered = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if numbered:
            p = doc.add_paragraph(style="List Number")
            set_paragraph_spacing(p, before=1, after=3, line=1.18)
            add_mixed_runs(p, numbered.group(2), size=12)
            i += 1
            continue

        if stripped.startswith("\\[") or stripped.endswith("\\]"):
            buf = [stripped]
            if not stripped.endswith("\\]"):
                i += 1
                while i < len(lines) and not lines[i].strip().endswith("\\]"):
                    buf.append(lines[i].strip())
                    i += 1
                if i < len(lines):
                    buf.append(lines[i].strip())
            formula = pretty_math(" ".join(buf))
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            set_paragraph_spacing(p, before=8, after=8)
            shade_paragraph(p, "F4F1EC")
            run = p.add_run(formula)
            set_run_font(run, name="Cambria Math", size=13, italic=True, color=NAVY)
            i += 1
            continue

        if stripped.startswith("*") and stripped.endswith("*") and not stripped.startswith("**"):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            set_paragraph_spacing(p, before=10, after=6)
            run = p.add_run(stripped.strip("*"))
            set_run_font(run, size=10, italic=True, color=SLATE)
            i += 1
            continue

        p = doc.add_paragraph()
        set_paragraph_spacing(p, before=2, after=7, line=1.28, first_line=0.74)
        add_mixed_runs(p, stripped, size=12)
        i += 1

    doc.save(DOCX)
    print(f"wrote {DOCX} ({DOCX.stat().st_size} bytes)")


if __name__ == "__main__":
    convert()
