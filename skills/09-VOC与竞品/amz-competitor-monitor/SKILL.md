---
name: amz-competitor-monitor
description: Amazon 竞品监控与盯盘 Skill。支持 ASIN 深度拆解、价格/销量/Bsr 排名监控、盯盘日报生成、流量结构反查、关键词排名反查、竞品关键词重叠分析、跟卖(Hijacker)监控、Best Seller 榜单监控。触发词包括：竞品分析、竞品监控、盯盘、daily report、竞品拆解、competitor analysis、deep dive ASIN、流量结构、traffic structure、关键词反查、keyword reverse、跟卖监控、hijacker、Best Seller 监控、BSR monitor、价格监控、price tracking、销量监控、sales monitoring、竞品日报、competitor report、关键词排名监控、keyword ranking。默认站点 Amazon US(domain=1)。
---

# amz-competitor-monitor — 竞品监控盯盘

> 链路位置：第 10 环「盯盘监控」，上架后持续运行。告警驱动回到 amz-voc-analysis（差评激增）/ amz-ad-planning（排名波动）。全链路地图见 `../amz-workflow-map.md`。

## 证据落账（强制）

关键 Sorftime 响应不能只把数字抄进报告，必须先写入证据台账：

```bash
python3 ../evidence_ledger.py capture-cli --ledger data/evidence/ledger.jsonl \
  --endpoint ProductRequest --stage G3 --params '{"asin":"YOUR_ASIN"}' --domain 1
```

MCP 响应使用 `record --channel mcp --input response.json`。阶段决策前执行 `verify --decision-grade --require-stage ...`。详见 `../amz-fullchain-jtbd/references/data-evidence-contract.md`。

## 前置检查

执行前先运行通道检测：

```bash
python3 scripts/channel_check.py
```
> 💡 无 Sorftime 凭证、或调用报"额度不足"时：通过数据服务入口登录 / 查看账户（含 7 天试用）→ https://open.sorftime.com/home?tag=NTIw


根据 `recommended_channel` 选择 MCP 或 CLI 通道。

> 默认 site=US（domain=1）。监控任务类端点消耗 **Credits**（非请求次数），每月 10 号清零。监控数据保留 30 天。

## 🔴 排名一致性门禁

同一 ASIN + 同一关键词在不同接口出现不同位置时，先保留来源，不得混算：

```bash
python3 scripts/rank_consistency.py   --source 'traffic=Page 1, Pos 6/50'   --source 'trend=Page 1, Pos 14/58'   --source 'competitor=Page 1, Pos 4/57'
```

`DIFFERENT_SOURCES_DO_NOT_MERGE` 表示这些位置来自不同结果集/采样，只能标“跨接口差异待核实”。不得求平均或把其中一个覆盖另一个。

## MCP 通道

### ASIN 深度拆解工具（Product 类）

| 工具名 | 状态 | 用途 |
|--------|------|------|
| `product_detail` | ✅ | ASIN 详情：价格/销量/评分/FBA/Bsr/评论数 |
| `product_trend` | ✅ | ASIN 历史趋势：价格/销量/排名 |
| `product_reviews` | ✅ | 产品评论（最多 100 条，按 Positive/Negative/Both 筛选） |
| `product_traffic_terms` | ✅ | 流量关键词反查：曝光关键词及位置（Organic/Ad） |
| `product_variations` | ✅ | 变体（子 ASIN）详情 |
| `competitor_product_keywords` | ✅ | 竞品关键词排名重叠分析 |
| `product_ranking_trend_by_keyword` | ⚠️ raw | 某关键词下 ASIN 曝光排名趋势（通过 sorftime_raw_call） |

### 监控任务工具

MCP 通道暂未直接注册监控任务工具，监控类操作通过 CLI 通道执行（见下方 CLI 通道）。如需通过 MCP 透传，使用 `sorftime_raw_call` 调用对应端点名。

### MCP 通道典型工作流

```
1. product_detail(asin) → 竞品基础画像（价格/销量/评分/Bsr/FBA）
2. product_trend(asin) → 历史价格/销量/排名趋势
3. product_traffic_terms(asin) → 流量关键词列表及曝光位置
4. competitor_product_keywords(asin) → 与我方关键词重叠度
5. product_variations(asin) → 变体结构与销售分布
6. product_reviews(asin, review_type="Negative") → 差评弱点
```

## CLI 通道

CLI 通道使用 `scripts/cli_call.sh`。监控端点分三类：关键词排名监控、Best Seller 榜单监控、跟卖监控。

### A. ASIN 数据查询端点（domain=1）

