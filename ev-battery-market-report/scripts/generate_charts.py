#!/usr/bin/env python3
"""Generate charts for the EV battery market investment briefing."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
CHARTS = ROOT / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)

FONT = "WenQuanYi Micro Hei"
font_manager.fontManager.addfont("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc")
plt.rcParams.update(
    {
        "font.family": FONT,
        "font.size": 11,
        "axes.titlesize": 14,
        "axes.labelsize": 11,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": "#1f2937",
        "axes.grid": False,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "text.color": "#111827",
        "axes.labelcolor": "#111827",
        "xtick.color": "#374151",
        "ytick.color": "#374151",
        "savefig.dpi": 180,
        "savefig.bbox": "tight",
        "savefig.facecolor": "white",
    }
)

NAVY = "#0f3d5e"
TEAL = "#0e7490"
AMBER = "#d97706"
SLATE = "#64748b"
RED = "#b91c1c"
GREEN = "#15803d"
STEEL = "#334155"
LIGHT = "#e5e7eb"
CHINA = "#b45309"
KOREA = "#0369a1"
JAPAN = "#7c3aed"
OTHER = "#94a3b8"


def save(fig, name: str) -> None:
    path = CHARTS / name
    fig.savefig(path, pad_inches=0.25)
    plt.close(fig)
    print(f"wrote {path}")


def fig01_market_share_2025() -> None:
    labels = [
        "宁德时代",
        "比亚迪",
        "LGES",
        "中创新航",
        "国轩高科",
        "SK On",
        "松下",
        "亿纬锂能",
        "三星SDI",
        "蜂巢能源",
        "其他",
    ]
    shares = [39.2, 16.4, 9.2, 5.3, 4.5, 3.7, 3.7, 2.6, 2.4, 2.4, 10.5]
    colors = [
        CHINA,
        CHINA,
        KOREA,
        CHINA,
        CHINA,
        KOREA,
        JAPAN,
        CHINA,
        KOREA,
        CHINA,
        OTHER,
    ]
    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    y = np.arange(len(labels))[::-1]
    bars = ax.barh(y, shares, color=colors, height=0.68, zorder=3)
    ax.set_yticks(y, labels)
    ax.set_xlabel("全球装机份额（%）")
    ax.set_title("2025年全球动力电池装机份额（SNE Research）")
    ax.set_xlim(0, 46)
    ax.axvline(0, color="#111827", lw=0.8)
    ax.grid(axis="x", color="#e5e7eb", lw=0.8, zorder=0)
    for bar, val in zip(bars, shares):
        ax.text(
            val + 0.5,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}%",
            va="center",
            fontsize=10,
            color="#111827",
        )
    from matplotlib.patches import Patch

    ax.legend(
        handles=[
            Patch(facecolor=CHINA, label="中国企业"),
            Patch(facecolor=KOREA, label="韩国企业"),
            Patch(facecolor=JAPAN, label="日本企业"),
            Patch(facecolor=OTHER, label="其他"),
        ],
        loc="lower right",
        frameon=False,
    )
    ax.text(
        0,
        -1.55,
        "资料：SNE Research，2025年全球动力电池装机 1,187 GWh。宁德时代 + 比亚迪合计 55.6%。",
        fontsize=8.5,
        color=SLATE,
    )
    save(fig, "fig01_market_share_2025.png")


def fig02_share_shift() -> None:
    names = ["宁德时代", "比亚迪", "LGES", "中创新航", "国轩高科", "SK On", "松下"]
    y2025 = [39.2, 16.4, 9.2, 5.3, 4.5, 3.7, 3.7]
    y2026 = [40.2, 14.4, 8.7, 5.1, 4.6, 3.4, 3.2]
    x = np.arange(len(names))
    w = 0.36
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    b1 = ax.bar(x - w / 2, y2025, w, color=NAVY, label="2025全年")
    b2 = ax.bar(x + w / 2, y2026, w, color=AMBER, label="2026年1–5月")
    ax.set_xticks(x, names)
    ax.set_ylabel("全球装机份额（%）")
    ax.set_title("头部厂商份额变动：2025全年 vs 2026年1–5月")
    ax.grid(axis="y", color="#e5e7eb", lw=0.8, zorder=0)
    ax.legend(frameon=False, loc="upper right")
    ax.set_ylim(0, 48)
    for bars in (b1, b2):
        for bar in bars:
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                h + 0.6,
                f"{h:.1f}",
                ha="center",
                va="bottom",
                fontsize=8.5,
            )
    ax.text(
        0,
        -7.2,
        "资料：SNE Research。2026年前五个月全球装机 469.2 GWh，同比 +16.3%；中国企业合计约 72.6%。",
        fontsize=8.5,
        color=SLATE,
    )
    save(fig, "fig02_share_shift.png")


def fig03_pack_price() -> None:
    years = [2010, 2020, 2022, 2023, 2024, 2025]
    prices = [1436, 137, 151, 139, 115, 108]
    fig, ax = plt.subplots(figsize=(10.2, 5.6))
    ax.plot(years, prices, color=NAVY, lw=2.4, marker="o", ms=7, zorder=3)
    ax.fill_between(years, prices, color=NAVY, alpha=0.08)
    ax.set_title("锂离子电池包均价（BloombergNEF）")
    ax.set_ylabel("美元 / kWh（名义）")
    ax.set_xticks(years)
    ax.grid(axis="y", color="#e5e7eb", lw=0.8)
    ax.set_ylim(0, 1600)
    for x, y in zip(years, prices):
        offset = 70 if y > 200 else 18
        ax.annotate(
            f"${y}",
            (x, y),
            textcoords="offset points",
            xytext=(0, offset if y < 200 else -18),
            ha="center",
            fontsize=10,
            color=NAVY,
        )
    ax.annotate(
        "2022年金属价格冲击\n出现唯一年度上涨",
        xy=(2022, 151),
        xytext=(2016.2, 420),
        arrowprops=dict(arrowstyle="->", color=SLATE),
        fontsize=9,
        color=STEEL,
    )
    ax.text(
        2010,
        -220,
        "资料：BloombergNEF 锂离子电池价格调查。2025年纯电车电池包均价约 99 美元/kWh，储能约 70 美元/kWh。",
        fontsize=8.5,
        color=SLATE,
    )
    save(fig, "fig03_pack_price.png")


def fig04_regional_price() -> None:
    regions = ["中国", "北美", "欧洲"]
    p2022 = [121, 151, 161]
    p2025 = [84, 120, 129]
    x = np.arange(len(regions))
    w = 0.34
    fig, ax = plt.subplots(figsize=(8.8, 5.6))
    ax.bar(x - w / 2, p2022, w, color=SLATE, label="2022")
    bars = ax.bar(x + w / 2, p2025, w, color=[CHINA, NAVY, TEAL], label="2025")
    ax.set_xticks(x, regions)
    ax.set_ylabel("电池包均价（美元 / kWh）")
    ax.set_title("区域价差扩大：中国相对北美、欧洲更便宜")
    ax.legend(frameon=False)
    ax.grid(axis="y", color="#e5e7eb", lw=0.8)
    ax.set_ylim(0, 200)
    for i, (a, b) in enumerate(zip(p2022, p2025)):
        ax.text(i - w / 2, a + 4, f"{a}", ha="center", fontsize=9, color=STEEL)
        ax.text(i + w / 2, b + 4, f"{b}", ha="center", fontsize=9)
    ax.annotate(
        "2025年中国比北美低约30%、\n比欧洲低约35%（IEA）",
        xy=(0.35, 84),
        xytext=(0.85, 175),
        arrowprops=dict(arrowstyle="->", color=SLATE),
        fontsize=9,
        color=STEEL,
    )
    ax.text(
        -0.45,
        -28,
        "资料：IEA《全球电动汽车展望 2026》；BloombergNEF。区域均价含本地生产与进口。",
        fontsize=8.5,
        color=SLATE,
    )
    save(fig, "fig04_regional_price.png")


def fig05_chemistry() -> None:
    years = np.array([2020, 2023, 2024, 2025])
    lfp = np.array([9, 43, 50, 55])
    other = 100 - lfp
    fig, ax = plt.subplots(figsize=(9.6, 5.6))
    ax.stackplot(years, lfp, other, colors=[AMBER, "#cbd5e1"], labels=["LFP（含LMFP）", "三元及其他（NMC/NCA等）"])
    ax.plot(years, lfp, color="#9a3412", lw=2, marker="o")
    for x, y in zip(years, lfp):
        ax.text(x, y + 3.2, f"{y}%", ha="center", fontsize=10, color="#9a3412")
    ax.set_ylim(0, 100)
    ax.set_xlim(2019.7, 2025.4)
    ax.set_xticks(years)
    ax.set_ylabel("全球动力电池装机占比（%）")
    ax.set_title("磷酸铁锂已超过全球动力电池市场一半")
    ax.legend(loc="upper left", frameon=False)
    ax.axhline(50, color=SLATE, ls="--", lw=0.9, alpha=0.7)
    ax.text(
        2019.7,
        -16,
        "资料：IEA GEO 2026。中国 2025 年 LFP 装机占比约 79%–81%；欧盟约 10%；美国约 5% 且受关税与溯源规则压制。",
        fontsize=8.5,
        color=SLATE,
    )
    save(fig, "fig05_chemistry.png")


def fig06_concentration() -> None:
    stages = [
        "电芯名义产能",
        "动力电池装机\n（中国企业）",
        "LFP正极材料",
        "石墨负极",
        "锂精炼",
        "钴精炼",
        "电池回收产能",
    ]
    china = [80, 75, 98, 90, 65, 70, 85]
    fig, ax = plt.subplots(figsize=(10.6, 5.8))
    y = np.arange(len(stages))[::-1]
    ax.barh(y, china, color=CHINA, height=0.62, zorder=3)
    ax.barh(y, [100 - v for v in china], left=china, color="#e5e7eb", height=0.62, zorder=2)
    ax.set_yticks(y, stages)
    ax.set_xlim(0, 100)
    ax.set_xlabel("中国占全球份额（%）")
    ax.set_title("供应链最脆弱的环节：中游材料高度集中于中国")
    ax.axvline(50, color=SLATE, ls="--", lw=0.9)
    for yi, v in zip(y, china):
        ax.text(min(v - 3, 92), yi, f"{v}%", va="center", ha="right", color="white", fontsize=10)
    ax.text(
        0,
        -1.45,
        "资料：IEA GEO 2026、RMI。LFP正极、前驱体与石墨负极是非中国产能最难补齐的环节；2025年10月出口管制曾覆盖部分材料与设备。",
        fontsize=8.5,
        color=SLATE,
    )
    save(fig, "fig06_concentration.png")


def fig07_capacity_demand() -> None:
    labels = ["2025实际", "2030 STEPS", "2035 STEPS"]
    ev_demand = [1.2, 3.0, 4.7]
    nameplate_2025 = 4.0
    fig, ax = plt.subplots(figsize=(9.4, 5.7))
    x = np.arange(len(labels))
    bars = ax.bar(x, ev_demand, color=[NAVY, TEAL, AMBER], width=0.55, zorder=3)
    ax.axhline(nameplate_2025, color=RED, ls="--", lw=1.4, label="2025年末全球名义产能 ≈ 4 TWh")
    ax.set_xticks(x, labels)
    ax.set_ylabel("TWh")
    ax.set_title("产能已经过剩，需求要到2030年代中期才追上当前名义产能")
    ax.set_ylim(0, 5.4)
    ax.legend(frameon=False, loc="upper left")
    ax.grid(axis="y", color="#e5e7eb", lw=0.8)
    for bar, v in zip(bars, ev_demand):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.08, f"{v} TWh", ha="center", fontsize=10)
    ax.annotate(
        "中国约占名义产能 80%\n欧美合计约 12–14%",
        xy=(0, 4.0),
        xytext=(0.55, 4.55),
        arrowprops=dict(arrowstyle="->", color=RED),
        fontsize=9,
        color=RED,
    )
    ax.text(
        -0.45,
        -0.85,
        "资料：IEA GEO 2026。STEPS 为既定政策情景；2035 年 CPS 约 4 TWh、STEPS 近 5 TWh。名义产能爬坡通常需 5 年以上才接近满产。",
        fontsize=8.5,
        color=SLATE,
    )
    save(fig, "fig07_capacity_demand.png")


def fig08_regional_deployment() -> None:
    labels = ["中国", "欧盟", "美国", "其他新兴市场", "其余发达市场"]
    shares = [60, 15, 10, 6, 9]
    colors = [CHINA, TEAL, NAVY, AMBER, OTHER]
    fig, ax = plt.subplots(figsize=(8.6, 5.8))
    wedges, texts, autotexts = ax.pie(
        shares,
        labels=labels,
        colors=colors,
        autopct="%1.0f%%",
        startangle=90,
        pctdistance=0.72,
        wedgeprops=dict(width=0.46, edgecolor="white", linewidth=1.5),
    )
    for t in texts:
        t.set_fontsize(11)
    for t in autotexts:
        t.set_fontsize(10)
        t.set_color("white")
        t.set_fontweight("bold")
    ax.set_title("2025年全球动力电池装机的区域结构（1.2 TWh）")
    ax.text(
        0,
        -1.28,
        "资料：IEA GEO 2026。电动卡车贡献约 8% 装机（同比翻倍以上），乘用车仍占 85% 以上。",
        ha="center",
        fontsize=8.5,
        color=SLATE,
    )
    save(fig, "fig08_regional_deployment.png")


def fig09_margin_split() -> None:
    names = ["宁德时代 2025\n营业利润率", "松下能源 2025\n营业利润率", "SK On\n近年经营", "LGES 2025 EBIT\n剔除美国税收抵免"]
    values = [18, 14, -4, -3]
    colors = [GREEN, GREEN, RED, RED]
    fig, ax = plt.subplots(figsize=(9.8, 5.8))
    bars = ax.bar(names, values, color=colors, width=0.55, zorder=3)
    ax.axhline(0, color="#111827", lw=0.9)
    ax.set_ylabel("利润率或经营方向（示意）")
    ax.set_title("同样卖电芯，利润结构已经分化")
    ax.grid(axis="y", color="#e5e7eb", lw=0.8)
    ax.set_ylim(-10, 24)
    labels_on = ["18%", "14%", "持续亏损", "约 -2 亿美元"]
    for bar, lab, val in zip(bars, labels_on, values):
        y = val + (0.7 if val >= 0 else -0.5)
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            y,
            lab,
            ha="center",
            va="bottom" if val >= 0 else "top",
            fontsize=10,
        )
    ax.text(
        1.55,
        8.5,
        "LGES 含税收抵免后转为正利润\n（IEA：政策是盈亏分界）",
        fontsize=9,
        color=TEAL,
        ha="center",
    )
    ax.text(
        -0.45,
        -14.5,
        "资料：IEA GEO 2026。宁德时代 2020–2024 年营业利润率 10%–15%，2025 年 18%。SK On 近年反复录得经营亏损。LGES 柱高为方向示意，不是公开利润率。",
        fontsize=8.5,
        color=SLATE,
    )
    save(fig, "fig09_margin_split.png")


def fig10_investment_map() -> None:
    """Qualitative heatmap of investment attractiveness vs risk."""
    rows = [
        "中国一线电芯（宁德时代）",
        "中国二线电芯（国轩/中创/亿纬）",
        "韩日电芯（LGES/松下/SDI）",
        "欧美纯电芯初创",
        "LFP正极（湖南裕能等）",
        "石墨负极 / 电解液 / 隔膜",
        "锂资源与精炼",
        "镍（印尼HPAL）",
        "钴",
        "钠离子（规模化初期）",
        "全固态（量产前）",
        "回收（中国闭环）",
        "回收（欧美独立商）",
        "储能用LFP电芯",
    ]
    # attractiveness 1-5, risk 1-5
    attract = [5, 4, 3, 1, 3, 3, 4, 3, 2, 3, 2, 4, 2, 5]
    risk = [3, 4, 4, 5, 4, 4, 4, 4, 4, 4, 5, 3, 5, 3]
    fig, ax = plt.subplots(figsize=(10.4, 7.2))
    ax.set_xlim(0.4, 5.6)
    ax.set_ylim(0.4, 5.6)
    ax.set_xlabel("商业吸引力（规模、成本、客户绑定）  →")
    ax.set_ylabel("风险（政策、价格、技术、产能）  →")
    ax.set_title("投资地图：高吸引力并不等于低风险")
    ax.axvline(3, color="#e5e7eb", lw=1)
    ax.axhline(3, color="#e5e7eb", lw=1)
    ax.fill_between([3, 5.6], 0.4, 3, color="#dcfce7", alpha=0.45, zorder=0)
    ax.fill_between([0.4, 3], 3, 5.6, color="#fee2e2", alpha=0.4, zorder=0)
    ax.fill_between([3, 5.6], 3, 5.6, color="#fef3c7", alpha=0.45, zorder=0)
    ax.fill_between([0.4, 3], 0.4, 3, color="#e2e8f0", alpha=0.35, zorder=0)
    ax.text(4.3, 1.0, "相对更可配置", ha="center", color=GREEN, fontsize=10)
    ax.text(1.7, 5.15, "高风险、低赔率", ha="center", color=RED, fontsize=10)
    ax.text(4.3, 5.15, "高赔率但波动大", ha="center", color=AMBER, fontsize=10)
    ax.text(1.7, 1.0, "防守不足", ha="center", color=SLATE, fontsize=10)

    # jitter labels
    offsets = {
        "中国一线电芯（宁德时代）": (0.15, 0.22),
        "中国二线电芯（国轩/中创/亿纬）": (0.05, -0.28),
        "韩日电芯（LGES/松下/SDI）": (0.15, 0.22),
        "欧美纯电芯初创": (0.0, 0.22),
        "LFP正极（湖南裕能等）": (0.2, -0.28),
        "石墨负极 / 电解液 / 隔膜": (-0.05, 0.22),
        "锂资源与精炼": (0.15, 0.22),
        "镍（印尼HPAL）": (0.2, -0.28),
        "钴": (0.0, 0.22),
        "钠离子（规模化初期）": (0.2, -0.28),
        "全固态（量产前）": (0.15, 0.22),
        "回收（中国闭环）": (0.15, 0.22),
        "回收（欧美独立商）": (0.0, -0.28),
        "储能用LFP电芯": (0.15, -0.28),
    }
    for name, a, r in zip(rows, attract, risk):
        ax.scatter(a, r, s=70, color=NAVY, zorder=4)
        dx, dy = offsets.get(name, (0.12, 0.18))
        ax.text(a + dx, r + dy, name, fontsize=8.2, color=STEEL, zorder=4)
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.text(
        0.4,
        -0.15,
        "示意框架，非量化评分。吸引力综合规模、成本位置与客户结构；风险综合政策、价格周期、技术路线与产能利用率。",
        fontsize=8.5,
        color=SLATE,
    )
    save(fig, "fig10_investment_map.png")


def fig11_value_chain() -> None:
    fig, ax = plt.subplots(figsize=(11.4, 6.4))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7)
    ax.axis("off")
    ax.set_title("动力电池价值链：投资需要按环节拆开看", pad=12)

    boxes = [
        (0.3, 4.6, 2.2, 1.6, "上游资源", "锂：雅保/SQM/\n赣锋/天齐\n镍：印尼HPAL\n钴：刚果+嘉能可", CHINA),
        (3.0, 4.6, 2.4, 1.6, "中游材料", "正极：湖南裕能\n负极：贝特瑞\n电解液：天赐\n隔膜：恩捷", AMBER),
        (5.9, 4.6, 2.4, 1.6, "电芯与系统", "宁德时代 / 比亚迪\nLGES / 松下\nCTP / CTC / BMS", NAVY),
        (8.8, 4.6, 2.6, 1.6, "下游需求", "乘用车 OEM\n电动卡车\n储能 / 数据中心", TEAL),
        (3.0, 1.5, 2.4, 1.5, "设备与工艺", "先导智能等\n良率>90%才赚钱", SLATE),
        (5.9, 1.5, 2.4, 1.5, "回收闭环", "邦普 / 红木材料\n废料主导至2030s", GREEN),
        (8.8, 1.5, 2.6, 1.5, "规则与地缘", "IRA/FEOC、欧盟电池法\n出口管制、关税", RED),
    ]
    for x, y, w, h, title, body, color in boxes:
        rect = FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.03,rounding_size=0.12",
            facecolor="white",
            edgecolor=color,
            linewidth=2.0,
        )
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h - 0.32, title, ha="center", va="top", fontsize=12, color=color, fontweight="bold")
        ax.text(x + w / 2, y + h - 0.62, body, ha="center", va="top", fontsize=9, color=STEEL)

    # arrows
    ax.annotate("", xy=(3.0, 5.4), xytext=(2.5, 5.4), arrowprops=dict(arrowstyle="->", color=STEEL, lw=1.6))
    ax.annotate("", xy=(5.9, 5.4), xytext=(5.4, 5.4), arrowprops=dict(arrowstyle="->", color=STEEL, lw=1.6))
    ax.annotate("", xy=(8.8, 5.4), xytext=(8.3, 5.4), arrowprops=dict(arrowstyle="->", color=STEEL, lw=1.6))
    ax.annotate("", xy=(7.1, 4.6), xytext=(7.1, 3.05), arrowprops=dict(arrowstyle="->", color=STEEL, lw=1.2))
    ax.annotate("", xy=(4.2, 4.6), xytext=(4.2, 3.05), arrowprops=dict(arrowstyle="->", color=STEEL, lw=1.2))

    ax.text(6.0, 0.35, "真正决定投资回报的，往往不是“电池需求会不会增长”，而是你处在哪一段、以什么成本、受哪套规则约束。", ha="center", fontsize=9.5, color=STEEL)
    save(fig, "fig11_value_chain.png")


def main() -> None:
    fig01_market_share_2025()
    fig02_share_shift()
    fig03_pack_price()
    fig04_regional_price()
    fig05_chemistry()
    fig06_concentration()
    fig07_capacity_demand()
    fig08_regional_deployment()
    fig09_margin_split()
    fig10_investment_map()
    fig11_value_chain()


if __name__ == "__main__":
    main()
