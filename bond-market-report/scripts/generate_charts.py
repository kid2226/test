#!/usr/bin/env python3
"""Generate publication-quality charts for the US-China bond market report."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CHARTS = ROOT / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)

FONT_PATH = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
font_manager.fontManager.addfont(FONT_PATH)
plt.rcParams.update(
    {
        "font.family": "WenQuanYi Micro Hei",
        "axes.unicode_minus": False,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": "#2c3e50",
        "axes.labelcolor": "#1b2a4a",
        "xtick.color": "#1b2a4a",
        "ytick.color": "#1b2a4a",
        "text.color": "#1b2a4a",
        "axes.grid": True,
        "grid.color": "#d9e2ec",
        "grid.linewidth": 0.7,
        "axes.titlesize": 14,
        "axes.labelsize": 11,
        "figure.dpi": 140,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
        "savefig.facecolor": "white",
    }
)

NAVY = "#1b365d"
TEAL = "#0e7c7b"
CRIMSON = "#c0392b"
GOLD = "#c9a227"
SLATE = "#5d6d7e"
ORANGE = "#d35400"
GREEN = "#1e8449"
PURPLE = "#6c3483"


def _source(ax, text: str) -> None:
    ax.figure.text(
        0.01,
        0.005,
        text,
        fontsize=8,
        color=SLATE,
        ha="left",
        va="bottom",
    )


def load_ust() -> pd.DataFrame:
    df = pd.read_csv(DATA / "fred_ust_yields.csv")
    df["observation_date"] = pd.to_datetime(df["observation_date"])
    for col in ["DGS2", "DGS10", "DGS30", "T10Y2Y"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["s2s30"] = df["DGS30"] - df["DGS2"]
    return df


def load_tips() -> pd.DataFrame:
    df = pd.read_csv(DATA / "fred_tips_breakeven.csv")
    df["observation_date"] = pd.to_datetime(df["observation_date"])
    for col in ["T10YIE", "DFII10", "DFII30"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def fig01_four_regimes() -> None:
    fig, axes = plt.subplots(2, 2, figsize=(11.2, 8.6))
    fig.suptitle("收益率曲线四种形态：牛陡、熊陡、牛平、熊平", fontsize=16, fontweight="bold", y=0.98)

    tenors = np.array([2, 10])
    specs = [
        ("牛陡 Bull Steepener", "短端下行更快（央行降息/衰退定价）\n利差走阔，债券价格整体上涨", GREEN, [3.8, 4.2], [2.6, 3.8]),
        ("熊陡 Bear Steepener", "长端上行更快（期限溢价/财政担忧）\n利差走阔，债券价格整体下跌", CRIMSON, [3.6, 4.0], [3.7, 5.1]),
        ("牛平 Bull Flattener", "长端下行更快（避险/增长放缓）\n利差收窄，债券价格整体上涨", TEAL, [3.8, 4.6], [3.5, 3.8]),
        ("熊平 Bear Flattener", "短端上行更快（央行加息周期）\n利差收窄，常通向倒挂", ORANGE, [3.2, 4.4], [4.6, 4.7]),
    ]
    for ax, (title, note, color, before, after) in zip(axes.ravel(), specs):
        ax.plot(tenors, before, "--o", color=SLATE, linewidth=2, markersize=8, label="变动前")
        ax.plot(tenors, after, "-o", color=color, linewidth=2.6, markersize=9, label="变动后")
        ax.annotate(
            "",
            xy=(2.0, after[0]),
            xytext=(2.0, before[0]),
            arrowprops=dict(arrowstyle="->", color=color, lw=1.6),
        )
        ax.annotate(
            "",
            xy=(10.0, after[1]),
            xytext=(10.0, before[1]),
            arrowprops=dict(arrowstyle="->", color=color, lw=1.6),
        )
        ax.set_title(title, color=color, fontsize=13, pad=8)
        ax.set_xticks([2, 10])
        ax.set_xticklabels(["2年", "10年"])
        ax.set_ylabel("收益率（%）")
        ax.set_ylim(2.2, 5.6)
        ax.text(6, 2.45, note, ha="center", va="bottom", fontsize=9, color="#334155")
        ax.legend(frameon=False, loc="upper left", fontsize=9)

    _source(axes[1, 0], "示意：纵轴为收益率，箭头方向表示该期限收益率变动。牛/熊以债券价格涨跌定义，陡/平以期限利差走阔/收窄定义。")
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig.savefig(CHARTS / "fig01_four_regimes.png")
    plt.close(fig)


def fig02_us_curve_snapshots() -> None:
    fig, ax = plt.subplots(figsize=(11.2, 6.4))
    tenors = np.array([1 / 12, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30])
    labels = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]

    # Treasury par curve snapshots (official CMT)
    curves = {
        "2023-10-19 深度倒挂后期": dict(
            y=[5.58, 5.60, 5.56, 5.44, 5.14, 5.01, 4.95, 5.00, 4.98, 5.30, 5.11],
            color=ORANGE,
            ls="--",
        ),
        "2025-08-21 一年前": dict(
            y=[None, None, None, None, 3.79, None, None, None, 4.33, None, 4.92],
            color=SLATE,
            ls=":",
        ),
        "2026-01-02 年初": dict(
            y=[None, None, None, None, 3.47, None, None, None, 4.19, None, 4.86],
            color=TEAL,
            ls="-.",
        ),
        "2026-08-21 最新": dict(
            y=[3.80, 3.88, 3.95, 4.03, 4.24, 4.31, 4.43, 4.57, 4.74, 5.25, 5.27],
            color=CRIMSON,
            ls="-",
        ),
    }

    for name, spec in curves.items():
        y = np.array(spec["y"], dtype=float)
        mask = ~np.isnan(y)
        ax.plot(
            tenors[mask],
            y[mask],
            spec["ls"],
            color=spec["color"],
            linewidth=2.4 if "最新" in name else 1.8,
            marker="o",
            markersize=6 if mask.sum() > 5 else 7,
            label=name,
        )

    ax.axhline(0, color="#94a3b8", lw=0.6)
    ax.set_xscale("symlog", linthresh=1)
    ax.set_xticks(tenors)
    ax.set_xticklabels(labels)
    ax.set_ylabel("到期收益率（%）")
    ax.set_title("美国国债收益率曲线：从倒挂到长端熊陡", fontsize=15, fontweight="bold")
    ax.legend(frameon=False, loc="lower right")
    ax.set_ylim(3.2, 5.9)
    ax.annotate(
        "短端受联邦基金利率锚定\n3.50%–3.75%",
        xy=(0.25, 3.88),
        xytext=(0.35, 5.35),
        fontsize=9,
        arrowprops=dict(arrowstyle="->", color=NAVY),
        color=NAVY,
    )
    ax.annotate(
        "30年期 5.27%\n2007年以来高位附近",
        xy=(30, 5.27),
        xytext=(8.5, 5.65),
        fontsize=9,
        arrowprops=dict(arrowstyle="->", color=CRIMSON),
        color=CRIMSON,
    )
    _source(
        ax,
        "数据：美国财政部每日国债平价曲线 / 美联储 H.15（FRED DGS2/DGS10/DGS30）。2025-08-21、2026-01-02 仅标示 2Y/10Y/30Y。",
    )
    fig.savefig(CHARTS / "fig02_us_yield_curve_snapshots.png")
    plt.close(fig)


def fig03_us_yields_timeseries(ust: pd.DataFrame) -> None:
    df = ust[(ust["observation_date"] >= "2022-01-01") & (ust["observation_date"] <= "2026-08-20")].copy()
    fig, ax = plt.subplots(figsize=(11.2, 6.2))
    ax.plot(df["observation_date"], df["DGS2"], color=TEAL, lw=1.5, label="2年期")
    ax.plot(df["observation_date"], df["DGS10"], color=NAVY, lw=1.7, label="10年期")
    ax.plot(df["observation_date"], df["DGS30"], color=CRIMSON, lw=1.7, label="30年期")
    ax.axhspan(3.50, 3.75, color=GOLD, alpha=0.18, label="当前联邦基金目标区间")
    ax.set_title("美国国债关键期限收益率（2022–2026）", fontsize=15, fontweight="bold")
    ax.set_ylabel("收益率（%）")
    ax.legend(frameon=False, ncol=4, loc="upper left")
    ax.annotate("加息周期\n熊平/倒挂", xy=(pd.Timestamp("2023-07-03"), 4.94), xytext=(pd.Timestamp("2022-03-01"), 5.55),
                fontsize=8.5, arrowprops=dict(arrowstyle="->", color=ORANGE), color=ORANGE)
    ax.annotate("2026年7–8月\n长端熊陡", xy=(pd.Timestamp("2026-08-17"), 5.31), xytext=(pd.Timestamp("2025-06-01"), 5.55),
                fontsize=8.5, arrowprops=dict(arrowstyle="->", color=CRIMSON), color=CRIMSON)
    _source(ax, "数据：FRED DGS2 / DGS10 / DGS30，截至 2026-08-20。阴影为 2026 年 7 月 FOMC 维持的联邦基金目标区间 3.50%–3.75%。")
    fig.savefig(CHARTS / "fig03_us_yields_2022_2026.png")
    plt.close(fig)


def fig04_us_spreads(ust: pd.DataFrame) -> None:
    df = ust[(ust["observation_date"] >= "2022-01-01") & (ust["observation_date"] <= "2026-08-20")].copy()
    fig, ax = plt.subplots(figsize=(11.2, 6.2))
    ax.fill_between(df["observation_date"], 0, df["T10Y2Y"] * 100, where=df["T10Y2Y"] < 0,
                    color=ORANGE, alpha=0.25, interpolate=True, label="10Y–2Y 倒挂区间")
    ax.plot(df["observation_date"], df["T10Y2Y"] * 100, color=NAVY, lw=1.7, label="10Y–2Y（bp）")
    ax.plot(df["observation_date"], df["s2s30"] * 100, color=CRIMSON, lw=1.5, label="30Y–2Y（bp）")
    ax.axhline(0, color="#334155", lw=1)
    ax.set_title("美国国债期限利差：倒挂解除后的再陡峭化", fontsize=15, fontweight="bold")
    ax.set_ylabel("利差（基点）")
    ax.legend(frameon=False, loc="lower right")
    ax.annotate("最深倒挂\n–108bp\n(2023-07-03)", xy=(pd.Timestamp("2023-07-03"), -108),
                xytext=(pd.Timestamp("2022-04-01"), -70), fontsize=8.5,
                arrowprops=dict(arrowstyle="->", color=ORANGE), color=ORANGE)
    ax.annotate("2026-08-17\n2s30s ≈113bp", xy=(pd.Timestamp("2026-08-17"), 112),
                xytext=(pd.Timestamp("2025-02-01"), 130), fontsize=8.5,
                arrowprops=dict(arrowstyle="->", color=CRIMSON), color=CRIMSON)
    _source(ax, "数据：FRED T10Y2Y、DGS30–DGS2。正值表示正向曲线，负值表示倒挂。")
    fig.savefig(CHARTS / "fig04_us_term_spreads.png")
    plt.close(fig)


def fig05_july_bear_steepener(ust: pd.DataFrame) -> None:
    df = ust[(ust["observation_date"] >= "2026-07-01") & (ust["observation_date"] <= "2026-08-20")].copy()
    fig, ax1 = plt.subplots(figsize=(11.2, 6.2))
    ax1.plot(df["observation_date"], df["DGS2"], color=TEAL, lw=2.1, marker="o", markersize=3.5, label="2年期（左轴）")
    ax1.plot(df["observation_date"], df["DGS10"], color=NAVY, lw=2.0, marker="o", markersize=3.5, label="10年期（左轴）")
    ax1.plot(df["observation_date"], df["DGS30"], color=CRIMSON, lw=2.1, marker="o", markersize=3.5, label="30年期（左轴）")
    ax1.axvline(pd.Timestamp("2026-07-29"), color=GOLD, ls="--", lw=1.4)
    ax1.text(pd.Timestamp("2026-07-29"), 5.38, " 7/29 FOMC\n 连续第五次按兵不动\n 3票反对、主张加息", fontsize=8.5, color="#7a5c00")
    ax1.set_ylabel("收益率（%）")
    ax1.set_ylim(3.95, 5.55)

    ax2 = ax1.twinx()
    ax2.plot(df["observation_date"], df["s2s30"] * 100, color=PURPLE, lw=1.8, ls="--", label="30Y–2Y（右轴，bp）")
    ax2.set_ylabel("30Y–2Y 利差（bp）", color=PURPLE)
    ax2.tick_params(axis="y", colors=PURPLE)
    ax2.set_ylim(70, 125)
    ax2.grid(False)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, frameon=False, loc="upper left", ncol=2)
    ax1.set_title("2026年7–8月美债：典型熊陡（长端领涨、短端锚定）", fontsize=15, fontweight="bold")
    _source(ax1, "数据：FRED。7/27–7/31：2年期 4.31%→4.28%，30年期 5.12%→5.27%，2s30s 由约81bp升至99bp；8/17 30年期收于5.31%。")
    fig.savefig(CHARTS / "fig05_july_aug_bear_steepener.png")
    plt.close(fig)


def fig06_term_premium() -> None:
    labels = ["2年期国债", "10年期国债"]
    expected = {
        "一年前\n2025-08-21": [3.59, 3.14],
        "上次FOMC\n2026-07-29": [3.96, 3.44],
        "最新\n2026-08-20": [3.87, 3.43],
    }
    premium = {
        "一年前\n2025-08-21": [0.17, 1.25],
        "上次FOMC\n2026-07-29": [0.21, 1.31],
        "最新\n2026-08-20": [0.25, 1.34],
    }
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 5.8), sharey=True)
    x = np.arange(len(labels))
    width = 0.24
    colors = [SLATE, TEAL, CRIMSON]
    for ax, title, data in zip(
        axes,
        ["平均预期隔夜利率", "期限溢价（Term Premium）"],
        [expected, premium],
    ):
        for i, (name, vals) in enumerate(data.items()):
            ax.bar(x + (i - 1) * width, vals, width, label=name, color=colors[i], zorder=3)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_title(title)
        ax.set_ylabel("百分比（%）")
        ax.legend(frameon=False, fontsize=8)
        ax.set_ylim(0, 4.4)

    fig.suptitle("旧金山联储收益率分解：政策预期下行，期限溢价上行", fontsize=15, fontweight="bold")
    axes[0].annotate("短端预期回落", xy=(0, 3.87), xytext=(-0.35, 4.2), fontsize=8, color=TEAL)
    axes[1].annotate("10年期期限溢价\n升至 1.34%", xy=(1, 1.34), xytext=(0.55, 2.15),
                    fontsize=8.5, color=CRIMSON, arrowprops=dict(arrowstyle="->", color=CRIMSON))
    _source(axes[0], "数据：旧金山联储 Christensen–Rudebusch 国债收益率溢价模型（零息收益率分解，2026-08-20 更新）。")
    fig.tight_layout(rect=[0, 0.04, 1, 0.92])
    fig.savefig(CHARTS / "fig06_term_premium_decomposition.png")
    plt.close(fig)


def fig07_real_vs_nominal(tips: pd.DataFrame, ust: pd.DataFrame) -> None:
    m = pd.merge(ust, tips, on="observation_date", how="inner")
    m = m[(m["observation_date"] >= "2024-01-01") & (m["observation_date"] <= "2026-08-20")]
    fig, ax = plt.subplots(figsize=(11.2, 6.2))
    ax.plot(m["observation_date"], m["DGS30"], color=CRIMSON, lw=1.8, label="30年期名义收益率")
    ax.plot(m["observation_date"], m["DFII30"], color=NAVY, lw=1.8, label="30年期实际收益率（TIPS）")
    ax.plot(m["observation_date"], m["T10YIE"], color=GOLD, lw=1.6, label="10年期盈亏平衡通胀")
    ax.set_title("长端美债：2026年上涨几乎全部来自实际利率", fontsize=15, fontweight="bold")
    ax.set_ylabel("百分比（%）")
    ax.legend(frameon=False, loc="upper left")
    ax.annotate("2026年初→8/17：名义+45bp，实际+43bp，通胀补偿仅+2bp",
                xy=(pd.Timestamp("2026-08-17"), 5.31), xytext=(pd.Timestamp("2024-06-01"), 5.35),
                fontsize=9, color=CRIMSON, arrowprops=dict(arrowstyle="->", color=CRIMSON))
    _source(ax, "数据：FRED DGS30、DFII30、T10YIE。TIPS 实际收益率与名义收益率同步上移，说明定价主因是实际补偿/期限溢价，而非通胀预期飙升。")
    fig.savefig(CHARTS / "fig07_real_vs_nominal_long_end.png")
    plt.close(fig)


def fig08_china_vs_us_10y(ust: pd.DataFrame) -> None:
    # China 10Y month-end series compiled from OECD-sourced public extracts + latest market quotes.
    china = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2022-01-31", "2022-06-30", "2022-12-31",
                    "2023-06-30", "2023-12-31",
                    "2024-06-30", "2024-12-31",
                    "2025-02-28", "2025-04-30", "2025-07-31", "2025-08-31", "2025-12-31",
                    "2026-01-31", "2026-02-28", "2026-03-31", "2026-04-30", "2026-05-31", "2026-08-21",
                ]
            ),
            "cn10": [2.70, 2.82, 2.84, 2.64, 2.56, 2.21, 1.68, 1.72, 1.62, 1.70, 1.84, 1.85, 1.81, 1.78, 1.82, 1.75, 1.71, 1.70],
        }
    )
    us = (
        ust[(ust["observation_date"] >= "2022-01-01") & (ust["observation_date"] <= "2026-08-20")]
        .set_index("observation_date")["DGS10"]
        .dropna()
    )
    fig, ax = plt.subplots(figsize=(11.2, 6.2))
    ax.plot(us.index, us.values, color=CRIMSON, lw=1.7, label="美国 10年期国债")
    ax.plot(china["date"], china["cn10"], color=TEAL, lw=2.3, marker="o", markersize=5, label="中国 10年期国债（月度/最新）")
    ax.set_title("中美10年期国债收益率：政策周期背离与利差走阔", fontsize=15, fontweight="bold")
    ax.set_ylabel("收益率（%）")
    ax.legend(frameon=False, loc="upper right")
    ax.annotate("美国 4.69%\n(2026-08-20)", xy=(pd.Timestamp("2026-08-20"), 4.69),
                xytext=(pd.Timestamp("2025-04-01"), 5.15), fontsize=9, color=CRIMSON,
                arrowprops=dict(arrowstyle="->", color=CRIMSON))
    ax.annotate("中国约 1.70%\n接近2025年7月以来低点", xy=(pd.Timestamp("2026-08-21"), 1.70),
                xytext=(pd.Timestamp("2024-02-01"), 1.15), fontsize=9, color=TEAL,
                arrowprops=dict(arrowstyle="->", color=TEAL))
    spread = 4.69 - 1.70
    ax.text(pd.Timestamp("2026-03-01"), 3.15, f"最新10年期利差约 {spread:.2f} 个百分点", fontsize=10, color=NAVY)
    _source(ax, "美国：FRED DGS10。中国：OECD 月度序列公开摘录（至 2026-05）及 2026-08-21 市场报价（Trading Economics / 中债）。")
    fig.savefig(CHARTS / "fig08_cn_us_10y.png")
    plt.close(fig)


def fig09_current_curves_cn_us() -> None:
    fig, ax = plt.subplots(figsize=(11.2, 6.2))
    us_t = np.array([1 / 12, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30])
    us_y = np.array([3.80, 3.88, 3.95, 4.03, 4.24, 4.31, 4.43, 4.57, 4.74, 5.25, 5.27])
    cn_t = np.array([1 / 12, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30])
    cn_y = np.array([1.15, 1.17, 1.17, 1.20, 1.24, 1.25, 1.39, 1.52, 1.68, 2.13, 2.19])
    ax.plot(us_t, us_y, "-o", color=CRIMSON, lw=2.2, label="美国 2026-08-21")
    ax.plot(cn_t, cn_y, "-o", color=TEAL, lw=2.2, label="中国 2026-08-21")
    ax.set_xscale("symlog", linthresh=1)
    ax.set_xticks(us_t)
    ax.set_xticklabels(["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"])
    ax.set_ylabel("收益率（%）")
    ax.set_title("中美国债曲线对照（2026年8月21日）", fontsize=15, fontweight="bold")
    ax.legend(frameon=False, loc="upper left")
    ax.annotate("美债短端≈政策利率\n长端由财政与期限溢价主导", xy=(30, 5.27), xytext=(6, 5.55),
                fontsize=9, color=CRIMSON, arrowprops=dict(arrowstyle="->", color=CRIMSON))
    ax.annotate("中国曲线整体低位、斜率为正\n10Y–2Y 约 44bp", xy=(10, 1.68), xytext=(12, 2.7),
                fontsize=9, color=TEAL, arrowprops=dict(arrowstyle="->", color=TEAL))
    _source(ax, "美国：财政部平价曲线。中国：中债国债收益率曲线（ChinaBond，2026-08-21）；30年期取市场报价 2.19%。")
    fig.savefig(CHARTS / "fig09_cn_us_current_curves.png")
    plt.close(fig)


def fig10_china_yoy_curve_shift() -> None:
    tenors = ["1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
    latest = np.array([1.20, 1.28, 1.25, 1.39, 1.52, 1.70, 2.14, 2.19])
    yoy = np.array([-18.5, -16.3, -20.3, -24.3, -24.8, -9.4, -0.8, 11.4])  # bp
    year_ago = latest - yoy / 100.0

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 5.8))
    ax = axes[0]
    x = np.arange(len(tenors))
    ax.plot(x, year_ago, "--o", color=SLATE, label="一年前")
    ax.plot(x, latest, "-o", color=TEAL, lw=2.2, label="2026-08-21")
    ax.set_xticks(x)
    ax.set_xticklabels(tenors)
    ax.set_ylabel("收益率（%）")
    ax.set_title("中国国债曲线：一年前后对照")
    ax.legend(frameon=False)

    ax2 = axes[1]
    colors = [GREEN if v < 0 else CRIMSON for v in yoy]
    ax2.bar(x, yoy, color=colors, zorder=3)
    ax2.axhline(0, color="#334155", lw=1)
    ax2.set_xticks(x)
    ax2.set_xticklabels(tenors)
    ax2.set_ylabel("同比变动（bp）")
    ax2.set_title("分期限同比变动：中短端牛、超长端熊")
    ax2.annotate("3–7年下行最多\n=牛陡/牛平交织", xy=(3, -24.3), xytext=(0.2, -8),
                 fontsize=8.5, color=GREEN, arrowprops=dict(arrowstyle="->", color=GREEN))
    ax2.annotate("30年期同比上行\n超长端相对熊陡", xy=(7, 11.4), xytext=(4.3, 16),
                 fontsize=8.5, color=CRIMSON, arrowprops=dict(arrowstyle="->", color=CRIMSON))

    fig.suptitle("中国债市：短端与中端走牛，超长端供给与制度因素形成相对熊陡", fontsize=14, fontweight="bold")
    _source(axes[0], "数据：Trading Economics 中国国债收益率（2026-08-21）及其同比变动。负值表示收益率下行（债券上涨）。")
    fig.tight_layout(rect=[0, 0.04, 1, 0.92])
    fig.savefig(CHARTS / "fig10_china_yoy_curve.png")
    plt.close(fig)


def fig11_policy_rate_map() -> None:
    fig, ax = plt.subplots(figsize=(11.2, 6.0))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.2)
    ax.axis("off")
    ax.set_title("央行能决定什么、不能决定什么：短端锚定 vs 长端定价", fontsize=15, fontweight="bold", pad=8)

    boxes = [
        (0.4, 3.6, 4.2, 2.2, NAVY, "美联储（FOMC）",
         "政策利率：3.50%–3.75%\n有效联邦基金利率：3.63%\n2026-07-29 连续第五次按兵不动\n3名委员投票主张加息"),
        (5.4, 3.6, 4.2, 2.2, TEAL, "中国人民银行",
         "7天逆回购：1.40%（2025年5月至今）\n1年期 LPR：3.00% / 5年期以上：3.50%\n连续15个月未降息\n基调：实施好适度宽松的货币政策"),
        (0.4, 0.35, 4.2, 2.7, CRIMSON, "美债长端：市场定价",
         "30年期 5.23%–5.31%\n10年期期限溢价 1.34%\n财政赤字约 2.1 万亿美元\n供给、期限溢价、买家结构主导"),
        (5.4, 0.35, 4.2, 2.7, GOLD, "中国长端：配置+基本面",
         "10年期约 1.68%–1.70%\nCPI 仅 0.5%（2026年7月）\n银行/保险配置盘仍强\n长端难下、短端易落的结构分化"),
    ]
    for x, y, w, h, color, title, body in boxes:
        rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.12",
                              linewidth=1.6, edgecolor=color, facecolor=color + "18")
        ax.add_patch(rect)
        ax.text(x + 0.18, y + h - 0.35, title, fontsize=12, color=color, fontweight="bold")
        ax.text(x + 0.18, y + 0.25, body, fontsize=9.5, color="#1b2a4a", va="bottom")

    ax.annotate("", xy=(2.5, 3.55), xytext=(2.5, 3.05),
                arrowprops=dict(arrowstyle="->", color=SLATE, lw=1.5))
    ax.text(2.55, 3.2, "短端传导强、长端传导弱", fontsize=8.5, color=SLATE)
    ax.annotate("", xy=(7.5, 3.55), xytext=(7.5, 3.05),
                arrowprops=dict(arrowstyle="->", color=SLATE, lw=1.5))
    ax.text(7.55, 3.2, "流动性工具+预期管理", fontsize=8.5, color=SLATE)
    fig.savefig(CHARTS / "fig11_policy_vs_long_end.png")
    plt.close(fig)


def fig12_spread_cn_us(ust: pd.DataFrame) -> None:
    china = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2022-12-31", "2023-06-30", "2023-12-31", "2024-06-30", "2024-12-31",
                    "2025-04-30", "2025-08-31", "2025-12-31", "2026-05-31", "2026-08-20",
                ]
            ),
            "cn10": [2.84, 2.64, 2.56, 2.21, 1.68, 1.62, 1.84, 1.85, 1.71, 1.70],
        }
    )
    us_m = ust.set_index("observation_date")["DGS10"]
    rows = []
    for _, r in china.iterrows():
        # nearest available US yield
        idx = us_m.index.get_indexer([r["date"]], method="nearest")[0]
        rows.append((r["date"], us_m.iloc[idx] - r["cn10"], us_m.iloc[idx], r["cn10"]))
    out = pd.DataFrame(rows, columns=["date", "spread", "us", "cn"])

    fig, ax = plt.subplots(figsize=(11.2, 6.0))
    ax.plot(out["date"], out["spread"] * 100, color=PURPLE, lw=2.3, marker="o", markersize=7)
    ax.set_title("中美10年期国债利差（美国减中国）", fontsize=15, fontweight="bold")
    ax.set_ylabel("利差（基点）")
    for _, r in out.iterrows():
        ax.annotate(f"{r['spread']*100:.0f}", (r["date"], r["spread"] * 100 + 6), ha="center", fontsize=8, color=PURPLE)
    ax.set_ylim(80, 360)
    _source(ax, "美国：FRED DGS10 就近交易日。中国：OECD 月度摘录及 2026-08-20 市场报价。利差走阔反映两国增长、通胀与货币政策周期持续背离。")
    fig.savefig(CHARTS / "fig12_us_china_10y_spread.png")
    plt.close(fig)


def main() -> None:
    ust = load_ust()
    tips = load_tips()
    fig01_four_regimes()
    fig02_us_curve_snapshots()
    fig03_us_yields_timeseries(ust)
    fig04_us_spreads(ust)
    fig05_july_bear_steepener(ust)
    fig06_term_premium()
    fig07_real_vs_nominal(tips, ust)
    fig08_china_vs_us_10y(ust)
    fig09_current_curves_cn_us()
    fig10_china_yoy_curve_shift()
    fig11_policy_rate_map()
    fig12_spread_cn_us(ust)
    print("Wrote", len(list(CHARTS.glob("*.png"))), "charts to", CHARTS)


if __name__ == "__main__":
    main()
