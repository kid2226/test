#!/usr/bin/env python3
"""Build annual/quarterly A-share capital-flow panels and performance stats."""

from __future__ import annotations

import json
import math
import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore", category=FutureWarning)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
FIG = ROOT / "reports" / "figures"
PROC.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

FOCUS_INDUSTRIES = [
    "银行",
    "非银金融",
    "房地产",
    "食品饮料",
    "医药生物",
    "电子",
    "计算机",
    "电力设备",
    "汽车",
    "煤炭",
    "有色金属",
    "石油石化",
    "国防军工",
    "通信",
    "家用电器",
    "基础化工",
    "机械设备",
    "交通运输",
]

LONG_INDUSTRIES = [
    "电子",
    "医药生物",
    "食品饮料",
    "房地产",
    "有色金属",
    "基础化工",
    "家用电器",
    "农林牧渔",
    "公用事业",
    "交通运输",
    "钢铁",
    "纺织服饰",
    "轻工制造",
    "商贸零售",
    "社会服务",
    "综合",
]

AS_OF = pd.Timestamp("2026-08-26")
LAST_COMPLETE_YEAR = 2025
LAST_COMPLETE_Q = pd.Period("2026Q2", freq="Q")


def _num(s) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def parse_cn_month(x) -> pd.Timestamp | pd.NaT:
    if pd.isna(x):
        return pd.NaT
    s = str(x).strip()
    m = re.search(r"(\d{4})\s*年\s*(\d{1,2})", s)
    if m:
        return pd.Timestamp(int(m.group(1)), int(m.group(2)), 1)
    m = re.match(r"(\d{4})\.(\d{1,2})", s)
    if m:
        return pd.Timestamp(int(m.group(1)), int(m.group(2)), 1)
    ts = pd.to_datetime(s, errors="coerce")
    if pd.isna(ts):
        return pd.NaT
    return pd.Timestamp(ts.year, ts.month, 1)


def compound(s: pd.Series, n: int) -> pd.Series:
    x = np.log1p(s)
    return np.expm1(sum(x.shift(-i) for i in range(1, n + 1)))


def zscore_expanding(s: pd.Series, min_periods: int = 12) -> pd.Series:
    mu = s.expanding(min_periods=min_periods).mean()
    sd = s.expanding(min_periods=min_periods).std()
    return (s - mu) / sd.replace(0, np.nan)


def label_quintile(s: pd.Series) -> pd.Series:
    q = pd.qcut(s.rank(method="first"), 5, labels=["大幅流出", "流出", "中性", "流入", "大幅流入"])
    return q.astype("object")


def ttest_mean(x: pd.Series) -> tuple[float, float]:
    x = x.dropna()
    if len(x) < 3:
        return float("nan"), float("nan")
    t, p = stats.ttest_1samp(x, 0.0)
    return float(t), float(p)


def mean_se(x: pd.Series) -> dict:
    x = x.dropna().astype(float)
    n = int(len(x))
    if n == 0:
        return {"n": 0, "mean": None, "median": None, "win": None, "t": None, "p": None}
    t, p = ttest_mean(x)
    return {
        "n": n,
        "mean": float(x.mean()),
        "median": float(x.median()),
        "win": float((x > 0).mean()),
        "t": t,
        "p": p,
    }


def load_index(symbol: str) -> pd.DataFrame:
    df = pd.read_parquet(RAW / f"index_{symbol}.parquet")
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date")[["date", "close", "volume"]].drop_duplicates("date")


def load_tx_amount(symbol: str) -> pd.DataFrame:
    df = pd.read_parquet(RAW / f"tx_{symbol}.parquet")
    df["date"] = pd.to_datetime(df["date"])
    df["amount_yi"] = _num(df["amount"]) / 1e5  # 千元 -> 亿元
    return df.sort_values("date")[["date", "amount_yi"]].drop_duplicates("date")


def spliced_alla() -> pd.DataFrame:
    """上证A指 (1990-2005) spliced onto 国证A指 (2005-)."""
    sh = load_index("sh000002").rename(columns={"close": "sh_a"})
    gz = load_index("sz399317").rename(columns={"close": "gz_a"})
    df = pd.merge(sh[["date", "sh_a"]], gz[["date", "gz_a"]], on="date", how="outer").sort_values("date")
    overlap = df.dropna(subset=["sh_a", "gz_a"])
    if overlap.empty:
        df["close"] = df["gz_a"].fillna(df["sh_a"])
        return df[["date", "close"]]
    scale = float(overlap.iloc[0]["sh_a"] / overlap.iloc[0]["gz_a"])
    df["close"] = np.where(df["gz_a"].notna(), df["gz_a"] * scale, df["sh_a"])
    return df.dropna(subset=["close"])[["date", "close"]]


