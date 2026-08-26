# A股资金流动长周期分析

从 **1990 年上证开市** 起，按年度、季度考察全市场和申万一级行业在资金流入/流出期的当期表现与后续行情。

完整结论与交互图表：[reports/ashare_capital_flow.html](reports/ashare_capital_flow.html)  
摘要：[REPORT.md](REPORT.md)

## 主要发现

- 资金流与 **当期** 行情显著正相关（顺周期），与 **下一期** 基本无关，和随后一年甚至负相关。
- M1-M2 剪刀差是可追溯到 1990 年代的风险偏好代理：高分位年涨得多，次年转弱。
- 两融、北向是同步温度计，不是领先买点。
- 行业成交额占比上升当季跑赢、下季倾向拥挤回撤；年频份额迁移则有一定动量。

## 复现

```bash
python3 -m pip install -r requirements.txt
python3 scripts/fetch_data.py      # 下载公开行情/宏观/行业数据
python3 scripts/analyze.py         # 构建年度/季度面板与统计
python3 scripts/build_report.py    # 生成图表与 HTML/Markdown 报告
```

数据源：新浪/腾讯指数、东方财富（北向、IPO、基金）、乐咕乐股申万行业、央行货币统计。北向成交净买入在 2024-08-16 之后源字段缺失，报告中已标明。

处理后的面板在 `data/processed/`，原始缓存为 `data/raw/`。