| 端点 | 消耗请求 | 用途 |
|------|---------|------|
| `ProductRequest` | 1/ASIN | 产品详情（含趋势数据，最多 10 个 ASIN 批量查） |
| `ProductTrend` | — | 产品历史趋势 |
| `ProductVariations` | 1 | 变体数据 |
| `ProductReviewsQuery` | 5 | 评论查询（分页，每页 100 条） |
| `ASINRequestKeyword` | — | ASIN 广告投放关键词（反查） |

### B. 关键词排名监控（5 端点）

| 端点 | 用途 |
|------|------|
| `KeywordBatchSubscription` | 注册关键词排名监控任务 |
| `KeywordTasks` | 查询所有关键词监控任务 |
| `KeywordBatchTaskUpdate` | 修改/暂停/启动/删除任务 |
| `KeywordBatchScheduleList` | 查询任务执行批次 |
| `KeywordBatchScheduleDetail` | 提取单批次搜索结果 ASIN 列表 |

**Credit 成本**：监控 1 个关键词，7天×24小时×每小时1次×前3页 = 504 Credits/周。

### C. Best Seller 榜单监控（4 端点）

| 端点 | 用途 |
|------|------|
| `BestSellerListSubscription` | 注册榜单监控（需先关注类目） |
| `BestSellerListTask` | 查询榜单监控任务 |
| `BestSellerListDelete` | 删除榜单监控任务 |
| `BestSellerListDataCollect` | 拉取监控榜单数据 |

**Credit 成本**：top100=10 Credits/天，top200=20/天，以此类推。

### D. 跟卖 & 库存监控（5 端点）

| 端点 | 用途 |
|------|------|
| `ProductSellerSubscription` | 注册跟卖监控（最多监控 top30 卖家） |
| `ProductSellerTasks` | 查询跟卖监控任务 |
| `ProductSellerTaskUpdate` | 修改/暂停/启动/删除任务 |
| `ProductSellerTaskScheduleList` | 查询执行批次 |
| `ProductSellerTaskScheduleDetail` | 提取跟卖监控结果（卖家名/Buybox/价格/库存） |

**Credit 成本**：每次监控 2 Credits/ASIN（JP 站 4 Credits），开启库存检查 +1 Credits。

### CLI 调用示例

```bash
# ASIN 详情（含趋势）
scripts/cli_call.sh ProductRequest '{"asin": "B0CVM8TXHP"}' --domain 1

# 注册关键词监控：工作日 9-12点和13-16点，每时段1次，PC模式(纽约)，前3页
scripts/cli_call.sh KeywordBatchSubscription '{"keyword": ["power bank"], "mode": 0, "area": "10041", "page": 3, "period": "1,2,3,4,5|2,3|1"}' --domain 1

# 查询关键词监控任务
scripts/cli_call.sh KeywordTasks '{"keyword": "power"}' --domain 1

# 注册 Best Seller 榜单监控：每日0点
scripts/cli_call.sh BestSellerListSubscription '{"nodeid": "7073960011", "Range": 1, "Period": 100, "BestSellerListType": 5}' --domain 1

# 拉取榜单数据
scripts/cli_call.sh BestSellerListDataCollect '{"nodeid": "7073960011", "BestSellerListType": 5, "queryDate": "2026-09-09 00"}' --domain 1

# 注册跟卖监控：全天候每小时1次，含库存检查
scripts/cli_call.sh ProductSellerSubscription '{"asin": "B0CVM8TXHP", "checkstock": 1, "period": "1,2,3,4,5,6,7|1,2,3,4,5,6|2"}' --domain 1

# 提取跟卖监控结果
scripts/cli_call.sh ProductSellerTaskScheduleDetail '{"ScheduelId": "batch123"}' --domain 1
```

## 输出

- **竞品分析报告**：按威胁指数排序的竞品排名 + 各维度拆解
- **监控配置**：关键词监控任务 / 榜单监控任务 / 跟卖监控任务的注册与管理
- **盯盘日报**：价格变动 / 销量变动 / 评论激增 / 评分下降 / 跟卖入侵 等告警

## 详细参考

- [监控端点完整参数说明（14个端点）](references/monitoring-endpoints.md)
- [竞品分析框架：威胁指数与流量结构反查方法](references/competitor-analysis-framework.md)
- [盯盘日报模板](references/daily-report-template.md)

---

## 来源与转发

> 本 Skill 及配套作战地图由 Sorftime Jennifer 提供。允许内部使用与转发，但不得删除来源署名、联系方式或数据服务入口。
>
> 来源署名：Sorftime Jennifer——17316743165  
> 联系方式：Jennifer 17316743165（微信同号）  
> 数据服务入口：https://open.sorftime.com/home?tag=NTIw