def period_panel(daily: pd.DataFrame, close_col: str, freq: str) -> pd.DataFrame:
    g = daily.set_index("date").sort_index()
    close = g[close_col].resample(freq).last()
    out = pd.DataFrame({"close": close, "ret": close.pct_change()})
    if "amount_yi" in g.columns:
        out["amount_yi"] = g["amount_yi"].resample(freq).sum()
        out["amount_yoy"] = out["amount_yi"].pct_change(4 if freq.startswith("Q") else 1)
    return out


def load_money() -> pd.DataFrame:
    long = pd.read_parquet(RAW / "money_supply_long.parquet")
    df = pd.DataFrame(
        {
            "month": long["统计时间"].map(parse_cn_month),
            "m2": _num(long["货币和准货币（广义货币M2）"]),
            "m1": _num(long["货币(狭义货币M1)"]),
            "m2_yoy_off": _num(long["货币和准货币（广义货币M2）同比增长"]),
            "m1_yoy_off": _num(long["货币(狭义货币M1)同比增长"]),
        }
    ).dropna(subset=["month"]).drop_duplicates("month").sort_values("month")
    df["m1_yoy"] = df["m1_yoy_off"].fillna(df["m1"].pct_change(12) * 100)
    df["m2_yoy"] = df["m2_yoy_off"].fillna(df["m2"].pct_change(12) * 100)
    df["scissors"] = df["m1_yoy"] - df["m2_yoy"]
    return df


def load_credit() -> pd.DataFrame:
    raw = pd.read_parquet(RAW / "new_credit.parquet")
    df = pd.DataFrame(
        {
            "month": raw["月份"].map(parse_cn_month),
            "credit": _num(raw["当月"]),
            "credit_yoy": _num(raw["当月-同比增长"]),
        }
    ).dropna(subset=["month"]).sort_values("month")
    return df


def load_margin() -> pd.DataFrame:
    sh = pd.read_parquet(RAW / "margin_sh.parquet")
    sz = pd.read_parquet(RAW / "margin_sz.parquet")
    sh["date"] = pd.to_datetime(sh["日期"])
    sz["date"] = pd.to_datetime(sz["日期"])
    a = sh.rename(columns={"融资余额": "rz_sh", "融资买入额": "buy_sh"})[["date", "rz_sh", "buy_sh"]]
    b = sz.rename(columns={"融资余额": "rz_sz", "融资买入额": "buy_sz"})[["date", "rz_sz", "buy_sz"]]
    df = pd.merge(a, b, on="date", how="outer").sort_values("date")
    df["rz_yi"] = (_num(df["rz_sh"]).fillna(0) + _num(df["rz_sz"]).fillna(0)) / 1e8
    df["rz_buy_yi"] = (_num(df["buy_sh"]).fillna(0) + _num(df["buy_sz"]).fillna(0)) / 1e8
    return df[["date", "rz_yi", "rz_buy_yi"]]


def load_north() -> pd.DataFrame:
    df = pd.read_parquet(RAW / "hsgt_north.parquet")
    df["date"] = pd.to_datetime(df["日期"])
    df["north_yi"] = _num(df["当日成交净买额"])
    return df.dropna(subset=["date"])[["date", "north_yi"]].sort_values("date")


def load_ipo() -> pd.DataFrame:
    df = pd.read_parquet(RAW / "ipo_em.parquet")
    listed = pd.to_datetime(df["上市日期"], errors="coerce")
    apply = pd.to_datetime(df["申购日期"], errors="coerce")
    df = df.copy()
    df["date"] = listed.fillna(apply)
    df["ipo_yi"] = _num(df["发行总数"]) * _num(df["发行价格"]) / 1e4
    return df.dropna(subset=["date", "ipo_yi"])[["date", "ipo_yi", "股票代码", "股票简称"]]


