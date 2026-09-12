#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate charts for the global capital-flow research note."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

FONT = font_manager.FontProperties(fname="/usr/share/fonts/truetype/wqy/wqy-microhei.ttc")
plt.rcParams["font.family"] = FONT.get_name()
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.facecolor"] = "white"
plt.rcParams["axes.facecolor"] = "#F7F8FA"
plt.rcParams["axes.edgecolor"] = "#D0D5DD"
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.color"] = "#E4E7EC"
plt.rcParams["grid.linewidth"] = 0.6
plt.rcParams["axes.titleweight"] = "bold"

NAVY = "#0F2C59"
BLUE = "#1B4F8A"
TEAL = "#0E7C7B"
AMBER = "#C27A2E"
RED = "#B42318"
SLATE = "#475467"


def _save(fig, name):
    path = FIG / name
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print("wrote", path)


def fig1_regimes():
    fig, ax = plt.subplots(figsize=(13.2, 4.8))
    eras = [
        (1820, 1870, "早期主权债\n与运河铁路", "#98A2B3"),
        (1870, 1914, "古典金本位\n伦敦为中心", TEAL),
        (1914, 1945, "战争与大萧条\n资本管制崩坏", RED),
        (1945, 1973, "布雷顿森林\n官方资本主导", AMBER),
        (1973, 2008, "金融全球化\n私人资本复兴", BLUE),
        (2008, 2026, "危机后重构\n再碎片化", NAVY),
    ]
    for start, end, label, color in eras:
        ax.barh(0, end - start, left=start, height=0.62, color=color, edgecolor="white", linewidth=1.2)
        ax.text((start + end) / 2, 0, label, ha="center", va="center", color="white",
                fontproperties=FONT, fontsize=10, fontweight="bold")
    ax.set_xlim(1820, 2028)
    ax.set_ylim(-0.7, 1.55)
    ax.set_yticks([])
    ax.set_xlabel("年份", fontproperties=FONT)
    ax.set_title("过去两百年全球资本流动的六个制度周期（示意）", fontproperties=FONT, fontsize=15, loc="left", color=NAVY)
    notes = [
        (1885, 0.95, "英国年均输出约4% GDP", TEAL),
        (1932, 0.95, "净流动接近冰点", RED),
        (1958, 0.95, "马歇尔计划/官方援助", AMBER),
        (1992, 0.95, "新兴市场私人资本浪潮", BLUE),
        (2016, 1.18, "美国再吸金、中国转净流出", NAVY),
    ]
    for x, y, t, c in notes:
        ax.text(x, y, t, ha="center", va="bottom", fontproperties=FONT, fontsize=8.5, color=c)
    ax.axvline(2000, color="#98A2B3", linestyle="--", linewidth=0.9)
    ax.text(2001, -0.52, "21世纪", fontproperties=FONT, fontsize=8, color=SLATE)
    ax.spines["left"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    _save(fig, "fig1_six_regimes.png")


def fig2_fdi_top20():
    labels = [
        "美国", "新加坡", "中国香港", "中国内地", "巴西", "英国", "德国", "加拿大",
        "阿联酋", "墨西哥", "印度", "澳大利亚", "沙特", "瑞典", "以色列",
        "俄罗斯", "法国", "印度尼西亚", "越南", "西班牙",
    ]
    y2025 = [277, 151, 116, 105, 77, 75, 75, 67, 48, 41, 39, 35, 33, 30, 26, 25, 22, 21, 20, 20]
    y2024 = [284, 136, 138, 116, 63, 16, 21, 67, 46, 38, 27, 51, 21, 22, 15, 2, 42, 25, 20, 34]
    y = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(12.4, 8.2))
    ax.barh(y + 0.18, y2024[::-1], height=0.34, color="#B9C7D6", label="2024")
    ax.barh(y - 0.18, y2025[::-1], height=0.34, color=BLUE, label="2025")
    ax.set_yticks(y)
    ax.set_yticklabels(labels[::-1], fontproperties=FONT)
    ax.set_xlabel("FDI 流入（十亿美元）", fontproperties=FONT)
    ax.set_title("2025年全球FDI流入前20名：资本高度集中于少数枢纽与大国", fontproperties=FONT, fontsize=14, loc="left", color=NAVY)
    ax.legend(prop=FONT, loc="lower right")
    ax.annotate("前20名合计占全球80%以上", xy=(260, 18.6), fontproperties=FONT, fontsize=9, color=SLATE)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    _save(fig, "fig2_fdi_top20_2025.png")


