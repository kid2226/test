from pathlib import Path
from datetime import date
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from docx.shared import Cm, Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
CHARTS = OUT / "charts"
OUT.mkdir(exist_ok=True)
CHARTS.mkdir(exist_ok=True)

NAVY = "17365D"
BLUE = "2F75B5"
TEAL = "2A7F7F"
LIGHT_BLUE = "DCEAF7"
LIGHT_GRAY = "F2F4F7"
MID_GRAY = "667085"
DARK = "1D2939"
RED = "B54747"
GREEN = "2E7D5B"
GOLD = "B7791F"


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=90, start=100, bottom=90, end=100):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for m, v in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{m}"))
        if node is None:
            node = OxmlElement(f"w:{m}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(v))
        node.set(qn("w:type"), "dxa")


def set_repeat_table_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_keep_with_next(paragraph, value=True):
    p_pr = paragraph._p.get_or_add_pPr()
    keep = p_pr.find(qn("w:keepNext"))
    if keep is None:
        keep = OxmlElement("w:keepNext")
        p_pr.append(keep)
    keep.set(qn("w:val"), "1" if value else "0")


def set_table_borders(table, color="D0D5DD", size="4"):
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = borders.find(qn(f"w:{edge}"))
        if tag is None:
            tag = OxmlElement(f"w:{edge}")
            borders.append(tag)
        tag.set(qn("w:val"), "single")
        tag.set(qn("w:sz"), size)
        tag.set(qn("w:color"), color)


def add_field(paragraph, instruction):
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instruction
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instr, separate, text, end])


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    paragraph.add_run("第 ")
    add_field(paragraph, "PAGE")
    paragraph.add_run(" 页")


def setup_styles(doc):
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Noto Sans CJK SC"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Noto Sans CJK SC")
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor.from_string(DARK)
    normal.paragraph_format.line_spacing = 1.35
    normal.paragraph_format.space_after = Pt(6)

    for style_name, size, color, before, after in [
        ("Title", 30, NAVY, 0, 12),
        ("Subtitle", 13, MID_GRAY, 0, 8),
        ("Heading 1", 20, NAVY, 18, 8),
        ("Heading 2", 15, BLUE, 14, 6),
        ("Heading 3", 12, TEAL, 10, 4),
    ]:
        st = styles[style_name]
        st.font.name = "Noto Sans CJK SC"
        st._element.rPr.rFonts.set(qn("w:eastAsia"), "Noto Sans CJK SC")
        st.font.size = Pt(size)
        st.font.color.rgb = RGBColor.from_string(color)
        st.font.bold = style_name != "Subtitle"
        st.paragraph_format.space_before = Pt(before)
        st.paragraph_format.space_after = Pt(after)
        st.paragraph_format.keep_with_next = True

    if "Caption Source" not in styles:
        st = styles.add_style("Caption Source", WD_STYLE_TYPE.PARAGRAPH)
        st.font.name = "Noto Sans CJK SC"
        st._element.rPr.rFonts.set(qn("w:eastAsia"), "Noto Sans CJK SC")
        st.font.size = Pt(8)
        st.font.color.rgb = RGBColor.from_string(MID_GRAY)
        st.paragraph_format.space_after = Pt(8)

    if "Key Finding" not in styles:
        st = styles.add_style("Key Finding", WD_STYLE_TYPE.PARAGRAPH)
        st.font.name = "Noto Sans CJK SC"
        st._element.rPr.rFonts.set(qn("w:eastAsia"), "Noto Sans CJK SC")
        st.font.size = Pt(11)
        st.font.bold = True
        st.font.color.rgb = RGBColor.from_string(NAVY)
        st.paragraph_format.space_before = Pt(6)
        st.paragraph_format.space_after = Pt(6)
        st.paragraph_format.left_indent = Cm(0.45)


def configure_page(section):
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.15)
    section.bottom_margin = Cm(1.9)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.0)
    section.header_distance = Cm(0.8)
    section.footer_distance = Cm(0.8)


def add_header_footer(section):
    hp = section.header.paragraphs[0]
    hp.text = "中国房地产市场发展研究｜2026—2030"
    hp.style = "Caption Source"
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    line = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "4")
    bottom.set(qn("w:color"), "D0D5DD")
    line.append(bottom)
    hp._p.get_or_add_pPr().append(line)
    fp = section.footer.paragraphs[0]
    fp.style = "Caption Source"
    add_page_number(fp)


def add_paragraph(doc, text="", style=None, bold_prefix=None):
    p = doc.add_paragraph(style=style)
    if bold_prefix and text.startswith(bold_prefix):
        p.add_run(bold_prefix).bold = True
        p.add_run(text[len(bold_prefix):])
    else:
        p.add_run(text)
    return p


def add_bullets(doc, items, level=0):
    for item in items:
        p = doc.add_paragraph(style="List Bullet" if level == 0 else "List Bullet 2")
        p.paragraph_format.space_after = Pt(3)
        if isinstance(item, tuple):
            r = p.add_run(item[0])
            r.bold = True
            p.add_run(item[1])
        else:
            p.add_run(item)


def add_numbered(doc, items):
    for item in items:
        p = doc.add_paragraph(style="List Number")
        p.paragraph_format.space_after = Pt(4)
        if isinstance(item, tuple):
            p.add_run(item[0]).bold = True
            p.add_run(item[1])
        else:
            p.add_run(item)


def add_callout(doc, title, text, color=LIGHT_BLUE):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table, color=color, size="0")
    cell = table.cell(0, 0)
    set_cell_shading(cell, color)
    set_cell_margins(cell, top=140, bottom=140, start=180, end=180)
    p = cell.paragraphs[0]
    p.style = "Key Finding"
    p.add_run(title + " ").bold = True
    p.add_run(text).bold = False
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def add_table(doc, headers, rows, widths=None, font_size=8.5):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table)
    hdr = table.rows[0]
    set_repeat_table_header(hdr)
    for i, h in enumerate(headers):
        c = hdr.cells[i]
        set_cell_shading(c, NAVY)
        set_cell_margins(c)
        c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(str(h))
        r.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        r.font.size = Pt(font_size)
        if widths:
            c.width = Cm(widths[i])
    for ridx, row in enumerate(rows):
        cells = table.add_row().cells
        for i, value in enumerate(row):
            c = cells[i]
            if ridx % 2 == 1:
                set_cell_shading(c, LIGHT_GRAY)
            set_cell_margins(c)
            c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if i == 0 else WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(str(value))
            r.font.size = Pt(font_size)
            if widths:
                c.width = Cm(widths[i])
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return table


def caption(doc, text, source=None):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(9)
    r.font.color.rgb = RGBColor.from_string(DARK)
    if source:
        s = doc.add_paragraph(f"资料来源：{source}", style="Caption Source")
        s.alignment = WD_ALIGN_PARAGRAPH.CENTER


def add_picture(doc, path, title, source, width=Inches(6.35)):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path), width=width)
    caption(doc, title, source)


def choose_font():
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return font_manager.FontProperties(fname=p)
    return font_manager.FontProperties(family="DejaVu Sans")


FONT = choose_font()
plt.rcParams["axes.unicode_minus"] = False


def style_ax(ax):
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="y", color="#E4E7EC", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors="#475467", labelsize=9)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(FONT)