def load_fund_new() -> pd.DataFrame:
    df = pd.read_parquet(RAW / "fund_new.parquet")
    df = df.copy()
    df["date"] = pd.to_datetime(df["成立日期"], errors="coerce")
    df["raise"] = _num(df["募集份额"])
    name = df["基金简称"].astype(str)
    df = df[~name.str.endswith("C") & ~name.str.endswith("C类")]
    equity = {"指数型-股票", "混合型-偏股", "股票型", "混合型-灵活", "混合型-平衡"}
    df["is_equity"] = df["基金类型"].isin(equity)
    return df.dropna(subset=["date"])


def load_fund_scale() -> pd.DataFrame:
    df = pd.read_parquet(RAW / "fund_scale_q.parquet")
    out = pd.DataFrame(
        {
            "date": pd.to_datetime(df["截止日期"]),
            "fund_n": _num(df["基金家数"]),
            "sub": _num(df["期间申购"]),
            "red": _num(df["期间赎回"]),
            "shares": _num(df["期末总份额"]),
            "aum": _num(df["期末净资产"]),
        }
    ).sort_values("date")
    out["fund_net"] = out["sub"] - out["red"]
    out["aum_chg"] = out["aum"].diff()
    return out


def load_pe_pb() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    pe = pd.read_parquet(RAW / "pe_hs300.parquet")
    pe = pe.rename(columns={"日期": "date", "滚动市盈率": "pe"})
    pe["date"] = pd.to_datetime(pe["date"])
    pb = pd.read_parquet(RAW / "pb_all.parquet")
    pb = pb.rename(columns={"middlePB": "pb"})
    pb["date"] = pd.to_datetime(pb["date"])
    pe_sh = pd.read_parquet(RAW / "pe_sh.parquet")
    pe_sh = pe_sh.rename(columns={"日期": "date", "平均市盈率": "pe_sh"})
    pe_sh["date"] = pd.to_datetime(pe_sh["date"])
    return pe[["date", "pe"]], pb[["date", "pb"]], pe_sh[["date", "pe_sh"]]


def resample_month_end(df: pd.DataFrame, value_cols: list[str], on: str, freq: str) -> pd.DataFrame:
    x = df.dropna(subset=[on]).set_index(on).sort_index()
    return x[value_cols].resample(freq).last()


def resample_sum(s: pd.Series, freq: str) -> pd.Series:
    return s.resample(freq).apply(lambda x: x.sum(min_count=1))


