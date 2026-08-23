# 中美债券市场、利率与央行货币政策研究报告

本目录包含一份关于中美国债市场、收益率曲线形态（牛陡 / 熊陡 / 牛平 / 熊平）与央行货币政策的系统性研究报告，以及用于复现图表的数据和脚本。

## 阅读

主报告（中文）：

- [研究报告_中美债券市场利率与货币政策.md](./研究报告_中美债券市场利率与货币政策.md)

报告结合 2026 年 8 月前后的官方利率数据，重点解释：

- 熊陡、牛陡、熊平、牛平的定义与识别；
- 美国 2023 年深度倒挂之后、2026 年 7–8 月由长端主导的熊陡；
- 中国低利率环境下“中短端偏牛、超长端相对偏熊”的结构分化；
- 美联储与中国人民银行对短端、长端的不同影响力。

## 图表

图表位于 [`charts/`](./charts/)，由 [`scripts/generate_charts.py`](./scripts/generate_charts.py) 生成。

```bash
python3 -m pip install matplotlib pandas numpy
python3 bond-market-report/scripts/generate_charts.py
```

输入数据：

- `data/fred_ust_yields.csv`：FRED DGS2 / DGS10 / DGS30 / T10Y2Y
- `data/fred_tips_breakeven.csv`：FRED T10YIE / DFII10 / DFII30

## 免责声明

报告仅供研究讨论，不构成投资建议。