def fig3_china_us_fdi():
    years = list(range(2004, 2026))
    # China: BPM6 direct-investment liabilities (GAC / SAFE / AMRO compilation), 2025 GAC.
    china_bop = [62, 104, 124, 156, 172, 131, 244, 280, 241, 291, 268, 243, 175, 166, 235, 187, 253, 344, 190, 51, 43, 80]
    # US: UNCTAD / WIR selected years; 2021-2025 from WIR 2026 China factsheet.
    # Earlier years are UNCTAD/WIR commonly cited levels (rounded).
    us = {
        2004: 136, 2005: 105, 2006: 237, 2007: 216, 2008: 306, 2009: 144, 2010: 198,
        2011: 227, 2012: 161, 2013: 187, 2014: 107, 2015: 348, 2016: 457, 2017: 277,
        2018: 254, 2019: 246, 2020: 121, 2021: 386, 2022: 316, 2023: 263, 2024: 284, 2025: 277,
    }
    us_series = [us[y] for y in years]
    fig, ax = plt.subplots(figsize=(12.6, 5.6))
    ax.plot(years, us_series, color=BLUE, linewidth=2.4, marker="o", markersize=4.2, label="美国 FDI 流入（UNCTAD）")
    ax.plot(years, china_bop, color=RED, linewidth=2.4, marker="s", markersize=4.2, label="中国 FDI 负债（国际收支/BPM6）")
    ax.fill_between(years, china_bop, alpha=0.08, color=RED)
    ax.axvspan(2022, 2025.3, color="#FEE4E2", alpha=0.45)
    ax.text(2023.5, 410, "近五年：中国BPM6口径\nFDI流入塌陷", ha="center", fontproperties=FONT, fontsize=9, color=RED)
    ax.set_ylabel("十亿美元", fontproperties=FONT)
    ax.set_title("中美FDI流入：21世纪中国崛起，近五年出现历史级反转", fontproperties=FONT, fontsize=14, loc="left", color=NAVY)
    ax.legend(prop=FONT, loc="upper left")
    ax.set_xlim(2003.5, 2026)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.annotate("2021峰值 3440亿", xy=(2021, 344), xytext=(2016.2, 390),
                fontproperties=FONT, fontsize=8.5, color=RED,
                arrowprops=dict(arrowstyle="->", color=RED, lw=0.8))
    ax.annotate("中国为国际收支负债口径（含再投资收益与关联借贷）；美国为UNCTAD/WIR，2021–2025为WIR 2026，更早年份为历史公报约数。",
                xy=(0, -0.12), xycoords="axes fraction", fontproperties=FONT, fontsize=8, color=SLATE)
    _save(fig, "fig3_china_us_fdi.png")


def fig4_china_bop():
    years = ["2022", "2023", "2024", "2025"]
    ca = [402, 253, 424, 735]
    fa = [-211, -210, -496, -820]
    x = np.arange(len(years))
    fig, ax = plt.subplots(figsize=(11.4, 5.6))
    w = 0.36
    ax.bar(x - w / 2, ca, w, color=TEAL, label="经常账户顺差")
    ax.bar(x + w / 2, fa, w, color=AMBER, label="非储备金融账户（负值=净流出）")
    ax.axhline(0, color="#344054", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(years, fontproperties=FONT)
    ax.set_ylabel("十亿美元", fontproperties=FONT)
    ax.set_title("近四年中国国际收支：贸易顺差越做越大，资本项净流出同步放大", fontproperties=FONT, fontsize=14, loc="left", color=NAVY)
    ax.legend(prop=FONT, loc="upper left")
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    for i, v in enumerate(ca):
        ax.text(i - w / 2, v + 18, str(int(v)), ha="center", fontsize=8, color=TEAL, fontproperties=FONT)
    for i, v in enumerate(fa):
        ax.text(i + w / 2, v - 48, str(int(v)), ha="center", fontsize=8, color=AMBER, fontproperties=FONT)
    ax.set_ylim(-980, 900)
    ax.annotate("数据来源：国家外汇管理局《国际收支报告》",
                xy=(0, -0.10), xycoords="axes fraction", fontproperties=FONT, fontsize=8, color=SLATE)
    _save(fig, "fig4_china_ca_fa.png")


def fig5_stocks():
    # US NIIP (BEA, trillion USD, negative = net debtor)
    us_years = [2019, 2020, 2021, 2022, 2023, 2024, 2025]
    us_niip = [-11.0, -14.0, -18.1, -16.2, -19.85, -26.54, -27.54]
    # China net foreign assets (SAFE, trillion)
    cn_years = [2022, 2023, 2024, 2025]
    cn_nfa = [2.42, 2.91, 3.30, 4.07]
    fig, ax1 = plt.subplots(figsize=(12.0, 5.6))
    ax1.plot(us_years, us_niip, color=BLUE, marker="o", linewidth=2.4, label="美国净国际投资头寸（左轴，万亿美元）")
    ax1.set_ylabel("美国 NIIP（万亿美元）", fontproperties=FONT, color=BLUE)
    ax1.tick_params(axis="y", labelcolor=BLUE)
    ax2 = ax1.twinx()
    ax2.plot(cn_years, cn_nfa, color=RED, marker="s", linewidth=2.4, label="中国对外净资产（右轴，万亿美元）")
    ax2.set_ylabel("中国对外净资产（万亿美元）", fontproperties=FONT, color=RED)
    ax2.tick_params(axis="y", labelcolor=RED)
    ax2.grid(False)
    ax1.set_title("存量对照：美国净负债急剧扩大，中国净债权升至全球第二", fontproperties=FONT, fontsize=14, loc="left", color=NAVY)
    lines = ax1.get_lines() + ax2.get_lines()
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, prop=FONT, loc="center left")
    ax1.spines["top"].set_visible(False)
    ax2.spines["top"].set_visible(False)
    ax1.annotate("估值效应：美股大涨使外国持有的\n美国资产升值，NIIP更负", xy=(2024, -26.5), xytext=(2020.1, -24.8),
                 fontproperties=FONT, fontsize=8.5, color=BLUE,
                 arrowprops=dict(arrowstyle="->", color=BLUE, lw=0.8))
    _save(fig, "fig5_us_niip_china_nfa.png")