def build_market(freq: str) -> pd.DataFrame:
    sh = load_index("sh000001").rename(columns={"close": "sh_close"})
    sz = load_index("sz399001").rename(columns={"close": "sz_close"})
    hs = load_index("sh000300").rename(columns={"close": "hs_close"})
    gz = load_index("sz399317").rename(columns={"close": "gz_close"})
    cyb = load_index("sz399006").rename(columns={"close": "cyb_close"})
    alla = spliced_alla().rename(columns={"close": "alla_close"})

    amt_sh = load_tx_amount("sh000001").rename(columns={"amount_yi": "amt_sh"})
    amt_sz = load_tx_amount("sz399001").rename(columns={"amount_yi": "amt_sz"})
    amt = pd.merge(amt_sh, amt_sz, on="date", how="outer").sort_values("date")
    amt["amount_yi"] = amt["amt_sh"].fillna(0) + amt["amt_sz"].fillna(0)

    daily = sh.merge(sz[["date", "sz_close"]], on="date", how="left")
    daily = daily.merge(hs[["date", "hs_close"]], on="date", how="left")
    daily = daily.merge(gz[["date", "gz_close"]], on="date", how="left")
    daily = daily.merge(cyb[["date", "cyb_close"]], on="date", how="left")
    daily = daily.merge(alla, on="date", how="left")
    daily = daily.merge(amt[["date", "amount_yi"]], on="date", how="left")

    g = daily.set_index("date").sort_index()
    out = pd.DataFrame(
        {
            "sh_close": g["sh_close"].resample(freq).last(),
            "sz_close": g["sz_close"].resample(freq).last(),
            "hs_close": g["hs_close"].resample(freq).last(),
            "gz_close": g["gz_close"].resample(freq).last(),
            "cyb_close": g["cyb_close"].resample(freq).last(),
            "alla_close": g["alla_close"].resample(freq).last(),
            "amount_yi": g["amount_yi"].resample(freq).sum(),
        }
    )
    for col in ["sh", "sz", "hs", "gz", "cyb", "alla"]:
        out[f"{col}_ret"] = out[f"{col}_close"].pct_change()
    out["amount_yoy"] = out["amount_yi"].pct_change(4 if freq.startswith("Q") else 1)
    out.loc[out["amount_yi"] == 0, "amount_yi"] = np.nan

    money = load_money().set_index("month").sort_index()
    money_p = money[["m1_yoy", "m2_yoy", "scissors", "m1", "m2"]].resample(freq).last()
    out = out.join(money_p)

    credit = load_credit().set_index("month").sort_index()
    credit_p = credit[["credit", "credit_yoy"]].resample(freq).last()
    if freq.startswith("Q") or freq.startswith("Y"):
        credit_sum = resample_sum(credit["credit"], freq).rename("credit_sum")
        out = out.join(credit_p).join(credit_sum)
    else:
        out = out.join(credit_p)

    margin = load_margin().set_index("date").sort_index()
    out = out.join(margin[["rz_yi"]].resample(freq).last())
    out = out.join(resample_sum(margin["rz_buy_yi"], freq).rename("rz_buy_yi"))
    out["rz_chg"] = out["rz_yi"].diff()

    north = load_north().set_index("date").sort_index()
    out = out.join(resample_sum(north["north_yi"], freq).rename("north_yi"))

    ipo = load_ipo().set_index("date").sort_index()
    out = out.join(resample_sum(ipo["ipo_yi"], freq).rename("ipo_yi"))
    out = out.join(ipo.resample(freq).size().rename("ipo_n"))

    funds = load_fund_new().set_index("date").sort_index()
    eq = funds.loc[funds["is_equity"], "raise"]
    out = out.join(resample_sum(eq, freq).rename("eq_fund_raise"))
    out = out.join(funds.resample(freq).size().rename("fund_n_new"))

    fscale = load_fund_scale().set_index("date").sort_index()
    out = out.join(fscale[["fund_net", "aum", "aum_chg", "sub", "red"]].resample(freq).last())

    pe, pb, pe_sh = load_pe_pb()
    out = out.join(pe.set_index("date").sort_index().resample(freq).last())
    out = out.join(pb.set_index("date").sort_index().resample(freq).last())
    out = out.join(pe_sh.set_index("date").sort_index().resample(freq).last())

    # incremental capital where observable (亿元)
    inc = out["rz_chg"].copy()
    inc = inc.add(out["north_yi"], fill_value=0)
    inc = inc.add(out["eq_fund_raise"], fill_value=0)
    inc = inc.sub(out["ipo_yi"], fill_value=0)
    inc[out["rz_chg"].isna() & out["north_yi"].isna()] = np.nan
    out["inc_capital"] = inc

    # composite flow score from expanding z-scores of available components
    comps = {
        "z_scissors": out["scissors"],
        "z_m2": out["m2_yoy"],
        "z_credit": out["credit_yoy"],
        "z_turnover": out["amount_yoy"],
        "z_fundnet": out["fund_net"],
        "z_ipo": -out["ipo_yi"],
        "z_margin": out["rz_chg"],
        "z_north": out["north_yi"],
    }
    zcols = []
    minp = 8 if freq.startswith("Q") else 6
    for name, series in comps.items():
        out[name] = zscore_expanding(series, min_periods=minp)
        zcols.append(name)
    out["flow_score"] = out[zcols].mean(axis=1, skipna=True)
    out["flow_bucket"] = label_quintile(out["flow_score"])

    out["ret_next1"] = out["sh_ret"].shift(-1)
    out["ret_next2"] = compound(out["sh_ret"], 2)
    out["ret_next4"] = compound(out["sh_ret"], 4)
    out["alla_next1"] = out["alla_ret"].shift(-1)
    out["alla_next2"] = compound(out["alla_ret"], 2)
    out["alla_next4"] = compound(out["alla_ret"], 4)
    out["gz_next1"] = out["gz_ret"].shift(-1)
    out["gz_next4"] = compound(out["gz_ret"], 4)
    return out


def complete_mask(idx: pd.DatetimeIndex, freq: str) -> pd.Series:
    if freq.startswith("Q"):
        periods = idx.to_period("Q")
        return pd.Series(periods <= LAST_COMPLETE_Q, index=idx)
    return pd.Series(idx.year <= LAST_COMPLETE_YEAR, index=idx)


