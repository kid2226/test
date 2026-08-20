#!/usr/bin/env python3
"""Generate figures for the China bonds vs equities allocation report."""

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch, Wedge
import numpy as np
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

FONT = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
font_manager.fontManager.addfont(FONT)
plt.rcParams.update(
    {
        "font.family": "WenQuanYi Micro Hei",
        "font.size": 11,
        "axes.unicode_minus": False,
        "figure.facecolor": "#F7F5F2",
        "axes.facecolor": "#F7F5F2",
        "axes.edgecolor": "#1B365D",
        "axes.labelcolor": "#1B365D",
        "xtick.color": "#1B365D",
        "ytick.color": "#1B365D",
        "text.color": "#1A1A1A",
        "axes.titleweight": "bold",
        "axes.titlesize": 13,
        "savefig.dpi": 180,
        "savefig.bbox": "tight",
        "savefig.facecolor": "#F7F5F2",
    }
)

NAVY = "#1B365D"
STEEL = "#4A6FA5"
GOLD = "#C4A35A"
TEAL = "#2A9D8F"
CORAL = "#E07A5F"
SLATE = "#6B7C93"
CREAM = "#F7F5F2"
WHITE = "#FFFFFF"


def save(fig, name: str) -> None:
    fig.savefig(OUT / name, dpi=180)
    plt.close(fig)
    print(f"wrote {name}")


