# 电动汽车电池市场投资分析

本目录是一份面向投资决策的电动汽车电池市场研究报告：拆开**主要参与者、技术趋势、供应链挑战**，并给出可跟踪的情景与指标。

## 阅读

主报告（中文）：

- [研究报告_电动汽车电池市场投资分析.md](./研究报告_电动汽车电池市场投资分析.md)

报告结合 2026 年 8 月前后的公开数据，重点回答：

- 谁在控制电芯、材料、资源和回收，谁的利润依赖政策；
- 磷酸铁锂、钠离子、半固态/全固态、CTP/CTC 与快充各自处在哪一阶段；
- 中游集中、欧美本地化成本、出口管制、回收时滞如何改变风险收益。

## 图表

图表位于 [`charts/`](./charts/)，由 [`scripts/generate_charts.py`](./scripts/generate_charts.py) 生成。

```bash
python3 -m pip install -r ev-battery-market-report/requirements.txt
python3 ev-battery-market-report/scripts/generate_charts.py
```

输入数据：

- `data/sne_market_share.csv`：SNE Research 2025 全年及 2026 年 1–5 月装机份额
- `data/bnef_pack_prices.csv`：BloombergNEF 电池包均价（摘录）

系统需提供中文字体（脚本默认 `WenQuanYi Micro Hei`）。

## 免责声明

报告仅供研究讨论，不构成投资建议。