def bucket_stats(df: pd.DataFrame, ret_cols: list[str]) -> pd.DataFrame:
    rows = []
    for bucket, g in df.groupby("flow_bucket", dropna=True):
        row = {"flow_bucket": bucket, "n": int(len(g))}
        row["flow_score_mean"] = float(g["flow_score"].mean())
        row["sh_ret_mean"] = float(g["sh_ret"].mean()) if g["sh_ret"].notna().any() else None
        for c in ret_cols:
            st = mean_se(g[c])
            row[f"{c}_mean"] = st["mean"]
            row[f"{c}_win"] = st["win"]
            row[f"{c}_n"] = st["n"]
            row[f"{c}_t"] = st["t"]
            row[f"{c}_p"] = st["p"]
        rows.append(row)
    order = ["大幅流出", "流出", "中性", "流入", "大幅流入"]
    out = pd.DataFrame(rows)
    out["flow_bucket"] = pd.Categorical(out["flow_bucket"], order, ordered=True)
    return out.sort_values("flow_bucket")


def spread_stats(df: pd.DataFrame, ret_col: str) -> dict:
    top = df.loc[df["flow_bucket"] == "大幅流入", ret_col]
    bot = df.loc[df["flow_bucket"] == "大幅流出", ret_col]
    a, b = top.dropna(), bot.dropna()
    if len(a) < 3 or len(b) < 3:
        return {"spread": None, "t": None, "p": None, "n_top": int(len(a)), "n_bot": int(len(b))}
    t, p = stats.ttest_ind(a, b, equal_var=False)
    return {
        "spread": float(a.mean() - b.mean()),
        "t": float(t),
        "p": float(p),
        "n_top": int(len(a)),
        "n_bot": int(len(b)),
        "top_mean": float(a.mean()),
        "bot_mean": float(b.mean()),
        "top_win": float((a > 0).mean()),
        "bot_win": float((b > 0).mean()),
    }


def corr_pair(df: pd.DataFrame, x: str, y: str) -> dict:
    sub = df[[x, y]].dropna()
    if len(sub) < 8:
        return {"n": int(len(sub)), "corr": None, "p": None}
    r, p = stats.pearsonr(sub[x], sub[y])
    return {"n": int(len(sub)), "corr": float(r), "p": float(p)}


def build_industry(freq: str) -> pd.DataFrame:
    sw = pd.read_parquet(RAW / "sw_industries_daily.parquet")
    sw["date"] = pd.to_datetime(sw["日期"])
    sw["close"] = _num(sw["收盘"])
    sw["amount"] = _num(sw["成交额"])
    sw = sw.dropna(subset=["date", "close"])
    frames = []
    for name, g in sw.groupby("行业名称"):
        d = g.set_index("date").sort_index()
        p = pd.DataFrame(
            {
                "industry": name,
                "close": d["close"].resample(freq).last(),
                "amount": d["amount"].resample(freq).sum(),
            }
        )
        p["ret"] = p["close"].pct_change()
        frames.append(p.reset_index().rename(columns={"index": "date"}))
    ind = pd.concat(frames, ignore_index=True)
    tot = ind.groupby("date")["amount"].transform("sum")
    ind["share"] = ind["amount"] / tot.replace(0, np.nan)
    ind["share_chg"] = ind.groupby("industry")["share"].diff()
    ind["amount_yoy"] = ind.groupby("industry")["amount"].pct_change(4 if freq.startswith("Q") else 1)
    # excess vs equal-weight of industries present
    ew = ind.groupby("date")["ret"].transform("mean")
    ind["exret"] = ind["ret"] - ew
    ind["ret_next1"] = ind.groupby("industry")["ret"].shift(-1)
    ind["exret_next1"] = ind.groupby("industry")["exret"].shift(-1)
    ind["ret_next4"] = ind.groupby("industry", group_keys=False)["ret"].apply(lambda s: compound(s, 4))
    ind["exret_next4"] = ind.groupby("industry", group_keys=False)["exret"].apply(lambda s: compound(s, 4))
    # flow bucket within each date (cross-sectional)
    ind["flow_bucket"] = (
        ind.groupby("date")["share_chg"]
        .transform(lambda s: label_quintile(s) if s.notna().sum() >= 8 else pd.Series([np.nan] * len(s), index=s.index))
    )
    return ind


