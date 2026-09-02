#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成《浙商银行2026-2030年分支机构发展规划》初稿及审阅意见。"""

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn, nsmap
from docx.shared import Cm, Pt, Emu, Twips
from docx.table import Table
from copy import deepcopy

OUT_DIR = "/workspace/浙商银行2026-2030年分支机构发展规划"


def set_run_font(run, east_asia, ascii_font=None, size_pt=16, bold=False, color=None):
    run.bold = bold
    run.font.size = Pt(size_pt)
    ascii_font = ascii_font or east_asia
    run.font.name = ascii_font
    r = run._element
    rPr = r.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:ascii"), ascii_font)
    rFonts.set(qn("w:hAnsi"), ascii_font)
    rFonts.set(qn("w:eastAsia"), east_asia)
    rFonts.set(qn("w:cs"), ascii_font)
    if color:
        run.font.color.rgb = color


def set_paragraph_format(
    p,
    first_line_chars=None,
    space_before=0,
    space_after=0,
    line_pt=28,
    align=WD_ALIGN_PARAGRAPH.JUSTIFY,
    outline=None,
):
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    pf.line_spacing = Pt(line_pt)
    p.alignment = align
    if first_line_chars:
        pPr = p._p.get_or_add_pPr()
        ind = pPr.find(qn("w:ind"))
        if ind is None:
            ind = OxmlElement("w:ind")
            pPr.append(ind)
        ind.set(qn("w:firstLineChars"), str(int(first_line_chars * 100)))
        # 三号字约16磅，2字符≈32磅≈640 twips
        ind.set(qn("w:firstLine"), str(int(first_line_chars * 320)))
    if outline is not None:
        p.paragraph_format.outline_level = outline


def add_text(p, text, east_asia, size_pt=16, bold=False, ascii_font="Times New Roman"):
    run = p.add_run(text)
    set_run_font(run, east_asia, ascii_font=ascii_font, size_pt=size_pt, bold=bold)
    return run


def shade_cell(cell, fill="D9E2F3"):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    shd.set(qn("w:val"), "clear")
    tcPr.append(shd)


def set_cell_border(cell):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "5B7C99")
        tcBorders.append(el)
    tcPr.append(tcBorders)


def set_cell_text(cell, text, east_asia="宋体", size_pt=10.5, bold=False, align=WD_ALIGN_PARAGRAPH.CENTER):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    pf = p.paragraph_format
    pf.space_before = Pt(2)
    pf.space_after = Pt(2)
    pf.line_spacing = 1.15
    run = p.add_run(text)
    set_run_font(run, east_asia, ascii_font="Times New Roman", size_pt=size_pt, bold=bold)
    set_cell_border(cell)
    # 垂直居中
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    vAlign = OxmlElement("w:vAlign")
    vAlign.set(qn("w:val"), "center")
    tcPr.append(vAlign)


def set_repeat_header(row):
    tr = row._tr
    trPr = tr.get_or_add_trPr()
    tblHeader = OxmlElement("w:tblHeader")
    trPr.append(tblHeader)


def prevent_row_split(row):
    tr = row._tr
    trPr = tr.get_or_add_trPr()
    cant = OxmlElement("w:cantSplit")
    trPr.append(cant)


def set_table_widths(table, widths_cm):
    table.autofit = False
    table.allow_autofit = False
    tbl = table._tbl
    tblPr = tbl.tblPr if tbl.tblPr is not None else OxmlElement("w:tblPr")
    tblW = tblPr.find(qn("w:tblW"))
    if tblW is None:
        tblW = OxmlElement("w:tblW")
        tblPr.append(tblW)
    total = int(sum(widths_cm) * 567)
    tblW.set(qn("w:w"), str(total))
    tblW.set(qn("w:type"), "dxa")
    grid = tbl.find(qn("w:tblGrid"))
    if grid is not None:
        for i, child in enumerate(list(grid)):
            grid.remove(child)
        for w in widths_cm:
            gridCol = OxmlElement("w:gridCol")
            gridCol.set(qn("w:w"), str(int(w * 567)))
            grid.append(gridCol)
    for row in table.rows:
        for idx, cell in enumerate(row.cells):
            if idx < len(widths_cm):
                cell.width = Cm(widths_cm[idx])
                tc = cell._tc
                tcPr = tc.get_or_add_tcPr()
                tcW = tcPr.find(qn("w:tcW"))
                if tcW is None:
                    tcW = OxmlElement("w:tcW")
                    tcPr.append(tcW)
                tcW.set(qn("w:w"), str(int(widths_cm[idx] * 567)))
                tcW.set(qn("w:type"), "dxa")


def add_caption(doc, text):
    p = doc.add_paragraph()
    set_paragraph_format(p, first_line_chars=0, space_before=6, space_after=4, line_pt=20, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_text(p, text, "黑体", size_pt=12, bold=True)


def add_note(doc, text):
    p = doc.add_paragraph()
    set_paragraph_format(p, first_line_chars=0, space_before=2, space_after=8, line_pt=18, align=WD_ALIGN_PARAGRAPH.LEFT)
    add_text(p, text, "仿宋", size_pt=10.5)


def setup_document():
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.8)
    section.bottom_margin = Cm(2.6)
    section.left_margin = Cm(2.8)
    section.right_margin = Cm(2.6)
    section.header_distance = Cm(1.5)
    section.footer_distance = Cm(1.5)

    # 页脚页码
    footer = section.footer
    footer.is_linked_to_previous = False
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_text(fp, "— ", "仿宋", size_pt=10.5)
    run = fp.add_run()
    fld1 = OxmlElement("w:fldChar")
    fld1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    instr.text = " PAGE "
    fld2 = OxmlElement("w:fldChar")
    fld2.set(qn("w:fldCharType"), "end")
    run._r.append(fld1)
    run._r.append(instr)
    run._r.append(fld2)
    set_run_font(run, "仿宋", ascii_font="Times New Roman", size_pt=10.5)
    add_text(fp, " —", "仿宋", size_pt=10.5)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(16)
    rPr = normal.element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:eastAsia"), "仿宋")
    return doc