def fig01_terminal_wealth():
    labels = [
        "A股整体",
        "大盘股",
        "小盘股",
        "长期国债",
        "短期国债",
        "通货膨胀",
    ]
    wealth = [7.98, 7.00, 8.74, 2.45, 1.66, 1.56]
    colors = [CORAL, "#D48A74", "#B94A48", TEAL, STEEL, SLATE]
    fig, ax = plt.subplots(figsize=(10.2, 5.6))
    bars = ax.bar(labels, wealth, color=colors, width=0.62, zorder=3)
    ax.axhline(1.0, color=NAVY, lw=0.8, ls="--", alpha=0.5)
    for bar, v in zip(bars, wealth):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            v + 0.18,
            f"{v:.2f}元",
            ha="center",
            va="bottom",
            fontsize=10,
            color=NAVY,
        )
    ax.set_ylabel("2004年底投入1元，2025年底财富（元）")
    ax.set_title("图1  中国主要资产21年累计财富（全收益，再投资）")
    ax.set_ylim(0, 10.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#D9D4CC", lw=0.7, zorder=0)
    ax.text(
        0.0,
        -0.16,
        "资料来源：陈鹏、有知有行《中国大类资产投资2025年报》（SBBI框架）。A股=中证全指全收益；大盘=沪深300全收益；小盘=中证1000全收益；长期国债=中债7-10年国债财富。",
        transform=ax.transAxes,
        fontsize=8,
        color=SLATE,
    )
    save(fig, "fig01_terminal_wealth.png")


def fig02_risk_return():
    assets = [
        ("A股整体", 54.10, 10.40, CORAL),
        ("大盘股", 53.44, 9.71, "#D48A74"),
        ("小盘股", 60.93, 10.87, "#B94A48"),
        ("长期信用债", 6.18, 5.19, GOLD),
        ("长期国债", 6.16, 4.36, TEAL),
        ("短期国债", 0.88, 2.43, STEEL),
        ("上海黄金", 17.32, 10.57, "#C9A227"),
        ("通货膨胀", 1.69, 2.13, SLATE),
    ]
    fig, ax = plt.subplots(figsize=(10.2, 6.2))
    for name, vol, ret, c in assets:
        ax.scatter(vol, ret, s=120, color=c, zorder=4, edgecolors=NAVY, lw=0.6)
        dx, dy = 1.2, 0.25
        if name == "大盘股":
            dy = -0.55
        if name == "长期信用债":
            dy = 0.45
        if name == "长期国债":
            dy = -0.55
        ax.annotate(name, (vol + dx, ret + dy), fontsize=10, color=NAVY)
    ax.set_xlabel("年化波动率（%，年度收益标准差）")
    ax.set_ylabel("年化收益率（%）")
    ax.set_title("图2  风险—收益平面：股票提供风险溢价，债券提供效率")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(color="#D9D4CC", lw=0.7, zorder=0)
    ax.set_xlim(-2, 70)
    ax.set_ylim(0, 13)
    ax.text(
        0.0,
        -0.14,
        "资料来源：同上。长期信用债统计区间为2007–2025年，其余为2005–2025年。波动率按年度收益率标准差计算，高于日度收益年化波动率，口径需与卖方常用的月度/日度年化区分。",
        transform=ax.transAxes,
        fontsize=8,
        color=SLATE,
    )
    save(fig, "fig02_risk_return.png")


def fig03_bond_structure():
    labels = [
        "地方政府债\n27.8%",
        "金融债\n20.9%",
        "国债\n20.8%",
        "同业存单\n10.0%",
        "公司债\n9.0%",
        "债务融资工具\n8.7%",
        "ABS及其他\n2.7%",
    ]
    sizes = [27.82, 20.93, 20.80, 10.03, 9.02, 8.74, 2.66]
    colors = [NAVY, STEEL, TEAL, GOLD, CORAL, "#8E6B4A", SLATE]
    fig, ax = plt.subplots(figsize=(9.6, 6.0))
    wedges, _ = ax.pie(
        sizes,
        colors=colors,
        startangle=90,
        wedgeprops={"width": 0.46, "edgecolor": CREAM, "linewidth": 2},
    )
    ax.legend(
        wedges,
        labels,
        loc="center left",
        bbox_to_anchor=(0.95, 0.5),
        frameon=False,
        fontsize=10,
    )
    ax.set_title("图3  2025年末中国债券余额结构（约196.3万亿元）")
    ax.text(
        0,
        0,
        "利率债\n压舱石",
        ha="center",
        va="center",
        fontsize=12,
        color=NAVY,
        fontweight="bold",
    )
    ax.text(
        0.0,
        -1.22,
        "资料来源：Wind，转引自有知有行SBBI 2025；合计约196.3万亿元，与人民银行公布的全市场托管余额196.7万亿元口径接近。",
        ha="center",
        fontsize=8,
        color=SLATE,
    )
    save(fig, "fig03_bond_structure.png")


def fig04_social_financing():
    labels = [
        "人民币贷款",
        "政府债券",
        "企业债券",
        "非金融企业\n境内股票",
        "其他*",
    ]
    values = [60.7, 21.5, 7.7, 2.8, 7.3]
    colors = [NAVY, STEEL, TEAL, CORAL, SLATE]
    fig, ax = plt.subplots(figsize=(10.0, 5.6))
    bars = ax.barh(labels[::-1], values[::-1], color=colors[::-1], height=0.58, zorder=3)
    for bar, v in zip(bars, values[::-1]):
        ax.text(v + 0.6, bar.get_y() + bar.get_height() / 2, f"{v:.1f}%", va="center", color=NAVY)
    ax.set_xlim(0, 72)
    ax.set_xlabel("占社会融资规模存量比重（%）")
    ax.set_title("图4  2025年末社会融资存量结构：贷款仍是主体")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", color="#D9D4CC", lw=0.7, zorder=0)
    ax.text(
        0.0,
        -0.18,
        "*其他含委托贷款、信托贷款、未贴现银票、外币贷款等。资料来源：中国人民银行《2025年金融统计数据报告》。",
        transform=ax.transAxes,
        fontsize=8,
        color=SLATE,
    )
    save(fig, "fig04_social_financing.png")


def fig05_market_size():
    labels = ["债券市场\n托管余额", "沪深A股\n总市值", "2025年GDP"]
    values = [196.7, 107.84, 140.19]
    colors = [TEAL, CORAL, NAVY]
    fig, ax = plt.subplots(figsize=(8.8, 5.6))
    bars = ax.bar(labels, values, color=colors, width=0.55, zorder=3)
    for bar, v in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            v + 4,
            f"{v:.1f}万亿",
            ha="center",
            color=NAVY,
            fontsize=11,
        )
    ax.set_ylabel("万亿元人民币")
    ax.set_title("图5  规模对照：债市大于股市，也大于当年GDP")
    ax.set_ylim(0, 230)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#D9D4CC", lw=0.7, zorder=0)
    ax.text(
        0.0,
        -0.16,
        "资料来源：人民银行金融市场运行情况（债市托管196.7万亿元）；中国结算统计年鉴（沪深A股总市值107.84万亿元）；国家统计局（GDP 140.19万亿元，初步核算）。",
        transform=ax.transAxes,
        fontsize=8,
        color=SLATE,
    )
    save(fig, "fig05_market_size.png")


