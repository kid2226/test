#!/usr/bin/env python3
"""Render matplotlib figures plus a self-contained Chinese HTML/Markdown report."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.offline import plot as plotly_plot

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
FIG = ROOT / "reports" / "figures"
REPORTS = ROOT / "reports"
FIG.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

mpl.rcParams["font.sans-serif"] = ["WenQuanYi Micro Hei", "Droid Sans Fallback", "DejaVu Sans"]
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["figure.dpi"] = 140
mpl.rcParams["savefig.bbox"] = "tight"
mpl.rcParams["axes.facecolor"] = "#f7f8fb"
mpl.rcParams["figure.facecolor"] = "white"

NAVY = "#1f3b73"
GOLD = "#c9a227"
RED = "#c0392b"
GREEN = "#1e8449"
GRAY = "#5d6d7e"
FOCUS = [
    "银行", "非银金融", "房地产", "食品饮料", "医药生物", "电子",
    "计算机", "电力设备", "汽车", "煤炭", "有色金属", "石油石化",
    "国防军工", "通信", "家用电器", "基础化工",
]
BUCKET_ORDER = ["大幅流出", "流出", "中性", "流入", "大幅流入"]
BUCKET_COLOR = {
    "大幅流出": "#1a5276",
    "流出": "#5dade2",
    "中性": "#aab7b8",
    "流入": "#e67e22",
    "大幅流入": "#922b21",
}


def pct(x, d=1) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)) or pd.isna(x):
        return "—"
    return f"{float(x) * 100:.{d}f}%"


def num(x, d=1) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)) or pd.isna(x):
        return "—"
    return f"{float(x):.{d}f}"


def pval(x) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)) or pd.isna(x):
        return "—"
    if x < 0.001:
        return "<0.001"
    return f"{x:.3f}"


def load() -> dict:
    annual = pd.read_csv(PROC / "annual_market_view.csv")
    quarterly = pd.read_csv(PROC / "quarterly_market_view.csv")
    findings = json.loads((PROC / "findings.json").read_text(encoding="utf-8"))
    q_bkt = pd.read_csv(PROC / "quarterly_bucket_stats.csv")
    y_bkt = pd.read_csv(PROC / "annual_bucket_stats.csv")
    comp = pd.read_csv(PROC / "component_bucket_stats.csv")
    pooled = pd.read_csv(PROC / "industry_pooled_buckets.csv")
    sig_q = pd.read_csv(PROC / "industry_quarterly_signal.csv")
    sig_y = pd.read_csv(PROC / "industry_annual_signal.csv")
    rot_q = pd.read_csv(PROC / "industry_quarterly_rotation.csv", parse_dates=["date"])
    rot_y = pd.read_csv(PROC / "industry_annual_rotation.csv", parse_dates=["date"])
    extremes = pd.read_csv(PROC / "extreme_years.csv")
    ind_y = pd.read_csv(PROC / "annual_industry.csv", parse_dates=["date"])
    ind_q = pd.read_csv(PROC / "quarterly_industry.csv", parse_dates=["date"])
    return locals()


def plot_pngs(d: dict) -> None:
    annual = d["annual"]
    quarterly = d["quarterly"]
    q_bkt = d["q_bkt"]
    pooled = d["pooled"]
    ind_y = d["ind_y"]
    rot_q = d["rot_q"]
    rot_y = d["rot_y"]
    comp = d["comp"]

    # 1. long index
    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.plot(annual["year"], annual["sh_ret"] * 100, color=NAVY, lw=1.6, marker="o", ms=3.5, label="上证综指年度收益")
    ax.axhline(0, color="#ccc", lw=1)
    colors = [BUCKET_COLOR.get(x, GRAY) for x in annual["flow_bucket"].fillna("中性")]
    ax.bar(annual["year"], annual["sh_ret"] * 100, color=colors, alpha=0.45, width=0.7)
    ax.set_title("上证综指年度收益（颜色=综合资金环境分位）")
    ax.set_ylabel("%")
    ax.set_xlim(1989.5, 2026.5)
    from matplotlib.patches import Patch
    ax.legend([Patch(facecolor=BUCKET_COLOR[k], label=k) for k in BUCKET_ORDER], [k for k in BUCKET_ORDER], ncol=5, loc="upper right", fontsize=8, framealpha=0.9)
    fig.savefig(FIG / "annual_sse_returns.png")
    plt.close()

    # 2. scissors
    fig, ax1 = plt.subplots(figsize=(11, 4.2))
    ax1.bar(annual["year"], annual["scissors"], color=GOLD, alpha=0.75, label="M1-M2剪刀差（百分点）")
    ax2 = ax1.twinx()
    ax2.plot(annual["year"], annual["sh_ret"] * 100, color=NAVY, lw=1.8, label="上证收益%")
    ax1.axhline(0, color="#bbb", lw=1)
    ax1.set_title("M1-M2 剪刀差与上证年度收益（1991–2025）")
    ax1.set_ylabel("剪刀差（百分点）")
    ax2.set_ylabel("上证收益 %")
    fig.savefig(FIG / "scissors_vs_return.png")
    plt.close()

    # 3. subsequent quarterly
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.0))
    qb = q_bkt.set_index("flow_bucket").reindex(BUCKET_ORDER)
    axes[0].bar(BUCKET_ORDER, qb["sh_ret_mean"] * 100, color=[BUCKET_COLOR[x] for x in BUCKET_ORDER])
    axes[0].axhline(0, color="#ccc")
    axes[0].set_title("当季上证收益")
    axes[0].set_ylabel("%")
    axes[0].tick_params(axis="x", rotation=20)
    axes[1].bar(BUCKET_ORDER, qb["ret_next4_mean"] * 100, color=[BUCKET_COLOR[x] for x in BUCKET_ORDER])
    axes[1].axhline(0, color="#ccc")
    axes[1].set_title("随后四个季度累计收益")
    axes[1].tick_params(axis="x", rotation=20)
    fig.suptitle("全市场：资金环境分位的当期 vs 后续表现（季度，上证综指）")
    fig.savefig(FIG / "market_quintile_subsequent.png")
    plt.close()

    # 4. scissors annual subsequent
    sc = comp[(comp["freq"] == "annual") & (comp["component"] == "scissors")].set_index("flow_bucket").reindex(BUCKET_ORDER)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.0))
    axes[0].bar(BUCKET_ORDER, sc["sh_ret_mean"] * 100, color=[BUCKET_COLOR[x] for x in BUCKET_ORDER])
    axes[0].axhline(0, color="#ccc")
    axes[0].set_title("当年上证收益")
    axes[0].tick_params(axis="x", rotation=20)
    axes[1].bar(BUCKET_ORDER, sc["ret_next1_mean"] * 100, color=[BUCKET_COLOR[x] for x in BUCKET_ORDER])
    axes[1].axhline(0, color="#ccc")
    axes[1].set_title("次年上证收益")
    axes[1].tick_params(axis="x", rotation=20)
    fig.suptitle("M1-M2 剪刀差分位：当年拥挤、次年回归")
    fig.savefig(FIG / "scissors_quintile.png")
    plt.close()

    # 5. north / margin quarterly
    q = quarterly.copy()
    fig, ax1 = plt.subplots(figsize=(11, 4.2))
    ax1.bar(range(len(q)), q["rz_chg"], color="#7f8c8d", alpha=0.7, label="融资余额变动")
    ax2 = ax1.twinx()
    ax2.plot(range(len(q)), q["sh_ret"] * 100, color=NAVY, lw=1.2, label="上证当季%")
    step = max(1, len(q) // 12)
    ax1.set_xticks(range(0, len(q), step), q["quarter"].iloc[::step], rotation=45, ha="right")
    ax1.set_title("融资余额变动与上证当季收益（2010 起）")
    ax1.set_ylabel("亿元")
    fig.savefig(FIG / "margin_vs_return.png")
    plt.close()

    # 6. industry heatmap returns
    sub = ind_y[ind_y["industry"].isin(FOCUS)].copy()
    sub["year"] = sub["date"].dt.year
    pv = sub.pivot_table(index="industry", columns="year", values="ret", aggfunc="last")
    pv = pv.reindex([i for i in FOCUS if i in pv.index])
    fig, ax = plt.subplots(figsize=(12.5, 6.2))
    im = ax.imshow(pv.values * 100, cmap="RdYlGn", aspect="auto", vmin=-50, vmax=80)
    ax.set_yticks(range(len(pv.index)), pv.index)
    ax.set_xticks(range(len(pv.columns)), pv.columns, rotation=90)
    ax.set_title("重点行业年度收益热力图（申万一级）")
    fig.colorbar(im, ax=ax, label="%")
    fig.savefig(FIG / "industry_return_heatmap.png")
    plt.close()

    # 7. industry share change heatmap
    pv2 = sub.pivot_table(index="industry", columns="year", values="share_chg", aggfunc="last")
    pv2 = pv2.reindex([i for i in FOCUS if i in pv2.index])
    fig, ax = plt.subplots(figsize=(12.5, 6.2))
    im = ax.imshow(pv2.values * 100, cmap="PuOr", aspect="auto", vmin=-4, vmax=4)
    ax.set_yticks(range(len(pv2.index)), pv2.index)
    ax.set_xticks(range(len(pv2.columns)), pv2.columns, rotation=90)
    ax.set_title("重点行业成交额占比变化（百分点，正值=相对资金流入）")
    fig.colorbar(im, ax=ax, label="占比变化 ppt")
    fig.savefig(FIG / "industry_flow_heatmap.png")
    plt.close()

    # 8. pooled industry
    pb = pooled.set_index("flow_bucket").reindex(BUCKET_ORDER)
    x = np.arange(len(BUCKET_ORDER))
    fig, ax = plt.subplots(figsize=(9.5, 4.2))
    ax.bar(x - 0.18, pb["exret_now"] * 100, 0.36, color=NAVY, label="当季超额")
    ax.bar(x + 0.18, pb["exret_next"] * 100, 0.36, color=GOLD, label="下季超额")
    ax.axhline(0, color="#ccc")
    ax.set_xticks(x, BUCKET_ORDER)
    ax.set_ylabel("%")
    ax.set_title("行业资金分位：当季顺势、下季反转（相对行业等权）")
    ax.legend()
    fig.savefig(FIG / "industry_pooled_buckets.png")
    plt.close()

    # 9. rotation
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.0))
    axes[0].plot(rot_q["date"], (1 + rot_q["spread"]).cumprod() - 1, color=NAVY)
    axes[0].axhline(0, color="#ccc")
    axes[0].set_title("季度：买入资金流入行业 / 卖出流出行业（下季收益差累计）")
    axes[1].plot(rot_y["date"], (1 + rot_y["spread"]).cumprod() - 1, color=GREEN)
    axes[1].axhline(0, color="#ccc")
    axes[1].set_title("年度：买入资金流入行业 / 卖出流出行业（次年收益差累计）")
    fig.savefig(FIG / "industry_rotation.png")
    plt.close()

    # 10. incremental capital
    a = annual.dropna(subset=["inc_capital"])
    fig, ax1 = plt.subplots(figsize=(10, 4.2))
    cols = np.where(a["inc_capital"] >= 0, GREEN, RED)
    ax1.bar(a["year"], a["inc_capital"], color=cols, alpha=0.8)
    ax2 = ax1.twinx()
    ax2.plot(a["year"], a["sh_ret"] * 100, color=NAVY, marker="o")
    ax1.axhline(0, color="#ccc")
    ax1.set_title("可观测增量资金（北向+两融变动+偏股新发−IPO）与上证收益")
    ax1.set_ylabel("亿元")
    ax2.set_ylabel("%")
    fig.savefig(FIG / "incremental_capital.png")
    plt.close()


def fig_to_html(fig, include_js: bool) -> str:
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Noto Sans SC, WenQuanYi Micro Hei, Microsoft YaHei, sans-serif", size=13),
        margin=dict(l=50, r=30, t=60, b=50),
        legend=dict(orientation="h", y=1.12),
    )
    return plotly_plot(fig, output_type="div", include_plotlyjs=include_js, config={"displayModeBar": False})


def plotly_divs(d: dict) -> list[str]:
    annual = d["annual"]
    quarterly = d["quarterly"]
    q_bkt = d["q_bkt"].set_index("flow_bucket").reindex(BUCKET_ORDER)
    y_bkt = d["y_bkt"].set_index("flow_bucket").reindex(BUCKET_ORDER)
    pooled = d["pooled"].set_index("flow_bucket").reindex(BUCKET_ORDER)
    ind_y = d["ind_y"]
    rot_q, rot_y = d["rot_q"], d["rot_y"]
    sc = d["comp"]
    sc = sc[(sc["freq"] == "annual") & (sc["component"] == "scissors")].set_index("flow_bucket").reindex(BUCKET_ORDER)

    divs = []
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(x=annual["year"], y=annual["sh_ret"] * 100, name="上证年度%", marker_color=NAVY, opacity=0.75)
    fig.add_scatter(x=annual["year"], y=annual["flow_score"], name="资金环境得分", mode="lines+markers", marker_color=GOLD, secondary_y=True)
    fig.update_yaxes(title_text="上证收益 %", secondary_y=False)
    fig.update_yaxes(title_text="资金环境得分", secondary_y=True)
    fig.update_layout(title="全市场年度：上证收益 vs 综合资金环境")
    divs.append(fig_to_html(fig, True))

    fig = go.Figure()
    fig.add_bar(x=annual["year"], y=annual["scissors"], name="M1-M2剪刀差", marker_color=GOLD)
    fig.add_scatter(x=annual["year"], y=annual["sh_ret"] * 100, name="上证%", yaxis="y2", line=dict(color=NAVY, width=2))
    fig.update_layout(
        title="长周期风险偏好：M1-M2 剪刀差（可追溯到 1990 年代）",
        yaxis=dict(title="百分点"),
        yaxis2=dict(title="上证 %", overlaying="y", side="right"),
    )
    divs.append(fig_to_html(fig, False))

    fig = make_subplots(rows=1, cols=2, subplot_titles=("当季收益", "随后四季度累计"))
    fig.add_bar(x=BUCKET_ORDER, y=q_bkt["sh_ret_mean"] * 100, marker_color=[BUCKET_COLOR[x] for x in BUCKET_ORDER], row=1, col=1)
    fig.add_bar(x=BUCKET_ORDER, y=q_bkt["ret_next4_mean"] * 100, marker_color=[BUCKET_COLOR[x] for x in BUCKET_ORDER], row=1, col=2)
    fig.update_layout(title="季度资金环境分位：当期顺周期，一年后均值回归", showlegend=False)
    divs.append(fig_to_html(fig, False))

    fig = make_subplots(rows=1, cols=2, subplot_titles=("当年上证", "次年上证"))
    fig.add_bar(x=BUCKET_ORDER, y=sc["sh_ret_mean"] * 100, marker_color=[BUCKET_COLOR[x] for x in BUCKET_ORDER], row=1, col=1)
    fig.add_bar(x=BUCKET_ORDER, y=sc["ret_next1_mean"] * 100, marker_color=[BUCKET_COLOR[x] for x in BUCKET_ORDER], row=1, col=2)
    fig.update_layout(title="按 M1-M2 剪刀差分位：高风险偏好年份涨得多，但次年转弱", showlegend=False)
    divs.append(fig_to_html(fig, False))

    qn = quarterly.dropna(subset=["north_yi"])
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(x=qn["quarter"], y=qn["north_yi"], name="北向净买入（亿元）", marker_color="#2980b9")
    fig.add_scatter(x=qn["quarter"], y=qn["sh_ret"] * 100, name="上证当季%", secondary_y=True, line=dict(color=NAVY))
    fig.update_layout(title="北向资金净买入 vs 上证当季收益（2014Q4–2024Q3，之后东财净买入字段缺失）")
    divs.append(fig_to_html(fig, False))

    qm = quarterly.dropna(subset=["rz_chg"])
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(x=qm["quarter"], y=qm["rz_chg"], name="融资余额变动（亿元）", marker_color="#7f8c8d")
    fig.add_scatter(x=qm["quarter"], y=qm["sh_ret"] * 100, name="上证当季%", secondary_y=True, line=dict(color=NAVY))
    fig.update_layout(title="两融融资余额变动 vs 上证当季收益（2010 起）")
    divs.append(fig_to_html(fig, False))

    fig = go.Figure()
    fig.add_bar(x=BUCKET_ORDER, y=pooled["exret_now"] * 100, name="当季超额", marker_color=NAVY)
    fig.add_bar(x=BUCKET_ORDER, y=pooled["exret_next"] * 100, name="下季超额", marker_color=GOLD)
    fig.update_layout(title="申万行业资金分位（成交额占比变化）：当季跟涨、下季拥挤回撤", barmode="group")
    divs.append(fig_to_html(fig, False))

    sub = ind_y[ind_y["industry"].isin(FOCUS)].copy()
    sub["year"] = sub["date"].dt.year
    pv = sub.pivot_table(index="industry", columns="year", values="ret", aggfunc="last")
    pv = pv.reindex([i for i in FOCUS if i in pv.index])
    fig = go.Figure(
        data=go.Heatmap(
            z=pv.values * 100,
            x=pv.columns.astype(str),
            y=pv.index,
            colorscale="RdYlGn",
            zmid=0,
            colorbar=dict(title="%"),
        )
    )
    fig.update_layout(title="重点行业年度涨跌热力图", height=560)
    divs.append(fig_to_html(fig, False))

    pv2 = sub.pivot_table(index="industry", columns="year", values="share_chg", aggfunc="last")
    pv2 = pv2.reindex([i for i in FOCUS if i in pv2.index])
    fig = go.Figure(
        data=go.Heatmap(
            z=pv2.values * 100,
            x=pv2.columns.astype(str),
            y=pv2.index,
            colorscale="PuOr",
            zmid=0,
            colorbar=dict(title="ppt"),
        )
    )
    fig.update_layout(title="重点行业成交额占比变化（相对资金流入/流出）", height=560)
    divs.append(fig_to_html(fig, False))

    fig = go.Figure()
    fig.add_scatter(x=rot_q["date"], y=((1 + rot_q["spread"]).cumprod() - 1) * 100, name="季度轮动累计", line=dict(color=NAVY))
    fig.add_scatter(x=rot_y["date"], y=((1 + rot_y["spread"]).cumprod() - 1) * 100, name="年度轮动累计", line=dict(color=GREEN))
    fig.update_layout(title="行业资金轮动：下期多空收益差累计（季度为负、年度为正）", yaxis_title="%")
    divs.append(fig_to_html(fig, False))
    return divs


def html_table(df: pd.DataFrame, fmt: dict | None = None) -> str:
    fmt = fmt or {}
    cols = list(df.columns)

    def cell(col, v):
        if col in fmt:
            return fmt[col](v)
        if pd.isna(v):
            return "—"
        return str(v)

    head = "".join(f"<th>{c}</th>" for c in cols)
    body = []
    for _, row in df.iterrows():
        tds = "".join(f"<td>{cell(c, row[c])}</td>" for c in cols)
        body.append(f"<tr>{tds}</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def build_html(d: dict, divs: list[str]) -> str:
    f = d["findings"]
    annual = d["annual"]
    q_bkt = d["q_bkt"].set_index("flow_bucket").reindex(BUCKET_ORDER)
    y_bkt = d["y_bkt"].set_index("flow_bucket").reindex(BUCKET_ORDER)
    pooled = d["pooled"].set_index("flow_bucket").reindex(BUCKET_ORDER)
    sig_q = d["sig_q"].sort_values("corr_next")
    sig_y = d["sig_y"].sort_values("corr_next")
    extremes = d["extremes"].copy()
    if "date" in extremes.columns:
        extremes["year"] = pd.to_datetime(extremes["date"]).dt.year
    comp = d["comp"]
    sc = comp[(comp["freq"] == "annual") & (comp["component"] == "scissors")].set_index("flow_bucket").reindex(BUCKET_ORDER)

    aq, an = f["quarterly"], f["annual"]
    rotq, roty = f["rotation_q"], f["rotation_y"]

    annual_view = annual[annual["year"].between(1991, 2025)].copy()
    annual_tbl = html_table(
        annual_view[
            ["year", "sh_ret", "alla_ret", "flow_bucket", "scissors", "m2_yoy", "amount_yoy", "north_yi", "rz_chg", "ipo_yi", "inc_capital", "ret_next1"]
        ].rename(
            columns={
                "year": "年份",
                "sh_ret": "上证",
                "alla_ret": "全A近似",
                "flow_bucket": "资金分位",
                "scissors": "剪刀差",
                "m2_yoy": "M2同比",
                "amount_yoy": "成交额同比",
                "north_yi": "北向净买入",
                "rz_chg": "两融变动",
                "ipo_yi": "IPO募资",
                "inc_capital": "增量资金",
                "ret_next1": "次年上证",
            }
        ),
        fmt={
            "上证": pct,
            "全A近似": pct,
            "剪刀差": lambda x: num(x, 1),
            "M2同比": lambda x: num(x, 1),
            "成交额同比": pct,
            "北向净买入": lambda x: num(x, 0),
            "两融变动": lambda x: num(x, 0),
            "IPO募资": lambda x: num(x, 0),
            "增量资金": lambda x: num(x, 0),
            "次年上证": pct,
        },
    )

    bkt_q = q_bkt.reset_index()[["flow_bucket", "n", "sh_ret_mean", "ret_next1_mean", "ret_next4_mean", "ret_next4_win"]]
    bkt_q = bkt_q.rename(
        columns={
            "flow_bucket": "资金分位",
            "n": "样本数",
            "sh_ret_mean": "当季上证",
            "ret_next1_mean": "下季上证",
            "ret_next4_mean": "随后一年",
            "ret_next4_win": "一年胜率",
        }
    )
    bkt_q_html = html_table(
        bkt_q,
        fmt={"当季上证": pct, "下季上证": pct, "随后一年": pct, "一年胜率": pct},
    )

    bkt_y = y_bkt.reset_index()[["flow_bucket", "n", "sh_ret_mean", "ret_next1_mean", "ret_next1_win"]]
    bkt_y = bkt_y.rename(
        columns={
            "flow_bucket": "资金分位",
            "n": "样本数",
            "sh_ret_mean": "当年上证",
            "ret_next1_mean": "次年上证",
            "ret_next1_win": "次年胜率",
        }
    )
    bkt_y_html = html_table(bkt_y, fmt={"当年上证": pct, "次年上证": pct, "次年胜率": pct})

    pooled_html = html_table(
        pooled.reset_index()[["flow_bucket", "n", "exret_now", "exret_now_win", "exret_next", "exret_next_win", "exret_next_p"]].rename(
            columns={
                "flow_bucket": "行业资金分位",
                "n": "行业-季度数",
                "exret_now": "当季超额",
                "exret_now_win": "当季跑赢占比",
                "exret_next": "下季超额",
                "exret_next_win": "下季跑赢占比",
                "exret_next_p": "下季p值",
            }
        ),
        fmt={
            "当季超额": pct,
            "当季跑赢占比": pct,
            "下季超额": pct,
            "下季跑赢占比": pct,
            "下季p值": pval,
        },
    )

    focus_sig = sig_q[sig_q["industry"].isin(FOCUS)][["industry", "n", "start", "corr_now", "corr_next", "p_next", "spread_next"]]
    focus_sig = focus_sig.rename(
        columns={
            "industry": "行业",
            "n": "季度数",
            "start": "起点",
            "corr_now": "资金 vs 当季超额",
            "corr_next": "资金 vs 下季超额",
            "p_next": "下季p值",
            "spread_next": "流入-流出下季差",
        }
    )
    sig_html = html_table(
        focus_sig,
        fmt={
            "资金 vs 当季超额": lambda x: num(x, 2),
            "资金 vs 下季超额": lambda x: num(x, 2),
            "下季p值": pval,
            "流入-流出下季差": pct,
        },
    )

    ext = extremes.copy()
    ext["year"] = pd.to_datetime(ext["date"]).dt.year
    ext_html = html_table(
        ext[["kind", "year", "sh_ret", "ret_next1", "scissors", "north_yi", "rz_chg", "ipo_yi"]].rename(
            columns={
                "kind": "类型",
                "year": "年份",
                "sh_ret": "当年上证",
                "ret_next1": "次年上证",
                "scissors": "剪刀差",
                "north_yi": "北向",
                "rz_chg": "两融变动",
                "ipo_yi": "IPO",
            }
        ),
        fmt={"当年上证": pct, "次年上证": pct, "剪刀差": lambda x: num(x, 1), "北向": lambda x: num(x, 0), "两融变动": lambda x: num(x, 0), "IPO": lambda x: num(x, 0)},
    )

    sc_html = html_table(
        sc.reset_index()[["flow_bucket", "n", "sh_ret_mean", "ret_next1_mean", "ret_next1_win"]].rename(
            columns={"flow_bucket": "剪刀差分位", "n": "年数", "sh_ret_mean": "当年上证", "ret_next1_mean": "次年上证", "ret_next1_win": "次年胜率"}
        ),
        fmt={"当年上证": pct, "次年上证": pct, "次年胜率": pct},
    )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>A股市场资金流动：年度与季度长周期研究</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root {{ --navy:#1f3b73; --gold:#c9a227; --bg:#f4f6fb; --card:#fff; --text:#1c2833; --muted:#5d6d7e; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:"Noto Sans SC","WenQuanYi Micro Hei",sans-serif; background:var(--bg); color:var(--text); line-height:1.65; }}
header {{ background:linear-gradient(135deg,#13294b,#1f3b73 55%,#2e86c1); color:#fff; padding:48px 24px 36px; }}
header .wrap, main {{ max-width:1120px; margin:0 auto; }}
header h1 {{ margin:0 0 8px; font-size:32px; font-weight:700; }}
header p {{ margin:0; opacity:.92; }}
.badge {{ display:inline-block; background:rgba(255,255,255,.15); padding:4px 10px; border-radius:999px; font-size:12px; margin-top:14px; }}
main {{ padding:28px 20px 80px; }}
h2 {{ color:var(--navy); border-left:4px solid var(--gold); padding-left:12px; margin-top:42px; }}
h3 {{ color:#1a365d; }}
.card {{ background:var(--card); border-radius:14px; padding:20px 22px; margin:16px 0; box-shadow:0 8px 24px rgba(31,59,115,.06); }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:12px; }}
.kpi {{ background:var(--card); border-radius:12px; padding:16px; box-shadow:0 6px 16px rgba(31,59,115,.05); }}
.kpi .k {{ font-size:13px; color:var(--muted); }}
.kpi .v {{ font-size:22px; font-weight:700; color:var(--navy); margin-top:4px; }}
.kpi .s {{ font-size:12px; color:var(--muted); }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th, td {{ border-bottom:1px solid #e8edf5; padding:7px 8px; text-align:right; }}
th:first-child, td:first-child {{ text-align:left; }}
th {{ background:#eef2fa; color:#1f3b73; position:sticky; top:0; }}
.callout {{ background:#fff8e7; border-left:4px solid var(--gold); padding:12px 16px; border-radius:8px; }}
.note {{ color:var(--muted); font-size:13px; }}
.chart {{ background:var(--card); border-radius:14px; padding:8px 8px 16px; margin:18px 0; box-shadow:0 8px 24px rgba(31,59,115,.06); }}
ul.tight li {{ margin:6px 0; }}
footer {{ color:#7b8a9a; font-size:12px; padding:24px; text-align:center; }}
</style>
</head>
<body>
<header>
  <div class="wrap">
    <div class="badge">数据截至 {f['as_of']} · 上证综指自 1990-12-19 · 完整年至 {f['last_complete_year']} · 完整季至 {f['last_complete_quarter']}</div>
    <h1>A股市场资金流动长周期研究</h1>
    <p>从年度和季度两个频率，考察全市场与申万一级行业在资金流入/流出期的当期表现，以及随后 1 季、1 年的行情。</p>
  </div>
</header>
<main>
<h2>一、核心结论</h2>
<div class="grid">
  <div class="kpi"><div class="k">资金与当年行情</div><div class="v">顺周期</div><div class="s">年度相关系数 {num(an['corr_flow_now']['corr'],2)}（p={pval(an['corr_flow_now']['p'])}）</div></div>
  <div class="kpi"><div class="k">大幅流入年当年上证</div><div class="v">{pct(y_bkt.loc['大幅流入','sh_ret_mean'])}</div><div class="s">大幅流出年仅 {pct(y_bkt.loc['大幅流出','sh_ret_mean'])}</div></div>
  <div class="kpi"><div class="k">流入季随后一年</div><div class="v">{pct(q_bkt.loc['大幅流入','ret_next4_mean'])}</div><div class="s">流出季随后一年 {pct(q_bkt.loc['大幅流出','ret_next4_mean'])}，差额 p={pval(aq['spread_next4_sh']['p'])}</div></div>
  <div class="kpi"><div class="k">行业下季超额</div><div class="v">{pct(pooled.loc['大幅流入','exret_next'])}</div><div class="s">资金扎堆行业下季跑输；流出行业 {pct(pooled.loc['大幅流出','exret_next'])}</div></div>
</div>
<div class="card callout">
<strong>一句话：</strong>A股的资金流是行情的同步指标，不是可靠的领先指标。钱进来的时候指数往往已经在涨；资金环境过热之后的四个季度，回报倾向于变差（流出组随后一年好于流入组）。行业层面同样如此——成交额占比抬升的行业当季大涨，下一季倾向拥挤回撤。相对有赔率的，是资金冰点之后的年度维度。
</div>
<ul class="tight">
<li><strong>全市场当期：</strong>综合资金环境、融资余额变化、可观测增量资金都与同期股指显著正相关。两融变动与当季上证相关 {num(aq['corr_margin_now']['corr'],2)}。</li>
<li><strong>全市场后续：</strong>季度资金“大幅流入”之后一年上证平均 {pct(q_bkt.loc['大幅流入','ret_next4_mean'])}（胜率 {pct(q_bkt.loc['大幅流入','ret_next4_win'])}）；“大幅流出”之后一年平均 {pct(q_bkt.loc['大幅流出','ret_next4_mean'])}（胜率 {pct(q_bkt.loc['大幅流出','ret_next4_win'])}）。</li>
<li><strong>最长的宏观资金代理——M1-M2 剪刀差：</strong>高剪刀差年份上证平均 {pct(sc.loc['大幅流入','sh_ret_mean'])}，但次年转为 {pct(sc.loc['大幅流入','ret_next1_mean'])}；低剪刀差年份当年偏弱、次年 {pct(sc.loc['大幅流出','ret_next1_mean'])}。</li>
<li><strong>行业：</strong>追涨季度资金流入行业、做空流出行业，下季收益差平均 {pct(rotq['mean'])}（t={num(rotq['t'],2)}）。但按年持有，同一规则平均 {pct(roty['mean'])}（胜率 {pct(roty['win'])}），说明年频有配置动量、季频是拥挤反转。</li>
</ul>

<h2>二、研究框架与数据边界</h2>
<div class="card">
<p>A股没有一条从 1990 年连续至今的“主力净流入”官方序列。本研究把“资金流动”拆成三层，能用多长的历史就用多长：</p>
<ol>
<li><strong>长周期流动性（约 1991–2025）：</strong>M1/M2 同比与剪刀差、沪深成交额同比、公募基金份额/净申赎（1998 起）。全A价格用上证A指（1990）在 2005 年拼接国证A指。</li>
<li><strong>可观测增量资金（2010/2014 起）：</strong>沪深融资余额变动（2010-03）、北向成交净买入（2014-11 至 2024-08-16，之后东方财富该字段缺失）、IPO 募资与偏股型基金新发（约 2010/2013 起）。增量资金 ≈ 北向净买入 + 两融余额变化 + 偏股新发 − IPO 募资。</li>
<li><strong>行业相对资金（1999/2014 起）：</strong>申万一级行业成交额占全部已上市行业的比重变化，作为“钱流向哪里”的代理。电子、医药、食品饮料、房地产等 16 个行业可追溯到 1999 年末；银行、非银、计算机、电新、军工等为 2014 年行业分类修订后序列；煤炭、石油石化、环保、美容护理更短。</li>
</ol>
<p class="note">综合资金环境得分 = 上述可得分量的扩张窗口 z 分数等权平均（避免用全样本均值造成前视偏差）。分位（五档）仍是描述性分组，用于回答“流入期/流出期当时和之后发生了什么”，不是可直接下单的交易信号。2026 年为截至 8 月 26 日的未完结年度，统计推断只用到 2025 年与 2026Q2。</p>
</div>

<h2>三、全市场：年度</h2>
<div class="chart">{divs[0]}</div>
<div class="chart">{divs[1]}</div>
<p>年度样本里，资金环境与<strong>当年</strong>上证收益正相关 {num(an['corr_flow_now']['corr'],2)}，与<strong>次年</strong>转为 {num(an['corr_flow_next']['corr'],2)}（p={pval(an['corr_flow_next']['p'])}）。剪刀差同样是当年正、次年负。这是典型的风险偏好顺周期：活期化（M1 快于 M2）和成交活跃往往伴随着牛市，但这些年份之后常有消化期。</p>
<h3>按综合资金分位</h3>
{bkt_y_html}
<h3>按 M1-M2 剪刀差分位（最长、也最干净的一组）</h3>
{sc_html}
<div class="chart">{divs[3]}</div>
<h3>极端流入 / 流出年份</h3>
{ext_html}
<p class="note">流入年份集中在 2006–2007、2009、2019–2021、2025 这类风险偏好扩张期；流出年份包括 2008、2013、2018、2022。2008 年大流出后 2009 年大涨、2022 年流出后并非立刻单边修复，说明“冰点”提供的是赔率而不是精确择时。</p>
<h3>年度明细</h3>
<div class="card" style="overflow:auto;max-height:480px;">{annual_tbl}</div>
<p class="note">北向 2024 年仅含截至 8 月 16 日的净买入，其后缺失；2025 年起北向净买入记为缺失，增量资金主要反映两融与 IPO。成交额为沪市+深市腾讯口径（千元换算亿元）。</p>

<h2>四、全市场：季度</h2>
<div class="chart">{divs[2]}</div>
{bkt_q_html}
<p>当季：大幅流入季度上证平均 {pct(q_bkt.loc['大幅流入','sh_ret_mean'])}，大幅流出 {pct(q_bkt.loc['大幅流出','sh_ret_mean'])}，差额显著（p={pval(aq['spread_now_sh']['p'])}）。下一季几乎没有预测力（相关 {num(aq['corr_flow_next']['corr'],2)}）。把持有期拉长到随后四个季度，流出组反而明显更好：平均 {pct(q_bkt.loc['大幅流出','ret_next4_mean'])} 对流入组 {pct(q_bkt.loc['大幅流入','ret_next4_mean'])}，t={num(aq['spread_next4_sh']['t'],2)}。</p>
<div class="chart">{divs[5]}</div>
<div class="chart">{divs[4]}</div>
<p>融资余额是最强的<strong>同步</strong>指标（当季相关 {num(aq['corr_margin_now']['corr'],2)}），但对下一季无效（{num(aq['corr_margin_next']['corr'],2)}）。北向净买入同样偏同步（{num(aq['corr_north_now']['corr'],2)}），对下一季甚至略为负（{num(aq['corr_north_next']['corr'],2)}）。把北向当成“聪明钱领先指标”去追涨，历史统计并不支持。</p>

<h2>五、重点行业</h2>
<p>行业“资金流入”定义为该行业成交额占全部申万一级成交额的比重较上一期上升。价格涨、成交跟上来，占比就会抬升，所以它与当季超额高度正相关——这是机制，不是发现。真正要看的是<strong>之后</strong>。</p>
<div class="chart">{divs[6]}</div>
{pooled_html}
<p>资金大幅流入的行业-季度，当季超额 {pct(pooled.loc['大幅流入','exret_now'])}（跑赢占比 {pct(pooled.loc['大幅流入','exret_now_win'])}）；下一季超额 {pct(pooled.loc['大幅流入','exret_next'])}（p={pval(pooled.loc['大幅流入','exret_next_p'])}）。流出组下一季转为正超额。行业资金是拥挤度，不是价值。</p>
<div class="chart">{divs[7]}</div>
<div class="chart">{divs[8]}</div>
<h3>分行业：资金占比变化对下季超额的预测</h3>
<p class="note">相关系数为负，表示“越被资金追逐，下季越容易跑输”。银行、电子、汽车、公用事业的负向关系更清楚；煤炭在较短样本里呈正向，更像高贝塔资源品的年频动量，不宜外推。</p>
{sig_html}
<div class="chart">{divs[9]}</div>
<p>把每个期末成交额占比上升最多的一组行业等权持有到下一期、并做空下降最多的一组：<strong>季度规则亏钱</strong>（平均 {pct(rotq['mean'])}/季，胜率 {pct(rotq['win'])}）；<strong>年度规则赚钱</strong>（平均 {pct(roty['mean'])}/年，胜率 {pct(roty['win'])}）。年频层面，有色、交运、电子等行业的份额提升对次年超额偏正，更接近产业趋势与配置迁移；季频则是主题炒作后的回撤。</p>

<h2>六、怎么用这些结果</h2>
<div class="card">
<ul class="tight">
<li>把北向、两融、成交额暴增当成<strong>温度计</strong>，不要当成买点。它们确认的是风险偏好已经升温。</li>
<li>更有历史赔率的是反面：M1-M2 极低、成交额同比收缩、两融下降、行业被资金抛弃之后的 <strong>1 年</strong>维度，而不是下一周。</li>
<li>行业上，季度资金榜前列往往已经贵了；若要做轮动，历史更支持按年观察份额迁移（电新、电子、有色这类中期主线），而不是按周追板块资金榜。</li>
<li>IPO 大年对二级市场是抽水，但单独用 IPO 做择时样本太短、效果不稳定。</li>
</ul>
</div>

<h2>七、局限</h2>
<div class="card note">
<ul>
<li>1990–2009 没有北向和两融，长周期结论主要依赖货币剪刀差、成交额和价格本身，不是券商软件里的“主力净流入”。</li>
<li>申万 2021 分类修订导致银行、电新、军工等序列从 2014 才完整；行业结论在长短样本之间不可简单拼接。</li>
<li>北向净买入在 2024-08-16 之后缺失，2024 全年与 2025–2026 的北向数字不可用。</li>
<li>成交额占比会被价格上涨放大，并非独立的资金计量；本研究已尽量用占比变化而非成交额绝对值，并报告超额而非绝对收益。</li>
<li>五组分位是样本内描述，年度每组大约 6–7 个观测，统计功效有限。季度随后一年结果更可靠。</li>
</ul>
</div>
</main>
<footer>可复现脚本：scripts/fetch_data.py → analyze.py → build_report.py · 数据源为新浪/腾讯指数、东方财富、乐咕乐股申万、央行货币统计</footer>
</body>
</html>
"""
    return html