def industry_signal_table(ind: pd.DataFrame, complete: pd.Series) -> pd.DataFrame:
    d = ind.merge(complete.rename("ok"), left_on="date", right_index=True, how="left")
    d = d[d["ok"].fillna(False)]
    rows = []
    for name, g in d.groupby("industry"):
        g2 = g.dropna(subset=["share_chg", "exret_next1"])
        if len(g2) < 16:
            continue
        r1, p1 = stats.pearsonr(g2["share_chg"], g2["exret_next1"])
        r0, p0 = stats.pearsonr(g2.dropna(subset=["share_chg", "exret"])["share_chg"], g2.dropna(subset=["share_chg", "exret"])["exret"])
        top = g2.loc[g2["share_chg"] >= g2["share_chg"].quantile(0.8), "exret_next1"]
        bot = g2.loc[g2["share_chg"] <= g2["share_chg"].quantile(0.2), "exret_next1"]
        rows.append(
            {
                "industry": name,
                "n": int(len(g2)),
                "start": str(g2["date"].min().date()),
                "corr_now": float(r0),
                "corr_next": float(r1),
                "p_next": float(p1),
                "top_next_ex": float(top.mean()) if len(top) else None,
                "bot_next_ex": float(bot.mean()) if len(bot) else None,
                "spread_next": float(top.mean() - bot.mean()) if len(top) and len(bot) else None,
            }
        )
    return pd.DataFrame(rows).sort_values("corr_next")