def fig06_year_2025():
    labels = ["小盘股", "A股整体", "大盘股", "短期国债", "长期国债", "长期信用债", "CPI"]
    rets = [29.02, 27.03, 20.98, 1.23, 0.89, 0.30, 0.00]
    colors = [CORAL if r > 5 else TEAL if r > 0.5 else SLATE for r in rets]
    fig, ax = plt.subplots(figsize=(10.2, 5.6))
    bars = ax.barh(labels[::-1], rets[::-1], color=colors[::-1], height=0.58, zorder=3)
    for bar, v in zip(bars, rets[::-1]):
        ax.text(v + 0.4, bar.get_y() + bar.get_height() / 2, f"{v:.2f}%", va="center", color=NAVY)
    ax.set_xlabel("2025年全收益率（%）")
    ax.set_title("图6  2025年：股强债弱，短债好于长债与信用债")
    ax.set_xlim(0, 34)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", color="#D9D4CC", lw=0.7, zorder=0)
    ax.text(
        0.0,
        -0.16,
        "资料来源：有知有行SBBI 2025。黄金2025年收益58.57%，图中未列入以免压缩股债对比尺度。",
        transform=ax.transAxes,
        fontsize=8,
        color=SLATE,
    )
    save(fig, "fig06_year_2025.png")


def fig07_sharpe():
    labels = ["长期信用债", "长期国债", "上海黄金", "A股整体", "小盘股", "大盘股"]
    sharpe = [0.45, 0.31, 0.47, 0.15, 0.14, 0.14]
    colors = [GOLD, TEAL, "#C9A227", CORAL, "#B94A48", "#D48A74"]
    fig, ax = plt.subplots(figsize=(10.0, 5.4))
    bars = ax.barh(labels[::-1], sharpe[::-1], color=colors[::-1], height=0.55, zorder=3)
    for bar, v in zip(bars, sharpe[::-1]):
        ax.text(v + 0.01, bar.get_y() + bar.get_height() / 2, f"{v:.2f}", va="center", color=NAVY)
    ax.set_xlabel("夏普比率 ≈ (年化收益 − 短期国债) / 年度收益标准差")
    ax.set_title("图7  单位风险回报：债券与黄金高于A股（年度波动口径）")
    ax.set_xlim(0, 0.58)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", color="#D9D4CC", lw=0.7, zorder=0)
    ax.text(
        0.0,
        -0.18,
        "作者按SBBI 2005–2025年数据计算；长期信用债为2007–2025年。夏普对波动口径高度敏感，若改用日度年化波动，股票夏普会上升，但排序方向通常不变。",
        transform=ax.transAxes,
        fontsize=8,
        color=SLATE,
    )
    save(fig, "fig07_sharpe.png")