def build_markdown(d: dict) -> str:
    f = d["findings"]
    q_bkt = d["q_bkt"].set_index("flow_bucket").reindex(BUCKET_ORDER)
    y_bkt = d["y_bkt"].set_index("flow_bucket").reindex(BUCKET_ORDER)
    pooled = d["pooled"].set_index("flow_bucket").reindex(BUCKET_ORDER)
    an, aq = f["annual"], f["quarterly"]
    rotq, roty = f["rotation_q"], f["rotation_y"]
    sc = d["comp"]
    sc = sc[(sc["freq"] == "annual") & (sc["component"] == "scissors")].set_index("flow_bucket").reindex(BUCKET_ORDER)
    return f"""# A股市场资金流动长周期研究

数据截至 **{f['as_of']}**。完整年 {f['last_complete_year']}，完整季 {f['last_complete_quarter']}。交互版报告见 [reports/ashare_capital_flow.html](reports/ashare_capital_flow.html)。

## 核心结论

A股资金流是行情的**同步指标**，不是可靠的领先指标。

| 问题 | 结果 |
| --- | --- |
| 资金流入时市场表现如何？ | 顺周期。年度相关 {num(an['corr_flow_now']['corr'],2)}；大幅流入年当年上证 {pct(y_bkt.loc['大幅流入','sh_ret_mean'])}，流出年 {pct(y_bkt.loc['大幅流出','sh_ret_mean'])}。 |
| 流入之后呢？ | 变差。流入季随后一年 {pct(q_bkt.loc['大幅流入','ret_next4_mean'])}，流出季随后一年 {pct(q_bkt.loc['大幅流出','ret_next4_mean'])}（p={pval(aq['spread_next4_sh']['p'])}）。 |
| 最长的宏观代理？ | M1-M2 剪刀差：高分位年当年 {pct(sc.loc['大幅流入','sh_ret_mean'])}，次年 {pct(sc.loc['大幅流入','ret_next1_mean'])}。 |
| 行业资金？ | 当季跟涨、下季拥挤回撤。流入组下季超额 {pct(pooled.loc['大幅流入','exret_next'])}。季频轮动 {pct(rotq['mean'])}/季，年频轮动 {pct(roty['mean'])}/年。 |

![年度收益](reports/figures/annual_sse_returns.png)

![剪刀差](reports/figures/scissors_vs_return.png)

![季度分位](reports/figures/market_quintile_subsequent.png)

![行业拥挤](reports/figures/industry_pooled_buckets.png)

## 数据覆盖

- 上证综指 / 上证A指：1990-12-19 起
- 深证成指：1991-04-03 起
- 全A近似：上证A指拼接国证A指（2005）
- M1/M2：1990 年代起（早期为年末或低频）
- 公募基金规模：1998Q2 起
- 两融：2010-03-31 起
- IPO 募资：2010 起
- 北向净买入：2014-11-17 至 **2024-08-16**（之后源字段缺失）
- 申万一级：16 个行业 1999-12-30 起，其余多自 2014-02-21

复现：

```bash
python3 scripts/fetch_data.py
python3 scripts/analyze.py
python3 scripts/build_report.py
```
"""


def main() -> None:
    print("loading processed data")
    d = load()
    print("writing png figures")
    plot_pngs(d)
    print("writing plotly html")
    divs = plotly_divs(d)
    html = build_html(d, divs)
    (REPORTS / "ashare_capital_flow.html").write_text(html, encoding="utf-8")
    (ROOT / "REPORT.md").write_text(build_markdown(d), encoding="utf-8")
    print("wrote", REPORTS / "ashare_capital_flow.html")
    print("wrote", ROOT / "REPORT.md")


if __name__ == "__main__":
    main()