def add_title(doc, text, size=22):
    p = doc.add_paragraph()
    set_paragraph_format(p, first_line_chars=0, space_before=12, space_after=12, line_pt=36, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_text(p, text, "黑体", size_pt=size, bold=True)


def add_h1(doc, text):
    p = doc.add_paragraph()
    set_paragraph_format(p, first_line_chars=0, space_before=12, space_after=6, line_pt=30, align=WD_ALIGN_PARAGRAPH.LEFT, outline=0)
    add_text(p, text, "黑体", size_pt=16, bold=True)


def add_h2(doc, text):
    p = doc.add_paragraph()
    set_paragraph_format(p, first_line_chars=0, space_before=8, space_after=4, line_pt=28, align=WD_ALIGN_PARAGRAPH.LEFT, outline=1)
    add_text(p, text, "黑体", size_pt=16, bold=True)


def add_h3(doc, text):
    p = doc.add_paragraph()
    set_paragraph_format(p, first_line_chars=0, space_before=6, space_after=2, line_pt=28, align=WD_ALIGN_PARAGRAPH.LEFT, outline=2)
    add_text(p, text, "楷体", size_pt=16, bold=True)


def add_body(doc, text, first_line=2):
    p = doc.add_paragraph()
    set_paragraph_format(p, first_line_chars=first_line, space_before=0, space_after=0, line_pt=28, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_text(p, text, "仿宋", size_pt=16)
    return p


def add_body_mixed(doc, parts, first_line=2):
    """parts: list of (text, bold)"""
    p = doc.add_paragraph()
    set_paragraph_format(p, first_line_chars=first_line, space_before=0, space_after=0, line_pt=28, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    for text, bold in parts:
        add_text(p, text, "仿宋", size_pt=16, bold=bold)
    return p


def add_sign(doc, text, align=WD_ALIGN_PARAGRAPH.RIGHT):
    p = doc.add_paragraph()
    set_paragraph_format(p, first_line_chars=0, space_before=6, space_after=0, line_pt=28, align=align)
    add_text(p, text, "仿宋", size_pt=16)
    return p


def fill_table(table, rows, header=True, col_align=None, widths=None):
    if widths:
        set_table_widths(table, widths)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r_idx, row_data in enumerate(rows):
        row = table.rows[r_idx]
        prevent_row_split(row)
        if r_idx == 0 and header:
            set_repeat_header(row)
        is_header = header and r_idx == 0
        is_total = (not is_header) and any(
            str(row_data[0]).endswith("合计") or str(row_data[0]) in ("全行合计", "省内合计", "省外合计")
            for _ in [0]
        )
        for c_idx, val in enumerate(row_data):
            align = WD_ALIGN_PARAGRAPH.CENTER
            if col_align and c_idx < len(col_align):
                align = col_align[c_idx]
            set_cell_text(
                row.cells[c_idx],
                str(val),
                east_asia="黑体" if is_header else "宋体",
                size_pt=9 if not is_header else 9,
                bold=is_header or is_total,
                align=align,
            )
            if is_header:
                shade_cell(row.cells[c_idx], "1F4E79")
                for p in row.cells[c_idx].paragraphs:
                    for run in p.runs:
                        from docx.shared import RGBColor
                        run.font.color.rgb = RGBColor(255, 255, 255)
            elif is_total:
                shade_cell(row.cells[c_idx], "D6E3F0")
            elif r_idx % 2 == 0:
                shade_cell(row.cells[c_idx], "F4F7FB")


def build_plan():
    doc = setup_document()

    add_title(doc, "浙商银行2026—2030年分支机构发展规划")

    add_body(
        doc,
        "为深入贯彻全行“五五”发展战略，统筹考虑总体规划目标、存量网点效能和监管准入政策，立足当前监管政策窗口，加快省内网点布局，进一步提升市场空间大、网均效能高的重点区域网点密度，稳步推进一级分行、二级分行设立和支行建设，兼顾其他区域分行布局需求，适度撤并低效网点，持续优化机构布局，制定本规划。",
    )
    add_body(
        doc,
        "2026年至2030年，全行规划净新增网点130家，其中省内净新增44家、省外净新增86家，到2030年末各级网点总数达到500家（不含小企业信贷中心、资金营运中心等分行级专营机构）。各分行辖内规划数量已经明确，作为本规划期内机构发展的控制数。区县层面具体布局仍有沟通空间，由分行结合当地市场资源和监管准入实际，在本规划确定的导向范围内提出方案，与总行沟通后确定。",
    )
    add_body(doc, "现将有关安排明确如下。")

    # 一
    add_h1(doc, "一、总体安排")
    add_body(
        doc,
        "本规划坚持“省内加快布局、重点区域加密、其他区域兼顾、低效网点优化”的总体原则。着力推进一级分行、二级分行规划落地，稳步推进支行建设；优先支持市场空间大、网均效能高、综合贡献突出的重点分行提升网点密度；对展业环境受限、网均效能持续偏低的分行，以存量提质为主，必要时撤并低效网点。",
    )
    add_body(
        doc,
        "规划期内机构安排为：新设一级分行4家、二级分行7家；省内新设支行44家（含在筹1家）；省外新设支行78家（含在筹14家），撤并低效支行3家。以上安排与全行2030年末网点总数500家的目标相衔接，各分行要按规划数量推进，不得擅自突破。",
    )

    # 二
    add_h1(doc, "二、一级分行、二级分行规划")
    add_h2(doc, "（一）新设一级分行4家")
    add_body(
        doc,
        "规划期内推进省会及重点区域一级分行建设，设立乌鲁木齐分行、海口分行、昆明分行、雄安分行等4家一级分行。相关分行（筹备组）要按照总行统一部署，抓紧推进选址、报批和开业准备。",
    )
    add_h2(doc, "（二）新设二级分行7家")
    add_body(
        doc,
        "规划期内设立泉州分行、赣州分行、菏泽分行、芜湖分行、榆林分行、马鞍山分行、宜宾分行等7家地市二级分行。管辖分行要切实履行筹备主体责任，做好监管沟通、人员配置和开业运营衔接。",
    )

    # 三
    add_h1(doc, "三、省内支行规划")
    add_body(
        doc,
        "规划期内省内新设支行44家（含在筹1家），到2030年末省内网点数量达到167家。重点支持杭州、宁波、绍兴等网均水平高、市场空间大的分行提升网点密度，同时安排温州、台州、嘉兴、金华、湖州等分行适度补点。具体安排如下。",
    )

    add_h2(doc, "（一）杭州分行")
    add_body(
        doc,
        "杭州作为浙江省会和总行大本营所在地，财富管理与总部经济资源集聚，网均规模居省内首位、辖内支行密度相对不足。规划新设支行18家，到2030年末网点数量达到48家，重点提升余杭、上城、拱墅、西湖、萧山等存款超5000亿元区域网点密度。",
    )

    add_h2(doc, "（二）宁波分行")
    add_body(
        doc,
        "宁波作为长三角重要中心城市和现代海洋城市，制造业基础扎实、外贸活跃，现有网点数量与当地市场容量和同业布局差距较大。规划新设支行10家，到2030年末网点数量达到30家，重点提升鄞州、海曙、北仑等存款超3000亿元区域网点密度。",
    )

    add_h2(doc, "（三）绍兴分行")
    add_body(
        doc,
        "绍兴县域经济发达、小微企业活跃，分行网均效益居省内前列。规划新设支行4家，到2030年末网点数量达到14家，重点提升越城、上虞等存款超3000亿元区域网点密度。",
    )

    add_h2(doc, "（四）省内其他分行")
    add_body(
        doc,
        "温州、台州、嘉兴、金华、湖州等分行规划新设支行合计12家（含在筹1家），到2030年末网点数量分别达到15家、13家、10家、14家、8家。衢州、丽水、舟山分行以存量网点提质为主，到2030年末网点数量分别保持5家、6家、4家。",
    )
    add_body(
        doc,
        "上述区县（市）为布局导向，不作为选址的最终清单。各分行要在规划数量内，结合街区经济、客群资源和监管准入条件，提出区县层面布局方案，与总行沟通确定。",
    )

    # 四
    add_h1(doc, "四、省外支行规划")
    add_body(
        doc,
        "规划期内省外新设支行78家、撤并3家，净新增75家；加上新设一级分行4家、二级分行7家，省外净新增网点86家，到2030年末省外网点数量达到333家。",
    )

    add_h2(doc, "（一）重点分行")
    add_body(
        doc,
        "对上海、北京、南京、苏州、广州、深圳等网均效能高、市场空间大的分行加大布局力度，规划新设支行52家，推动覆盖辖内GDP、存款规模超千亿元区（县），并提升存款余额3000亿元以上区（县）的网点密度。",
    )

    add_h3(doc, "1.上海分行")
    add_body(
        doc,
        "上海作为全国经济、金融、贸易、航运和科创中心，网均效能引领全行，市辖区尚未全覆盖。规划新设支行10家，到2030年末网点数量达到27家，加快填补虹口、宝山、青浦等空白区域，提升浦东、黄浦、静安、徐汇、杨浦、闵行等存款超5000亿元区域网点密度。",
    )

    add_h3(doc, "2.南京分行")
    add_body(
        doc,
        "江苏经济总量领先、发达地市和百强县众多，南京分行营收贡献突出，部分强市、强县覆盖不足。规划新设支行11家，到2030年末网点数量达到46家，重点在南京、无锡、镇江、扬州等城市存款超2000亿元的同城强区、强县增设网点。",
    )

    add_h3(doc, "3.苏州分行")
    add_body(
        doc,
        "苏州制造业规模居全国地级市首位，辖内重点市辖区和头部强县目前均仅有1个网点。规划新设支行6家，到2030年末网点数量达到17家，重点在吴江、吴中、昆山、常熟、张家港等存款超5000亿元区域增设网点。",
    )

    add_h3(doc, "4.北京分行")
    add_body(
        doc,
        "北京集聚央国企总部、金融机构总部和高价值客群，分行作为北方中心网均规模优势明显。规划新设支行6家，到2030年末网点数量达到30家，重点提升东城、西城、海淀等存款规模超万亿元市辖区网点密度。",
    )

    add_h3(doc, "5.广州分行")
    add_body(
        doc,
        "广州作为国家中心城市，市辖区尚未全覆盖或覆盖不足。规划新设支行10家，到2030年末网点数量达到29家，加快覆盖白云、南沙等GDP超2000亿元空白区域，重点提升黄埔、天河、越秀等存款万亿元级区域网点密度。",
    )

    add_h3(doc, "6.深圳分行")
    add_body(
        doc,
        "深圳科技创新与高净值客群资源全国领先，半数以上市辖区存款超万亿元。规划新设支行9家，到2030年末网点数量达到25家，重点提升南山、福田、宝安等存款超万亿元市辖区网点数量。",
    )

    add_h2(doc, "（二）其他分行")
    add_body(
        doc,
        "济南、福州、合肥、成都、青岛、武汉、太原等分行规划新设支行合计12家，用于提升辖内重点区域覆盖。各分行要在总行已明确的规划数量内，围绕GDP、存款规模较大的区（县）提出布局方案。",
    )
    add_body(
        doc,
        "西安、南昌、合肥、成都、福州、济南等分行要同步落实本规划确定的二级分行设立任务，做好与支行布局的统筹。",
    )

    add_h2(doc, "（三）在筹支行")
    add_body(
        doc,
        "已在筹支行14家，分布在上海、南京、青岛、广州、长沙、济南、武汉、合肥、南宁、郑州、呼和浩特等分行辖内。相关分行要加快推进开业，确保按期纳入规划期末网点总量。",
    )

    add_h2(doc, "（四）低效网点撤并")
    add_body(
        doc,
        "规划期内撤并贵阳、兰州、沈阳分行辖内低效支行各1家，共3家。上述分行要对照网点效能，研究提出撤并对象和人员、业务安置方案，报总行审定后实施。确因展业环境变化需要扩大撤并范围的，由分行报告，总行统筹研究。",
    )
    add_body(
        doc,
        "未列入新增规划的省外分行，以存量网点提质和结构优化为主，原则上不新增网点。",
    )
    add_body(
        doc,
        "省外重点分行所列区县（市）为布局导向。具体到区县的选址由分行结合市场资源和监管准入条件，在规划数量内与总行沟通确定。",
    )

    # 五 工作要求 —— 对第七部分的取舍已融入
    add_h1(doc, "五、工作要求")
    add_body(
        doc,
        "规划落地既要看新增，也要看质效。各分行要在稳步推进网点建设、持续优化网点布局的同时，主动对接监管、做强重点分行、深挖存量潜力，严格控制机构和运营成本。",
    )

    add_h2(doc, "（一）主动对接监管，抓好规划落地")
    add_body(
        doc,
        "当前监管对网点准入总体保持从紧管控。各分行要把监管沟通作为规划落地的前置工作，加强与属地监管的常态化汇报，前瞻把握政策导向，用好准入窗口。浙江、上海、江苏、广东、北京等重点区域分行要主要负责人亲自过问，明确专人跟踪报批，确保规划项目成熟一个、申报一个、落地一个。",
    )

    add_h2(doc, "（二）发挥大行挑大梁作用")
    add_body(
        doc,
        "上海、北京、南京、苏州、广州、深圳、杭州、宁波、绍兴等分行市场空间大、网均效能高、综合贡献突出，要切实承担“大行挑大梁”责任，按规划加快网点布局落地，持续提升网均效能和综合贡献，发挥对全行发展的带动作用。省外重点分行要充分挖掘当地市场潜力，做强做优，与浙江大本营形成协同发展。其他分行要立足自身定位，把规划内项目做实、把存量网点做优，不简单比规模、比数量。",
    )

    add_h2(doc, "（三）深挖存量潜力，提升网点质效")
    add_body(
        doc,
        "新增布局与存量提质并重。各分行要加强营销队伍建设，优化人员结构，推动网均、人均指标稳步改善。对存款、营收持续低于全行平均水平的网点，要制定限期提升方案；对长期低效、扭亏无望的网点，主动研究迁址或撤并，腾挪机构资源。分行本级营销团队要提升对公、零售协同能力，防止“行强点弱、点多效低”。",
    )

    add_h2(doc, "（四）合理配置人员，严控建设成本")
    add_body(
        doc,
        "新设网点人员配置要精干高效，优先通过大学生培养、分行内部人员结构调整解决中后台需求，开业初期营销团队可按总行人力资源政策引进急需人才。新设和装修改造网点要推进小型化、智能化，合理控制租赁面积，提高智能机具使用率，实行综合柜员制，降低场所和运营成本。具体编制、薪酬和运营模式按总行人力资源、运营管理、财务管理等部门有关制度执行。",
    )

    add_h2(doc, "（五）加强组织实施，实行动态管理")
    add_body(
        doc,
        "各分行要按照本规划确定的数量和布局导向，抓紧研究提出辖内区县布局方案，明确项目排序、选址区域和监管沟通安排，报总行发展规划部。规划数量原则上不得突破；区县层面在导向范围内可与总行沟通调整。因监管政策变化、城市规划调整或市场环境发生重大变化确需优化的，由分行书面报告，总行在全行规划总量内统筹调剂。总行对规划执行情况开展跟踪评估，作为机构管理的重要依据。",
    )
    add_body(
        doc,
        "本规划由总行发展规划部负责解释。",
    )

    p = doc.add_paragraph()
    set_paragraph_format(p, first_line_chars=0, space_before=18, space_after=0, line_pt=28, align=WD_ALIGN_PARAGRAPH.LEFT)
    add_text(p, "附件：2026—2030年网点规划汇总表", "仿宋", size_pt=16)

    add_sign(doc, "发展规划部")
    add_sign(doc, "2026年6月")

    # 分页附件
    doc.add_page_break()
    add_title(doc, "附件", size=16)
    add_title(doc, "2026—2030年网点规划汇总表", size=18)

    add_caption(doc, "表1  一级分行、二级分行规划表")
    rows1 = [
        ["序号", "机构类型", "机构名称", "规划安排", "管辖关系"],
        ["1", "一级分行", "乌鲁木齐分行", "新设", "总行直接管理"],
        ["2", "一级分行", "海口分行", "新设", "总行直接管理"],
        ["3", "一级分行", "昆明分行", "新设", "总行直接管理"],
        ["4", "一级分行", "雄安分行", "新设", "总行直接管理"],
        ["5", "二级分行", "泉州分行", "新设", "福州分行管辖"],
        ["6", "二级分行", "赣州分行", "新设", "南昌分行管辖"],
        ["7", "二级分行", "菏泽分行", "新设", "济南分行管辖"],
        ["8", "二级分行", "芜湖分行", "新设", "合肥分行管辖"],
        ["9", "二级分行", "榆林分行", "新设", "西安分行管辖"],
        ["10", "二级分行", "马鞍山分行", "新设", "合肥分行管辖"],
        ["11", "二级分行", "宜宾分行", "新设", "成都分行管辖"],
        ["合计", "—", "一级分行4家、二级分行7家", "新设11家", "—"],
    ]
    t1 = doc.add_table(rows=len(rows1), cols=5)
    fill_table(
        t1,
        rows1,
        col_align=[WD_ALIGN_PARAGRAPH.CENTER] * 5,
        widths=[1.4, 2.4, 3.4, 2.4, 5.4],
    )
    add_note(doc, "注：二级分行计入管辖一级分行2030年末网点总量。")

    add_caption(doc, "表2  省内各分行网点规划表")
    rows2 = [
        ["分行名称", "规划新设支行（家）", "2030年末网点（家）", "布局导向"],
        ["杭州分行", "18", "48", "余杭、上城、拱墅、西湖、萧山等存款超5000亿元区域"],
        ["宁波分行", "10", "30", "鄞州、海曙、北仑等存款超3000亿元区域"],
        ["绍兴分行", "4", "14", "越城、上虞等存款超3000亿元区域"],
        ["温州分行", "12家合计\n（含在筹1家）", "15", "由分行结合实际与总行沟通确定"],
        ["台州分行", "12家合计\n（含在筹1家）", "13", "由分行结合实际与总行沟通确定"],
        ["嘉兴分行", "12家合计\n（含在筹1家）", "10", "由分行结合实际与总行沟通确定"],
        ["金华分行", "12家合计\n（含在筹1家）", "14", "由分行结合实际与总行沟通确定"],
        ["湖州分行", "12家合计\n（含在筹1家）", "8", "由分行结合实际与总行沟通确定"],
        ["衢州分行", "—", "5", "以存量提质为主，原则上不新增"],
        ["丽水分行", "—", "6", "以存量提质为主，原则上不新增"],
        ["舟山分行", "—", "4", "以存量提质为主，原则上不新增"],
        ["省内合计", "44", "167", "区县布局为导向，具体选址与总行沟通确定"],
    ]
    t2 = doc.add_table(rows=len(rows2), cols=4)
    fill_table(
        t2,
        rows2,
        col_align=[
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.LEFT,
        ],
        widths=[2.8, 3.2, 3.2, 5.8],
    )
    # 温州至湖州“规划新设”列合并为合计12家
    t2.cell(4, 1).merge(t2.cell(8, 1))
    set_cell_text(t2.cell(4, 1), "合计12家\n（含在筹1家）", east_asia="宋体", size_pt=9, bold=True)
    add_note(
        doc,
        "注：1.温州、台州、嘉兴、金华、湖州等5家分行规划新设支行合计12家（含在筹1家），各分行具体数量按总行已明确安排执行。2.布局导向不作为区县选址最终清单。",
    )

    add_caption(doc, "表3  省外各分行网点规划表")
    rows3 = [
        ["分行名称", "规划新设支行（家）", "2030年末网点（家）", "布局导向及备注"],
        ["上海分行", "10", "27", "填补虹口、宝山、青浦等空白；提升浦东、黄浦、静安、徐汇、杨浦、闵行等；含在筹"],
        ["南京分行", "11", "46", "南京、无锡、镇江、扬州等城市存款超2000亿元同城强区、强县；含在筹"],
        ["苏州分行", "6", "17", "吴江、吴中、昆山、常熟、张家港等存款超5000亿元区域"],
        ["北京分行", "6", "30", "东城、西城、海淀等存款超万亿元市辖区"],
        ["广州分行", "10", "29", "覆盖白云、南沙；提升黄埔、天河、越秀等；含在筹"],
        ["深圳分行", "9", "25", "南山、福田、宝安等存款超万亿元市辖区"],
        ["重点分行小计", "52", "174", "上述6家重点分行"],
        ["济南分行", "12家合计", "21", "适当提升辖内支行布局；含在筹；新设菏泽二级分行"],
        ["福州分行", "12家合计", "6", "适当提升辖内支行布局；新设泉州二级分行"],
        ["合肥分行", "12家合计", "11", "适当提升辖内支行布局；含在筹；新设芜湖、马鞍山二级分行"],
        ["成都分行", "12家合计", "16", "适当提升辖内支行布局；新设宜宾二级分行"],
        ["青岛分行", "12家合计", "7", "适当提升辖内支行布局；含在筹"],
        ["武汉分行", "12家合计", "9", "适当提升辖内支行布局；含在筹"],
        ["太原分行", "12家合计", "3", "适当提升辖内支行布局"],
        ["其他可批分行小计", "12", "73", "上述7家分行新设支行合计12家"],
        ["长沙分行", "在筹", "8", "推进在筹支行开业"],
        ["南宁分行", "在筹", "2", "推进在筹支行开业"],
        ["郑州分行", "在筹", "10", "推进在筹支行开业"],
        ["呼和浩特分行", "在筹", "4", "推进在筹支行开业"],
        ["西安分行", "—", "17", "新设榆林二级分行；支行以存量提质为主"],
        ["重庆分行", "—", "10", "以存量提质为主，原则上不新增支行"],
        ["天津分行", "—", "13", "以存量提质为主，原则上不新增支行"],
        ["南昌分行", "—", "5", "新设赣州二级分行；支行以存量提质为主"],
        ["沈阳分行", "撤并1家", "5", "撤并辖内低效支行1家"],
        ["兰州分行", "撤并1家", "7", "撤并辖内低效支行1家"],
        ["贵阳分行", "撤并1家", "1", "撤并辖内低效支行1家"],
        ["乌鲁木齐分行", "新设一级分行", "1", "规划新设一级分行"],
        ["海口分行", "新设一级分行", "1", "规划新设一级分行"],
        ["昆明分行", "新设一级分行", "1", "规划新设一级分行"],
        ["雄安分行", "新设一级分行", "1", "规划新设一级分行"],
        ["省外合计", "新设支行78、撤并3；一级4、二级7", "333", "净新增86家"],
        ["全行合计", "净新增130", "500", "不含2家分行级专营机构"],
    ]
    t3 = doc.add_table(rows=len(rows3), cols=4)
    fill_table(
        t3,
        rows3,
        col_align=[
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.LEFT,
        ],
        widths=[2.8, 3.6, 2.8, 5.8],
    )
    t3.cell(8, 1).merge(t3.cell(14, 1))
    set_cell_text(t3.cell(8, 1), "合计12家", east_asia="宋体", size_pt=9, bold=True)
    add_note(
        doc,
        "注：1.省外新设支行78家=重点分行52家+其他可批分行12家+在筹14家；撤并3家；净新增75家。2.济南、福州、合肥、成都、青岛、武汉、太原等7家分行规划新设支行合计12家，各分行具体数量按总行已明确安排执行。3.在筹14家分布在上海、南京、青岛、广州、长沙、济南、武汉、合肥、南宁、郑州、呼和浩特等分行，表中“含在筹”表示该行规划新设与在筹一并纳入2030年末总量。4.2030年末网点数量含一级分行、二级分行。5.布局导向不作为区县选址最终清单。",
    )

    add_caption(doc, "表4  规划总量平衡表")
    rows4 = [
        ["项目", "省内", "省外", "全行"],
        ["2025年末网点数", "123", "247", "370"],
        ["新设一级分行", "—", "4", "4"],
        ["新设二级分行", "—", "7", "7"],
        ["新设支行（含在筹）", "44", "78", "122"],
        ["其中：在筹支行", "1", "14", "15"],
        ["撤并支行", "—", "3", "3"],
        ["净新增", "44", "86", "130"],
        ["2030年末网点数", "167", "333", "500"],
    ]
    t4 = doc.add_table(rows=len(rows4), cols=4)
    fill_table(
        t4,
        rows4,
        col_align=[WD_ALIGN_PARAGRAPH.CENTER] * 4,
        widths=[4.5, 3.5, 3.5, 3.5],
    )
    add_note(doc, "注：2025年末、2030年末网点数均不含小企业信贷中心、资金营运中心等2家分行级专营机构。")

    path = f"{OUT_DIR}/浙商银行2026-2030年分支机构发展规划.docx"
    doc.save(path)
    return path


def build_review():
    doc = setup_document()
    add_title(doc, "关于《浙商银行2026—2030年分支机构发展规划》初稿的审阅意见", size=18)

    p = doc.add_paragraph()
    set_paragraph_format(p, first_line_chars=0, space_before=0, space_after=12, line_pt=24, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_text(p, "（站在总行发展规划部领导角度）", "楷体", size_pt=14)

    add_body(
        doc,
        "初稿已按面向分行发文的定位作了改写，帽段、语气和结构总体可用，比原建议报告更像一份规划。下面按“能不能下发、下发后会不会被动、数字能不能站住”来看，建议在正式会签和提交行领导前，再改以下几个方面。",
    )

    add_h1(doc, "一、总体判断")
    add_body(
        doc,
        "这份稿子的方向是对的：决策材料里的同业分析、效能对比、营收和人员测算没有放进正文，重点分行长段落压成了“一句依据+数量+区域”，区县布局留了沟通口子，“预计”“拟”等请示用语基本去掉了。作为发展规划部内部初稿，可以进入下一轮修改；作为马上印发分行的文件，还不够硬、不够干净，主要短板是“名实、数量分解、发文边界、分年安排、会签事项”五块。",
    )

    add_h1(doc, "二、建议修改的具体方面")

    add_h2(doc, "1.先定发文形式，再定正文写法")
    add_body(
        doc,
        "现在的稿子既像规划正文，又像直接发给分行的通知，落款是“发展规划部”，但没有发文字号、主送分行、抄送部门和施行说明。建议明确两种选一：一是以总行名义印发通知，规划作附件，通知里写“请认真贯彻执行”；二是规划经行党委（或行长办公会）审议后，由办公室正式发文。不宜以部门落款直接下发涉及一级分行设立、网点撤并的五年规划。对应修改：补一页印发通知（主送各分行，抄送董事会办公室、人力资源部、财务管理部、运营管理部、风险管理部、法律合规部等），规划正文去掉部门落款，或改为“本规划自印发之日起施行”。",
    )

    add_h2(doc, "2.标题与内容要匹配，避免“发展规划”做成“设点清单”")
    add_body(
        doc,
        "文件名叫《分支机构发展规划》，正文几乎全是设多少家、往哪设，对机构功能定位、差异化权限、建设标准和与业务规划的衔接着墨不够。分行拿到后只会盯数量，不会理解总行要什么样的网点。建议在“总体安排”中增加一小节“机构定位”，用很短的几句话明确：一级分行重区域辐射，二级分行重城市覆盖，综合型支行是主体，新设网点以综合型支行为主；省内加密与省外重点区域补点的目的，是服务“五五”存款、客户和营收目标，而不是铺摊子。不写测算表，但要点明规划服从全行“五五”目标。",
    )

    add_h2(doc, "3.帽段还要再压一遍，决策痕迹去干净")
    add_body(
        doc,
        "目前帽段两段可以保留，但“立足当前监管政策窗口”偏内部判断，下发后容易被理解成“窗口期很快关闭、必须抢批”，部分分行会据此倒逼总行。建议改为“结合监管准入政策，积极稳妥推进机构建设”。第二段“各分行辖内规划数量已经明确”这句必须留，这是压住分行争盘子的关键；但后面“仍有沟通空间”要限定范围，建议改为“规划数量不得突破，区县选址在导向范围内可与总行商议，不就数量重新开口”。否则重点分行会拿着“沟通空间”回头要增加家数。",
    )

    add_h2(doc, "4.省内12家、省外12家必须分解到分行，否则不能发")
    add_body(
        doc,
        "这是初稿最大的硬伤。原文写“各分行辖内规划数量总行已经确定”，但建议报告对温州、台州、嘉兴、金华、湖州只给了合计12家，对济南、福州、合肥、成都、青岛、武汉、太原也只给了合计12家；在筹14家只写了涉及分行，没有各行家数。附件表2、表3只能写“12家合计”，发下去这12家分行第一件事就是来问“到底几家”。建议发文前由部门把分解数补进附件，正文改为“各行数量见附件”，不要在正文里长期留着“合计”。若个别分行数量还在与监管或分行沟通，附件可单列“待确认”并注明时限，不宜用模糊写法覆盖12家。",
    )

    add_h2(doc, "5.区县名单与“尚未完全确定”还存在张力，要改成导向表述")
    add_body(
        doc,
        "重点分行段落已经缩短，这点是好的。但上海列了9个区、杭州列了5个区、苏州列了5个区（市），分行会默认“就是这些地方、每个都要有”。建议统一改成“重点考虑……等区域”，并在每类分行后只保留一处总述：“名单为布局导向，不分解到具体街道和项目，选址由分行论证后报总行”。苏州“辖内重点市辖区和头部强县目前均仅有1个网点”这类内部判断，下发后等于把家底告诉分行，可删，只保留布局方向。南京把无锡、镇江、扬州写进南京分行规划，要确认是异地支行还是二级分行管辖关系，避免与机构管理权限打架。",
    )

    add_h2(doc, "6.一级、二级分行新设要加“视监管审批推进”，不宜写成已经定局")
    add_body(
        doc,
        "乌鲁木齐、海口、昆明、雄安和7家二级分行都还没有批。规划可以对内明确意向，对外（对分行）应写成“规划设立、按监管审批进度推进”，不要让管辖分行按已获批来配人、租房、对监管表态。建议增加一句：一级分行、二级分行项目由总行统筹报批，未经批准不得对外宣传、不得提前装修开业。雄安分行的机构层级和监管口径还要再核一次，避免与现有北京分行、雄安相关机构安排冲突。",
    )

    add_h2(doc, "7.撤并三家点名全系统印发，建议改为“一对一”+附件内部掌握")
    add_body(
        doc,
        "贵阳、兰州、沈阳各撤并1家，作为规划内部安排可以，但写进发给全部分行的文件，等于系统内通报这三家分行。建议正文只写原则：“对展业环境受限、网均效能持续偏低的网点，规划期内实施撤并优化，具体名单由总行另行通知。”三家分行的名单放部门掌握或只发这三家。若行领导要求必须写进规划，建议加上“以总行核定名单为准，分行先报方案”，并明确业务、人员、客户安置责任，避免只写撤并数量、不写后续。",
    )

    add_h2(doc, "8.“大行挑大梁”可以保留，但不要写成两类分行")
    add_body(
        doc,
        "第七部分里这一条应当下发，初稿保留是对的。需要改三处：一是九家分行点名后，紧接着写对其他分行的要求，初稿已有，可再明确“不因此减少对其他分行的支持政策，但资源配置与贡献匹配”。二是不要出现“市场潜力远超浙江省内”“反哺浙江大本营”等原报告表述，初稿已改成“协同发展”，这句可保留，不要再加码。三是“大行”要有可检验的要求，不能只喊口号，建议补“规划项目落地率、网均存款（或营收）保持全行前列、新设网点开业后达标时限”等几条硬要求，否则重点分行只记得自己多了几十个指标，不记得要挑梁。",
    )

    add_h2(doc, "9.第七部分其他内容：监管沟通应留，人员编制和费用管控要收口")
    add_body(
        doc,
        "对原报告第七部分的取舍，同意初稿的处理，再收一收：第一，“加大监管沟通”适合下发，是分行能做、也必须做的事，保留为工作要求第一条。第二，“存量挖潜”方向对，原报告60%、40%、53%等数据不宜原文下发，初稿改为定性要求是对的；但全是定性又会变软，建议改成“各分行要对标全行网均、人均，列出后三分之一网点清单，每年报告提升情况”，数字由总行掌握、任务由分行认领。第三，“人员编制”三条来源可以保留为原则，但必须加“按总行人力资源政策执行”，发展规划部文件不规定进人指标。第四，“严控费用”中，小型化、智能机具、综合柜员制可以写；原报告“四级管理机制”“控制行员等级”不要写进本规划，那是组织架构和薪酬事项，应会签后由人力资源部、党委组织部另发。初稿已删这两句，定稿时不要加回来。",
    )

    add_h2(doc, "10.缺少分年安排，五年一本账分行无法执行")
    add_body(
        doc,
        "现在只有2026—2030年总数。监管一年批1—2家，分行需要知道先做哪几家。建议附件增加“分年实施安排（原则数）”，哪怕按“前期重点报批在筹和成熟项目、中期推进重点区域、后期收口”三阶段，也比只有一个期末数好。不要把内部“乐观预计每年1—2家”写进对分行文件，但总行自己要有一张分年表，作为与监管沟通和年度机构计划的依据。",
    )

    add_h2(doc, "11.口径、平衡关系和附件还要再核")
    add_body(
        doc,
        "需要逐项核对后再发：一是2025年末370家是否含社区、小微，杭州、绍兴辖内8家小微支行升格算不算规划占用指标，正文应有一句。二是省外2030年末333家是否已含4家一级分行和7家二级分行，附件表3把二级分行计入管辖行总量，要与机构统计口径一致。三是上海、南京、广州等既有“规划新设”又有“在筹”，2030年末27家、46家、29家是含在筹还是不含，必须在注里写死，否则会重复计算。四是原建议报告附件1测算表不要随本规划下发，营收、净息差情景属于对行领导的测算，发给分行没有好处。五是原件中的“网点规划汇总表”未随Word稿提供电子表，初稿是按第四部分重编的，正式发文前应用部门台账把每家分行2025年末数、在筹数、新设数、撤并数、2030年末数五列对齐，能横加竖加。六是附件表1中二级分行管辖关系（泉州归福州、赣州归南昌、菏泽归济南、芜湖和马鞍山归合肥、榆林归西安、宜宾归成都）系按行政区划推定，原文未写，发文前须用机构管理台账核对，重点确认菏泽是归济南还是青岛。",
    )

    add_h2(doc, "12.要补会签和与年度计划的接口")
    add_body(
        doc,
        "这份规划动到机构、编制、费用、监管报批，不能发展规划部一家定稿。建议会签人力资源部、财务管理部、运营管理部、法律合规部（机构准入），重点区域规划还应征求相关分行意见后再报。文中应写明：年度机构设置计划以本规划为上限，由发展规划部商相关部门列入年度计划后实施；未纳入年度计划的，即使在规划数以内，也不得自行申报。这样规划才不会变成分行直接向监管报批的“尚方宝剑”。",
    )

    add_h2(doc, "13.几处文字和口径再打磨")
    add_body(
        doc,
        "建议一并改掉：一是“不得擅自突破”后面要加“不得在规划外向监管承诺设点”。二是“主要负责人亲自过问”可用于浙、沪、苏、粤、京，但不要写成问责条款，发展规划部文件管不到干部管理。三是“防止行强点弱、点多效低”口语可以，正式文改为“避免分行本级强、网点弱，机构增加而效能不增”。四是“本规划由总行发展规划部负责解释”可保留，但如以总行名义发文，解释权写“由发展规划部会同有关部门解释”更稳。五是日期“2026年6月”待审议通过后落正式发文日，不要沿用建议报告的6月7日，以免版本混乱。",
    )

    add_h1(doc, "三、对原报告第七部分的取舍结论")

    rows = [
        ["原报告条目", "是否纳入对分行规划", "处理意见"],
        ["（一）加大监管沟通力度", "纳入", "改为工作要求，语气由建议改为任务；重点区域分行点名可保留。"],
        ["（二）推动大行挑大梁", "纳入", "按领导要求保留；去掉“反哺浙江”等内部建议口径，补可检验要求。"],
        ["（三）大力推进存量挖潜", "纳入方向，不纳数据", "60%、40%、53%等诊断数据留在给行领导的材料里；对分行改成清单管理和限期提升。"],
        ["（四）优化管控人员编制", "原则纳入", "只写配置原则和执行总行人力政策；不写进人规模、不写行员等级。"],
        ["（五）严控网点费用支出", "部分纳入", "保留小型化、智能化、综合柜员制；删除四级管理和职级压降，改由相关部门发文。"],
    ]
    t = doc.add_table(rows=len(rows), cols=3)
    fill_table(
        t,
        rows,
        col_align=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT],
        widths=[4.2, 3.6, 7.2],
    )

    add_h1(doc, "四、建议的改稿顺序")
    add_body(
        doc,
        "第一，补齐省内12家、省外12家和在筹14家的分行分解数，这是发文前提。第二，核对准入口径、在筹是否重复计算、二级分行统计归属。第三，加印发通知、会签部门和分年安排（内部掌握即可）。第四，把撤并名单和区县清单的效力写清楚。第五，再送行领导，避免用建议报告的汇报语气发规划。按这个顺序改完，这份规划才能既对分行有约束，又不把内部决策过程暴露出去。",
    )

    add_sign(doc, "（审阅意见，供修改初稿使用）")

    path = f"{OUT_DIR}/发展规划初稿审阅意见.docx"
    doc.save(path)
    return path


if __name__ == "__main__":
    p1 = build_plan()
    p2 = build_review()
    print(p1)
    print(p2)
