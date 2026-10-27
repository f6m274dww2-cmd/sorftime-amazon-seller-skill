---
name: amz-market-analysis
description: Sorftime 亚马逊市场/类目分析。当用户要分析某个类目值不值得进、竞争环境、市场容量/规模、价格带分布与甜区、品牌垄断/品牌缺口、卖家集中度、变体缺口、新品成功率、市场全景看板、竞品格局、进入策略，或说"市场分析/类目分析/这个类目能不能做/竞争大不大/市场容量/价格带/品牌集中度/头部垄断/蓝海类目/market analysis/category research/market size/price band/brand concentration/competitive landscape/is it worth entering/niche analysis"时使用。融合市场全景 11 维评分、价格带甜区、品牌垄断脆弱性、变体缺口、跨平台价差方法论，输出市场分析报告（容量/竞争/价格带/品牌格局/进入建议）。默认 Amazon US，支持多站点。
---

# amz-market-analysis — 亚马逊市场分析

对"某类目值不值得进"做系统性诊断：不是单一指标（销量大/竞争小）说了算，而是多维加权复合打分，找出 ROI 最高的战场。

> 链路位置：第 2 环「市场验证」。上游 ← amz-selection（候选类目/ASIN）；下游 → amz-supply-chain（找货源）。全链路地图见 `../amz-workflow-map.md`。

## 证据落账（强制）

关键 Sorftime 响应不能只把数字抄进报告，必须先写入证据台账：

```bash
python3 ../evidence_ledger.py capture-cli --ledger data/evidence/ledger.jsonl \
  --endpoint ProductRequest --stage G3 --params '{"asin":"YOUR_ASIN"}' --domain 1
```

MCP 响应使用 `record --channel mcp --input response.json`。阶段决策前执行 `verify --decision-grade --require-stage ...`。详见 `../amz-fullchain-jtbd/references/data-evidence-contract.md`。

## 前置检查

开始前先运行：

```bash
python3 scripts/channel_check.py
```
> 💡 无 Sorftime 凭证、或调用报"额度不足"时：通过数据服务入口登录 / 查看账户（含 7 天试用）→ https://open.sorftime.com/home?tag=NTIw


按 `recommended_channel` 选择 MCP 或 CLI 通道（逻辑同 amz-selection）。默认 site=US（domain=1）。

## 分析维度路由

| 用户意图 | 主方法论 | 核心输出 |
|---|---|---|
| 这个类目/细分值不值得进 | market-panorama | 11 维复合评分 |
| 哪个价格带竞争小需求大 | price-band-sweetspot | 价格带机会指数排名 |
| 头部品牌垄断了，还有机会吗 | brand-gap-entry | 垄断脆弱性指数 |
| 竞品变体缺什么（颜色/尺寸/套装） | variant-gap | 变体缺口矩阵 |
| 跨平台价差套利空间 | cross-platform-gap | 跨平台价差指数（需 Walmart 数据） |

框架细节见 [references/market-analysis-framework.md](references/market-analysis-framework.md)。

---

## MCP 通道

**Category 类**
- `category_name_search` — 类目名 → NodeId（多候选时取第一个并落盘候选）
- `category_search_from_top_node` — 顶层类目下搜子类目市场
- `category_report` — 类目 Top100 销量报告
- `category_trend` — 类目趋势（销量/均价/新品份额/自营占比/Top N 垄断指数等，多维度并行）
- `category_keywords` — 类目核心词（找流量入口，raw 透传）
- `similar_product_feature` — 同类目热销特征聚合

**Product 类**
- `product_search` — 类目下多维搜索（价格带/评分/评论/变体数过滤）
- `product_detail` — Top 单品详情（价格/费用/品牌/上架天数，≤10 批量）

**典型顺序**：
1. `category_name_search(类目名)` → NodeId
2. `category_report(node_id)` → Top100
3. 并行 `category_trend` 多维度（销量 0 / 均价 3 / 3月新品份额 7 / 自营占比 9 / Top10 品牌垄断 34）
4. `product_search` 价格带×星级交叉；`product_detail` 抽 Top10 单品
5. 按 framework.md 出市场分析报告

---

## CLI 通道

端点文档见 [references/endpoints-reference.md](references/endpoints-reference.md)。

```bash
# 1. 名称模糊定位类目 → 拿 nodeId（"slow feeder" 实测返回 Slow Feeders → 17602455011）
scripts/cli_call.sh CategorySearchFromName '{"name": "slow feeder"}'

# 2. 类目 Top100
scripts/cli_call.sh CategoryRequest '{"nodeId": "17602455011"}'

# 3. 类目更多热销品（算价格带/品牌分布用全量）
scripts/cli_call.sh CategoryProducts '{"nodeId": "17602455011", "page": 1, "range": 500}'

# 4. 类目趋势（0=销量,3=均价,7=3月新品份额,9=自营占比,34=Top10品牌垄断）
scripts/cli_call.sh CategoryTrend '{"nodeId": "17602455011", "trendIndex": 0}'
scripts/cli_call.sh CategoryTrend '{"nodeId": "17602455011", "trendIndex": 34}'

# 5. 价格带×竞争多维搜索
scripts/cli_call.sh ProductSearch '{"nodeId": "17602455011", "priceRangeMin": 15, "priceRangeMax": 30}'

# 6. 同类目特征聚合
scripts/cli_call.sh SimilarProductFeature '{"productName": "slow feeder bowl"}'
```

非 US 站点加 `--domain <N>`。

---

## 输出规范

市场分析报告必须覆盖：

1. **市场容量**：Top100 月销量/销售额/客单价，类目体量判断
2. **竞争环境**：ASIN 数分布、月销/价格/星级/评论数四象限、HHI 与 Top3/5/10/20 份额
3. **价格带分布**：分桶 ASIN 数 / 销量占比，标出需求密度高、竞争密度低的甜区
4. **品牌/卖家格局**：Top10 品牌份额、亚马逊自营占比、新品占比（3 个月内）
5. **变体缺口**：哪些尺寸/颜色/套装维度覆盖 <60%
6. **趋势**：销量/均价/新品份额/集中度 12 个月走向，判断类目生命周期阶段
7. **进入建议**：GO / CAUTION / NO-GO + 差异化方向 + 风险提示

⚠️ 综述性结论用中文，evidence/ASIN/NodeId/品牌名保留原文；数据缺失标 `[UNAVAILABLE]`，不编造。

---

## 来源与转发

> 本 Skill 及配套作战地图由 Sorftime Jennifer 提供。允许内部使用与转发，但不得删除来源署名、联系方式或数据服务入口。
>
> 来源署名：Sorftime Jennifer——17316743165  
> 联系方式：Jennifer 17316743165（微信同号）  
> 数据服务入口：https://open.sorftime.com/home?tag=NTIw