def fig08_merrill_clock():
    fig, ax = plt.subplots(figsize=(9.4, 9.0))
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.45, 1.35)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("图8  增长—通胀四象限与股债含义（美林时钟中国化）", pad=8)

    quads = [
        (0, 90, TEAL, "衰退\n增长↓ 通胀↓", "债券领先\n股票左侧布局"),
        (90, 180, GOLD, "复苏\n增长↑ 通胀↓", "股票领先\n缩短久期"),
        (180, 270, CORAL, "过热\n增长↑ 通胀↑", "商品/周期股\n债券承压"),
        (270, 360, STEEL, "滞胀\n增长↓ 通胀↑", "现金/黄金\n股债双杀风险"),
    ]
    for start, end, color, title, note in quads:
        wedge = Wedge((0, 0), 1.0, start, end, facecolor=color, edgecolor=CREAM, lw=4, alpha=0.88)
        ax.add_patch(wedge)
        theta = np.deg2rad((start + end) / 2)
        r = 0.62
        ax.text(
            r * np.cos(theta),
            r * np.sin(theta),
            f"{title}\n\n{note}",
            ha="center",
            va="center",
            fontsize=10,
            color=WHITE,
            fontweight="bold",
        )
    inner = Circle((0, 0), 0.28, facecolor=CREAM, edgecolor=NAVY, lw=1.2)
    ax.add_patch(inner)
    ax.text(0, 0.02, "中国\n投研时钟", ha="center", va="center", fontsize=11, color=NAVY, fontweight="bold")
    ax.text(
        0,
        -1.28,
        "经典美林时钟（Merrill Lynch, 2004）以产出缺口与CPI划分周期。中国实践中多用工业增加值/PMI与CPI/PPI，\n并叠加“货币+信用”维度。滞胀阶段在中国样本中常出现背离，不可机械套用。",
        ha="center",
        fontsize=8,
        color=SLATE,
    )
    save(fig, "fig08_merrill_clock.png")


def fig09_research_stack():
    fig, ax = plt.subplots(figsize=(11.0, 6.4))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7.2)
    ax.axis("off")
    ax.set_title("图9  大类资产投研的三层工作台")

    layers = [
        (0.4, 5.0, 11.2, 1.6, NAVY, "战略配置 SAA", "目标、约束、负债 → 中枢仓位\n60/40、风险平价、全天候、LDI"),
        (0.4, 2.9, 11.2, 1.6, STEEL, "战术配置 TAA", "宏观状态、股债性价比、动量与拥挤度 → 偏离中枢\n时钟、ERP分位、货币信用、政策窗口"),
        (0.4, 0.8, 11.2, 1.6, TEAL, "底层构建", "债券：利率/信用/久期/杠杆    股票：行业/风格/因子/个股\n工具：现券、国债期货、股指期货、ETF、基金、可转债"),
    ]
    for x, y, w, h, c, title, body in layers:
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", facecolor=c, edgecolor="none", alpha=0.92)
        ax.add_patch(box)
        ax.text(x + 0.3, y + h - 0.45, title, fontsize=14, color=WHITE, fontweight="bold")
        ax.text(x + 0.3, y + 0.35, body, fontsize=11, color=WHITE)
    save(fig, "fig09_research_stack.png")