def rotation_backtest(ind: pd.DataFrame) -> pd.DataFrame:
    """Equal-weight next-period return of top vs bottom flow industries each date."""
    rows = []
    for dt, g in ind.groupby("date"):
        g = g.dropna(subset=["share_chg", "ret_next1"])
        if len(g) < 8:
            continue
        k = max(3, len(g) // 5)
        top = g.nlargest(k, "share_chg")
        bot = g.nsmallest(k, "share_chg")
        rows.append(
            {
                "date": dt,
                "top_ret": float(top["ret_next1"].mean()),
                "bot_ret": float(bot["ret_next1"].mean()),
                "spread": float(top["ret_next1"].mean() - bot["ret_next1"].mean()),
                "top_ex": float(top["exret_next1"].mean()),
                "bot_ex": float(bot["exret_next1"].mean()),
                "n": int(len(g)),
            }
        )
    return pd.DataFrame(rows).sort_values("date")


def extreme_years(annual: pd.DataFrame, n: int = 8) -> pd.DataFrame:
    d = annual.dropna(subset=["flow_score", "sh_ret"]).copy()
    d = d[d.index.year <= LAST_COMPLETE_YEAR]
    top = d.nlargest(n, "flow_score")
    bot = d.nsmallest(n, "flow_score")
    top["kind"] = "流入年份"
    bot["kind"] = "流出年份"
    out = pd.concat([top, bot])
    keep = [
        "kind",
        "flow_score",
        "sh_ret",
        "alla_ret",
        "ret_next1",
        "alla_next1",
        "scissors",
        "m2_yoy",
        "amount_yoy",
        "north_yi",
        "rz_chg",
        "ipo_yi",
        "eq_fund_raise",
        "inc_capital",
        "pe",
        "pb",
    ]
    return out[keep]


def fmt_pct(x) -> str:
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "—"
    return f"{x * 100:.1f}%"


def main() -> None:
    print("building quarterly / annual market panels")
    quarterly = build_market("QE")
    annual = build_market("YE")
    q_ok = complete_mask(quarterly.index, "QE")
    y_ok = complete_mask(annual.index, "YE")

    quarterly.index.name = "date"
    annual.index.name = "date"
    quarterly.to_csv(PROC / "quarterly_market.csv")
    annual.to_csv(PROC / "annual_market.csv")
    quarterly.to_parquet(PROC / "quarterly_market.parquet")
    annual.to_parquet(PROC / "annual_market.parquet")

    q_use = quarterly.loc[q_ok].copy()
    y_use = annual.loc[y_ok].copy()
    # subsequent 1 period needs next period complete
    q_pred = q_use.copy()
    q_pred.loc[q_pred.index.to_period("Q") >= LAST_COMPLETE_Q, ["ret_next1", "alla_next1", "gz_next1"]] = np.nan
    y_pred = y_use.copy()
    y_pred.loc[y_pred.index.year >= LAST_COMPLETE_YEAR, ["ret_next1", "alla_next1"]] = np.nan

    q_buckets = bucket_stats(q_pred.dropna(subset=["flow_bucket"]), ["ret_next1", "ret_next4", "alla_next1", "alla_next4", "sh_ret"])
    y_buckets = bucket_stats(y_pred.dropna(subset=["flow_bucket"]), ["ret_next1", "alla_next1", "sh_ret"])
    q_buckets.to_csv(PROC / "quarterly_bucket_stats.csv", index=False)
    y_buckets.to_csv(PROC / "annual_bucket_stats.csv", index=False)

    def component_buckets(df: pd.DataFrame, col: str, prefix: str) -> pd.DataFrame:
        x = df.dropna(subset=[col, "sh_ret"]).copy()
        rank_col = -x[col] if col == "ipo_yi" else x[col]
        x["flow_bucket"] = label_quintile(rank_col)
        stats_df = bucket_stats(
            x,
            ["ret_next1", "ret_next4", "alla_next1", "sh_ret"]
            if "ret_next4" in x.columns
            else ["ret_next1", "alla_next1", "sh_ret"],
        )
        stats_df.insert(0, "component", col)
        stats_df.insert(0, "freq", prefix)
        return stats_df

    comp_rows = []
    for col in ["scissors", "amount_yoy", "rz_chg", "north_yi", "inc_capital", "ipo_yi", "m2_yoy"]:
        if col in q_pred.columns:
            comp_rows.append(component_buckets(q_pred, col, "quarterly"))
        if col in y_pred.columns:
            comp_rows.append(component_buckets(y_pred, col, "annual"))
    pd.concat(comp_rows, ignore_index=True).to_csv(PROC / "component_bucket_stats.csv", index=False)

    print("building industry panels")
    ind_q = build_industry("QE")
    ind_y = build_industry("YE")
    ind_q.to_parquet(PROC / "quarterly_industry.parquet")
    ind_y.to_parquet(PROC / "annual_industry.parquet")
    ind_q.to_csv(PROC / "quarterly_industry.csv", index=False)
    ind_y.to_csv(PROC / "annual_industry.csv", index=False)

    q_complete = complete_mask(pd.DatetimeIndex(ind_q["date"].unique()), "QE")
    y_complete = complete_mask(pd.DatetimeIndex(ind_y["date"].unique()), "YE")
    ind_q_sig = industry_signal_table(ind_q, q_complete)
    ind_y_sig = industry_signal_table(ind_y, y_complete)
    ind_q_sig.to_csv(PROC / "industry_quarterly_signal.csv", index=False)
    ind_y_sig.to_csv(PROC / "industry_annual_signal.csv", index=False)

    rot_q = rotation_backtest(ind_q[ind_q["date"].isin(q_complete[q_complete].index)])
    rot_y = rotation_backtest(ind_y[ind_y["date"].isin(y_complete[y_complete].index)])
    rot_q.to_csv(PROC / "industry_quarterly_rotation.csv", index=False)
    rot_y.to_csv(PROC / "industry_annual_rotation.csv", index=False)

    extremes = extreme_years(annual, n=8)
    extremes.to_csv(PROC / "extreme_years.csv")

    # Cross-section flow buckets for industries (pooled)
    ind_q2 = ind_q.merge(q_complete.rename("ok"), left_on="date", right_index=True, how="left")
    ind_q2 = ind_q2[ind_q2["ok"].fillna(False) & ind_q2["flow_bucket"].notna()]
    # drop last complete quarter for next-period stats
    last_q_ts = pd.Period(LAST_COMPLETE_Q, freq="Q").to_timestamp(how="end").normalize()
    pooled_rows = []
    for bucket, g in ind_q2.groupby("flow_bucket"):
        st0 = mean_se(g["exret"])
        st1 = mean_se(g.loc[g["date"] < last_q_ts, "exret_next1"])
        pooled_rows.append(
            {
                "flow_bucket": bucket,
                "n": int(len(g)),
                "exret_now": st0["mean"],
                "exret_now_win": st0["win"],
                "exret_next": st1["mean"],
                "exret_next_win": st1["win"],
                "exret_next_t": st1["t"],
                "exret_next_p": st1["p"],
            }
        )
    pooled = pd.DataFrame(pooled_rows)
    order = ["大幅流出", "流出", "中性", "流入", "大幅流入"]
    pooled["flow_bucket"] = pd.Categorical(pooled["flow_bucket"], order, ordered=True)
    pooled = pooled.sort_values("flow_bucket")
    pooled.to_csv(PROC / "industry_pooled_buckets.csv", index=False)

    findings = {
        "as_of": str(AS_OF.date()),
        "last_complete_year": LAST_COMPLETE_YEAR,
        "last_complete_quarter": str(LAST_COMPLETE_Q),
        "sample": {
            "sse_start": "1990-12-19",
            "szse_start": "1991-04-03",
            "alla_splice": "上证A指(1990) + 国证A指(2005)",
            "sw_long_n": 16,
            "sw_long_start": "1999-12-30",
            "sw_full_start": "2014-02-21",
            "north_start": "2014-11-17",
            "margin_start": "2010-03-31",
            "ipo_start": "2010-01",
            "fund_scale_start": "1998-06",
        },
        "annual": {
            "n": int(y_pred["flow_score"].notna().sum()),
            "corr_flow_now": corr_pair(y_pred, "flow_score", "sh_ret"),
            "corr_flow_next": corr_pair(y_pred, "flow_score", "ret_next1"),
            "corr_scissors_now": corr_pair(y_pred, "scissors", "sh_ret"),
            "corr_scissors_next": corr_pair(y_pred, "scissors", "ret_next1"),
            "corr_inc_now": corr_pair(y_pred, "inc_capital", "sh_ret"),
            "corr_inc_next": corr_pair(y_pred, "inc_capital", "ret_next1"),
            "spread_next_sh": spread_stats(y_pred, "ret_next1"),
            "spread_now_sh": spread_stats(y_pred, "sh_ret"),
            "spread_next_alla": spread_stats(y_pred, "alla_next1"),
        },
        "quarterly": {
            "n": int(q_pred["flow_score"].notna().sum()),
            "corr_flow_now": corr_pair(q_pred, "flow_score", "sh_ret"),
            "corr_flow_next": corr_pair(q_pred, "flow_score", "ret_next1"),
            "corr_scissors_now": corr_pair(q_pred, "scissors", "sh_ret"),
            "corr_scissors_next": corr_pair(q_pred, "scissors", "ret_next1"),
            "corr_north_now": corr_pair(q_pred, "north_yi", "sh_ret"),
            "corr_north_next": corr_pair(q_pred, "north_yi", "ret_next1"),
            "corr_margin_now": corr_pair(q_pred, "rz_chg", "sh_ret"),
            "corr_margin_next": corr_pair(q_pred, "rz_chg", "ret_next1"),
            "corr_inc_now": corr_pair(q_pred, "inc_capital", "sh_ret"),
            "corr_inc_next": corr_pair(q_pred, "inc_capital", "ret_next1"),
            "spread_next_sh": spread_stats(q_pred, "ret_next1"),
            "spread_next4_sh": spread_stats(q_pred, "ret_next4"),
            "spread_now_sh": spread_stats(q_pred, "sh_ret"),
            "spread_next_alla": spread_stats(q_pred, "alla_next1"),
        },
        "rotation_q": mean_se(rot_q["spread"]) if len(rot_q) else {},
        "rotation_y": mean_se(rot_y["spread"]) if len(rot_y) else {},
        "focus_industries": FOCUS_INDUSTRIES,
        "long_industries": LONG_INDUSTRIES,
    }
    (PROC / "findings.json").write_text(json.dumps(findings, ensure_ascii=False, indent=2), encoding="utf-8")

    # compact annual table for the report
    annual_out = y_use.reset_index()
    annual_out["year"] = annual_out["date"].dt.year
    cols = [
        "year",
        "sh_ret",
        "alla_ret",
        "sz_ret",
        "hs_ret",
        "flow_score",
        "flow_bucket",
        "scissors",
        "m1_yoy",
        "m2_yoy",
        "amount_yi",
        "amount_yoy",
        "north_yi",
        "rz_chg",
        "ipo_yi",
        "eq_fund_raise",
        "inc_capital",
        "pe",
        "pb",
        "ret_next1",
        "alla_next1",
    ]
    annual_out[cols].to_csv(PROC / "annual_market_view.csv", index=False)

    q_out = q_use.reset_index()
    q_out["quarter"] = q_out["date"].dt.to_period("Q").astype(str)
    qcols = [
        "quarter",
        "sh_ret",
        "alla_ret",
        "flow_score",
        "flow_bucket",
        "scissors",
        "m2_yoy",
        "amount_yoy",
        "north_yi",
        "rz_chg",
        "ipo_yi",
        "inc_capital",
        "ret_next1",
        "ret_next4",
        "alla_next1",
    ]
    q_out[qcols].to_csv(PROC / "quarterly_market_view.csv", index=False)
    print("processed tables written to", PROC)


if __name__ == "__main__":
    main()