def make_charts():
    # Chart 1: China annual market indicators
    years = ["2021", "2022", "2023", "2024", "2025"]
    sales_area = [17.94, 13.58, 11.17, 9.74, 8.81]
    investment = [14.76, 13.29, 11.09, 10.03, 8.28]
    fig, ax = plt.subplots(figsize=(8.3, 4.4))
    x = range(len(years))
    ax.plot(x, sales_area, marker="o", linewidth=2.6, color="#2F75B5", label="新建商品房销售面积（亿㎡）")
    ax.plot(x, investment, marker="o", linewidth=2.6, color="#2A7F7F", label="房地产开发投资（万亿元）")
    ax.set_xticks(list(x), years, fontproperties=FONT)
    ax.set_ylim(0, 20)
    style_ax(ax)
    ax.legend(prop=FONT, frameon=False, loc="upper right")
    for series, color in [(sales_area, "#2F75B5"), (investment, "#2A7F7F")]:
        for i, v in enumerate(series):
            ax.text(i, v + 0.45, f"{v:.2f}", ha="center", fontsize=8, color=color, fontproperties=FONT)
    fig.tight_layout()
    p1 = CHARTS / "china_market_contraction.png"
    fig.savefig(p1, dpi=220, bbox_inches="tight")
    plt.close(fig)

    # Chart 2: latest China indicators (Jan-Jul 2026)
    labels = ["开发投资", "新开工面积", "竣工面积", "销售面积", "销售额"]
    values = [-19.2, -24.0, -23.2, -11.8, -13.1]
    fig, ax = plt.subplots(figsize=(8.3, 4.4))
    bars = ax.barh(labels[::-1], values[::-1], color=["#B54747", "#C65B57", "#D06A62", "#D7796E", "#DE887A"])
    ax.axvline(0, color="#98A2B3", linewidth=0.8)
    ax.set_xlim(-28, 2)
    style_ax(ax)
    for label in ax.get_yticklabels():
        label.set_fontproperties(FONT)
    for bar, v in zip(bars, values[::-1]):
        ax.text(v + 0.5, bar.get_y() + bar.get_height()/2, f"{v:.1f}%", va="center", ha="left", color="white", fontsize=9, fontproperties=FONT)
    fig.tight_layout()
    p2 = CHARTS / "china_2026m7_indicators.png"
    fig.savefig(p2, dpi=220, bbox_inches="tight")
    plt.close(fig)

    # Chart 3: city latest price changes
    cities = ["北京", "上海", "深圳", "杭州"]
    new = [-2.3, 3.0, -2.9, 2.6]
    used = [-4.5, -2.0, -3.6, -3.4]
    fig, ax = plt.subplots(figsize=(8.3, 4.5))
    x = list(range(len(cities)))
    w = 0.35
    b1 = ax.bar([i-w/2 for i in x], new, width=w, color="#2F75B5", label="新建商品住宅")
    b2 = ax.bar([i+w/2 for i in x], used, width=w, color="#2A7F7F", label="二手住宅")
    ax.axhline(0, color="#98A2B3", linewidth=0.8)
    ax.set_xticks(x, cities, fontproperties=FONT)
    ax.set_ylabel("同比变化（%）", fontproperties=FONT)
    style_ax(ax)
    ax.legend(prop=FONT, frameon=False)
    for bars in (b1, b2):
        for bar in bars:
            v = bar.get_height()
            ax.text(bar.get_x()+bar.get_width()/2, v + (0.15 if v >= 0 else -0.35), f"{v:.1f}", ha="center", va="bottom" if v >= 0 else "top", fontsize=8, fontproperties=FONT)
    fig.tight_layout()
    p3 = CHARTS / "four_city_latest_prices.png"
    fig.savefig(p3, dpi=220, bbox_inches="tight")
    plt.close(fig)

    # Chart 4: city demographics/economy
    gdp = [5.4, 5.4, 5.5, 5.2]
    pop_change = [-3.2, -5.7, 25.9, 7.6]
    fig, ax = plt.subplots(figsize=(8.3, 4.5))
    x = list(range(len(cities)))
    ax.bar(x, gdp, color="#2F75B5", width=0.55)
    ax.set_xticks(x, cities, fontproperties=FONT)
    ax.set_ylabel("2025年GDP实际增速（%）", color="#2F75B5", fontproperties=FONT)
    ax.set_ylim(0, 7)
    style_ax(ax)
    ax2 = ax.twinx()
    ax2.plot(x, pop_change, color="#B7791F", linewidth=2.5, marker="o")
    ax2.axhline(0, color="#D0D5DD", linewidth=0.7)
    ax2.set_ylabel("常住人口增量（万人）", color="#B7791F", fontproperties=FONT)
    ax2.set_ylim(-10, 30)
    ax2.spines[["top", "left"]].set_visible(False)
    ax2.tick_params(colors="#B7791F")
    for i, (g, p) in enumerate(zip(gdp, pop_change)):
        ax.text(i, g+0.12, f"{g:.1f}%", ha="center", color="#2F75B5", fontsize=8, fontproperties=FONT)
        ax2.text(i, p+(1.0 if p >= 0 else -2.0), f"{p:+.1f}", ha="center", color="#B7791F", fontsize=8, fontproperties=FONT)
    fig.tight_layout()
    p4 = CHARTS / "four_city_fundamentals.png"
    fig.savefig(p4, dpi=220, bbox_inches="tight")
    plt.close(fig)

    # Chart 5: scenario bands annualized
    cities = ["北京", "上海", "深圳", "杭州"]
    downside = [(-4.0, -2.0), (-3.5, -1.5), (-5.0, -2.0), (-4.0, -1.5)]
    base = [(-0.5, 1.5), (0.5, 2.5), (0.0, 3.0), (0.5, 3.0)]
    upside = [(2.5, 4.5), (3.0, 5.0), (3.5, 6.0), (3.5, 5.5)]
    fig, ax = plt.subplots(figsize=(8.3, 4.8))
    y = list(range(len(cities)))
    for i in y:
        for rng, color, off in [(downside[i], "#D7796E", -0.18), (base[i], "#2F75B5", 0), (upside[i], "#66A58C", 0.18)]:
            ax.plot(rng, [i+off, i+off], linewidth=7, solid_capstyle="round", color=color)
    ax.axvline(0, color="#98A2B3", linewidth=0.9)
    ax.set_yticks(y, cities, fontproperties=FONT)
    ax.set_xlabel("2026—2030年名义房价年化变化区间（%）", fontproperties=FONT)
    style_ax(ax)
    from matplotlib.lines import Line2D
    ax.legend(handles=[
        Line2D([0],[0], color="#D7796E", lw=7, label="下行情景"),
        Line2D([0],[0], color="#2F75B5", lw=7, label="基准情景"),
        Line2D([0],[0], color="#66A58C", lw=7, label="上行情景"),
    ], prop=FONT, frameon=False, ncol=3, loc="lower right")
    fig.tight_layout()
    p5 = CHARTS / "scenario_bands.png"
    fig.savefig(p5, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return p1, p2, p3, p4, p5


def add_city_section(doc, city, thesis, facts, segments, scenario, action, risks):
    doc.add_heading(city, level=2)
    add_callout(doc, "核心判断", thesis)
    doc.add_heading("基本面与当前市场", level=3)
    add_bullets(doc, facts)
    doc.add_heading("结构分化", level=3)
    add_table(doc, ["细分市场", "相对判断", "关键逻辑"], segments, widths=[3.3, 2.3, 10.1], font_size=8.3)
    doc.add_heading("2026—2030情景", level=3)
    add_table(doc, ["情景", "名义房价年化区间", "成立条件"], scenario, widths=[2.3, 3.5, 9.9], font_size=8.3)
    doc.add_heading("投资执行", level=3)
    add_bullets(doc, action)
    doc.add_heading("主要风险", level=3)
    add_bullets(doc, risks)


def build_report():
    p1, p2, p3, p4, p5 = make_charts()
    doc = Document()
    setup_styles(doc)
    for s in doc.sections:
        configure_page(s)
        add_header_footer(s)
    section = doc.sections[0]

    # Cover
    for _ in range(3):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("中国房地产市场发展研究")
    r.bold = True
    r.font.size = Pt(30)
    r.font.color.rgb = RGBColor.from_string(NAVY)
    r.font.name = "Noto Sans CJK SC"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "Noto Sans CJK SC")
    p2c = doc.add_paragraph()
    p2c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rr = p2c.add_run("国际周期比较、2026—2030城市房价情景与投资策略")
    rr.font.size = Pt(15)
    rr.font.color.rgb = RGBColor.from_string(BLUE)
    doc.add_paragraph()
    line_table = doc.add_table(rows=1, cols=1)
    line_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = line_table.cell(0, 0)
    set_cell_shading(c, BLUE)
    c.height = Cm(0.12)
    set_cell_margins(c, 0, 0, 0, 0)
    doc.add_paragraph()
    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta.add_run("重点城市：北京｜上海｜深圳｜杭州\n").bold = True
    meta.add_run("数据截止：2026年8月17日　报告日期：2026年8月22日\n")
    meta.add_run("研究属性：独立研究 / 情景分析 / 非个性化投资建议")
    meta.runs[-1].font.color.rgb = RGBColor.from_string(MID_GRAY)
    doc.add_paragraph()
    add_callout(doc, "阅读提示", "本报告对“全国市场、城市市场、具体房源”作严格区分。国家统计局新房指数可能受到成交结构和限价项目影响；二手房更接近存量资产的边际定价。所有2026—2030数字均为条件情景，不是保证收益。", color="EAF2F8")
    doc.add_page_break()

    # Legal / methodology note
    doc.add_heading("重要声明", level=1)
    add_bullets(doc, [
        "本报告用于市场研究与资产配置讨论，不构成证券、基金、信贷、税务或法律意见，也不替代对具体房屋的产权、抵押、学区、租约、税费和工程质量尽调。",
        "报告中的价格预测采用区间和触发条件。房地产是高度异质、低流动性资产，同城不同板块、房龄、产品和学区的表现可能相差数十个百分点。",
        "“名义房价”未扣除通胀；若未来通胀回升，名义价格持平仍可能意味着实际价格下跌。总回报还应计入租金、空置、装修折旧、利息、税费与交易成本。",
        "公开数据存在口径差异。国家统计局70城指数覆盖市辖区且使用分类网签数据；市场机构挂牌价、样本均价与实际成交价不可直接互换。"
    ])
    doc.add_heading("目录", level=1)
    toc = doc.add_paragraph()
    add_field(toc, 'TOC \\o "1-3" \\h \\z \\u')
    add_paragraph(doc, "提示：在 Microsoft Word 中打开后，右键目录并选择“更新域”，即可显示最终页码。", style="Caption Source")
    doc.add_page_break()

    # Executive summary
    doc.add_heading("执行摘要", level=1)
    add_callout(doc, "结论先行", "中国房地产已从“全国同涨、增量开发、杠杆驱动”转入“总量收缩、存量交易、城市与产品分化”的新阶段。2026—2030年最可能不是V形普涨，而是核心城市先稳、优质二手与改善新房分化、低能级及人口流出区域继续出清。")
    add_numbered(doc, [
        ("调整尚未结束，但已进入后半程。", "2025年房地产开发投资同比下降17.2%，新建商品房销售面积下降8.7%；2026年1—7月投资、销售面积和新开工又分别下降19.2%、11.8%和24.0%。供给收缩有利于未来再平衡，但销售弱于库存去化意味着价格仍需时间发现底部。"),
        ("“价格筑底”早于“开发投资筑底”。", "国际经验显示，二手成交量和可负担性通常先改善，房价随后稳定，开发投资最后恢复。中国二手房在部分核心城市已出现量先稳；开发商资产负债表和预售交付风险仍制约新房。"),
        ("中国不等同于日本，但日本式拖尾风险真实存在。", "共同点是人口老龄化、资产负债表压力和住房高储蓄属性；不同点是中国城市化仍在推进、首付与资本管制更强、银行体系以国有为主，且政策有更大行政协调能力。结果更可能是“分城市的慢出清”，而非全国同步崩塌。"),
        ("四城风险调整韧性：上海＞北京≈深圳＞杭州；上行弹性则深圳、杭州更高。", "上海兼具全球城市产业、人口规模和较强二手流动性；北京资源稀缺但人口基本持平、远郊库存压制上限；深圳人口增量最大但租金收益率最低、波动更高；杭州数字经济强，但潜在供应和新房替代使二手调整可能更久。"),
        ("投资回报应从“赌涨价”切换为“现金流+折价+流动性”。", "若净租金收益率低于安全资产收益率且没有足够折价，单靠未来涨价难以覆盖5—8%的往返交易成本和装修折旧。基准策略是低杠杆、长持有、购买真实稀缺性，避免远郊同质化大盘、商业公寓和高溢价新房。")
    ])
    add_table(doc, ["市场/城市", "2026—2030基准名义年化", "核心判断", "策略立场"], [
        ["全国商品住宅", "-1%～+1%", "总量收缩、结构分化；低能级拖累", "中性偏谨慎"],
        ["一线及强二线核心区", "0%～+3%", "人口、产业、公共服务支撑，先量后价", "精选"],
        ["普通二线外围/三四线", "-3%～0%", "库存、人口和新增供应约束", "回避为主"],
        ["北京", "-0.5%～+1.5%", "资源稀缺但人口与二手价格承压", "只买核心流动性"],
        ["上海", "+0.5%～+2.5%", "基本面均衡，新房结构强、二手修复", "四城首选"],
        ["深圳", "0%～+3.0%", "人口增量强、科技周期弹性大", "逢折价布局"],
        ["杭州", "+0.5%～+3.0%", "人口与数字经济强，产品分化大", "核心改善优先"],
    ], widths=[3.1, 3.4, 7.0, 2.3])
    add_paragraph(doc, "注：区间为研究模型在基准情景下的城市整体名义价格年化变化，不含租金，不代表具体房源；2026年仍可能先跌后稳。", style="Caption Source")

    # Method
    doc.add_heading("1. 研究框架与预测方法", level=1)
    doc.add_heading("1.1 数据层级与口径", level=2)
    add_table(doc, ["层级", "主要指标", "主要来源", "用途与限制"], [
        ["宏观总量", "开发投资、销售、新开工、竣工、库存", "国家统计局", "判断全国供需与开发周期；不直接代表二手房"],
        ["跨国可比", "实际/名义住宅价格、价租比、价收比", "BIS、OECD、IMF", "比较周期；各国覆盖范围和税制不同"],
        ["城市价格", "70城新房/二手分类价格指数", "国家统计局", "高频方向可靠；新房受成交结构影响"],
        ["城市基本面", "GDP、人口、产业、就业", "四市统计公报", "判断中长期需求；人口增量不等于购房需求"],
        ["交易与挂牌", "成交套数、挂牌量、挂牌价、租金", "地方住建部门、CREIS等", "判断流动性；机构样本不可替代官方指数"],
    ], widths=[2.3, 4.0, 3.5, 6.0])
    doc.add_heading("1.2 五因子城市住宅模型", level=2)
    add_paragraph(doc, "本报告不以单一人口或货币指标外推房价，而采用五因子评分与情景触发：")
    add_table(doc, ["因子", "权重", "正向变量", "负向变量"], [
        ["需求与收入", "30%", "人口净流入、就业、可支配收入、家庭形成", "人口流出、青年失业、收入预期弱"],
        ["供给与库存", "25%", "可售库存下降、土地供应克制、稀缺区位", "远郊供应、同质化产品、法拍与挂牌上升"],
        ["估值与现金流", "20%", "租金增长、价格回撤充分、净租金收益率改善", "价租比过高、持有成本上升"],
        ["信贷与政策", "15%", "利率下降、限购优化、交付保障", "信用收缩、政策不确定、税费变化"],
        ["流动性与质量", "10%", "成交活跃、标准户型、地铁与公共服务", "非标产权、老化严重、流通受限"],
    ], widths=[3.1, 1.8, 5.7, 5.7])
    add_paragraph(doc, "房产预期总回报 ≈ 净租金收益率 + 名义房价变化 − 融资成本（按贷款占比） − 年化交易成本 − 资本性支出。年化交易成本按往返总成本除以预期持有年限估算。", style="Key Finding")
    doc.add_heading("1.3 三种情景", level=2)
    add_table(doc, ["情景", "宏观与政策条件", "市场表现"], [
        ["下行（约25%主观概率）", "通缩延续；居民收入预期弱；开发商风险外溢；库存收购和交付政策效果有限", "全国价格继续下探；核心城市优质资产抗跌但仍负收益"],
        ["基准（约55%）", "政策托底但不重启高杠杆刺激；按揭利率低位；供给快速收缩；收入温和增长", "2026—2027量先稳，2027—2028核心城市价格企稳；全国长期横盘偏弱"],
        ["上行（约20%）", "中央财政更强力处置库存与保交付；居民信心回升；实际利率下降；核心城市限购进一步优化", "核心城市成交与价格同步修复，但难复制2015—2017全国普涨"],
    ], widths=[3.2, 7.3, 5.8])

    # China cycle
    doc.add_heading("2. 中国房地产周期：从住房商品化到存量时代", level=1)
    doc.add_heading("2.1 五阶段演进", level=2)
    add_table(doc, ["阶段", "主要驱动", "市场特征", "政策/制度节点"], [
        ["1998—2007：商品化与城市化", "住房制度改革、城镇化、按揭扩张", "低基数、高增长，住房从福利品转为资产", "1998住房制度改革；土地招拍挂逐步建立"],
        ["2008—2014：刺激与反复调控", "全球危机后信贷刺激、地方土地财政", "2009与2012反弹，库存和区域分化累积", "限购、限贷、保障房并行"],
        ["2015—2018：去库存与棚改货币化", "降息、首付下调、棚改、居民加杠杆", "一线先涨、涨幅向低能级城市扩散", "因城施策；“房住不炒”确立"],
        ["2019—2021：高位钝化", "融资约束增强、疫情后短期宽松", "销售与投资在2021年前后见顶", "三道红线、贷款集中度管理"],
        ["2021—2026：信用收缩与出清", "开发商违约、预售置信心下降、人口转折", "量价齐跌，二手替代新房，城市分化加深", "保交楼、白名单、降首付/利率、收储"],
    ], widths=[3.2, 4.0, 5.0, 4.1])
    add_picture(doc, p1, "图1　中国房地产销售与投资规模明显收缩（2021—2025）", "国家统计局年度数据；2024销售面积为公开年度统计口径，图表取两位小数。")
    doc.add_heading("2.2 2025—2026：需求仍弱，供给更快收缩", level=2)
    add_paragraph(doc, "2025年全国房地产开发投资8.28万亿元，同比下降17.2%；新建商品房销售面积8.81亿平方米，同比下降8.7%，销售额8.39万亿元，下降12.6%；年末商品房待售面积7.66亿平方米，同比增长1.6%。2026年1—7月开发投资4.30万亿元、销售面积4.50亿平方米、销售额4.27万亿元，同比分别下降19.2%、11.8%和13.1%；房企到位资金下降20.3%，说明宽松政策改善了局部城市成交，但尚未改变全国总量趋势。")
    add_picture(doc, p2, "图2　2026年1—7月全国房地产主要指标同比变化", "国家统计局2026年1—7月房地产数据（2026年8月17日发布；官方内容转载页见附录）。")
    add_callout(doc, "关键辨析", "新开工下降24.0%不是纯粹利空。短期它反映开发商资金与信心不足；中期则意味着新增供给显著减少，是库存消化和价格稳定的必要条件。真正的转折信号应是“销售降幅收窄 + 待售库存持续下降 + 二手挂牌周期缩短”，而不是单看新开工。")
    doc.add_heading("2.3 人口、城镇化与住房需求重构", level=2)
    add_paragraph(doc, "2025年末全国人口14.0489亿，比上年减少339万；出生792万、死亡1,131万。常住人口城镇化率67.89%，城镇人口仍增加1,030万。这一组合意味着：全国自然人口红利转负，但人口向都市圈迁移仍能创造结构性住房需求。未来需求将更多来自城市间迁移、家庭小型化、改善置换和旧房更新，而非总人口增长。")
    add_bullets(doc, [
        ("刚性需求：", "由“首次置业数量扩张”转向“青年在就业中心的可负担置业”，更依赖收入与首付约束。"),
        ("改善需求：", "受益于家庭面积升级、低密度与品质住宅偏好，是核心城市新房指数较强的重要原因。"),
        ("养老与继承供给：", "老龄化增加旧房、非电梯房和远郊房源的潜在供给，强化产品折旧。"),
        ("租赁需求：", "人口流入城市的租赁仍有韧性，但保障性租赁住房和机构化供给会限制租金过快上涨。"),
    ])
    doc.add_heading("2.4 政策托底的边界", level=2)
    add_table(doc, ["政策工具", "已实施方向", "传导机制", "局限"], [
        ["需求端", "全国最低首付比例下调、取消全国层面房贷利率下限、限购优化", "降低月供和准入门槛", "不能替代收入预期；可能提前透支需求"],
        ["存量房贷", "支持利率重定价与加点调整", "减轻存量借款人现金流压力", "更多改善消费，不一定形成新增购房"],
        ["供给端", "城市房地产融资协调机制/白名单、保交付", "降低项目烂尾和信用风险", "弱开发商退出仍慢"],
        ["去库存", "3,000亿元保障性住房再贷款，支持地方国企收购已建成库存", "把商品库存转为保障房", "租金回报、收购价格和地方主体资产负债约束"],
        ["新模式", "保障房、城中村改造、城市更新、“好房子”", "从增量土地开发转向存量提质", "规模与落地节奏因城而异"],
    ], widths=[2.6, 4.5, 4.3, 4.5])

    # International cycles
    doc.add_heading("3. 国际主要经济体房地产周期比较", level=1)
    doc.add_heading("3.1 典型周期", level=2)
    add_table(doc, ["经济体/周期", "上行机制", "调整路径", "政策结果", "对中国启示"], [
        ["日本（1991Q2—2009Q2）", "金融自由化、低利率、土地抵押信贷、人口结构见顶", "达拉斯联储口径实际房价峰谷-47.3%、同期名义-49.0%", "宽松过慢、坏账确认迟，资产负债表衰退拖长", "及时确认损失、重组开发商和释放价格比长期“保价”更重要"],
        ["美国（2006Q4—2012Q2）", "低利率、宽松承销、证券化、家庭加杠杆", "达拉斯联储口径实际房价峰谷-27.0%、同期名义-18.9%", "快速银行资本重整、QE、房贷机构支持；2012后复苏", "金融体系损失确认速度决定宏观拖尾；交易出清先于开发复苏"],
        ["西班牙/爱尔兰（2007—2014）", "欧元低利率、跨境资金、建筑过度扩张", "实际峰谷约-36.1%/-51.2%；银行与主权风险互相强化", "银行重组、坏账平台、财政约束下缓慢修复", "高库存地区即使降息也难迅速反转，供给出清不可省略"],
        ["德国（2021Q4—2024Q1）", "低利率、城市化、供给约束推动十余年上涨", "利率急升后实际峰谷约-22.1%、同期名义-11.4%", "租赁市场深、长期融资缓冲系统风险", "租赁现金流和低杠杆可显著降低价格周期的金融放大"],
        ["韩国/新加坡（多轮）", "土地稀缺、城市集中、信贷与税制调控", "政策频繁切换，价格与成交对信贷、税费高度敏感", "宏观审慎、印花税/持有税、公共住房与土地供给并用", "高密度城市仍可周期波动；供给制度和交易税决定弹性"],
    ], widths=[2.9, 3.6, 4.6, 4.0, 4.7], font_size=7.7)
    add_paragraph(doc, "注：峰谷采用达拉斯联储International House Price Database 2025Q4版实际房价序列（季调、2005=100，PCE平减）；不同于BIS的CPI平减和各国官方指数。新加坡等缺少同口径长序列者仅作制度比较，不做伪精确估算。", style="Caption Source")
    doc.add_heading("3.2 共性规律", level=2)
    add_numbered(doc, [
        ("信贷比人口更能解释短周期。", "人口决定长期需求边界，但房价拐点通常由实际按揭利率、首付、承销标准和信用供给触发。"),
        ("库存决定调整长度。", "供给弹性高或开发过度的市场，降息后仍需先去库存；供给受限的全球城市通常更早稳定。"),
        ("量在价之前。", "成交量、挂牌天数和议价率先转向；价格指数滞后；开发投资和土地价格更滞后。"),
        ("实际价格可能在名义横盘中继续调整。", "若名义房价不跌而收入、租金和一般物价上涨，可负担性仍会逐步修复。"),
        ("政策可改变速度，难以取消基本面。", "流动性支持能阻止无序抛售，但无法长期维持人口流出、现金流不足地区的高估值。"),
    ])
    doc.add_heading("3.3 中国与日本：相似但不相同", level=2)
    add_table(doc, ["维度", "日本1990年代", "中国当前", "含义"], [
        ["人口", "劳动年龄人口占比见顶，随后老龄化", "总人口已下降，但城镇人口与核心城市仍净流入", "全国承压、都市圈分化"],
        ["价格对象", "土地和商业地产泡沫突出", "住宅、土地财政和预售开发链条突出", "交付与地方财政是中国特有传导点"],
        ["金融结构", "银行坏账长期延迟确认", "国有银行占主导、资本管制强，开发商而非居民先违约", "系统性挤兑风险低，但损失可能慢摊"],
        ["家庭杠杆", "企业部门去杠杆主导", "居民房贷较规范、首付较高，但资产集中于住房", "负财富效应与消费谨慎更关键"],
        ["政策空间", "早期应对偏慢", "行政、财政、货币工具多但地方财政约束强", "中央财政承担更多损失可缩短调整"],
    ], widths=[2.5, 4.2, 5.0, 4.1])

    # Outlook
    doc.add_heading("4. 2026—2030全国与主要城市房价展望", level=1)
    doc.add_heading("4.1 全国：名义横盘偏弱、实际价格继续消化", level=2)
    add_paragraph(doc, "基准情景下，全国商品住宅名义价格年化约-1%至+1%，但中位数城市可能弱于加权平均。若居民消费价格温和回升，实际房价仍会下降。全国指数的最大误导是被高价核心城市和改善型新房结构抬高，因此投资判断应下沉到“城市—板块—产品—楼栋—户型”。")
    add_table(doc, ["城市类型", "基准年化", "供需特征", "建议"], [
        ["一线核心区", "0%～+3%", "就业密集、供给稀缺、二手流动性高", "精选低总价/改善稀缺资产"],
        ["强二线核心区", "0%～+3%", "人口流入、产业增长，但供地与新房弹性更高", "控制新房溢价，优先地铁与成熟配套"],
        ["普通二线外围", "-2%～+1%", "新城供应与旧城折旧并存", "只做现金流明显改善的折价交易"],
        ["三四线人口稳定区", "-3%～0%", "自住为主，投资需求弱", "除自用外谨慎"],
        ["人口流出/高库存区", "-5%～-1%", "需求收缩、去化周期长、流动性折价", "回避"],
    ], widths=[3.2, 2.8, 7.1, 4.0])
    doc.add_heading("4.2 拐点监测仪表盘", level=2)
    add_table(doc, ["指标", "转稳信号", "当前判断（截至2026年8月）", "频率"], [
        ["二手成交量", "连续6个月同比增长且非单纯降价换量", "一线部分城市量改善", "月度"],
        ["二手价格", "环比3—6个月不再下跌，且上涨城市扩大", "一线整体改善，二三线仍弱", "月度"],
        ["挂牌/成交", "挂牌量下降、成交周期缩短、议价率收窄", "城市与板块分化", "月度"],
        ["库存", "待售面积及广义去化月数持续下降", "官方待售面积高位，IMF估算广义库存约30个月", "月/季"],
        ["土地", "核心地块溢价回归但不伴随大规模供给", "优质地块与普通地块分化", "季度"],
        ["信用", "民营开发商融资与交付改善、重组加速", "压力仍广泛", "季度"],
        ["租金", "租金同比转正且空置率下降", "总体偏弱、核心区更稳", "月/季"],
    ], widths=[2.7, 5.0, 6.5, 1.8])
    add_picture(doc, p5, "图3　四城2026—2030名义房价情景区间（年化）", "本报告研究模型。区间为条件推演，不代表概率分布或保证结果。")

    # Four cities
    doc.add_heading("5. 北京、上海、深圳、杭州专题", level=1)
    add_picture(doc, p4, "图4　四城2025年经济增速与常住人口增量", "北京、上海、深圳、杭州2025年统计公报。上海人口增量按年末常住人口与2024公报近似差额，主要用于方向观察。")
    add_picture(doc, p3, "图5　四城2026年7月新房与二手房价格同比", "国家统计局70城指数；杭州二手房为官方指数公开表所示约-3.4%。")
    add_table(doc, ["城市", "2025挂牌毛租金收益率", "现金流判断", "投资含义"], [
        ["北京", "约2.15%", "四城最高但净收益仍偏低", "核心保值优于纯租金策略"],
        ["上海", "约1.98%", "租赁深度较好、价格基数高", "风险调整后相对均衡"],
        ["深圳", "约1.27%", "四城最低，杠杆负现金流风险最高", "买入价格与压力测试最重要"],
        ["杭州", "约1.72%", "房价调整推动收益率被动改善", "需验证租金而非依赖挂牌报价"],
    ], widths=[2.5, 3.8, 5.2, 4.5])
    add_paragraph(doc, "注：58安居客2025租赁年报挂牌口径，未扣空置、维修、税费和中介费，不等于可实现净收益率；仅用于同口径横向观察。", style="Caption Source")
    add_callout(doc, "如何读图", "上海、杭州新房同比上涨不等于全城住宅普涨：高端改善项目集中入市会抬升新房指数。四城二手房同比仍为负，更接近存量住宅的边际价格。投资者应以同小区真实成交、挂牌库存和租金为定价锚。")

    add_city_section(
        doc, "5.1 北京",
        "最强公共资源与最低供给弹性之一，能提供长期保值底盘；但人口基本稳定、总价高、二手房房龄偏老，2026年前后的价格修复可能慢于上海。应把北京视为“核心资产筛选市场”，而非全城贝塔。",
        [
            ("经济与人口：", "2025年GDP 5.207万亿元、实际增长5.4%；年末常住人口2,180.0万，减少3.2万。第三产业占86%，科技、金融和总部经济支撑高收入需求。"),
            ("价格：", "2026年7月新房环比-0.3%、同比-2.3%；二手房环比持平、同比-4.5%。二手调整深于新房，显示存量房卖方已承担更多价格发现。"),
            ("交易：", "2025年二手住宅约17.4万套，同比略降；2026年1—7月网签约10.7万套，为近年同期较高水平，呈现量修复、价仍弱。"),
            ("政策：", "非京籍购房资格年限已进一步缩短，多孩家庭及公积金首付等有所优化；核心区仍保留约束，政策倾向托成交而非再造泡沫。"),
        ],
        [
            ["东西城优质教育/医疗资源", "抗跌但高溢价", "政策属性强、房龄老；必须核验入学规则与占用情况，不能把学区承诺资本化"],
            ["海淀/朝阳成熟就业区次新", "相对优选", "产业与通勤需求强，标准两居/三居流动性好"],
            ["城市副中心与轨交新城", "分化", "规划兑现度和新增供给决定表现，避免同质化大盘"],
            ["老旧无电梯小户型", "谨慎", "总价低但折旧、维修和适老化成本上升"],
        ],
        [
            ["下行", "-4.0%～-2.0%", "收入预期偏弱、挂牌持续上升、核心区政策边际效应减弱"],
            ["基准", "-0.5%～+1.5%", "成交先稳，库存缓降；核心就业区跑赢远郊"],
            ["上行", "+2.5%～+4.5%", "信贷与限购进一步优化，科技/金融收入改善，优质供给受限"],
        ],
        [
            ("买入阈值：", "同小区近90天可核验成交价基础上再争取5%—10%安全边际；不以挂牌均价估值。"),
            ("产品：", "优先地铁步行、成熟商业、标准户型、可电梯或次新、总价处于板块主流购买力。"),
            ("持有：", "自住改善可在现金流安全前提下分阶段决策；纯投资需至少8—10年持有并接受低租金收益。"),
        ],
        [
            "学区政策和公共服务资格变化导致溢价压缩。",
            "老旧小区资本性支出、加装电梯不确定性与物业品质折旧。",
            "高总价造成买方池窄，市场转弱时流动性折价放大。",
        ],
    )

    add_city_section(
        doc, "5.2 上海",
        "四城中风险调整后最均衡：全球城市产业组合、常住人口规模、成熟租赁市场和相对活跃的二手交易共同支撑。2026年新房同比走强，但主要由供应结构推动；二手房才是判断全市场底部的主指标。",
        [
            ("经济与人口：", "2025年GDP 5.671万亿元、增长5.4%；年末常住人口2,485.41万。金融、贸易、航运、先进制造和科创形成多元就业。"),
            ("价格：", "2026年7月新房环比+0.2%、同比+3.0%；二手房环比+0.3%、同比-2.0%。二手同比降幅在三座一线城市中最小。"),
            ("交易：", "2025年二手住宅约22.2万套，同比增长约4%，为2022年以来较高水平；2026年7月成交约2.3万套，量能领先。"),
            ("供给：", "核心区土地稀缺，五大新城和外围区仍有供应。新房限价与高端项目结构可能制造倒挂或指数偏差，需逐盘判断。"),
        ],
        [
            ["内环/中环成熟板块", "优选", "就业、地铁、教育医疗和租赁需求叠加，供应难复制"],
            ["浦东科创与产业走廊", "精选", "就业增长强，但板块跨度大，需验证通勤和供应"],
            ["五大新城核心节点", "中性偏多", "产业与轨交兑现可形成独立需求；远离核心节点的供给风险高"],
            ["高溢价豪宅/大平层", "波动较高", "稀缺性强但买方池窄，成交结构对指数影响大"],
        ],
        [
            ["下行", "-3.5%～-1.5%", "外需与金融就业转弱，二手挂牌回升，外围供应去化放慢"],
            ["基准", "+0.5%～+2.5%", "二手量价逐步稳定，核心区租赁与收入支撑"],
            ["上行", "+3.0%～+5.0%", "国际与民营经济信心改善，政策继续优化，核心供给紧张"],
        ],
        [
            ("首选策略：", "成熟就业中心45—120平方米主流户型，以二手真实成交价和租金反推合理价。"),
            ("新房纪律：", "把新房总价拆为土地/区位、产品、交付信用与限价红利；若相对周边次新成交溢价超过10%—15%，需有明确品质或稀缺性补偿。"),
            ("退出测试：", "假设未来成交量下降30%，验证总价段是否仍有足够买家。"),
        ],
        [
            "高端新房供应结构造成价格指数高估普遍涨幅。",
            "外围新城产业与人口导入低于规划。",
            "全球贸易与金融周期对高收入就业形成冲击。",
        ],
    )

    add_city_section(
        doc, "5.3 深圳",
        "人口与科技产业动能最强、土地最稀缺之一，也是四城中杠杆和预期弹性最大的市场。经历较深调整后估值改善，但不应据此假设迅速回到上一轮高点；核心是区分真实产业住房需求与旧改/概念溢价。",
        [
            ("经济与人口：", "2025年GDP 3.873万亿元、增长5.5%；常住人口1,824.85万，增加25.90万，增量居四城首位。先进制造、互联网、金融与跨境创新支撑需求。"),
            ("价格：", "2026年7月新房环比+0.2%、同比-2.9%；二手房环比+0.2%、同比-3.6%。环比修复但同比仍负。"),
            ("交易：", "2025年二手住宅约5.6万套，同比增长约3.2%；成交恢复基数低于北京、上海，流动性仍需持续验证。"),
            ("供给与城市结构：", "市域土地稀缺但深莞惠跨城供给可替代；旧改预期、产业迁移与轨道交通会重塑板块价值。"),
        ],
        [
            ["南山/福田核心就业区", "相对优选", "高收入岗位密集、供给稀缺，租赁与置换需求强"],
            ["宝安中心/前海兑现区", "精选", "规划兑现和新增供应并存，避免把远期利好一次性买满"],
            ["龙华轨交通勤区", "中性偏多", "总价与通勤平衡，供给和产品同质化需检查"],
            ["远郊/跨城概念板块", "谨慎", "通勤成本、学位与供给替代导致流动性折价"],
        ],
        [
            ["下行", "-5.0%～-2.0%", "科技就业与收入承压，杠杆买家去化，跨城替代供给增加"],
            ["基准", "0%～+3.0%", "人口流入持续、核心区库存下降、二手量价修复"],
            ["上行", "+3.5%～+6.0%", "科技资本开支和收入强劲，利率下降，政策显著放松"],
        ],
        [
            ("仓位：", "因波动更高，投资性房产不宜成为家庭净资产的过高集中；避免高杠杆追涨。"),
            ("定价：", "以税费后租金收益和同户型成交为锚，对旧改、名校、总部落地等未兑现预期打折。"),
            ("时点：", "优先观察连续6个月二手成交与议价率改善，再提高风险敞口。"),
        ],
        [
            "科技行业薪酬、股权财富和创业周期波动。",
            "跨城住房供给对外围区形成长期替代。",
            "旧改周期、回迁安排与产权复杂性。",
        ],
    )

    add_city_section(
        doc, "5.4 杭州",
        "人口净流入、数字经济和民营企业活力构成强基本面，新房改善需求在2026年表现突出；但供应弹性高于一线城市、板块扩张快，投资必须避免“规划即价值”的线性外推。",
        [
            ("经济与人口：", "2025年GDP 2.301万亿元、增长5.2%；常住人口1,270.0万，增加7.6万。数字经济核心产业增加值6,780亿元、增长9.3%，占GDP 29.5%。"),
            ("价格：", "2026年7月新房环比+0.3%、同比+2.6%，环比居70城前列；官方二手房环比约-0.1%、同比约-3.4%，机构样本同比跌幅更大，说明新旧房分化。"),
            ("交易：", "2025年二手住宅约6.8万套，同比下降约6%；2026年1—7月约4.0万套，同比下降约8.9%（机构监测），量能尚未确认全面修复。"),
            ("供给：", "城市扩张和轨交新城提供较多新增土地，新房品质迭代快，旧房折旧速度可能高于北京、上海。"),
        ],
        [
            ["西湖/滨江/拱墅成熟核心", "优选", "公共服务、产业与稀缺景观叠加，流动性较好"],
            ["未来科技城/城西科创走廊", "精选", "产业真实但供应较多，需贴近就业和轨交节点"],
            ["钱江新城/奥体改善", "中性偏多", "城市界面与改善需求强，警惕高总价和集中供应"],
            ["远郊新城/概念板块", "谨慎", "规划周期长、供应弹性高、租赁需求未必同步"],
        ],
        [
            ["下行", "-4.0%～-1.5%", "民营科技收入放缓，新房供应持续，二手折旧加速"],
            ["基准", "+0.5%～+3.0%", "人口与数字经济延续增长，核心板块去化改善"],
            ["上行", "+3.5%～+5.5%", "民营经济与资本市场强劲，改善需求释放，供地克制"],
        ],
        [
            ("新旧房选择：", "新房只有在交付信用、产品升级和相对次新成交价合理时才值得支付溢价；老旧二手需预留更高折旧。"),
            ("板块纪律：", "用15—30分钟通勤圈和当前就业密度验证需求，不以远期地铁或总部规划单独决策。"),
            ("流动性：", "优先90—140平方米主流改善户型，控制总价在板块活跃成交带。"),
        ],
        [
            "新房集中供应和高品质产品对存量二手形成替代。",
            "民营与数字经济周期对住房需求敏感。",
            "板块扩张过快导致基础设施与入住率滞后。",
        ],
    )

    # Investment
    doc.add_heading("6. 可执行投资指导", level=1)
    doc.add_heading("6.1 先判断“应不应该买”", level=2)
    add_table(doc, ["问题", "通过标准", "不通过时"], [
        ["家庭现金流", "首付后仍保留12—24个月家庭支出；压力利率下月供≤税后收入30%—35%", "降低总价或继续租房"],
        ["持有期限", "计划持有≥8年；短期工作与家庭地点稳定", "交易成本难摊薄，暂缓"],
        ["资产集中度", "购房后单一房产不致使净资产和现金流过度集中", "降低杠杆/面积或分散资产"],
        ["租售比较", "使用同小区可实现租金，净租金收益率与替代收益率差可接受", "租房并投资流动资产"],
        ["价格安全边际", "相对近90—180天可核验成交有折价，或稀缺品质足以解释溢价", "拒绝锚定挂牌价"],
    ], widths=[2.8, 8.0, 5.2])
    doc.add_heading("6.2 房源筛选评分卡（100分）", level=2)
    add_table(doc, ["维度", "分值", "加分项", "一票否决/重扣"], [
        ["就业与通勤", "20", "30—45分钟到多元就业中心，轨交通达", "只依赖单一雇主或远期线路"],
        ["人口与公共服务", "15", "真实入住率、医疗教育商业成熟", "空置新城、公共服务不确定"],
        ["供给稀缺", "15", "成熟区低新增供给、不可复制资源", "周边大量待开发土地"],
        ["产品与物业", "15", "标准户型、采光、梯户比、物业维护良好", "产权瑕疵、严重质量/消防问题"],
        ["流动性", "15", "主流面积和总价，近12月成交活跃", "超大户型、非标公寓、买方池窄"],
        ["现金流", "10", "可实现租金稳定、空置低", "租金依赖短期补贴或虚假报价"],
        ["价格与折价", "10", "低于可比成交或替代成本合理", "高溢价来自营销和未兑现规划"],
    ], widths=[2.7, 1.5, 6.2, 6.0])
    add_paragraph(doc, "建议：≥80分方进入财务测算；70—79分仅自住或显著折价；<70分原则上放弃。评分不能替代产权和工程尽调。", style="Key Finding")
    doc.add_heading("6.3 收益测算示例", level=2)
    add_paragraph(doc, "假设一套总价500万元住宅：首付200万元、贷款300万元；月租金9,000元，年空置1个月；物业与维修等每年1.5万元。则毛租金收益率约2.16%，净租金收益率约1.65%。若贷款成本3.2%，贷款占比60%，融资对股权现金流仍是负贡献。若往返税费与中介等合计6%、持有8年，年化交易成本约0.75%。")
    add_table(doc, ["项目", "计算", "结果"], [
        ["有效年租金", "9,000×11个月", "9.9万元"],
        ["净租金", "9.9万−1.5万", "8.4万元"],
        ["净租金收益率", "8.4万÷500万", "1.68%"],
        ["年利息近似", "300万×3.2%", "9.6万元"],
        ["年化交易成本", "500万×6%÷8年", "3.75万元/年"],
        ["盈亏平衡升值率（简化）", "融资成本与费用缺口÷房价", "约1%—2%/年"],
    ], widths=[3.3, 7.4, 4.9])
    add_paragraph(doc, "该示例未计本金摊还、个税差异、装修折旧和机会成本，只用于展示为什么低租金收益资产需要价格上涨才能获得正总回报。实际应以贷款摊销表和税务规则逐项计算。", style="Caption Source")
    doc.add_heading("6.4 税费与制度压力测试", level=2)
    add_paragraph(doc, "交易税费应以签约时当地税务机关和购房资格口径为准，不能把当前优惠永久化。现行全国契税优惠按住房套数和140平方米界限区分；自2026年1月1日起，个人出售购买不足2年的住房，按3%征收率全额缴纳增值税，持有满2年免征增值税。模型还应加入“优惠取消、年度持有税增加、出售税费上升”的压力项。")
    add_bullets(doc, [
        ("购入端：", "契税、中介费、贷款费用、装修和首期空置全部计入初始投入。"),
        ("持有端：", "物业、维修、保险、租赁税费及每5—8年的装修资本开支逐项计入。"),
        ("退出端：", "按保守成交折价、出售中介费和适用税费计算，不用挂牌价作为退出价。"),
        ("制度风险：", "房地产税改革存在授权框架，但实施城市、时间和税率不能预设；仅作为压力参数。"),
    ])
    doc.add_heading("6.5 买入、谈判与持有流程", level=2)
    add_numbered(doc, [
        ("建立可比池：", "收集同小区同户型近6个月网签/中介可核验成交，排除楼层、朝向、装修和特殊交易差异。"),
        ("倒推最高报价：", "最高报价 = 保守估值 − 未来3年必要装修/维修 − 产权与交付风险折价 − 目标安全边际。"),
        ("压力测试：", "房价再跌15%、租金跌10%、空置2个月、利率上升100bp时，家庭仍能持有。"),
        ("法律与工程尽调：", "核验产权、抵押、查封、租约、户口/学位占用、土地年限、物业欠费、违建、渗漏和结构风险。"),
        ("分散时点：", "改善或投资换房可先卖后买，避免同一周期双向暴露；不要把短期政策发布日当作唯一时点。"),
        ("设定退出条件：", "就业中心迁移、板块供应激增、物业持续恶化或家庭现金流变化时，重新评估而非锚定买入价。"),
    ])
    doc.add_heading("6.6 应回避的高风险品类", level=2)
    add_bullets(doc, [
        "远郊大体量、同质化、低入住率项目，尤其依赖单一规划或产业园招商。",
        "产权年限、土地用途、落户/学位或贷款条件与普通住宅不同的商业公寓。",
        "开发商交付与物业服务能力弱、资金监管和施工进度不透明的期房。",
        "以“保租、返租、包租”承诺替代真实市场租金的产品。",
        "高龄、无电梯、维护差且无明确更新计划的非稀缺旧房。",
        "总价显著高于板块主流购买力、未来接盘人极少的非标豪宅。",
    ])

    # Monitoring and conclusion
    doc.add_heading("7. 风险、触发器与结论", level=1)
    doc.add_heading("7.1 关键风险矩阵", level=2)
    add_table(doc, ["风险", "概率方向", "影响", "领先指标", "应对"], [
        ["通缩与收入预期弱", "中高", "高", "核心CPI、工资、居民中长期贷款", "低杠杆、提高现金流要求"],
        ["开发商/交付风险", "中", "高", "白名单融资、竣工、债务重组", "优先现房/次新，核验项目资金"],
        ["政策低于预期", "中", "中高", "库存收购落地、中央财政支持", "不把政策传闻计入价格"],
        ["核心城市再度过热后调控", "低中", "中", "成交/房价短期急涨、地王频现", "不追涨、保留退出流动性"],
        ["人口与产业迁移", "中", "高（局部）", "就业、写字楼吸纳、常住人口", "选择多元就业中心"],
        ["物业折旧与气候风险", "中高", "中高", "维修资金、保险、极端天气", "工程尽调与资本开支预算"],
    ], widths=[3.1, 2.0, 1.8, 5.0, 4.1])
    doc.add_heading("7.2 哪些变化会使本报告上调判断", level=2)
    add_bullets(doc, [
        "核心城市二手房价连续6个月环比非负，且上涨并非由极少数高端成交驱动。",
        "全国待售面积与IMF口径广义库存同步明显下降，销售降幅连续两个季度收窄。",
        "民营开发商实质性重组加快，预售交付与融资恢复，房企退出机制清晰。",
        "租金转为同比增长、居民收入预期改善，净租金收益率不靠价格下跌也能提高。",
        "中央财政承担更大规模的保交付、库存处置和地方债务成本，打破地方资产负债约束。",
    ])
    doc.add_heading("7.3 哪些变化会使本报告下调判断", level=2)
    add_bullets(doc, [
        "核心城市成交量回升完全依靠大幅降价，挂牌量、法拍和议价率继续上升。",
        "居民中长期贷款再度明显收缩，青年就业和民营企业投资转弱。",
        "库存收购因租金回报和地方国企杠杆约束落地缓慢。",
        "优质城市新增土地和保障性供给显著超过人口与家庭形成速度。",
        "地缘政治或外需冲击影响上海、深圳、杭州高收入行业就业。",
    ])
    add_callout(doc, "最终结论", "未来五年中国住宅最重要的投资变量不是“全国房价会不会涨”，而是“这套房是否位于持续创造高收入岗位的城市节点、是否足够稀缺、是否有可验证现金流、是否能在压力情景下被下一位买家接手”。在基准情景下，上海最均衡，杭州和深圳弹性更高，北京更偏核心保值；四城外围和老化非稀缺资产仍可能跑输城市平均。")

    # Sources
    doc.add_page_break()
    doc.add_heading("附录A　主要数据来源与链接", level=1)
    sources = [
        ("国家统计局（2026-01-19）《2025年全国房地产市场基本情况》", "https://www.stats.gov.cn/sj/zxfb/202601/t20260119_1962324.html"),
        ("国家统计局（2026-07-15）《2026年1—6月份全国房地产市场基本情况》", "https://www.stats.gov.cn/sj/zxfb/202607/t20260715_1964126.html"),
        ("国家统计局2026年1—7月房地产数据（官方内容转载页，2026-08-17）", "https://zzhz.zjol.com.cn/zjtd/ycbody/ctygrym/202608/t20260817_31854806.shtml"),
        ("国家统计局（2026-08-17）《2026年7月份商品住宅销售价格变动情况》解读", "https://www.stats.gov.cn/sj/sjjd/202608/t20260817_1965046.html"),
        ("国家统计局（2026-02-28）《中华人民共和国2025年国民经济和社会发展统计公报》", "https://www.stats.gov.cn/sj/zxfbhjd/202602/t20260228_1962662.html"),
        ("中国人民银行（2024-05-17）取消全国层面商业性个人住房贷款利率下限", "https://www.pbc.gov.cn/goutongjiaoliu/113456/113469/2025092212554062364/index.html"),
        ("中国人民银行公告〔2024〕第11号：完善商业性个人住房贷款利率定价机制", "http://www.pbc.gov.cn/zhengwugongkai/4081330/4406346/4700569/5523202/index.html"),
        ("中国政府网（2024-06）《3000亿元保障性住房再贷款进展怎样？如何运作？》", "https://www.gov.cn/zhengce/202406/content_6957105.htm"),
        ("IMF（2026）People’s Republic of China: 2025 Article IV Consultation, Country Report 26/044", "https://www.imf.org/en/publications/cr/issues/2026/02/17/peoples-republic-of-china-2025-article-iv-consultation-press-release-staff-report-and-574028"),
        ("BIS（2026-05）Residential property price statistics, Q4 2025", "https://www.bis.org/statistics/pp_residential_2605.htm"),
        ("BIS Data Portal — Residential Property Prices", "https://data.bis.org/topics/RPP"),
        ("达拉斯联储 — International House Price Database", "https://www.dallasfed.org/research/international/houseprice"),
        ("OECD — Housing prices and analytical indicators", "https://www.oecd.org/en/data/indicators/housing-prices.html"),
        ("日本银行（2012）How to detect and respond to property bubbles", "https://www.boj.or.jp/en/about/press/koen_2012/ko120821a.htm"),
        ("北京市统计局《北京市2025年国民经济和社会发展统计公报》", "https://tjj.beijing.gov.cn/tjsj_31433/tjgb_31445/ndgb_31446/202603/t20260326_4566469.html"),
        ("上海市统计局《2025年上海市国民经济和社会发展统计公报》", "https://tjj.sh.gov.cn/tjgb/20260330/e0772941e8e041eaaad2df850b44ef98.html"),
        ("深圳市统计局《深圳市2025年国民经济和社会发展统计公报》", "https://tjj.sz.gov.cn/szstjjwzgkml/szstjjwzgkml/sjfb/tjgb/content/post_12805132.html"),
        ("杭州市统计公报（杭州网转载）《2025年杭州市国民经济和社会发展统计公报》", "https://hznews.hangzhou.com.cn/chengshi/content/2026-04/30/content_9214808.htm"),
        ("中指研究院（2026-01）2025年重点城市二手住宅成交与价格", "https://m.cih-index.com/news/2026-01-28/54230778.html"),
        ("中国房地产指数系统（2026-08）2026年7月十大城市二手房房价地图", "http://news.szhome.com/393952.html"),
        ("58安居客（2025）全国租赁市场年度报告", "https://pdf.dfcfw.com/pdf/H3_AP202512281809763310_1.pdf?1766932156000.pdf="),
        ("财政部等（2024年第16号）房地产交易契税优惠政策", "https://www.gov.cn/zhengce/zhengceku/202411/content_6986750.htm"),
        ("国家税务总局：2026年起个人住房销售增值税政策", "https://fgk.chinatax.gov.cn/zcfgk/c102416/c5246356/content.html"),
    ]
    for i, (name, url) in enumerate(sources, 1):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        p.add_run(f"[{i}] {name}\n").bold = True
        rr = p.add_run(url)
        rr.font.size = Pt(8)
        rr.font.color.rgb = RGBColor.from_string(BLUE)
    add_paragraph(doc, "说明：部分政府网站会调整发布日期路径；若链接失效，可用报告标题在相应机构官网检索。报告所有网络数据的检索截止日为2026年8月22日。", style="Caption Source")

    doc.add_heading("附录B　术语与口径", level=1)
    add_table(doc, ["术语", "定义/本报告用法"], [
        ["新建商品住宅价格指数", "国家统计局基于网签数据、按面积分类计算；成交结构变化可能影响城市总指数。"],
        ["二手住宅价格指数", "存量住房交易价格变化，通常更能反映边际价格，但仍受样本与议价影响。"],
        ["待售面积", "统计局口径主要为已竣工可售库存，不等于施工中、已批未售等广义库存。"],
        ["广义库存/去化月数", "将可售、在建等库存与销售速度比较；机构和IMF口径可能不同。"],
        ["毛租金收益率", "年合同租金÷总房价，未扣空置、物业、维修、税费。"],
        ["净租金收益率", "扣除经常性运营成本后的年租金÷总投入；本报告建议用可实现租金。"],
        ["名义/实际房价", "名义为观察价格；实际房价为名义价格扣除一般物价变化。"],
        ["年化变化", "将多年度累计变化折算为复合年增长率；情景区间不是点预测。"],
    ], widths=[4.0, 12.0])

    # Document properties and update fields hint
    props = doc.core_properties
    props.title = "中国房地产市场发展研究：国际周期比较、2026—2030城市房价情景与投资策略"
    props.subject = "中国房地产市场，北京、上海、深圳、杭州，投资策略"
    props.author = "独立研究"
    props.keywords = "中国房地产, 房价预测, 北京, 上海, 深圳, 杭州, 国际房地产周期"
    props.comments = "数据截止2026年8月17日；报告日期2026年8月22日。"

    settings = doc.settings._element
    update_fields = settings.find(qn("w:updateFields"))
    if update_fields is None:
        update_fields = OxmlElement("w:updateFields")
        settings.append(update_fields)
    update_fields.set(qn("w:val"), "true")

    path = OUT / "中国房地产市场发展研究报告_2026-2030.docx"
    ascii_path = OUT / "china-real-estate-market-report-2026-2030.docx"
    doc.save(path)
    doc.save(ascii_path)
    return ascii_path


if __name__ == "__main__":
    report_path = build_report()
    print(report_path)
