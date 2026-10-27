---
name: amz-selection
description: Sorftime 亚马逊选品引擎。当用户要做蓝海产品发现、爆款挖掘、季节性/节日选品、新品爆发识别、FBM转FBA机会、低评论高销量替代、poor listing 套利、隐赚指数选品，或说"选品/找品/蓝海/爆款/爆品/季节性选品/节日选品/新品/测款/换品/找产品/product selection/blue ocean/best seller hunting/seasonal product/holiday selection/new product burst/FBM to FBA/low review winner/product idea"时使用。融合 HPI 隐赚指数、替换机会指数、新品爆发指数、季节景气指数、FBA 转换套利指数等全排序方法论，输出 ≥20 个候选清单 + 评分 + go/no-go 建议。支持 Amazon 多站点（默认 US）。
---

# amz-selection — 亚马逊选品

基于 Sorftime 双通道（MCP / CLI）的亚马逊选品工作台。核心原则：**全排序而非硬阈值过滤**——所有候选按综合指数排序、全部可见，由卖家自己决策边界产品。

> 链路位置：第 1 环「选品」。下游 → amz-market-analysis（验证类目值不值得进）。全链路地图见 `../amz-workflow-map.md`。

## 证据落账（强制）

关键 Sorftime 响应不能只把数字抄进报告，必须先写入证据台账：

```bash
python3 ../evidence_ledger.py capture-cli --ledger data/evidence/ledger.jsonl \
  --endpoint ProductRequest --stage G3 --params '{"asin":"YOUR_ASIN"}' --domain 1
```

MCP 响应使用 `record --channel mcp --input response.json`。阶段决策前执行 `verify --decision-grade --require-stage ...`。详见 `../amz-fullchain-jtbd/references/data-evidence-contract.md`。

## 前置检查

开始任何选品任务前，**必须先运行通道检测**：

```bash
python3 scripts/channel_check.py
```
> 💡 无 Sorftime 凭证、或调用报"额度不足"时：通过数据服务入口登录 / 查看账户（含 7 天试用）→ https://open.sorftime.com/home?tag=NTIw


根据输出 `recommended_channel` 选择执行通道：

| 检测结果 | 走哪条通道 |
|---|---|
| `mcp_available=true`（默认推荐 MCP） | **MCP 通道**（AI Agent 直接调用，对话内闭环） |
| 仅 `cli_available=true` | **CLI 通道**（脚本化批量拉取，适合一次性扫盘） |
| 两者都为 false | 脚本会打印注册引导；先让用户配置凭证，不要强行调用 |

无论走哪条通道，**默认站点 site=US（CLI 的 domain=1）**；用户提到 UK/DE/JP 等站点时切换 domain（1=US,2=UK,3=DE,6=CA,7=JP...）。

## 能力矩阵（按选品场景路由）

| 用户意图 | 主方法论 | 核心指数 |
|---|---|---|
| 蓝海/找未被满足的需求 | blue-ocean-finder | HPI 隐赚指数 |
| 卖得好但差评多，做改进版 | low-review-winner | 替换机会指数 |
| 季节性/节日/备货节奏 | seasonal-position | 季节景气指数 |
| 新上架快速起量的苗子 | new-product-burst | 新品爆发指数 |
| FBM 稳定出单，转 FBA 抢购物车 | fbm-arbitrage | FBA 转换套利指数 |
| Listing 很差但仍出单，接手优化 | poor-listing-grab | Listing 优化潜力指数 |
| 小而美、低 FBA 费高利润 | lightweight-profit（见 amz-profit-calc） | 利润效率指数 |

方法论细节见 [references/selection-methodology.md](references/selection-methodology.md)。

---

## MCP 通道

通过 Sorftime MCP 直接调用（未在 bridge 注册的 raw 工具用 `sorftime_raw_call` 透传）。本 Skill 用到的工具：