def fig10_erp():
    fig, ax = plt.subplots(figsize=(10.2, 5.8))
    cats = ["10年期国债\n到期收益率", "沪深300\n股息率", "沪深300\n盈利收益率"]
    vals = [1.7, 2.6, 7.0]
    colors = [TEAL, GOLD, CORAL]
    bars = ax.bar(cats, vals, color=colors, width=0.5, zorder=3)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.15, f"{v:.1f}%", ha="center", color=NAVY, fontsize=12)
    ax.annotate(
        "",
        xy=(2, 7.0),
        xytext=(0, 1.7),
        arrowprops=dict(arrowstyle="<->", color=NAVY, lw=1.4),
    )
    ax.text(1.15, 4.6, "股债利差（EY−YTM）\n约 5.3 个百分点", ha="center", color=NAVY, fontsize=10)
    ax.set_ylabel("%")
    ax.set_title("图10  2026年8月中旬股债比价示意")
    ax.set_ylim(0, 8.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#D9D4CC", lw=0.7, zorder=0)
    ax.text(
        0.0,
        -0.18,
        "国债收益率约1.7%（市场报价，约2026年8月）；沪深300 PE-TTM约14.3倍（盈利收益率≈7.0%），股息率约2.5%–2.7%（value500、理杏仁等第三方估值，需与中证官方口径交叉核验）。",
        transform=ax.transAxes,
        fontsize=8,
        color=SLATE,
    )
    save(fig, "fig10_erp.png")


def fig11_regimes():
    fig, ax = plt.subplots(figsize=(11.2, 6.0))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6.4)
    ax.axis("off")
    ax.set_title("图11  股债相关性的三种宏观状态")

    blocks = [
        (0.3, 1.0, 3.6, 4.4, TEAL, "需求冲击\n负相关", "增长预期同步驱动：\n经济走弱 → 股跌债涨\n经济走强 → 股涨债跌\n债券是权益的对冲器"),
        (4.2, 1.0, 3.6, 4.4, CORAL, "供给/通胀冲击\n正相关", "贴现率同步上行：\n通胀超预期 → 股债双杀\n2022年全球即典型\n60/40失效窗口"),
        (8.1, 1.0, 3.6, 4.4, GOLD, "流动性/政策冲击\n同涨同跌或脱敏", "宽货币且缺信用：\n股债可同时上涨\n低利率约束下债市震荡\n对冲效率下降"),
    ]
    for x, y, w, h, c, title, body in blocks:
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.12", facecolor=c, edgecolor="none", alpha=0.9)
        ax.add_patch(box)
        ax.text(x + w / 2, y + h - 0.85, title, ha="center", fontsize=13, color=WHITE, fontweight="bold")
        ax.text(x + 0.25, y + 0.45, body, fontsize=10.5, color=WHITE)
    ax.text(
        6,
        0.35,
        "理论锚点：Campbell & Ammer (1993)；Ilmanen；Vanguard 对股债相关性体制的综述。中国证据见财信证券等对近20年样本的复盘。",
        ha="center",
        fontsize=8,
        color=SLATE,
    )
    save(fig, "fig11_regimes.png")


def fig12_pricing():
    fig, ax = plt.subplots(figsize=(11.2, 6.2))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6.6)
    ax.axis("off")
    ax.set_title("图12  同一套折现逻辑，两种现金流")

    boxes = [
        (0.4, 3.6, 5.4, 2.4, TEAL, "债券价格", "P = Σ CFt / (1 + r + s)^t\nCFt 几乎锁定（票息+本金）\nr 实际利率+通胀预期\ns 信用/流动性/期限溢价"),
        (6.2, 3.6, 5.4, 2.4, CORAL, "股票价格", "P = Σ DPt / (1 + r + ERP)^t\nDPt 是剩余索取权，可变\n盈利增长、分红率、回购\nERP 随风险偏好大幅波动"),
    ]
    for x, y, w, h, c, title, body in boxes:
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.12", facecolor=c, edgecolor="none", alpha=0.9)
        ax.add_patch(box)
        ax.text(x + 0.3, y + h - 0.5, title, fontsize=14, color=WHITE, fontweight="bold")
        ax.text(x + 0.3, y + 0.35, body, fontsize=11, color=WHITE)
    bottom = FancyBboxPatch((0.4, 0.55), 11.2, 2.5, boxstyle="round,pad=0.03,rounding_size=0.12", facecolor=NAVY, edgecolor="none", alpha=0.92)
    ax.add_patch(bottom)
    ax.text(0.7, 2.35, "共同驱动因子", fontsize=14, color=WHITE, fontweight="bold")
    ax.text(
        0.7,
        0.85,
        "增长（盈利/税收/违约） · 通胀（实际利率与名义利率） · 贴现率（货币政策、期限溢价、风险偏好）\n债券久期把利率映射为价格；股票“久期”更长，对ERP更敏感。可转债、银行二级资本债、永续债是中间态。",
        fontsize=11,
        color=WHITE,
    )
    save(fig, "fig12_pricing.png")


