#!/usr/bin/env python3
"""Download long-history A-share market, flow, macro and industry series."""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

SW_INDUSTRIES = {
    "801010": "农林牧渔",
    "801030": "基础化工",
    "801040": "钢铁",
    "801050": "有色金属",
    "801080": "电子",
    "801110": "家用电器",
    "801120": "食品饮料",
    "801130": "纺织服饰",
    "801140": "轻工制造",
    "801150": "医药生物",
    "801160": "公用事业",
    "801170": "交通运输",
    "801180": "房地产",
    "801200": "商贸零售",
    "801210": "社会服务",
    "801230": "综合",
    "801710": "建筑材料",
    "801720": "建筑装饰",
    "801730": "电力设备",
    "801740": "国防军工",
    "801750": "计算机",
    "801760": "传媒",
    "801770": "通信",
    "801780": "银行",
    "801790": "非银金融",
    "801880": "汽车",
    "801890": "机械设备",
    "801950": "煤炭",
    "801960": "石油石化",
    "801970": "环保",
    "801980": "美容护理",
}

SINA_INDICES = {
    "sh000001": "上证综指",
    "sh000002": "上证A指",
    "sz399001": "深证成指",
    "sz399107": "深证A指",
    "sz399317": "国证A指",
    "sh000300": "沪深300",
    "sh000905": "中证500",
    "sh000016": "上证50",
    "sz399006": "创业板指",
    "sh000688": "科创50",
    "sh000852": "中证1000",
    "sz399330": "深证100",
}


def retry(fn, retries: int = 4, sleep: float = 2.0):
    last = None
    for i in range(retries):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            last = exc
            wait = sleep * (2**i)
            print(f"  retry {i + 1}/{retries} after {type(exc).__name__}: {exc} (sleep {wait:.0f}s)")
            time.sleep(wait)
    raise last


def save(df: pd.DataFrame, name: str) -> Path:
    path = RAW / f"{name}.parquet"
    df.to_parquet(path, index=False)
    print(f"saved {name}: {df.shape} -> {path}")
    return path


def cached(name: str) -> pd.DataFrame | None:
    path = RAW / f"{name}.parquet"
    if path.exists():
        df = pd.read_parquet(path)
        print(f"cache hit {name}: {df.shape}")
        return df
    return None


def fetch_sina_indices() -> None:
    import akshare as ak

    frames = []
    for symbol, name in SINA_INDICES.items():
        cache_name = f"index_{symbol}"
        df = cached(cache_name)
        if df is None:
            print(f"fetch sina index {symbol} {name}")
            df = retry(lambda s=symbol: ak.stock_zh_index_daily(symbol=s))
            df = df.copy()
            df["symbol"] = symbol
            df["name"] = name
            df["date"] = pd.to_datetime(df["date"])
            save(df, cache_name)
        frames.append(df)
        time.sleep(0.4)
    all_idx = pd.concat(frames, ignore_index=True)
    save(all_idx, "indices_daily")


def fetch_tencent_turnover() -> None:
    import akshare as ak

    for symbol, name in [("sh000001", "上证综指"), ("sz399001", "深证成指")]:
        cache_name = f"tx_{symbol}"
        if cached(cache_name) is not None:
            continue
        print(f"fetch tencent amount {symbol}")
        df = retry(lambda s=symbol: ak.stock_zh_index_daily_tx(symbol=s))
        df = df.copy()
        df["symbol"] = symbol
        df["name"] = name
        df["date"] = pd.to_datetime(df["date"])
        save(df, cache_name)
        time.sleep(1)


def fetch_macro() -> None:
    import akshare as ak

    jobs = [
        ("money_supply", ak.macro_china_money_supply),
        ("money_supply_long", ak.macro_china_supply_of_money),
        ("new_credit", ak.macro_china_new_financial_credit),
        ("margin_sh", ak.macro_china_market_margin_sh),
        ("margin_sz", ak.macro_china_market_margin_sz),
        ("account_stats", ak.stock_account_statistics_em),
        ("pe_sh", lambda: ak.stock_market_pe_lg(symbol="上证")),
        ("pe_sz", lambda: ak.stock_market_pe_lg(symbol="深证")),
        ("pe_hs300", lambda: ak.stock_index_pe_lg(symbol="沪深300")),
        ("pb_sh", lambda: ak.stock_market_pb_lg(symbol="上证")),
        ("pb_sz", lambda: ak.stock_market_pb_lg(symbol="深证")),
        ("pb_all", ak.stock_a_all_pb),
        ("fund_scale_q", ak.fund_scale_change_em),
        ("fund_new", ak.fund_new_found_em),
        ("ipo_em", lambda: ak.stock_xgsglb_em(symbol="全部股票")),
        ("sw_first_info", ak.sw_index_first_info),
    ]
    for name, fn in jobs:
        if cached(name) is not None:
            continue
        print(f"fetch {name}")
        try:
            df = retry(fn)
            if df is None or len(df) == 0:
                print(f"  empty {name}")
                continue
            save(df, name)
        except Exception as exc:  # noqa: BLE001
            print(f"  GIVE UP {name}: {type(exc).__name__}: {exc}")
        time.sleep(0.8)


def fetch_hsgt() -> None:
    import akshare as ak

    for symbol in ["北向资金", "沪股通", "深股通", "南向资金"]:
        name = {
            "北向资金": "hsgt_north",
            "沪股通": "hsgt_sh",
            "深股通": "hsgt_sz",
            "南向资金": "hsgt_south",
        }[symbol]
        if cached(name) is not None:
            continue
        print(f"fetch {symbol}")
        try:
            df = retry(lambda s=symbol: ak.stock_hsgt_hist_em(symbol=s))
            save(df, name)
        except Exception as exc:  # noqa: BLE001
            print(f"  GIVE UP {name}: {type(exc).__name__}: {exc}")
        time.sleep(1)


def fetch_sw_industries() -> None:
    import akshare as ak

    frames = []
    for code, name in SW_INDUSTRIES.items():
        cache_name = f"sw_{code}"
        df = cached(cache_name)
        if df is None:
            print(f"fetch SW {code} {name}")
            try:
                df = retry(lambda c=code: ak.index_hist_sw(symbol=c, period="day"))
                df = df.copy()
                df["行业代码"] = code
                df["行业名称"] = name
                save(df, cache_name)
            except Exception as exc:  # noqa: BLE001
                print(f"  GIVE UP SW {code}: {type(exc).__name__}: {exc}")
                continue
            time.sleep(0.6)
        else:
            if "行业名称" not in df.columns:
                df = df.copy()
                df["行业代码"] = code
                df["行业名称"] = name
        frames.append(df)
    if frames:
        all_sw = pd.concat(frames, ignore_index=True)
        save(all_sw, "sw_industries_daily")


def main() -> None:
    print("== fetch A-share capital-flow inputs ==")
    fetch_sina_indices()
    fetch_macro()
    fetch_hsgt()
    fetch_sw_industries()
    fetch_tencent_turnover()
    print("done.")


if __name__ == "__main__":
    main()