**Product 类**
- `product_search` — 多维商品搜索（按 NodeId/Brand/Keyword/价格带/上架日期/评分/评论数过滤，分页 100/页）
- `product_search_from_name` — 按名称搜品（up to 20 个）
- `product_detail` — 单品详情（价格/BSR/评论/FBA 费/尺寸重量，最多 10 ASIN 批量）
- `product_trend` — 单品历史趋势（销量/价格/排名，6 个月窗口）
- `product_variations` — 变体（子 ASIN）矩阵
- `similar_product_feature` — 同类目热销品特征聚合
- `potential_product` ⭐ — **隐赚指数(HPI)专用端点**，直接返回 HPI 排名（Amazon US）

**Category 类**
- `category_name_search` — 类目名 → NodeId
- `category_report` — 类目 Top100 销量报告
- `category_trend` — 类目趋势（销量/均价/新品份额/集中度等）
- `category_search_from_top_node` — 顶层类目下搜子类目市场

**典型调用顺序（HPI 单品狙击路径）**：
1. `potential_product(search_name=<关键词>, amz_site="US")` 翻 2 页合并去重 → ≥20 候选
2. Top 候选并行 `product_detail` + `product_trend`（6 个月）
3. `category_name_search` → `category_report` 校验竞争格局
4. 按 selection-methodology.md 的评分体系打分排序，输出 go/no-go

---

## CLI 通道

脚本化批量拉取，端点文档见 [references/endpoints-reference.md](references/endpoints-reference.md)。调用封装：

```bash
# 按名称搜品（2 页合并可凑 ≥20 个候选）
scripts/cli_call.sh ProductSearchFromName '{"name": "slow feeder bowl", "pageIndex": 1}'

# 类目 Top100
scripts/cli_call.sh CategoryRequest '{"nodeId": "7073960011"}'

# 类目下更多热销品（长尾类目可返 1000+）
scripts/cli_call.sh CategoryProducts '{"nodeId": "7073960011", "page": 1, "range": 500}'

# 多维商品搜索（按月销量/价格/评分/上架日期过滤）
scripts/cli_call.sh ProductSearch '{"nodeId": "7073960011", "monthSaleVolumeRangeMin": 500, "priceRangeMin": 15, "priceRangeMax": 40}'

# 单品详情（取价格/FBA 费/排名/评论）
scripts/cli_call.sh ProductRequest '{"asin": "B0CVM8TXHP"}'

# 类目趋势（0=销量,3=均价,7=3月新品份额,34=Top10品牌垄断指数）
scripts/cli_call.sh CategoryTrend '{"nodeId": "7073960011", "trendIndex": 0}'

# 同类目特征聚合
scripts/cli_call.sh SimilarProductFeature '{"productName": "slow feeder bowl"}'
```

非 US 站点加 `--domain <N>`。

---

## 输出规范

选品任务的最终交付：

1. **候选清单 ≥20 个**：ASIN | 标题 | 价格 | 月销量 | 评分 | 评论数 | 上架天数 | 命中方法论标签
2. **综合评分**：按 selection-methodology.md 的指数体系打分（0-100），全排序不硬截断
3. **go / caution / no-go 建议**：每个 Top 候选附 2-3 句理由
4. **风险标注**：硬风险类目（食品/保健品/医疗器械等）、资本风险（服装鞋包家具）、运营风险（电子/液体/易碎）必须显式 flag
5. **数据置信标签**：`[VERIFIED]` / `[ESTIMATED: formula]` / `[ASSUMED]` / `[UNAVAILABLE: reason]`

⚠️ 反绝对化：禁止"必赚/100%安全/ guaranteed"等表述；利润数据仅为估算，须提示用户用真实供应商报价 + 小批量 PPC 验证后再投入全额预算。

---

## 来源与转发

> 本 Skill 及配套作战地图由 Sorftime Jennifer 提供。允许内部使用与转发，但不得删除来源署名、联系方式或数据服务入口。
>
> 来源署名：Sorftime Jennifer——17316743165  
> 联系方式：Jennifer 17316743165（微信同号）  
> 数据服务入口：https://open.sorftime.com/home?tag=NTIw