def fig13_triangle():
    fig, ax = plt.subplots(figsize=(8.8, 7.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 9.2)
    ax.axis("off")
    ax.set_title("图13  中国居民配置的股—债—房三角")
    tri = plt.Polygon([[5, 8.1], [1.3, 1.6], [8.7, 1.6]], closed=True, fill=False, edgecolor=NAVY, lw=2.2)
    ax.add_patch(tri)
    nodes = [
        (5, 8.1, CORAL, "股票\n剩余索取 · 高波动"),
        (1.3, 1.6, TEAL, "债券/存款\n合同现金流 · 低波动"),
        (8.7, 1.6, GOLD, "住房\n使用价值+杠杆资产"),
    ]
    for x, y, c, text in nodes:
        circ = Circle((x, y), 0.85, facecolor=c, edgecolor=NAVY, lw=1.0, zorder=3)
        ax.add_patch(circ)
        ax.text(x, y, text, ha="center", va="center", fontsize=9, color=WHITE, fontweight="bold", zorder=4)
    ax.text(3.1, 5.1, "风险偏好\n再定价", ha="center", color=NAVY, fontsize=10)
    ax.text(6.9, 5.1, "财富效应\n抵押信用", ha="center", color=NAVY, fontsize=10)
    ax.text(5.0, 0.85, "存款搬家 / 资产荒 / 比价", ha="center", color=NAVY, fontsize=10)
    ax.text(
        5,
        0.28,
        "Eurizon SLJ (2025)：中国股债相关性不能脱离房地产这个第三极来理解。",
        ha="center",
        fontsize=8,
        color=SLATE,
    )
    save(fig, "fig13_triangle.png")


def fig14_playbook():
    fig, ax = plt.subplots(figsize=(11.4, 6.6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7.0)
    ax.axis("off")
    ax.set_title("图14  机构股债配置的约束决定仓位，而不是观点决定仓位")
    rows = [
        (0.3, 5.15, "商业银行自营", "LCR/NSFR、利率债偏好、\n票息与资本占用", TEAL),
        (4.15, 5.15, "保险 / 养老金", "负债久期匹配、偿付能力、\n权益上限与会计分类", NAVY),
        (8.0, 5.15, "公募偏债 / 固收+", "回撤约束、排名、\n杠杆与流动性", STEEL),
        (0.3, 2.35, "公募偏股 / 指数", "基准偏离、风格暴露、\n交易拥挤", CORAL),
        (4.15, 2.35, "外资 / 全球组合", "汇率、指数纳入、\n与全球股债低相关", GOLD),
        (8.0, 2.35, "个人投资者", "持有期、杠杆、\n行为偏误是第一风险", SLATE),
    ]
    for x, y, title, body, c in rows:
        box = FancyBboxPatch((x, y), 3.55, 1.7, boxstyle="round,pad=0.03,rounding_size=0.1", facecolor=c, edgecolor="none", alpha=0.92)
        ax.add_patch(box)
        ax.text(x + 0.18, y + 1.18, title, fontsize=12, color=WHITE, fontweight="bold")
        ax.text(x + 0.18, y + 0.28, body, fontsize=10, color=WHITE)
    ax.text(
        6,
        0.45,
        "同一宏观观点，落到不同机构会变成完全不同的组合。先写约束，再写观点。",
        ha="center",
        fontsize=10,
        color=NAVY,
    )
    save(fig, "fig14_playbook.png")


if __name__ == "__main__":
    fig01_terminal_wealth()
    fig02_risk_return()
    fig03_bond_structure()
    fig04_social_financing()
    fig05_market_size()
    fig06_year_2025()
    fig07_sharpe()
    fig08_merrill_clock()
    fig09_research_stack()
    fig10_erp()
    fig11_regimes()
    fig12_pricing()
    fig13_triangle()
    fig14_playbook()
    print("done")