def fig6_treasuries():
    # TIC major holders, June 2026 vs Dec 2015-ish CRS comparison year
    countries = ["日本", "英国", "中国内地", "比利时", "加拿大", "卢森堡", "开曼群岛", "法国", "爱尔兰"]
    # Dec 2025 CRS: Japan 1185.5, UK 866, China 683.5, Belgium 477, Canada 468, Lux 435, Cayman 421, France 369, Ireland 341
    now = [1185.5, 866.0, 683.5, 477.3, 468.2, 435.1, 421.2, 368.9, 340.7]
    # CRS older column: Japan 1300.8, China 1040.3, UK 649.3, Ireland 334.5, Lux 327.8, ...
    old_map = {
        "日本": 1300.8, "英国": 649.3, "中国内地": 1040.3, "比利时": 271.6,
        "加拿大": 250, "卢森堡": 327.8, "开曼群岛": 262.8, "法国": 240, "爱尔兰": 334.5,
    }
    # Canada/France older values less certain; plot only the confirmed three plus current ranking.
    fig, ax = plt.subplots(figsize=(11.8, 5.8))
    y = np.arange(len(countries))
    ax.barh(y, now[::-1], color=BLUE)
    ax.set_yticks(y)
    ax.set_yticklabels(countries[::-1], fontproperties=FONT)
    ax.set_xlabel("持有美国国债（十亿美元，2025年12月）", fontproperties=FONT)
    ax.set_title("外国持有美国国债：中国已不再是第二大债主，官方储备去美元化可见", fontproperties=FONT, fontsize=13.5, loc="left", color=NAVY)
    ax.axvline(683.5, color=RED, linestyle="--", linewidth=0.9, alpha=0.7)
    ax.text(700, 6.3, "中国内地 6835亿\n较峰值约腰斩", fontproperties=FONT, fontsize=9, color=RED)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    _save(fig, "fig6_ust_holders.png")


def fig7_share_shift():
    labels = ["疫情前十年（至2019）", "2021–2023"]
    us = [18, 33]
    cn = [7, 3]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(8.6, 5.4))
    w = 0.32
    ax.bar(x - w / 2, us, w, color=BLUE, label="美国占全球跨境资本总流入份额")
    ax.bar(x + w / 2, cn, w, color=RED, label="中国占全球跨境资本总流入份额")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontproperties=FONT)
    ax.set_ylabel("%", fontproperties=FONT)
    ax.set_title("近五年最深刻的份额转移：美国吸走约三分之一全球资本", fontproperties=FONT, fontsize=13.5, loc="left", color=NAVY)
    ax.legend(prop=FONT, loc="upper left")
    ax.set_ylim(0, 42)
    for i, v in enumerate(us):
        ax.text(i - w / 2, v + 0.8, f"{v}%", ha="center", fontproperties=FONT, color=BLUE, fontsize=11, fontweight="bold")
    for i, v in enumerate(cn):
        ax.text(i + w / 2, v + 0.8, f"{v}%", ha="center", fontproperties=FONT, color=RED, fontsize=11, fontweight="bold")
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    fig.subplots_adjust(bottom=0.18)
    ax.annotate("数据来源：IMF，转引自 Bloomberg 对 IMF 测算的报道", xy=(0, -0.16), xycoords="axes fraction",
                fontproperties=FONT, fontsize=8, color=SLATE)
    _save(fig, "fig7_us_china_share.png")


if __name__ == "__main__":
    fig1_regimes()
    fig2_fdi_top20()
    fig3_china_us_fdi()
    fig4_china_bop()
    fig5_stocks()
    fig6_treasuries()
    fig7_share_shift()
    print("done")
